"""
과제 제출 파싱 모듈
슬랙 댓글에서 과제 제출자 정보를 추출합니다.
"""
from typing import List, Dict, Set


class AssignmentParser:
    """과제 제출 체크 파서"""

    def parse_assignment_replies(self, replies: List[Dict]) -> List[str]:
        """
        과제 제출자 이름 수집
        - 스레드에 댓글 1번 이상 작성한 사람 모두 수집
        - 슬랙 표시 이름(display_name) 사용

        Args:
            replies (List[Dict]): 슬랙 댓글 리스트 (user_info 포함)

        Returns:
            List[str]: 제출자 이름 리스트 (중복 제거)
        """
        print(f"\n[과제 파싱] 과제 제출자 파싱 중...")

        submitted_names: Set[str] = set()

        for reply in replies:
            user_info = reply.get('user_info')

            if user_info:
                display_name = user_info.get('display_name', '')

                if not display_name:
                    # display_name이 없으면 real_name 사용
                    display_name = user_info.get('real_name', '')

                if display_name:
                    # "홍길동/클스학과" → "홍길동" 추출
                    name_only = self._extract_name(display_name)

                    if name_only:
                        submitted_names.add(name_only)
                        print(f"  ✓ {name_only} - 과제 제출 확인")

        result = list(submitted_names)
        print(f"\n✓ 과제 파싱 완료: {len(result)}명")

        return result

    def _extract_name(self, display_name: str) -> str:
        """
        슬랙 표시 이름에서 실제 이름만 추출

        Args:
            display_name (str): 슬랙 표시 이름

        Returns:
            str: 추출된 이름

        Examples:
            "홍길동/클스학과" → "홍길동"
            "홍길동_클스학과" → "홍길동"
            "홍길동" → "홍길동"
            "김철수 (학생)" → "김철수"
            "손형록 사이버보안전공" → "손형록"
            "김우진 컴퓨터공학전공" → "김우진"
        """
        # "/" 기준으로 분리
        if '/' in display_name:
            return display_name.split('/')[0].strip()

        # "_" 기준으로 분리
        if '_' in display_name:
            return display_name.split('_')[0].strip()

        # "(" 기준으로 분리
        if '(' in display_name:
            return display_name.split('(')[0].strip()

        # 공백 기준으로 분리 (첫 단어만 추출)
        # "손형록 사이버보안전공" → "손형록"
        # "홍길동" → "홍길동"
        parts = display_name.strip().split()
        if len(parts) > 1:
            # 2단어 이상이면 첫 단어만 (이름으로 간주)
            return parts[0]

        return display_name.strip()

    def get_submission_summary(self, submitted_list: List[str], total_students: int) -> Dict:
        """
        과제 제출 요약 정보 생성

        Args:
            submitted_list (List[str]): 제출자 명단
            total_students (int): 전체 학생 수

        Returns:
            Dict: 요약 정보
        """
        submitted_count = len(submitted_list)
        not_submitted_count = total_students - submitted_count
        submission_rate = (submitted_count / total_students * 100) if total_students > 0 else 0

        return {
            'total_students': total_students,
            'submitted_count': submitted_count,
            'not_submitted_count': not_submitted_count,
            'submission_rate': round(submission_rate, 1),
            'submitted_names': sorted(submitted_list)  # 가나다순 정렬
        }


# 테스트 코드
if __name__ == '__main__':
    parser = AssignmentParser()

    # 테스트 데이터
    test_replies = [
        {
            'text': '과제 제출합니다',
            'user_info': {'display_name': '홍길동/클스학과', 'real_name': '홍길동'}
        },
        {
            'text': '사진 첨부',
            'user_info': {'display_name': '김철수', 'real_name': '김철수'}
        },
        {
            'text': '제출',
            'user_info': {'display_name': '이영희 (학생)', 'real_name': '이영희'}
        },
        {
            'text': '과제 완료',
            'user_info': {'display_name': '홍길동/클스학과', 'real_name': '홍길동'}  # 중복
        },
    ]

    print("=== 과제 제출자 파싱 테스트 ===")
    submitted = parser.parse_assignment_replies(test_replies)

    print("\n=== 제출자 목록 ===")
    for name in submitted:
        print(f"  - {name}")

    print("\n=== 요약 ===")
    summary = parser.get_submission_summary(submitted, total_students=10)
    print(f"  전체 학생: {summary['total_students']}명")
    print(f"  제출: {summary['submitted_count']}명")
    print(f"  미제출: {summary['not_submitted_count']}명")
    print(f"  제출률: {summary['submission_rate']}%")
