"""과제 체크 라우트"""

from flask import Blueprint, request, jsonify
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.assignment_service import AssignmentService
from src.utils.error_handler import safe_error_response
from src.utils.workspace_helper import validate_workspace_name
from src.workspace_manager import WorkspaceManager
from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler
from src.utils import parse_slack_thread_link, column_letter_to_index

assignment_bp = Blueprint('assignment', __name__)

# 워크스페이스 매니저 (싱글톤)
workspace_manager = WorkspaceManager()


@assignment_bp.route('/api/run-assignment', methods=['POST'])
@safe_error_response
def run_assignment_check():
    """
    과제 체크 실행

    Request Body:
        workspace (str): 워크스페이스 이름
        thread_ts (str): Thread TS 또는 Slack URL
        column (str, optional): 과제 열 (기본값: D)
        mark_absent (bool, optional): 미제출자 X 표시 여부 (기본값: True)

    Returns:
        JSON: {
            success: True/False,
            result: {
                total_students: int,
                submitted: List[str],
                not_submitted: List[str],
                submitted_count: int,
                not_submitted_count: int,
                column: str,
                success_count: int
            }
        }
    """
    data = request.json

    # 파라미터 추출
    workspace_name = data.get('workspace')
    thread_input = data.get('thread_ts')
    column_input = data.get('column', 'D').strip().upper()
    mark_absent = data.get('mark_absent', True)

    # 1. 워크스페이스 검증
    if not validate_workspace_name(workspace_name):
        return jsonify({
            'success': False,
            'error': '유효하지 않은 워크스페이스 이름입니다.'
        }), 400

    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': f'{workspace_name} 워크스페이스를 찾을 수 없습니다.'
        }), 404

    # 2. 과제 채널 ID 확인
    assignment_channel_id = workspace.assignment_channel_id
    if not assignment_channel_id:
        return jsonify({
            'success': False,
            'error': '과제 채널 ID가 설정되지 않았습니다. config.json에 assignment_channel_id를 추가하세요.'
        }), 400

    # 3. Thread TS 파싱
    thread_ts = parse_slack_thread_link(thread_input)
    if not thread_ts:
        return jsonify({
            'success': False,
            'error': 'Thread TS 형식이 올바르지 않습니다.'
        }), 400

    # 4. 열 변환
    column_index = column_letter_to_index(column_input)
    if column_index is None:
        return jsonify({
            'success': False,
            'error': '올바른 열 형식이 아닙니다. (A-Z만 가능)'
        }), 400

    # 5. Handler 생성
    slack_handler = SlackHandler(workspace.slack_bot_token)

    if not slack_handler.test_connection():
        return jsonify({
            'success': False,
            'error': '슬랙 연결에 실패했습니다.'
        }), 500

    sheets_handler = SheetsHandler(
        credentials_path=workspace.credentials_path,
        spreadsheet_id=workspace.spreadsheet_id,
        sheet_name=workspace.assignment_sheet_name
    )

    if not sheets_handler.connect() or not sheets_handler.test_connection():
        return jsonify({
            'success': False,
            'error': '구글 시트 연결에 실패했습니다.'
        }), 500

    # 6. Service 생성 및 실행
    service = AssignmentService(slack_handler, sheets_handler)

    try:
        submitted_list, not_submitted_list, success_count = service.run_assignment_check(
            assignment_channel_id=assignment_channel_id,
            thread_ts=thread_ts,
            column_index=column_index,
            name_column=workspace.name_column,
            start_row=workspace.start_row,
            assignment_sheet_name=workspace.assignment_sheet_name,
            mark_absent=mark_absent
        )
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    # 7. 기록 저장
    service.save_history(
        workspace_path=workspace.path,
        thread_ts=thread_ts,
        thread_link=thread_input,
        column_name=column_input,
        submitted_list=submitted_list,
        not_submitted_list=not_submitted_list,
        total_students=len(submitted_list) + len(not_submitted_list)
    )

    # 8. 결과 반환
    return jsonify({
        'success': True,
        'result': {
            'total_students': len(submitted_list) + len(not_submitted_list),
            'submitted': submitted_list,
            'not_submitted': not_submitted_list,
            'submitted_count': len(submitted_list),
            'not_submitted_count': len(not_submitted_list),
            'column': column_input,
            'success_count': success_count
        }
    })


@assignment_bp.route('/api/assignment-history/<workspace_name>', methods=['GET'])
@safe_error_response
def get_assignment_history(workspace_name):
    """
    과제 체크 기록 조회

    Args:
        workspace_name: 워크스페이스 이름

    Query Parameters:
        limit (int, optional): 최대 조회 개수 (기본값: 20)

    Returns:
        JSON: {
            success: True/False,
            history: List[Dict]
        }
    """
    # 워크스페이스 검증
    if not validate_workspace_name(workspace_name):
        return jsonify({
            'success': False,
            'error': '유효하지 않은 워크스페이스 이름입니다.'
        }), 400

    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': f'{workspace_name} 워크스페이스를 찾을 수 없습니다.'
        }), 404

    # 조회 개수
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)  # 최대 100개

    # Service 생성 및 조회
    service = AssignmentService(None, None)  # Handler 불필요
    history = service.get_history(workspace.path, limit=limit)

    return jsonify({
        'success': True,
        'history': history
    })
