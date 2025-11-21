"""
슬랙 출석체크 자동화 - Flask 웹 애플리케이션
더블클릭으로 실행 가능한 독립 실행형 프로그램
"""
import sys
import webbrowser
import threading
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.workspace_manager import WorkspaceManager
from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler, AttendanceStatus
from src.parser import AttendanceParser
from src.assignment_parser import AssignmentParser
from src.utils import parse_slack_thread_link, column_letter_to_index, get_next_column, column_index_to_letter

# Blueprint import (리팩토링된 라우트)
from src.routes import (
    attendance_bp,
    assignment_bp,
    workspace_bp,
    schedule_bp,
    thread_bp
)
from src.utils.error_handler import register_error_handlers
import os
import secrets

# Flask 앱 초기화
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 한글 지원
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 템플릿 자동 리로드 (개발 모드)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 정적 파일 캐싱 비활성화 (개발 모드)

# 🔒 보안 설정
# Secret Key 설정 (세션 보호)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = False  # 로컬 개발 환경 (HTTPS 사용 시 True로 변경)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JS 접근 차단
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF 방어

# 에러 핸들러 등록
register_error_handlers(app)

# Blueprint 등록
app.register_blueprint(attendance_bp)
app.register_blueprint(assignment_bp)
app.register_blueprint(workspace_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(thread_bp)

# 워크스페이스 매니저 초기화
workspace_manager = WorkspaceManager()

# 스케줄러 초기화 (한국 시간대)
KST = pytz.timezone('Asia/Seoul')
scheduler = BackgroundScheduler(
    timezone=KST,
    job_defaults={
        'coalesce': False,  # 놓친 작업을 한 번에 실행하지 않음
        'max_instances': 1,  # 동시에 하나의 인스턴스만 실행
        'misfire_grace_time': 300  # 5분 이내 놓친 작업은 실행
    }
)


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """스케줄러 상태 조회"""
    try:
        jobs = scheduler.get_jobs()
        job_list = []

        for job in jobs:
            job_list.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return jsonify({
            'success': True,
            'running': scheduler.running,
            'jobs': job_list,
            'total_jobs': len(job_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# === 리팩토링 완료 ===
# 모든 API route는 src/routes/ 폴더의 Blueprint로 이동되었습니다:
# - attendance_routes.py: 출석 체크 관련 route
# - assignment_routes.py: 과제 체크 관련 route
# - workspace_routes.py: 워크스페이스 관리 route
# - schedule_routes.py: 스케줄 관리 route
# - thread_routes.py: 스레드 검색 route


def open_browser():
    """브라우저 자동 열기"""
    webbrowser.open('http://127.0.0.1:5000')


# === 스케줄러 관련 함수 ===

def create_attendance_thread_job(workspace, schedule_item):
    """출석 스레드 자동 생성 작업"""
    try:
        day = schedule_item.get('day', '')
        print(f"\n[자동실행] 출석 스레드 생성 시작 - {workspace.display_name} ({day})")
        print(f"시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")

        schedule_config = workspace.auto_schedule
        if not schedule_config or not schedule_config.get('enabled'):
            return

        slack_handler = SlackHandler(workspace.slack_bot_token)
        message = schedule_config.get('create_thread_message', '@channel\n📢 출석 스레드입니다.\n\n"이름/출석했습니다" 형식으로 댓글 달아주세요!')

        # 메시지 전송
        result = slack_handler.post_message(workspace.slack_channel_id, message)

        if result:
            thread_ts = result['ts']
            print(f"✓ 출석 스레드 생성 완료: {thread_ts}")

            # Thread TS 저장
            today = datetime.now(KST).strftime('%Y-%m-%d')
            check_column = schedule_item.get('check_attendance_column', '')
            if workspace.save_last_thread_info(thread_ts, today, check_column):
                print(f"✓ Thread TS 저장 완료 (날짜: {today}, 열: {check_column})")
            else:
                print(f"⚠ Thread TS 저장 실패")
        else:
            print(f"✗ 출석 스레드 생성 실패")

    except Exception as e:
        print(f"✗ 출석 스레드 생성 오류: {e}")
        import traceback
        traceback.print_exc()


def check_attendance_job(workspace, schedule_item):
    """출석 집계 자동 실행 작업"""
    try:
        day = schedule_item.get('day', '')
        check_column = schedule_item.get('check_attendance_column', 'K')

        print(f"\n[자동실행] 출석 집계 시작 - {workspace.display_name} ({day}, {check_column}열)")
        print(f"시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}")

        schedule_config = workspace.auto_schedule
        if not schedule_config or not schedule_config.get('enabled'):
            return

        # 1. 슬랙 연결
        slack_handler = SlackHandler(workspace.slack_bot_token)

        # 2. Hybrid 방식으로 출석 스레드 찾기
        thread_ts = None
        thread_user = None
        today = datetime.now(KST).strftime('%Y-%m-%d')

        # 2-1. 저장된 Thread TS 확인 (Option 3)
        last_thread_info = workspace.get_last_thread_info()
        if last_thread_info and last_thread_info.get('date') == today:
            thread_ts = last_thread_info.get('thread_ts')
            print(f"✓ 저장된 Thread TS 사용: {thread_ts} (날짜: {today})")
        else:
            # 2-2. 검색으로 찾기 (Option 1 - 봇 메시지만 필터링)
            print(f"⚠ 저장된 Thread TS 없음, 검색으로 찾기 시도...")
            thread_message = slack_handler.find_latest_attendance_thread(workspace.slack_channel_id, bot_only=True)
            if thread_message:
                thread_ts = thread_message['ts']
                thread_user = thread_message.get('user')
                print(f"✓ 검색으로 출석 스레드 발견: {thread_ts}")
            else:
                print("✗ 출석 스레드를 찾을 수 없습니다.")
                return

        if not thread_ts:
            print("✗ 출석 스레드를 찾을 수 없습니다.")
            return

        # 3. 댓글 수집
        replies = slack_handler.get_replies_with_user_info(workspace.slack_channel_id, thread_ts)
        if not replies:
            print("✗ 댓글을 가져올 수 없습니다.")
            return

        # 4. 출석 파싱 (동명이인 정보 전달)
        parser = AttendanceParser()
        duplicate_names = workspace.duplicate_names if hasattr(workspace, 'duplicate_names') else {}
        attendance_list = parser.parse_attendance_replies(replies, duplicate_names)

        if not attendance_list:
            print("✗ 출석한 학생이 없습니다.")
            return

        print(f"✓ 출석자 수: {len(attendance_list)}명")

        # 5. 구글 시트 연결
        sheets_handler = SheetsHandler(
            credentials_path=workspace.credentials_path,
            spreadsheet_id=workspace.spreadsheet_id,
            sheet_name=workspace.sheet_name
        )

        if not sheets_handler.connect() or not sheets_handler.test_connection():
            print("✗ 구글 시트 연결 실패")
            return

        # 6. 학생 명단 읽기
        students = sheets_handler.get_student_list(workspace.name_column, workspace.start_row)
        if not students:
            print("✗ 학생 명단을 읽을 수 없습니다.")
            return

        # 7. 출석 매칭
        # 스케줄 아이템에서 열 정보 가져오기
        column_input = check_column
        column_index = column_letter_to_index(column_input)

        # 자동 열 증가 모드 확인 (전역 설정)
        auto_column_enabled = schedule_config.get('auto_column_enabled', False)
        start_column = schedule_config.get('start_column', 'H')
        end_column = schedule_config.get('end_column', 'O')

        # 자동 열 증가가 활성화되어 있으면 다음 열로 이동
        if auto_column_enabled and start_column and end_column:
            print(f"📍 자동 열 증가 모드: {start_column} ~ {end_column}")
            print(f"   현재 열: {column_input}")

            # 끝 열에 도달했는지 확인
            if column_input == end_column:
                print(f"🎯 끝 열({end_column})에 도달했습니다. 해당 스케줄을 제거합니다.")

                # 해당 스케줄 아이템 제거
                schedules_list = schedule_config.get('schedules', [])
                updated_schedules = [s for s in schedules_list if not (s.get('day') == day and s.get('check_attendance_column') == check_column)]

                # 모든 스케줄이 제거되면 enabled를 False로
                if not updated_schedules:
                    schedule_config['enabled'] = False

                schedule_config['schedules'] = updated_schedules
                workspace.save_schedule(schedule_config)

                # 스케줄러에서 해당 작업 제거 (모든 인덱스)
                try:
                    # 해당 워크스페이스와 요일의 모든 작업 찾아서 제거
                    all_jobs = scheduler.get_jobs()
                    for job in all_jobs:
                        if (f'create_thread_{workspace.name}_{day}' in job.id or
                            f'check_attendance_{workspace.name}_{day}' in job.id):
                            scheduler.remove_job(job.id)
                    print(f"✓ 스케줄러에서 작업 제거 완료")
                except Exception as e:
                    print(f"⚠️ 스케줄러 작업 제거 중 오류 (무시 가능): {e}")

                # 관리자에게 완료 알림 전송
                notification_user = workspace.notification_user_id or thread_user
                if notification_user:
                    completion_message = f"""🎉 [출석체크 완료 알림]

📊 **{day} 출석체크가 완료되었습니다!**

✅ 시작 열: {start_column}
✅ 끝 열: {end_column}
✅ 마지막 실행 열: {column_input}

해당 요일의 자동 스케줄이 비활성화되었습니다.

워크스페이스: {workspace.display_name}
"""
                    slack_handler.send_dm(notification_user, completion_message)
                    print(f"✓ 완료 알림 DM 전송 완료")
            else:
                # 다음 실행을 위해 열 증가
                next_column = get_next_column(column_input, start_column, end_column)
                print(f"   다음 열: {next_column}")

                # 해당 스케줄 아이템의 열 업데이트
                schedules_list = schedule_config.get('schedules', [])
                for s in schedules_list:
                    if s.get('day') == day and s.get('check_attendance_column') == check_column:
                        s['check_attendance_column'] = next_column
                        break

                schedule_config['schedules'] = schedules_list
                workspace.save_schedule(schedule_config)

        updates = []
        matched_names = []
        unmatched_names = []

        for attendance in attendance_list:
            name = attendance['name']
            sheet_row = attendance.get('sheet_row')  # 동명이인인 경우 직접 지정된 행 번호

            # 동명이인으로 직접 행 번호가 지정된 경우
            if sheet_row is not None:
                updates.append({
                    'name': name,
                    'row': sheet_row,
                    'column': column_index,
                    'status': AttendanceStatus.PRESENT
                })
                matched_names.append(name)
            elif name in students:
                row = students[name]
                updates.append({
                    'name': name,
                    'row': row,
                    'column': column_index,
                    'status': AttendanceStatus.PRESENT
                })
                matched_names.append(name)
            else:
                unmatched_names.append(name)

        # 8. 미출석자 처리
        absent_names = [name for name in students.keys() if name not in matched_names]

        for name in absent_names:
            row = students[name]
            updates.append({
                'name': name,
                'row': row,
                'column': column_index,
                'status': AttendanceStatus.ABSENT
            })

        # 9. 업데이트
        success_count = sheets_handler.batch_update_attendance(updates)
        print(f"✓ 구글 시트 업데이트 완료: {success_count}개")

        # 10. 알림 전송
        notification_user = workspace.notification_user_id or thread_user

        # 스레드 댓글 (사용자 정의 메시지 또는 기본 메시지)
        completion_message_template = schedule_config.get('check_completion_message', '[자동] 출석 체크를 완료했습니다.\n출석: {present}명 / 미출석: {absent}명')
        completion_message = completion_message_template.format(
            present=len(matched_names),
            absent=len(absent_names),
            total=len(students)
        )

        slack_handler.post_thread_reply(
            workspace.slack_channel_id,
            thread_ts,
            completion_message
        )

        # DM 전송
        if notification_user:
            dm_message = f"""[자동 출석체크 완료 알림]

📅 열: {column_input}열
📊 총 인원: {len(students)}명
✅ 출석: {len(matched_names)}명 ({len(matched_names)/len(students)*100:.1f}%)
❌ 미출석: {len(absent_names)}명

📋 출석자: {', '.join(matched_names)}

⚠️ 미출석자 ({len(absent_names)}명):
"""
            for i, name in enumerate(absent_names[:50], 1):
                dm_message += f"{i}. {name}\n"

            if len(absent_names) > 50:
                dm_message += f"... 외 {len(absent_names) - 50}명"

            slack_handler.send_dm(notification_user, dm_message)

        print(f"✓ 출석 집계 완료!")

    except Exception as e:
        print(f"✗ 출석 집계 오류: {e}")
        import traceback
        traceback.print_exc()


def setup_scheduler():
    """스케줄러 설정"""
    # 한글 요일 → APScheduler 요일 코드 변환
    day_mapping = {
        '월요일': 'mon',
        '화요일': 'tue',
        '수요일': 'wed',
        '목요일': 'thu',
        '금요일': 'fri',
        '토요일': 'sat',
        '일요일': 'sun'
    }

    workspaces = workspace_manager.get_all_workspaces()

    for workspace in workspaces:
        schedule_config = workspace.auto_schedule

        if not schedule_config or not schedule_config.get('enabled'):
            continue

        schedules_list = schedule_config.get('schedules', [])

        if not schedules_list:
            continue

        print(f"\n📅 스케줄 등록: {workspace.display_name}")

        # 각 스케줄에 대해 작업 등록
        for idx, schedule_item in enumerate(schedules_list):
            day = schedule_item.get('day')
            create_time = schedule_item.get('create_thread_time')
            check_time = schedule_item.get('check_attendance_time')
            check_column = schedule_item.get('check_attendance_column')

            # 한글 요일을 영어로 변환
            day_en = day_mapping.get(day, day)  # 매핑 실패 시 원본 사용

            # 출석 스레드 생성 스케줄
            if day and create_time:
                try:
                    hour, minute = create_time.split(':')
                    job_id = f'create_thread_{workspace.name}_{day}_{idx}'
                    scheduler.add_job(
                        func=lambda ws=workspace, sched_item=schedule_item: create_attendance_thread_job(ws, sched_item),
                        trigger=CronTrigger(day_of_week=day_en, hour=int(hour), minute=int(minute), timezone=KST),
                        id=job_id,
                        replace_existing=True
                    )

                    print(f"  ✓ 출석 스레드 생성: 매주 {day} {create_time}")
                except Exception as e:
                    print(f"  ✗ 스케줄 등록 실패: {day} {create_time} - {e}")

            # 출석 집계 스케줄
            if day and check_time:
                try:
                    hour, minute = check_time.split(':')
                    job_id = f'check_attendance_{workspace.name}_{day}_{idx}'
                    scheduler.add_job(
                        func=lambda ws=workspace, sched_item=schedule_item: check_attendance_job(ws, sched_item),
                        trigger=CronTrigger(day_of_week=day_en, hour=int(hour), minute=int(minute), timezone=KST),
                        id=job_id,
                        replace_existing=True
                    )

                    print(f"  ✓ 출석 집계: 매주 {day} {check_time} (열: {check_column})")
                except Exception as e:
                    print(f"  ✗ 스케줄 등록 실패: {day} {check_time} - {e}")


def print_scheduler_status():
    """스케줄러 상태 출력 (scheduler.start() 이후에 호출해야 함)"""
    all_jobs = scheduler.get_jobs()
    print(f"\n✓ 총 {len(all_jobs)}개의 스케줄이 등록되었습니다")


def restart_scheduler():
    """스케줄러 재시작"""
    try:
        scheduler.remove_all_jobs()
        setup_scheduler()
        print("\n✓ 스케줄러가 재시작되었습니다.")
    except Exception as e:
        print(f"✗ 스케줄러 재시작 오류: {e}")


# schedule_bp에 restart_scheduler 함수 주입
from src.routes.schedule_routes import set_restart_scheduler
set_restart_scheduler(restart_scheduler)


if __name__ == '__main__':
    try:
        # 경로 확인
        print("=" * 50)
        print("슬랙 출석체크 관리 시스템 v2.0")
        print("=" * 50)
        print(f"현재 작업 디렉토리: {Path.cwd()}")
        print(f"실행 파일 위치: {Path(__file__).parent}")

        # 필수 폴더 확인
        required_folders = ['templates', 'static', 'src', 'workspaces']
        missing_folders = []

        for folder in required_folders:
            folder_path = Path(__file__).parent / folder
            if not folder_path.exists():
                missing_folders.append(folder)
                print(f"⚠️  {folder}/ 폴더를 찾을 수 없습니다: {folder_path}")

        if missing_folders:
            print()
            print("=" * 50)
            print("❌ 오류: 필수 폴더가 없습니다!")
            print("=" * 50)
            print("누락된 폴더:", ", ".join(missing_folders))
            print()
            print("해결 방법:")
            print("1. 개발 모드: 프로젝트 루트에서 실행하세요")
            print("   python app_flask.py")
            print()
            print("2. EXE 모드: dist/슬랙출석체크/ 폴더 전체를 복사하세요")
            print("=" * 50)
            input("\n아무 키나 누르면 종료됩니다...")
            sys.exit(1)

        print()
        print("✓ 모든 폴더 확인 완료")
        print()

        # 워크스페이스 확인
        workspaces = workspace_manager.get_all_workspaces()
        if not workspaces:
            print("⚠️  워크스페이스가 없습니다.")
            print("   workspaces/ 폴더에 워크스페이스를 추가하세요.")
        else:
            print(f"✓ {len(workspaces)}개의 워크스페이스를 찾았습니다")

        print()
        print("=" * 50)
        print("스케줄러 초기화 중...")
        print("=" * 50)

        # 스케줄러 시작
        setup_scheduler()
        scheduler.start()
        print("\n✓ 스케줄러 시작 완료 (한국 시간대: Asia/Seoul)")

        # 스케줄러 상태 출력 (start() 이후에 호출해야 next_run_time이 계산됨)
        print_scheduler_status()

        print()
        print("=" * 50)
        print("서버 시작 중...")
        print("=" * 50)
        print("URL: http://127.0.0.1:5000")
        print("종료하려면 Ctrl+C를 누르세요.")
        print("=" * 50)
        print()

        # 1초 후 브라우저 자동 열기
        threading.Timer(1.5, open_browser).start()

        # Flask 앱 실행
        app.run(host='127.0.0.1', port=5000, debug=False)

    except KeyboardInterrupt:
        print("\n\n서버 종료 중...")
        scheduler.shutdown()
        print("✓ 스케줄러 종료 완료")
        print("✓ 서버가 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        print()
        print("=" * 50)
        print("❌ 오류 발생!")
        print("=" * 50)
        print(f"오류 내용: {e}")
        print()
        import traceback
        print("상세 오류:")
        traceback.print_exc()
        print("=" * 50)
        input("\n아무 키나 누르면 종료됩니다...")
        sys.exit(1)
