"""
Google Sheets API 처리 모듈
스프레드시트에서 학생 명단을 읽고 출석 체크를 업데이트합니다.
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
from enum import Enum
import time


class AttendanceStatus(Enum):
    """출석 상태"""
    PRESENT = "O"      # 출석
    ABSENT = "X"       # 미출석
    LATE = "△"         # 지각


class SheetsHandler:
    """Google Sheets API를 처리하는 클래스"""

    # Google Sheets API 스코프
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, credentials_path: str, spreadsheet_id: str, sheet_name: str = '출석현황'):
        """
        SheetsHandler 초기화

        Args:
            credentials_path (str): 서비스 계정 JSON 키 파일 경로
            spreadsheet_id (str): 스프레드시트 ID
            sheet_name (str): 시트 이름
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service = None

    def connect(self) -> bool:
        """
        Google Sheets API 연결

        Returns:
            bool: 연결 성공 여부
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            print("✓ Google Sheets API 연결 성공!")
            return True
        except FileNotFoundError:
            print(f"✗ 인증 파일을 찾을 수 없습니다: {self.credentials_path}")
            return False
        except Exception as e:
            print(f"✗ Google Sheets API 연결 실패: {e}")
            return False

    def test_connection(self) -> bool:
        """
        연결 테스트 및 스프레드시트 정보 가져오기

        Returns:
            bool: 연결 성공 여부
        """
        if not self.service:
            return False

        try:
            # 스프레드시트 메타데이터 가져오기
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()

            title = sheet_metadata.get('properties', {}).get('title', 'Unknown')
            print(f"✓ 스프레드시트 접근 성공!")
            print(f"  - 제목: {title}")
            print(f"  - ID: {self.spreadsheet_id}")

            # 시트 목록 확인
            sheets = sheet_metadata.get('sheets', [])
            sheet_names = [s['properties']['title'] for s in sheets]
            print(f"  - 시트 목록: {', '.join(sheet_names)}")

            if self.sheet_name not in sheet_names:
                print(f"⚠ 경고: '{self.sheet_name}' 시트를 찾을 수 없습니다.")
                return False

            return True

        except HttpError as e:
            print(f"✗ 스프레드시트 접근 실패: {e}")
            print("  - 서비스 계정에 스프레드시트 공유 권한이 있는지 확인하세요.")
            return False
        except Exception as e:
            print(f"✗ 연결 테스트 실패: {e}")
            return False

    def get_student_list(self, name_column: int, start_row: int) -> Dict[str, int]:
        """
        스프레드시트에서 학생 명단 읽기

        Args:
            name_column (int): 이름 열 인덱스 (0-based)
            start_row (int): 시작 행 인덱스 (0-based)

        Returns:
            Dict[str, int]: {학생이름: 행번호} 매핑 딕셔너리
        """
        if not self.service:
            print("✗ API가 연결되지 않았습니다. connect()를 먼저 호출하세요.")
            return {}

        try:
            # A1 notation으로 변환
            col_letter = chr(65 + name_column)  # 0 -> A, 1 -> B, ...
            start_row_num = start_row + 1  # 0-based -> 1-based
            range_name = f"{self.sheet_name}!{col_letter}{start_row_num}:{col_letter}"

            print(f"\n[Google Sheets] 학생 명단 읽기 중...")
            print(f"  - 범위: {range_name}")

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            if not values:
                print("✗ 학생 명단이 비어있습니다.")
                return {}

            # {이름: 행번호} 매핑
            student_dict = {}
            for i, row in enumerate(values):
                if row and row[0]:  # 빈 셀이 아닌 경우
                    name = row[0].strip()
                    if name:
                        row_number = start_row + i  # 0-based 행 번호
                        student_dict[name] = row_number

            print(f"✓ 학생 명단 읽기 완료: {len(student_dict)}명")

            return student_dict

        except HttpError as e:
            print(f"✗ 학생 명단 읽기 실패: {e}")
            return {}
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return {}

    def update_attendance(self, row_number: int, column: int, status: AttendanceStatus = AttendanceStatus.PRESENT) -> bool:
        """
        특정 셀의 출석 체크 업데이트

        Args:
            row_number (int): 행 번호 (0-based)
            column (int): 열 인덱스 (0-based)
            status (AttendanceStatus): 출석 상태 (O/X/△)

        Returns:
            bool: 업데이트 성공 여부
        """
        if not self.service:
            return False

        try:
            # A1 notation으로 변환
            col_letter = chr(65 + column)  # 0 -> A, 1 -> B, ...
            row_num = row_number + 1  # 0-based -> 1-based
            cell_range = f"{self.sheet_name}!{col_letter}{row_num}"

            # 출석 상태 문자 (O, X, △)
            status_value = status.value if isinstance(status, AttendanceStatus) else status

            body = {
                'values': [[status_value]]
            }

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=cell_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            return True

        except HttpError as e:
            print(f"✗ 셀 업데이트 실패 ({cell_range}): {e}")
            return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def batch_update_attendance(self, updates: List[Dict]) -> int:
        """
        여러 학생의 출석을 한번에 업데이트 (배치 처리)

        Args:
            updates (List[Dict]): 업데이트 정보 리스트
                예: [{'name': '김철수', 'row': 4, 'column': 10, 'status': AttendanceStatus.PRESENT}, ...]

        Returns:
            int: 성공한 업데이트 수
        """
        if not self.service or not updates:
            return 0

        print(f"\n[Google Sheets] 출석 체크 업데이트 중...")

        success_count = 0

        for update in updates:
            name = update.get('name')
            row = update.get('row')
            column = update.get('column')
            status = update.get('status', AttendanceStatus.PRESENT)

            if row is None or column is None:
                continue

            if self.update_attendance(row, column, status):
                status_str = status.value if isinstance(status, AttendanceStatus) else status
                print(f"  ✓ {name} - {status_str} 업데이트 완료")
                success_count += 1
            else:
                print(f"  ✗ {name} - 업데이트 실패")

            # API Rate Limiting 방지
            time.sleep(0.1)

        print(f"\n✓ 출석 체크 완료: {success_count}/{len(updates)}명")

        return success_count

    def update_assignment(self, sheet_name: str, row_number: int, column: int, value: str = "O") -> bool:
        """
        과제 시트의 특정 셀 업데이트

        Args:
            sheet_name (str): 시트 이름 (예: "과제실습 모니터링")
            row_number (int): 행 번호 (0-based)
            column (int): 열 인덱스 (0-based)
            value (str): 기록할 값 (O/X 등)

        Returns:
            bool: 업데이트 성공 여부
        """
        if not self.service:
            return False

        try:
            # A1 notation으로 변환
            col_letter = chr(65 + column) if column < 26 else chr(65 + column // 26 - 1) + chr(65 + column % 26)
            row_num = row_number + 1  # 0-based -> 1-based
            cell_range = f"{sheet_name}!{col_letter}{row_num}"

            body = {
                'values': [[value]]
            }

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=cell_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            return True

        except HttpError as e:
            print(f"✗ 과제 셀 업데이트 실패 ({cell_range}): {e}")
            return False
        except Exception as e:
            print(f"✗ 오류 발생: {e}")
            return False

    def batch_update_assignment(self, sheet_name: str, column: int, students: Dict[str, int],
                                submitted: List[str], mark_absent: bool = True) -> int:
        """
        과제실습 모니터링 시트에 O/X 표시 (배치 처리)

        Args:
            sheet_name (str): 시트 이름 (예: "과제실습 모니터링")
            column (int): 기록할 열 인덱스 (0-based)
            students (Dict[str, int]): 학생 명단 딕셔너리 {이름: 행번호}
            submitted (List[str]): 제출자 이름 리스트
            mark_absent (bool): 미제출자 X 표시 여부

        Returns:
            int: 성공한 업데이트 수
        """
        if not self.service or not students:
            return 0

        print(f"\n[Google Sheets] 과제 제출 현황 업데이트 중...")
        print(f"  - 시트: {sheet_name}")
        print(f"  - 열: {chr(65 + column) if column < 26 else '??'}")

        success_count = 0

        for student_name, row in students.items():
            if student_name in submitted:
                value = "O"
                status_text = "제출"
            else:
                if mark_absent:
                    value = "X"
                    status_text = "미제출"
                else:
                    continue  # 미제출자 표시 안함

            if self.update_assignment(sheet_name, row, column, value):
                print(f"  ✓ {student_name} - {status_text} ({value})")
                success_count += 1
            else:
                print(f"  ✗ {student_name} - 업데이트 실패")

            # API Rate Limiting 방지
            time.sleep(0.1)

        print(f"\n✓ 과제 체크 완료: {success_count}/{len(students)}명")

        return success_count


# 테스트 코드
if __name__ == '__main__':
    from config.settings import (
        GOOGLE_SHEETS_CREDENTIALS_PATH,
        SPREADSHEET_ID,
        SHEET_NAME,
        NAME_COLUMN,
        SLACK_COLUMN,
        START_ROW,
        BASE_DIR
    )

    cred_path = BASE_DIR / GOOGLE_SHEETS_CREDENTIALS_PATH

    if not cred_path.exists():
        print("✗ credentials.json 파일을 찾을 수 없습니다.")
        print(f"  경로: {cred_path}")
        print("\n다음 단계:")
        print("  1. Google Cloud Console에서 서비스 계정 JSON 키 다운로드")
        print("  2. config/credentials.json으로 저장")
    else:
        handler = SheetsHandler(
            credentials_path=str(cred_path),
            spreadsheet_id=SPREADSHEET_ID,
            sheet_name=SHEET_NAME
        )

        # 연결 테스트
        if handler.connect():
            if handler.test_connection():
                print("\n✓ Google Sheets API가 정상적으로 작동합니다!")

                # 학생 명단 읽기 테스트
                students = handler.get_student_list(NAME_COLUMN, START_ROW)
                if students:
                    print(f"\n학생 명단 (최대 5명):")
                    for i, (name, row) in enumerate(list(students.items())[:5], 1):
                        print(f"  {i}. {name} (행: {row + 1})")
