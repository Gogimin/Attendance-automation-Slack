"""스케줄 관리 라우트"""

from flask import Blueprint, request, jsonify
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workspace_manager import WorkspaceManager
from src.utils.error_handler import safe_error_response

schedule_bp = Blueprint('schedule', __name__)

# 워크스페이스 매니저 (싱글톤)
workspace_manager = WorkspaceManager()

# restart_scheduler 함수는 app_flask.py에서 주입받음
_restart_scheduler = None


def set_restart_scheduler(func):
    """restart_scheduler 함수 주입"""
    global _restart_scheduler
    _restart_scheduler = func


@schedule_bp.route('/api/schedule/<workspace_name>', methods=['GET'])
@safe_error_response
def get_schedule(workspace_name):
    """워크스페이스 스케줄 조회"""
    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    return jsonify({
        'success': True,
        'schedule': workspace.auto_schedule or {},
        'notification_user_id': workspace.notification_user_id or ''
    })


@schedule_bp.route('/api/schedules/all', methods=['GET'])
@safe_error_response
def get_all_schedules():
    """모든 워크스페이스의 예약 현황 조회"""
    workspaces = workspace_manager.get_all_workspaces()
    result_schedules = []

    for workspace in workspaces:
        schedule_config = workspace.auto_schedule

        # enabled 여부와 관계없이 스케줄이 있으면 표시
        if schedule_config:
            schedules_list = schedule_config.get('schedules', [])
            enabled = schedule_config.get('enabled', False)

            # 스케줄 리스트가 비어있지 않을 때만 표시
            if schedules_list:
                for schedule_item in schedules_list:
                    result_schedules.append({
                        'workspace_name': workspace.display_name,
                        'folder_name': workspace.name,
                        'day': schedule_item.get('day', ''),
                        'create_thread_time': schedule_item.get('create_thread_time', ''),
                        'check_attendance_time': schedule_item.get('check_attendance_time', ''),
                        'check_attendance_column': schedule_item.get('check_attendance_column', ''),
                        'notification_user_id': workspace.notification_user_id or '',
                        'enabled': enabled
                    })

    return jsonify({
        'success': True,
        'schedules': result_schedules,
        'total': len(result_schedules)
    })


@schedule_bp.route('/api/schedule', methods=['POST'])
@safe_error_response
def save_schedule():
    """스케줄 저장"""
    data = request.json
    workspace_name = data.get('workspace')
    schedule = data.get('schedule')
    notification_user_id = data.get('notification_user_id', '')

    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    # 스케줄 저장
    if not workspace.save_schedule(schedule):
        return jsonify({
            'success': False,
            'error': '스케줄 저장에 실패했습니다.'
        }), 500

    # notification_user_id 저장
    workspace._config['notification_user_id'] = notification_user_id
    with open(workspace.config_file, 'w', encoding='utf-8') as f:
        json.dump(workspace._config, f, ensure_ascii=False, indent=2)

    # 스케줄러 재시작
    if _restart_scheduler:
        _restart_scheduler()

    return jsonify({
        'success': True,
        'message': '스케줄이 저장되었습니다.'
    })


@schedule_bp.route('/api/schedule/delete', methods=['POST'])
@safe_error_response
def delete_schedule():
    """특정 스케줄 아이템 삭제"""
    data = request.json
    workspace_name = data.get('workspace')
    schedule_index = data.get('schedule_index')  # 삭제할 스케줄의 인덱스

    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    schedule_config = workspace.auto_schedule
    if not schedule_config:
        return jsonify({
            'success': False,
            'error': '스케줄 설정이 없습니다.'
        }), 404

    schedules_list = schedule_config.get('schedules', [])

    if schedule_index < 0 or schedule_index >= len(schedules_list):
        return jsonify({
            'success': False,
            'error': '잘못된 스케줄 인덱스입니다.'
        }), 400

    # 스케줄 삭제
    deleted_schedule = schedules_list.pop(schedule_index)

    # 모든 스케줄이 삭제되면 enabled를 False로
    if not schedules_list:
        schedule_config['enabled'] = False

    # 저장
    if not workspace.save_schedule(schedule_config):
        return jsonify({
            'success': False,
            'error': '스케줄 저장에 실패했습니다.'
        }), 500

    # 스케줄러 재시작
    if _restart_scheduler:
        _restart_scheduler()

    return jsonify({
        'success': True,
        'message': '스케줄이 삭제되었습니다.',
        'deleted_schedule': deleted_schedule
    })


@schedule_bp.route('/api/schedule/toggle', methods=['POST'])
@safe_error_response
def toggle_schedule():
    """스케줄 활성화/비활성화 토글"""
    data = request.json
    workspace_name = data.get('workspace')

    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    schedule_config = workspace.auto_schedule
    if not schedule_config:
        return jsonify({
            'success': False,
            'error': '스케줄 설정이 없습니다.'
        }), 404

    # 활성화/비활성화 토글
    current_enabled = schedule_config.get('enabled', False)
    schedule_config['enabled'] = not current_enabled

    # 저장
    if not workspace.save_schedule(schedule_config):
        return jsonify({
            'success': False,
            'error': '스케줄 저장에 실패했습니다.'
        }), 500

    # 스케줄러 재시작
    if _restart_scheduler:
        _restart_scheduler()

    return jsonify({
        'success': True,
        'message': f'스케줄이 {"활성화" if schedule_config["enabled"] else "비활성화"}되었습니다.',
        'enabled': schedule_config['enabled']
    })
