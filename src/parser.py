"""
출석 댓글 파싱 모듈
슬랙 댓글에서 출석 정보를 추출합니다.
"""
import re
from typing import List, Dict, Optional, Set


class AttendanceParser:
    """출석 댓글을 파싱하는 클래스"""

    # 출석 키워드 패턴
    ATTENDANCE_KEYWORDS = [
        '출석',
        '출석했습니다',
        '출석해요',
        '출석합니다',
        '입실',
        '입실했습니다',
    ]

    def __init__(self):
        """AttendanceParser 초기화"""
        # 정규표현식 패턴 컴파일
        # 패턴: "이름/" 또는 "이름 출석" 또는 "이름/출석" 형태 (유연하게)
        # - "홍길동/" → 인정
        # - "홍길동 출석" → 인정
        # - "홍길동/출석" → 인정
        # - "홍길동출석" → 인정
        self.pattern = re.compile(
            r'([가-힣a-zA-Z]+)\s*(?:[/]|(?:' + '|'.join(self.ATTENDANCE_KEYWORDS) + '))',
            re.IGNORECASE
        )

    def extract_name_from_text(self, text: str) -> Optional[str]:
        """
        댓글 텍스트에서 이름 추출

        Args:
            text (str): 댓글 텍스트

        Returns:
            Optional[str]: 추출된 이름 (없으면 None)
        """
        # 패턴 매칭
        match = self.pattern.search(text)

        if match:
            name = match.group(1).strip()
            return self.normalize_name(name)

        return None

    def normalize_name(self, name: str) -> str:
        """
        이름 정규화 (공백 제거, / 또는 _ 앞의 이름만 추출)

        Args:
            name (str): 원본 이름

        Returns:
            str: 정규화된 이름
        """
        name = name.strip()

        # '/' 또는 '_' 앞의 이름만 추출
        # 예: "홍길동/클스학과" → "홍길동"
        # 예: "홍길동_클스학과" → "홍길동"
        if '/' in name:
            name = name.split('/')[0].strip()
        elif '_' in name:
            name = name.split('_')[0].strip()

        return name

    def parse_attendance_replies(self, replies: List[Dict], duplicate_names: Dict = None) -> List[Dict]:
        """
        댓글 리스트에서 출석 정보 파싱

        Args:
            replies (List[Dict]): 슬랙 댓글 리스트 (user_info 포함)
            duplicate_names (Dict): 동명이인 매핑 정보
                예: {"홍길동": [{"user_id": "U123", "display_name": "홍길동_컴공", "sheet_row": 5}, ...]}

        Returns:
            List[Dict]: 파싱된 출석 정보 리스트
        """
        print(f"\n[파싱] 출석 댓글 파싱 중...")

        if duplicate_names is None:
            duplicate_names = {}

        attendance_list = []
        seen_names = set()  # 일반 이름 기준 중복 제거
        seen_user_ids = set()  # 동명이인용 User ID 기준 중복 제거

        for reply in replies:
            text = reply.get('text', '')
            user_info = reply.get('user_info')
            user_id = reply.get('user_id')

            # 텍스트에서 이름 추출
            name = self.extract_name_from_text(text)

            if name:
                # 동명이인 처리: 댓글에서 추출한 이름이 duplicate_names에 있는지 확인
                final_name = name
                sheet_row = None

                if name in duplicate_names:
                    # 동명이인: User ID 중복 체크
                    if user_id in seen_user_ids:
                        print(f"  ⚠ User ID {user_id} - 중복 (이미 출석 처리됨)")
                        continue

                    # User ID로 정확한 이름과 행 번호 찾기
                    matched = False
                    print(f"  [디버그] '{name}' 동명이인 그룹 발견, User ID: {user_id}")
                    for person in duplicate_names[name]:
                        print(f"    - 비교: {person.get('user_id')} vs {user_id}")
                        if person.get('user_id') == user_id:
                            raw_display_name = person.get('display_name', name)
                            final_name = self.normalize_name(raw_display_name)
                            sheet_row = person.get('sheet_row')
                            matched = True
                            print(f"  ✓ {final_name} (동명이인 매칭: {name} → {final_name}, 행: {sheet_row})")
                            break

                    if not matched:
                        print(f"  ⚠ {name} - 동명이인 그룹에 있지만 User ID {user_id} 매칭 실패")
                        print(f"     등록된 User ID들: {[p.get('user_id') for p in duplicate_names[name]]}")
                        continue  # 매칭 실패 시 스킵

                    seen_user_ids.add(user_id)  # 동명이인은 User ID로 중복 체크
                else:
                    # 일반 이름: 이름 중복 체크
                    if name in seen_names:
                        print(f"  ⚠ {name} - 중복 (이미 출석 처리됨)")
                        continue

                    print(f"  ✓ {final_name} - 출석 확인")
                    seen_names.add(name)  # 일반 이름은 이름으로 중복 체크

                attendance_list.append({
                    'name': final_name,
                    'text': text,
                    'user_id': user_id,
                    'user_info': user_info,
                    'timestamp': reply.get('timestamp'),
                    'source': 'text_pattern',  # 텍스트 패턴으로 추출
                    'sheet_row': sheet_row  # 동명이인인 경우 직접 지정된 행 번호
                })
            else:
                # 패턴 매칭 실패 시 실명으로 시도
                if user_info:
                    real_name = user_info.get('real_name', '')
                    display_name = user_info.get('display_name', '')

                    # 실명 또는 표시 이름이 있고, 출석 키워드가 포함된 경우
                    if self._contains_attendance_keyword(text):
                        raw_fallback_name = display_name or real_name
                        # / 또는 _ 앞의 이름만 추출
                        fallback_name = self.normalize_name(raw_fallback_name) if raw_fallback_name else ''

                        if fallback_name and fallback_name not in seen_names:
                            attendance_list.append({
                                'name': fallback_name,
                                'text': text,
                                'user_id': user_id,
                                'user_info': user_info,
                                'timestamp': reply.get('timestamp'),
                                'source': 'slack_name',  # 슬랙 이름으로 추출
                                'sheet_row': None
                            })
                            seen_names.add(fallback_name)
                            # seen_user_ids.add(user_id)  # [주석처리] 추후 필요 시 활성화
                            print(f"  ✓ {fallback_name} - 출석 확인 (슬랙 이름 사용: {raw_fallback_name})")

        print(f"\n✓ 출석 파싱 완료: {len(attendance_list)}명")

        return attendance_list

    def _contains_attendance_keyword(self, text: str) -> bool:
        """
        텍스트에 출석 키워드가 포함되어 있는지 확인

        Args:
            text (str): 텍스트

        Returns:
            bool: 포함 여부
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.ATTENDANCE_KEYWORDS)

    def get_attendance_summary(self, attendance_list: List[Dict]) -> Dict:
        """
        출석 요약 정보 생성

        Args:
            attendance_list (List[Dict]): 출석 리스트

        Returns:
            Dict: 요약 정보
        """
        names = [item['name'] for item in attendance_list]

        return {
            'total_count': len(names),
            'names': sorted(names),  # 가나다순 정렬
            'by_source': {
                'text_pattern': len([x for x in attendance_list if x['source'] == 'text_pattern']),
                'slack_name': len([x for x in attendance_list if x['source'] == 'slack_name']),
            }
        }


# 테스트 코드
if __name__ == '__main__':
    parser = AttendanceParser()

    # 테스트 데이터
    test_replies = [
        {'text': '김철수/출석했습니다', 'user_info': {'real_name': '김철수'}},
        {'text': '이영희 출석', 'user_info': {'real_name': '이영희'}},
        {'text': '박민수/입실했습니다', 'user_info': {'real_name': '박민수'}},
        {'text': '최지우 출석해요', 'user_info': {'real_name': '최지우'}},
        {'text': '출석했습니다', 'user_info': {'real_name': '홍길동', 'display_name': '홍길동'}},
        {'text': '안녕하세요', 'user_info': {'real_name': '미출석자'}},  # 출석 아님
        {'text': '김철수/출석했습니다', 'user_info': {'real_name': '김철수'}},  # 중복
    ]

    print("=== 출석 파싱 테스트 ===")
    attendance_list = parser.parse_attendance_replies(test_replies)

    print("\n=== 출석자 목록 ===")
    for item in attendance_list:
        print(f"  - {item['name']} ({item['source']})")

    print("\n=== 요약 ===")
    summary = parser.get_attendance_summary(attendance_list)
    print(f"  총 출석: {summary['total_count']}명")
    print(f"  텍스트 패턴: {summary['by_source']['text_pattern']}명")
    print(f"  슬랙 이름: {summary['by_source']['slack_name']}명")
