"""출석 체크 서비스"""

from typing import List, Tuple, Dict, Optional
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler, AttendanceStatus
from src.parser import AttendanceParser


class AttendanceService:
    """출석 체크 비즈니스 로직을 담당하는 서비스"""

    def __init__(
        self,
        slack_handler: SlackHandler,
        sheets_handler: SheetsHandler,
        parser: Optional[AttendanceParser] = None
    ):
        """
        Args:
            slack_handler: 슬랙 API 핸들러
            sheets_handler: 구글 시트 API 핸들러
            parser: 출석 파서 (None이면 기본 파서 생성)
        """
        self.slack = slack_handler
        self.sheets = sheets_handler
        self.parser = parser or AttendanceParser()

    def run_attendance_check(
        self,
        channel_id: str,
        thread_ts: str,
        column_index: int,
        name_column: int,
        start_row: int,
        mark_absent: bool = True,
        duplicate_names: Dict = None
    ) -> Tuple[List[str], List[str], List[str], int, Dict]:
        """
        출석 집계 실행

        Args:
            channel_id: 슬랙 채널 ID
            thread_ts: 스레드 타임스탬프
            column_index: 출석 체크할 열 인덱스 (0-based)
            name_column: 학생 이름 열 인덱스
            start_row: 학생 명단 시작 행
            mark_absent: 미출석자 X 표시 여부
            duplicate_names: 동명이인 정보

        Returns:
            Tuple[
                매칭된 이름 리스트,
                미출석 이름 리스트,
                매칭 실패 이름 리스트,
                업데이트 성공 개수,
                상세 정보 딕셔너리
            ]

        Raises:
            ValueError: 댓글 수집 실패, 학생 명단 읽기 실패 등
        """
        # 0. 채널에 자동 참여 시도
        print(f"\n[출석체크] 채널 참여 확인 중...")
        self.slack.join_channel(channel_id)

        # 1. 슬랙 댓글 수집
        replies = self.slack.get_replies_with_user_info(channel_id, thread_ts)

        if not replies:
            raise ValueError('댓글을 가져올 수 없습니다.')

        # 2. 출석 파싱
        attendance_list = self.parser.parse_attendance_replies(
            replies,
            duplicate_names or {}
        )

        if not attendance_list:
            raise ValueError('출석한 학생이 없습니다.')

        # 3. 학생 명단 읽기
        students = self.sheets.get_student_list(name_column, start_row)

        if not students:
            raise ValueError('학생 명단을 읽을 수 없습니다.')

        # 4. 출석 매칭
        matched_names, unmatched_names, updates = self._match_attendance(
            attendance_list,
            students,
            column_index
        )

        # 5. 미출석자 처리
        absent_names = [name for name in students.keys() if name not in matched_names]

        if mark_absent:
            absent_updates = self._create_absent_updates(
                absent_names,
                students,
                column_index
            )
            updates.extend(absent_updates)

        # 6. 시트 업데이트
        success_count = self.sheets.batch_update_attendance(updates)

        # 7. 상세 정보 생성
        summary = self.parser.get_attendance_summary(attendance_list)

        return matched_names, absent_names, unmatched_names, success_count, summary

    def _match_attendance(
        self,
        attendance_list: List[Dict],
        students: Dict[str, int],
        column_index: int
    ) -> Tuple[List[str], List[str], List[Dict]]:
        """
        출석자와 학생 명단 매칭

        Args:
            attendance_list: 파싱된 출석 리스트
            students: {이름: 행번호} 딕셔너리
            column_index: 열 인덱스

        Returns:
            Tuple[매칭된 이름, 매칭 실패 이름, 업데이트 리스트]
        """
        matched_names = []
        unmatched_names = []
        updates = []

        for attendance in attendance_list:
            name = attendance['name']
            sheet_row = attendance.get('sheet_row')  # 동명이인인 경우 직접 지정된 행

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

        return matched_names, unmatched_names, updates

    def _create_absent_updates(
        self,
        absent_names: List[str],
        students: Dict[str, int],
        column_index: int
    ) -> List[Dict]:
        """
        미출석자 업데이트 생성

        Args:
            absent_names: 미출석자 이름 리스트
            students: {이름: 행번호} 딕셔너리
            column_index: 열 인덱스

        Returns:
            업데이트 리스트
        """
        updates = []
        for name in absent_names:
            row = students[name]
            updates.append({
                'name': name,
                'row': row,
                'column': column_index,
                'status': AttendanceStatus.ABSENT
            })
        return updates

    def send_notifications(
        self,
        channel_id: str,
        thread_ts: str,
        thread_user: Optional[str],
        matched_names: List[str],
        absent_names: List[str],
        total_students: int,
        column_name: str,
        send_thread_reply: bool = True,
        send_dm: bool = True
    ) -> List[str]:
        """
        알림 전송 (스레드 댓글 + DM)

        Args:
            channel_id: 슬랙 채널 ID
            thread_ts: 스레드 타임스탬프
            thread_user: 스레드 작성자 User ID (DM 수신자)
            matched_names: 출석자 이름 리스트
            absent_names: 미출석자 이름 리스트
            total_students: 총 학생 수
            column_name: 열 이름 (예: "K")
            send_thread_reply: 스레드 댓글 작성 여부
            send_dm: DM 전송 여부

        Returns:
            전송 완료 알림 리스트
        """
        notifications = []

        # 1. 스레드 댓글 작성
        if send_thread_reply:
            if self.slack.post_thread_reply(
                channel_id,
                thread_ts,
                "출석 체크를 완료했습니다."
            ):
                notifications.append('스레드 댓글 작성 완료')

        # 2. DM 전송
        if send_dm and thread_user:
            dm_message = self._create_dm_message(
                matched_names,
                absent_names,
                total_students,
                column_name
            )

            if self.slack.send_dm(thread_user, dm_message):
                notifications.append('DM 전송 완료')

        return notifications

    def _create_dm_message(
        self,
        matched_names: List[str],
        absent_names: List[str],
        total_students: int,
        column_name: str
    ) -> str:
        """
        DM 메시지 생성

        Args:
            matched_names: 출석자 이름
            absent_names: 미출석자 이름
            total_students: 총 학생 수
            column_name: 열 이름

        Returns:
            DM 메시지 문자열
        """
        present_rate = len(matched_names) / total_students * 100 if total_students > 0 else 0
        absent_rate = len(absent_names) / total_students * 100 if total_students > 0 else 0

        dm_message = f"""[출석체크 완료 알림]

📅 열: {column_name}열
📊 총 인원: {total_students}명
✅ 출석: {len(matched_names)}명 ({present_rate:.1f}%)
❌ 미출석: {len(absent_names)}명 ({absent_rate:.1f}%)

📋 출석자: {', '.join(matched_names)}

⚠️ 미출석자 ({len(absent_names)}명):
"""

        for i, name in enumerate(absent_names[:50], 1):
            dm_message += f"{i}. {name}\n"

        if len(absent_names) > 50:
            dm_message += f"... 외 {len(absent_names) - 50}명"

        return dm_message
