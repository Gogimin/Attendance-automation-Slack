"""과제 체크 서비스"""

from typing import List, Tuple, Dict, Optional
import sys
import json
from pathlib import Path
from datetime import datetime
import pytz

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.slack_handler import SlackHandler
from src.sheets_handler import SheetsHandler
from src.assignment_parser import AssignmentParser

KST = pytz.timezone('Asia/Seoul')


class AssignmentService:
    """과제 체크 비즈니스 로직을 담당하는 서비스"""

    def __init__(
        self,
        slack_handler: SlackHandler,
        sheets_handler: SheetsHandler,
        parser: Optional[AssignmentParser] = None
    ):
        """
        Args:
            slack_handler: 슬랙 API 핸들러
            sheets_handler: 구글 시트 API 핸들러
            parser: 과제 파서 (None이면 기본 파서 생성)
        """
        self.slack = slack_handler
        self.sheets = sheets_handler
        self.parser = parser or AssignmentParser()

    def run_assignment_check(
        self,
        assignment_channel_id: str,
        thread_ts: str,
        column_index: int,
        name_column: int,
        start_row: int,
        assignment_sheet_name: str,
        mark_absent: bool = True
    ) -> Tuple[List[str], List[str], int]:
        """
        과제 집계 실행

        Args:
            assignment_channel_id: 슬랙 과제 채널 ID
            thread_ts: 스레드 타임스탬프
            column_index: 과제 체크할 열 인덱스 (0-based)
            name_column: 학생 이름 열 인덱스
            start_row: 학생 명단 시작 행
            assignment_sheet_name: 과제 시트 이름
            mark_absent: 미제출자 X 표시 여부

        Returns:
            Tuple[제출자 리스트, 미제출자 리스트, 업데이트 성공 개수]

        Raises:
            ValueError: 댓글 수집 실패, 학생 명단 읽기 실패 등
        """
        # 0. 채널에 자동 참여 시도
        print(f"\n[과제체크] 채널 참여 확인 중...")
        self.slack.join_channel(assignment_channel_id)

        # 1. 슬랙 댓글 수집
        replies = self.slack.get_replies_with_user_info(
            assignment_channel_id,
            thread_ts
        )

        if not replies:
            raise ValueError('댓글을 가져올 수 없습니다.')

        # 2. 과제 제출자 파싱
        submitted = self.parser.parse_assignment_replies(replies)

        # 3. 학생 명단 읽기
        students = self.sheets.get_student_list(name_column, start_row)

        if not students:
            raise ValueError('학생 명단을 읽을 수 없습니다.')

        # 4. 제출 여부 매칭
        submitted_list = [name for name in students.keys() if name in submitted]
        not_submitted_list = [name for name in students.keys() if name not in submitted]

        # 5. 시트 업데이트
        success_count = self.sheets.batch_update_assignment(
            sheet_name=assignment_sheet_name,
            column=column_index,
            students=students,
            submitted=submitted,
            mark_absent=mark_absent
        )

        return submitted_list, not_submitted_list, success_count

    def save_history(
        self,
        workspace_path: Path,
        thread_ts: str,
        thread_link: str,
        column_name: str,
        submitted_list: List[str],
        not_submitted_list: List[str],
        total_students: int
    ) -> None:
        """
        과제 체크 기록 저장

        Args:
            workspace_path: 워크스페이스 경로
            thread_ts: 스레드 타임스탬프
            thread_link: 스레드 링크 (원본 입력)
            column_name: 열 이름
            submitted_list: 제출자 리스트
            not_submitted_list: 미제출자 리스트
            total_students: 총 학생 수
        """
        history_file = workspace_path / 'assignment_history.json'

        # 기존 기록 읽기
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        else:
            history_data = {'history': []}

        # 새 기록 추가
        record = {
            'id': datetime.now(KST).strftime('%Y%m%d%H%M%S'),
            'timestamp': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S'),
            'thread_ts': thread_ts,
            'thread_link': thread_link,
            'column': column_name,
            'total_students': total_students,
            'submitted_count': len(submitted_list),
            'not_submitted_count': len(not_submitted_list),
            'submitted_list': submitted_list,
            'not_submitted_list': not_submitted_list
        }

        history_data['history'].insert(0, record)  # 최신 기록이 맨 앞에

        # 최대 100개 기록만 유지
        history_data['history'] = history_data['history'][:100]

        # 파일 저장
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

    def get_history(self, workspace_path: Path, limit: int = 20) -> List[Dict]:
        """
        과제 체크 기록 조회

        Args:
            workspace_path: 워크스페이스 경로
            limit: 최대 조회 개수

        Returns:
            기록 리스트 (최신순)
        """
        history_file = workspace_path / 'assignment_history.json'

        if not history_file.exists():
            return []

        with open(history_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)

        return history_data.get('history', [])[:limit]
