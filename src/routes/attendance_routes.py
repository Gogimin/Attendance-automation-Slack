"""출석 체크 라우트"""

from flask import Blueprint, request, jsonify
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.attendance_service import AttendanceService
from src.utils.error_handler import safe_error_response
from src.utils.workspace_helper import validate_workspace_name
from src.workspace_manager import WorkspaceManager
from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler
from src.utils import parse_slack_thread_link, column_letter_to_index

attendance_bp = Blueprint('attendance', __name__)

# 워크스페이스 매니저 (싱글톤)
workspace_manager = WorkspaceManager()


@attendance_bp.route('/api/run-attendance', methods=['POST'])
@safe_error_response
def run_attendance():
    """
    출석 체크 실행

    Request Body:
        workspace (str): 워크스페이스 이름
        thread_ts (str): Thread TS 또는 Slack URL
        column (str, optional): 출석 열 (기본값: K)
        mark_absent (bool, optional): 미출석자 X 표시 여부 (기본값: True)
        send_thread_reply (bool, optional): 스레드 댓글 작성 여부 (기본값: True)
        send_dm (bool, optional): DM 전송 여부 (기본값: True)
        thread_user (str, optional): 스레드 작성자 User ID (DM 수신자)

    Returns:
        JSON: {
            success: True/False,
            result: {
                total_students: int,
                present: int,
                absent: int,
                matched_names: List[str],
                absent_names: List[str],
                unmatched_names: List[str],
                success_count: int,
                column: str,
                notifications: List[str]
            }
        }
    """
    data = request.json

    # 파라미터 추출
    workspace_name = data.get('workspace')
    thread_input = data.get('thread_ts')
    column_input = data.get('column', 'K').strip().upper()
    mark_absent = data.get('mark_absent', True)
    send_thread_reply = data.get('send_thread_reply', True)
    send_dm = data.get('send_dm', True)
    thread_user = data.get('thread_user')

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

    # 2. Thread TS 파싱
    thread_ts = parse_slack_thread_link(thread_input)
    if not thread_ts:
        return jsonify({
            'success': False,
            'error': 'Thread TS 형식이 올바르지 않습니다.'
        }), 400

    # 3. 열 변환
    column_index = column_letter_to_index(column_input)
    if column_index is None:
        return jsonify({
            'success': False,
            'error': '올바른 열 형식이 아닙니다. (A-Z만 가능)'
        }), 400

    # 4. Handler 생성
    slack_handler = SlackHandler(workspace.slack_bot_token)

    if not slack_handler.test_connection():
        return jsonify({
            'success': False,
            'error': '슬랙 연결에 실패했습니다.'
        }), 500

    sheets_handler = SheetsHandler(
        credentials_path=workspace.credentials_path,
        spreadsheet_id=workspace.spreadsheet_id,
        sheet_name=workspace.sheet_name
    )

    if not sheets_handler.connect() or not sheets_handler.test_connection():
        return jsonify({
            'success': False,
            'error': '구글 시트 연결에 실패했습니다.'
        }), 500

    # 5. Service 생성 및 실행
    service = AttendanceService(slack_handler, sheets_handler)

    try:
        duplicate_names = workspace.duplicate_names if hasattr(workspace, 'duplicate_names') else {}

        matched_names, absent_names, unmatched_names, success_count, summary = service.run_attendance_check(
            channel_id=workspace.slack_channel_id,
            thread_ts=thread_ts,
            column_index=column_index,
            name_column=workspace.name_column,
            start_row=workspace.start_row,
            mark_absent=mark_absent,
            duplicate_names=duplicate_names
        )
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    # 6. 알림 전송
    # notification_user_id를 우선 사용, 없으면 thread_user 사용
    dm_recipient = None
    if send_dm:
        notification_user_id = workspace._config.get('notification_user_id', '')
        if notification_user_id:
            dm_recipient = notification_user_id
            print(f"[INFO] notification_user_id 사용: {dm_recipient}")
        elif thread_user:
            # thread_user가 봇 ID가 아닌 경우만 사용
            if not (thread_user.startswith('B') or thread_user.startswith('U0SLACKBOT')):
                dm_recipient = thread_user
                print(f"[INFO] thread_user 사용: {dm_recipient}")
            else:
                print(f"[INFO] thread_user가 봇이므로 DM 전송 안 함: {thread_user}")

    notifications = service.send_notifications(
        channel_id=workspace.slack_channel_id,
        thread_ts=thread_ts,
        thread_user=dm_recipient,
        matched_names=matched_names,
        absent_names=absent_names,
        total_students=len(matched_names) + len(absent_names),
        column_name=column_input,
        send_thread_reply=send_thread_reply,
        send_dm=send_dm
    )

    # 7. 결과 반환
    return jsonify({
        'success': True,
        'result': {
            'total_students': len(matched_names) + len(absent_names),
            'present': len(matched_names),
            'absent': len(absent_names),
            'matched_names': matched_names,
            'absent_names': absent_names[:20],  # 최대 20명만
            'unmatched_names': unmatched_names,
            'success_count': success_count,
            'column': column_input,
            'notifications': notifications
        }
    })
