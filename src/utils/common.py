"""
유틸리티 함수 모듈
로깅, 날짜 처리 등 공통 기능
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def setup_logger(log_file: Path = None, console_level=logging.INFO):
    """
    로거 설정

    Args:
        log_file (Path): 로그 파일 경로
        console_level: 콘솔 로그 레벨

    Returns:
        logging.Logger: 설정된 로거
    """
    logger = logging.getLogger('attendance')
    logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거
    logger.handlers.clear()

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        '%(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def print_header(title: str):
    """
    헤더 출력

    Args:
        title (str): 제목
    """
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}\n")


def print_section(title: str):
    """
    섹션 출력

    Args:
        title (str): 섹션 제목
    """
    print(f"\n[{title}]")


def print_list(items: List[str], prefix: str = "  - "):
    """
    리스트 출력

    Args:
        items (List[str]): 아이템 리스트
        prefix (str): 접두사
    """
    for item in items:
        print(f"{prefix}{item}")


def get_timestamp() -> str:
    """
    현재 시간 문자열 반환

    Returns:
        str: 타임스탬프 (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_date_string() -> str:
    """
    현재 날짜 문자열 반환

    Returns:
        str: 날짜 (YYYY-MM-DD)
    """
    return datetime.now().strftime('%Y-%m-%d')


def format_duration(seconds: float) -> str:
    """
    초를 읽기 쉬운 형태로 변환

    Args:
        seconds (float): 초

    Returns:
        str: 포맷된 문자열 (예: "1.23초")
    """
    return f"{seconds:.2f}초"


def parse_slack_thread_link(link_or_ts: str) -> Optional[str]:
    """
    슬랙 링크 또는 Thread TS를 파싱하여 Thread TS 반환

    Args:
        link_or_ts (str): 슬랙 링크 또는 Thread TS
            - 링크 예시: https://workspace.slack.com/archives/C1234567890/p1760337471753399
            - TS 예시: 1760337471.753399

    Returns:
        Optional[str]: Thread TS (예: 1760337471.753399)
    """
    if not link_or_ts:
        return None

    link_or_ts = link_or_ts.strip()

    # 이미 올바른 Thread TS 형식인지 확인 (숫자.숫자)
    if re.match(r'^\d+\.\d+$', link_or_ts):
        return link_or_ts

    # 슬랙 링크에서 Thread TS 추출
    # 패턴: https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP
    match = re.search(r'/p(\d+)', link_or_ts)

    if match:
        # p1760337471753399 -> 1760337471.753399
        timestamp_str = match.group(1)

        # 마지막 6자리 앞에 점(.) 추가
        if len(timestamp_str) > 6:
            thread_ts = timestamp_str[:-6] + '.' + timestamp_str[-6:]
            return thread_ts

    # 파싱 실패
    return None


def column_letter_to_index(letter: str) -> Optional[int]:
    """
    열 문자를 인덱스로 변환 (A -> 0, B -> 1, ..., Z -> 25)

    Args:
        letter (str): 열 문자 (A-Z, 대소문자 구분 없음)

    Returns:
        Optional[int]: 열 인덱스 (0-based), 잘못된 입력 시 None
    """
    if not letter or not isinstance(letter, str):
        return None

    letter = letter.strip().upper()

    # 단일 문자 검증 (A-Z)
    if len(letter) == 1 and 'A' <= letter <= 'Z':
        return ord(letter) - ord('A')

    return None


def column_index_to_letter(index: int) -> Optional[str]:
    """
    열 인덱스를 문자로 변환 (0 -> A, 1 -> B, ..., 25 -> Z)

    Args:
        index (int): 열 인덱스 (0-based)

    Returns:
        Optional[str]: 열 문자, 범위 벗어나면 None
    """
    if not isinstance(index, int) or index < 0 or index > 25:
        return None

    return chr(ord('A') + index)


def get_next_column(current_column: str, start_column: str, end_column: str) -> str:
    """
    현재 열에서 다음 열을 계산 (순환)

    Args:
        current_column (str): 현재 열 (예: 'H')
        start_column (str): 시작 열 (예: 'H')
        end_column (str): 끝 열 (예: 'P')

    Returns:
        str: 다음 열. 끝에 도달하면 시작 열로 돌아감

    Examples:
        >>> get_next_column('H', 'H', 'P')
        'I'
        >>> get_next_column('P', 'H', 'P')
        'H'  # 순환
    """
    current_idx = column_letter_to_index(current_column)
    start_idx = column_letter_to_index(start_column)
    end_idx = column_letter_to_index(end_column)

    if current_idx is None or start_idx is None or end_idx is None:
        return current_column  # 오류 시 현재 열 유지

    # 다음 열 계산
    next_idx = current_idx + 1

    # 끝 열을 넘어가면 시작 열로 순환
    if next_idx > end_idx:
        next_idx = start_idx

    return column_index_to_letter(next_idx)


# 테스트 코드
if __name__ == '__main__':
    print_header("유틸리티 함수 테스트")

    print_section("타임스탬프 테스트")
    print(f"  현재 시간: {get_timestamp()}")
    print(f"  현재 날짜: {get_date_string()}")

    print_section("리스트 출력 테스트")
    test_items = ["김철수", "이영희", "박민수"]
    print_list(test_items)

    print_section("기간 포맷 테스트")
    print(f"  실행 시간: {format_duration(1.23456)}")

    print_section("로거 테스트")
    logger = setup_logger()
    logger.info("INFO 레벨 로그")
    logger.debug("DEBUG 레벨 로그")
    logger.warning("WARNING 레벨 로그")

    print_section("슬랙 링크 파싱 테스트")
    test_cases = [
        "https://iginihq.slack.com/archives/C09LZ0WBB4Y/p1760337471753399",
        "1760337471.753399",
        "https://workspace.slack.com/archives/C1234567890/p1234567890123456",
    ]
    for test in test_cases:
        result = parse_slack_thread_link(test)
        print(f"  입력: {test}")
        print(f"  결과: {result}\n")

    print_section("열 문자 변환 테스트")
    print(f"  K -> {column_letter_to_index('K')}")  # 10
    print(f"  H -> {column_letter_to_index('H')}")  # 7
    print(f"  A -> {column_letter_to_index('A')}")  # 0
    print(f"  10 -> {column_index_to_letter(10)}")  # K
    print(f"  7 -> {column_index_to_letter(7)}")   # H
