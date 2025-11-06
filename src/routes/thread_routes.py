"""스레드 관리 라우트"""

from flask import Blueprint, request, jsonify
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workspace_manager import WorkspaceManager
from src.slack_handler import SlackHandler
from src.utils.error_handler import safe_error_response

thread_bp = Blueprint('thread', __name__)

# 워크스페이스 매니저 (싱글톤)
workspace_manager = WorkspaceManager()


@thread_bp.route('/api/find-thread', methods=['POST'])
@safe_error_response
def find_thread():
    """최신 출석 스레드 자동 감지"""
    data = request.json
    workspace_name = data.get('workspace')

    workspace = workspace_manager.get_workspace(workspace_name)
    if not workspace:
        return jsonify({
            'success': False,
            'error': '워크스페이스를 찾을 수 없습니다.'
        }), 404

    slack_handler = SlackHandler(workspace.slack_bot_token)

    if not slack_handler.test_connection():
        return jsonify({
            'success': False,
            'error': '슬랙 연결에 실패했습니다.'
        }), 500

    thread_message = slack_handler.find_latest_attendance_thread(
        workspace.slack_channel_id
    )

    if not thread_message:
        return jsonify({
            'success': False,
            'error': '최신 출석 스레드를 찾을 수 없습니다.'
        }), 404

    return jsonify({
        'success': True,
        'thread_ts': thread_message['ts'],
        'thread_text': thread_message['text'][:100] + '...',
        'thread_user': thread_message.get('user', 'unknown')
    })
