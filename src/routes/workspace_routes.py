"""워크스페이스 관리 라우트"""

from flask import Blueprint, request, jsonify
import sys
import json
import shutil
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workspace_manager import WorkspaceManager
from src.slack_handler import SlackHandler
from src.utils.workspace_helper import validate_workspace_name, safe_path_join
from src.utils.error_handler import safe_error_response

workspace_bp = Blueprint('workspace', __name__)

# 워크스페이스 매니저 (싱글톤)
workspace_manager = WorkspaceManager()


@workspace_bp.route('/api/workspaces', methods=['GET'])
@safe_error_response
def get_workspaces():
    """모든 워크스페이스 목록 반환"""
    workspaces = workspace_manager.get_all_workspaces()

    workspace_list = []
    for ws in workspaces:
        workspace_list.append({
            'name': ws.display_name,
            'folder_name': ws.name,
            'channel_id': ws.slack_channel_id,
            'spreadsheet_id': ws.spreadsheet_id,
            'sheet_name': ws.sheet_name
        })

    return jsonify({
        'success': True,
        'workspaces': workspace_list
    })


@workspace_bp.route('/api/workspaces/delete', methods=['POST'])
@safe_error_response
def delete_workspace():
    """워크스페이스 삭제"""
    data = request.json
    workspace_name = data.get('workspace_name')

    if not workspace_name:
        return jsonify({
            'success': False,
            'error': 'workspace_name 필드가 필요합니다.'
        }), 400

    # 🔒 보안: 워크스페이스 이름 검증 (경로 탐색 방어)
    if not validate_workspace_name(workspace_name):
        return jsonify({
            'success': False,
            'error': '유효하지 않은 워크스페이스 이름입니다. (경로 탐색 시도 감지)'
        }), 400

    # 🔒 보안: 안전한 경로 조합
    try:
        workspace_folder = safe_path_join(
            project_root / 'workspaces',
            workspace_name
        )
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'경로 검증 실패: {str(e)}'
        }), 400

    # 폴더가 존재하는지 확인
    if not workspace_folder.exists():
        return jsonify({
            'success': False,
            'error': f'{workspace_name} 워크스페이스를 찾을 수 없습니다.'
        }), 404

    # 폴더 삭제
    shutil.rmtree(workspace_folder)

    # 워크스페이스 매니저 리로드
    workspace_manager.reload()

    return jsonify({
        'success': True,
        'message': f'{workspace_name} 워크스페이스가 삭제되었습니다.'
    })


@workspace_bp.route('/api/workspaces/add', methods=['POST'])
@safe_error_response
def add_workspace():
    """새 워크스페이스 추가"""
    data = request.json

    # 필수 필드 확인
    required_fields = ['workspace_name', 'display_name', 'slack_bot_token',
                      'slack_channel_id', 'spreadsheet_id', 'credentials_json']

    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False,
                'error': f'{field} 필드가 필요합니다.'
            }), 400

    workspace_name = data['workspace_name'].strip()
    display_name = data['display_name'].strip()
    slack_bot_token = data['slack_bot_token'].strip()
    slack_channel_id = data['slack_channel_id'].strip()
    assignment_channel_id = data.get('assignment_channel_id', '').strip()
    spreadsheet_id = data['spreadsheet_id'].strip()
    sheet_name = data.get('sheet_name', 'Sheet1').strip()
    assignment_sheet_name = data.get('assignment_sheet_name', '과제실습 모니터링').strip()
    name_column = data.get('name_column', 'B').strip()
    start_row = int(data.get('start_row', 4))
    credentials_json = data['credentials_json']

    # 워크스페이스 폴더 경로
    workspace_folder = project_root / 'workspaces' / workspace_name

    # 폴더가 이미 존재하는지 확인
    if workspace_folder.exists():
        return jsonify({
            'success': False,
            'error': f'{workspace_name} 워크스페이스가 이미 존재합니다.'
        }), 400

    # 폴더 생성
    workspace_folder.mkdir(parents=True, exist_ok=True)

    # config.json 생성
    config = {
        "name": display_name,
        "slack_bot_token": slack_bot_token,
        "slack_channel_id": slack_channel_id,
        "assignment_channel_id": assignment_channel_id if assignment_channel_id else slack_channel_id,
        "spreadsheet_id": spreadsheet_id,
        "sheet_name": sheet_name,
        "assignment_sheet_name": assignment_sheet_name,
        "name_column": name_column if name_column.isalpha() else 1,
        "start_row": start_row,
        "notification_user_id": "",
        "auto_schedule": {
            "enabled": False,
            "schedules": [],
            "create_thread_message": "@channel\n📢 출석 스레드입니다.\n\n\"이름/출석했습니다\" 형식으로 댓글 달아주세요!",
            "check_completion_message": "[자동] 출석 체크를 완료했습니다.\n출석: {present}명 / 미출석: {absent}명",
            "auto_column_enabled": False,
            "start_column": "H",
            "end_column": "O"
        }
    }

    config_path = workspace_folder / 'config.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # credentials.json 생성
    credentials_path = workspace_folder / 'credentials.json'

    # credentials_json이 문자열이면 JSON 파싱, 딕셔너리면 그대로 사용
    if isinstance(credentials_json, str):
        credentials_data = json.loads(credentials_json)
    else:
        credentials_data = credentials_json

    with open(credentials_path, 'w', encoding='utf-8') as f:
        json.dump(credentials_data, f, ensure_ascii=False, indent=2)

    # 워크스페이스 매니저 리로드
    workspace_manager.reload()

    return jsonify({
        'success': True,
        'message': f'{display_name} 워크스페이스가 추가되었습니다.',
        'workspace_name': workspace_name
    })


@workspace_bp.route('/api/workspaces/edit/<workspace_name>', methods=['POST'])
@safe_error_response
def edit_workspace(workspace_name):
    """기존 워크스페이스 정보 수정"""
    data = request.json

    # 워크스페이스 확인
    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    # 수정 가능한 필드들
    display_name = data.get('display_name', '').strip()
    slack_channel_id = data.get('slack_channel_id', '').strip()
    assignment_channel_id = data.get('assignment_channel_id', '').strip()
    sheet_name = data.get('sheet_name', '').strip()
    assignment_sheet_name = data.get('assignment_sheet_name', '').strip()
    name_column = data.get('name_column', '').strip()
    start_row = data.get('start_row')
    notification_user_id = data.get('notification_user_id', '').strip()

    # config.json 업데이트
    if display_name:
        workspace._config['name'] = display_name

    if slack_channel_id:
        workspace._config['slack_channel_id'] = slack_channel_id

    if assignment_channel_id:
        workspace._config['assignment_channel_id'] = assignment_channel_id
    else:
        # 비어있으면 출석 채널과 동일하게 설정
        workspace._config['assignment_channel_id'] = workspace._config['slack_channel_id']

    if sheet_name:
        workspace._config['sheet_name'] = sheet_name

    if assignment_sheet_name:
        workspace._config['assignment_sheet_name'] = assignment_sheet_name

    if name_column:
        workspace._config['name_column'] = name_column

    if start_row is not None:
        workspace._config['start_row'] = int(start_row)

    # notification_user_id는 빈 값도 허용
    workspace._config['notification_user_id'] = notification_user_id

    # 파일 저장
    with open(workspace.config_file, 'w', encoding='utf-8') as f:
        json.dump(workspace._config, f, ensure_ascii=False, indent=2)

    # 워크스페이스 매니저 리로드
    workspace_manager.reload()

    return jsonify({
        'success': True,
        'message': '워크스페이스 정보가 업데이트되었습니다.',
        'updated_config': workspace._config
    })


@workspace_bp.route('/api/workspaces/info/<workspace_name>', methods=['GET'])
@safe_error_response
def get_workspace_info(workspace_name):
    """워크스페이스 상세 정보 가져오기"""
    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    return jsonify({
        'success': True,
        'workspace': {
            'name': workspace.name,
            'display_name': workspace.display_name,
            'slack_channel_id': workspace.slack_channel_id,
            'assignment_channel_id': workspace._config.get('assignment_channel_id', ''),
            'spreadsheet_id': workspace.spreadsheet_id,
            'sheet_name': workspace.sheet_name,
            'assignment_sheet_name': workspace._config.get('assignment_sheet_name', '과제실습 모니터링'),
            'name_column': workspace._config.get('name_column'),
            'start_row': workspace.start_row,
            'notification_user_id': workspace._config.get('notification_user_id', '')
        }
    })


@workspace_bp.route('/api/duplicate-names/<workspace_name>', methods=['GET'])
@safe_error_response
def get_duplicate_names(workspace_name):
    """특정 워크스페이스의 동명이인 정보 가져오기"""
    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    duplicate_names = workspace.duplicate_names if hasattr(workspace, 'duplicate_names') else {}

    return jsonify({
        'success': True,
        'duplicate_names': duplicate_names
    })


@workspace_bp.route('/api/duplicate-names/<workspace_name>', methods=['POST'])
@safe_error_response
def save_duplicate_names(workspace_name):
    """특정 워크스페이스의 동명이인 정보 저장 (이메일 → User ID 변환)"""
    data = request.json
    duplicate_names_with_email = data.get('duplicate_names', {})

    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    # Slack Handler 초기화
    slack_handler = SlackHandler(workspace.slack_bot_token)

    # 이메일 → User ID 변환
    duplicate_names_with_user_id = {}
    conversion_errors = []

    for group_name, persons in duplicate_names_with_email.items():
        duplicate_names_with_user_id[group_name] = []

        for person in persons:
            email = person.get('email', '')
            display_name = person.get('display_name', '')
            sheet_row = person.get('sheet_row')
            note = person.get('note', '')

            if not email:
                conversion_errors.append(f"{group_name} - {display_name}: 이메일이 없습니다.")
                continue

            # 이메일로 User ID 찾기
            user_id = slack_handler.get_user_id_by_email(email)

            if not user_id:
                conversion_errors.append(f"{group_name} - {email}: User ID를 찾을 수 없습니다.")
                continue

            duplicate_names_with_user_id[group_name].append({
                'email': email,  # 이메일도 함께 저장 (참고용)
                'user_id': user_id,
                'display_name': display_name,
                'sheet_row': sheet_row,
                'note': note
            })

    # 변환 오류가 있으면 경고와 함께 반환
    if conversion_errors:
        return jsonify({
            'success': False,
            'error': '일부 이메일을 User ID로 변환할 수 없습니다.',
            'details': conversion_errors
        }), 400

    # config.json 업데이트
    workspace._config['duplicate_names'] = duplicate_names_with_user_id
    with open(workspace.config_file, 'w', encoding='utf-8') as f:
        json.dump(workspace._config, f, ensure_ascii=False, indent=2)

    # 워크스페이스 매니저 리로드
    workspace_manager.reload()

    return jsonify({
        'success': True,
        'message': '동명이인 정보가 저장되었습니다.',
        'converted_data': duplicate_names_with_user_id
    })
