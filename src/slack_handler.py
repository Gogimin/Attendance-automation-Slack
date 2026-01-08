"""
Slack API 처리 모듈
출석체크 스레드의 댓글을 수집하고 사용자 정보를 가져옵니다.
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import List, Dict, Optional
import time
import re


class SlackHandler:
    """Slack API를 처리하는 클래스"""

    def __init__(self, token: str):
        """
        SlackHandler 초기화

        Args:
            token (str): Slack Bot Token (xoxb-로 시작)
        """
        self.client = WebClient(token=token)
        self.user_cache = {}  # 사용자 정보 캐시

    @staticmethod
    def convert_mentions(message: str) -> str:
        """
        사용자가 입력한 @channel, @here 등을 슬랙 형식으로 변환

        Args:
            message (str): 원본 메시지

        Returns:
            str: 변환된 메시지
        """
        # @channel -> <!channel>
        message = re.sub(r'@channel\b', '<!channel>', message, flags=re.IGNORECASE)

        # @here -> <!here>
        message = re.sub(r'@here\b', '<!here>', message, flags=re.IGNORECASE)

        # @everyone -> <!everyone>
        message = re.sub(r'@everyone\b', '<!everyone>', message, flags=re.IGNORECASE)

        return message

    def test_connection(self) -> bool:
        """
        Slack API 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = self.client.auth_test()
            print(f"✓ Slack 연결 성공!")
            print(f"  - Bot 이름: {response['user']}")
            print(f"  - 팀: {response['team']}")
            return True
        except SlackApiError as e:
            print(f"✗ Slack 연결 실패: {e.response['error']}")
            return False

    def get_thread_replies(self, channel_id: str, thread_ts: str) -> List[Dict]:
        """
        특정 스레드의 모든 댓글 가져오기

        Args:
            channel_id (str): 채널 ID
            thread_ts (str): 스레드 타임스탬프

        Returns:
            List[Dict]: 댓글 리스트 (원본 메시지 제외)
        """
        try:
            print(f"\n[Slack] 스레드 댓글 수집 중...")
            print(f"  - Channel: {channel_id}")
            print(f"  - Thread TS: {thread_ts}")

            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=1000  # 최대 1000개
            )

            if not response['ok']:
                raise SlackApiError("API 호출 실패", response)

            messages = response['messages']

            # 첫 번째 메시지는 원본 메시지이므로 제외
            replies = messages[1:] if len(messages) > 1 else []

            print(f"✓ 댓글 수집 완료: {len(replies)}개")

            return replies

        except SlackApiError as e:
            error_msg = e.response.get('error', 'unknown')
            error_detail = e.response.get('needed', '')
            print(f"✗ 댓글 가져오기 실패: {error_msg}")
            if error_detail:
                print(f"  필요한 권한: {error_detail}")
            if error_msg == 'thread_not_found':
                print(f"  → Thread TS가 해당 채널에 존재하지 않습니다.")
                print(f"  → Bot이 채널에 초대되어 있는지 확인하세요.")
                print(f"  → 스레드가 삭제되었거나 URL이 댓글 URL일 수 있습니다.")
            print(f"  전체 응답: {e.response}")
            return []

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        사용자 ID로 사용자 정보 가져오기 (캐시 사용)

        Args:
            user_id (str): Slack User ID

        Returns:
            Optional[Dict]: 사용자 정보 (이름, 실명 등)
        """
        # 캐시에 있으면 반환
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            response = self.client.users_info(user=user_id)

            if not response['ok']:
                return None

            user = response['user']
            user_info = {
                'id': user_id,
                'name': user.get('name', ''),
                'real_name': user.get('real_name', ''),
                'display_name': user.get('profile', {}).get('display_name', ''),
            }

            # 캐시에 저장
            self.user_cache[user_id] = user_info

            # API Rate Limiting 방지
            time.sleep(0.1)

            return user_info

        except SlackApiError as e:
            print(f"✗ 사용자 정보 가져오기 실패 ({user_id}): {e.response['error']}")
            return None

    def get_replies_with_user_info(self, channel_id: str, thread_ts: str) -> List[Dict]:
        """
        스레드 댓글과 사용자 정보를 함께 가져오기

        Args:
            channel_id (str): 채널 ID
            thread_ts (str): 스레드 타임스탬프

        Returns:
            List[Dict]: 댓글 + 사용자 정보 리스트
        """
        replies = self.get_thread_replies(channel_id, thread_ts)

        if not replies:
            return []

        print(f"\n[Slack] 사용자 정보 수집 중...")

        enriched_replies = []

        for reply in replies:
            user_id = reply.get('user')
            text = reply.get('text', '')
            ts = reply.get('ts', '')

            # Bot 메시지 제외
            if reply.get('bot_id'):
                continue

            user_info = None
            if user_id:
                user_info = self.get_user_info(user_id)

            enriched_replies.append({
                'user_id': user_id,
                'user_info': user_info,
                'text': text,
                'timestamp': ts,
            })

        print(f"✓ 사용자 정보 수집 완료: {len(enriched_replies)}개")

        return enriched_replies

    def find_latest_attendance_thread(self, channel_id: str, keywords: List[str] = None, include_bot: bool = True, bot_only: bool = False) -> Optional[Dict]:
        """
        채널에서 가장 최신 출석체크 스레드 찾기

        Args:
            channel_id (str): 채널 ID
            keywords (List[str]): 검색 키워드 리스트 (기본값: ["출석 스레드", "출석체크", "출석"])
            include_bot (bool): 봇 메시지 포함 여부 (기본값: True)
            bot_only (bool): 봇 메시지만 검색 (기본값: False)

        Returns:
            Optional[Dict]: 찾은 메시지 정보 (ts, text, user 등), 없으면 None
        """
        if keywords is None:
            keywords = ["출석 스레드", "출석체크", "출석"]

        try:
            print(f"\n[Slack] 최신 출석체크 스레드 검색 중...")
            print(f"  - 검색 키워드: {', '.join(keywords)}")
            if bot_only:
                print(f"  - 봇 메시지만 검색")
            else:
                print(f"  - 봇 메시지 포함: {include_bot}")

            # 최근 메시지 가져오기 (최대 100개)
            response = self.client.conversations_history(
                channel=channel_id,
                limit=100
            )

            if not response['ok']:
                raise SlackApiError("API 호출 실패", response)

            messages = response['messages']

            # 키워드를 포함한 메시지 찾기 (최신순)
            for message in messages:
                text = message.get('text', '').lower()

                # 봇 메시지만 검색
                if bot_only and not message.get('bot_id'):
                    continue

                # Bot 메시지 제외 (옵션)
                if not include_bot and message.get('bot_id'):
                    continue

                # 키워드 검색
                for keyword in keywords:
                    if keyword.lower() in text:
                        print(f"✓ 출석체크 스레드 발견!")
                        print(f"  - 메시지: {message.get('text', '')[:100]}...")
                        print(f"  - 작성자: {'봇' if message.get('bot_id') else '사용자'}")

                        return {
                            'ts': message.get('ts'),
                            'text': message.get('text'),
                            'user': message.get('user'),
                            'bot_id': message.get('bot_id'),
                        }

            print("✗ 출석체크 스레드를 찾을 수 없습니다.")
            return None

        except SlackApiError as e:
            print(f"✗ 메시지 검색 실패: {e.response['error']}")
            return None

    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """
        이메일 주소로 User ID 찾기

        Args:
            email (str): 슬랙 이메일 주소

        Returns:
            Optional[str]: User ID (U로 시작), 실패 시 None
        """
        try:
            response = self.client.users_lookupByEmail(email=email)

            if response['ok']:
                user_id = response['user']['id']
                print(f"✓ 이메일로 User ID 찾기 성공: {email} → {user_id}")
                return user_id
            else:
                print(f"✗ 이메일로 User ID 찾기 실패: {email}")
                return None

        except SlackApiError as e:
            print(f"✗ 이메일로 User ID 찾기 실패: {e.response['error']}")
            return None

    def send_dm(self, user_id_or_email: str, message: str) -> bool:
        """
        특정 사용자에게 DM 전송 (User ID 또는 이메일 주소 모두 지원)

        Args:
            user_id_or_email (str): Slack User ID (U로 시작) 또는 이메일 주소
            message (str): 메시지 내용

        Returns:
            bool: 전송 성공 여부
        """
        try:
            user_id = user_id_or_email

            # 이메일 형식이면 User ID로 변환
            if '@' in user_id_or_email:
                print(f"[DM] 이메일 주소 감지: {user_id_or_email}")
                user_id = self.get_user_id_by_email(user_id_or_email)
                if not user_id:
                    print(f"✗ DM 전송 실패: 이메일로 사용자를 찾을 수 없습니다 ({user_id_or_email})")
                    return False

            # 봇 자신인지 확인
            if user_id.startswith('B'):
                print(f"✗ DM 전송 실패: 봇에게는 DM을 보낼 수 없습니다 (User ID: {user_id})")
                return False

            print(f"[DM] User ID로 DM 전송 시도: {user_id}")

            # DM 채널 열기
            response = self.client.conversations_open(users=[user_id])

            if not response['ok']:
                raise SlackApiError("DM 채널 열기 실패", response)

            channel_id = response['channel']['id']

            # 메시지 전송
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=message
            )

            if response['ok']:
                print(f"✓ DM 전송 성공")
                return True
            else:
                print(f"✗ DM 전송 실패")
                return False

        except SlackApiError as e:
            print(f"✗ DM 전송 실패: {e.response['error']}")
            return False

    def post_thread_reply(self, channel_id: str, thread_ts: str, message: str) -> bool:
        """
        스레드에 댓글 작성

        Args:
            channel_id (str): 채널 ID
            thread_ts (str): 스레드 타임스탬프
            message (str): 메시지 내용

        Returns:
            bool: 전송 성공 여부
        """
        try:
            # @channel, @here 등을 슬랙 형식으로 변환
            converted_message = self.convert_mentions(message)

            response = self.client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=converted_message
            )

            if response['ok']:
                print(f"✓ 스레드 댓글 작성 성공")
                return True
            else:
                print(f"✗ 스레드 댓글 작성 실패")
                return False

        except SlackApiError as e:
            print(f"✗ 스레드 댓글 작성 실패: {e.response['error']}")
            return False

    def post_message(self, channel_id: str, message: str) -> Optional[Dict]:
        """
        채널에 일반 메시지 전송 (출석 스레드 생성용)

        Args:
            channel_id (str): 채널 ID
            message (str): 메시지 내용

        Returns:
            Optional[Dict]: 전송 성공 시 메시지 정보 (ts, text 등), 실패 시 None
        """
        try:
            # @channel, @here 등을 슬랙 형식으로 변환
            converted_message = self.convert_mentions(message)

            response = self.client.chat_postMessage(
                channel=channel_id,
                text=converted_message
            )

            if response['ok']:
                print(f"✓ 메시지 전송 성공")
                return {
                    'ts': response['ts'],
                    'text': message,
                    'channel': channel_id
                }
            else:
                print(f"✗ 메시지 전송 실패")
                return None

        except SlackApiError as e:
            print(f"✗ 메시지 전송 실패: {e.response['error']}")
            return None

    def join_channel(self, channel_id: str) -> bool:
        """
        퍼블릭 채널에 자동으로 참여

        Args:
            channel_id (str): 채널 ID

        Returns:
            bool: 참여 성공 여부
        """
        try:
            response = self.client.conversations_join(channel=channel_id)

            if response['ok']:
                print(f"✓ 채널 참여 성공: {channel_id}")
                return True
            else:
                print(f"✗ 채널 참여 실패")
                return False

        except SlackApiError as e:
            error = e.response.get('error', 'unknown')

            # 이미 채널에 있는 경우
            if error == 'already_in_channel':
                print(f"✓ 이미 채널에 참여 중: {channel_id}")
                return True

            # 프라이빗 채널이거나 존재하지 않는 경우
            elif error == 'channel_not_found':
                print(f"✗ 채널 참여 실패: 프라이빗 채널이거나 존재하지 않는 채널입니다")
                print(f"  → 프라이빗 채널은 수동으로 봇을 초대해야 합니다")
                return False

            # 아카이브된 채널
            elif error == 'is_archived':
                print(f"✗ 채널 참여 실패: 아카이브된 채널입니다")
                return False

            # 권한 부족
            elif error == 'missing_scope':
                print(f"✗ 채널 참여 실패: 'channels:join' 권한이 필요합니다")
                print(f"  → Slack App 설정에서 'channels:join' scope를 추가하세요")
                return False

            print(f"✗ 채널 참여 실패: {error}")
            return False


# 테스트 코드
if __name__ == '__main__':
    from config.settings import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, SLACK_THREAD_TS

    if not SLACK_BOT_TOKEN:
        print("✗ SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        print("  .env 파일을 생성하고 토큰을 입력하세요.")
    else:
        handler = SlackHandler(SLACK_BOT_TOKEN)

        # 연결 테스트
        if handler.test_connection():
            print("\n슬랙 API 연결이 정상적으로 작동합니다!")

            # 스레드 댓글 가져오기 테스트 (SLACK_THREAD_TS가 설정된 경우)
            if SLACK_CHANNEL_ID and SLACK_THREAD_TS:
                replies = handler.get_replies_with_user_info(SLACK_CHANNEL_ID, SLACK_THREAD_TS)
                print(f"\n가져온 댓글 샘플 (최대 3개):")
                for i, reply in enumerate(replies[:3], 1):
                    user_info = reply['user_info']
                    name = user_info.get('real_name', '알 수 없음') if user_info else '알 수 없음'
                    print(f"  {i}. {name}: {reply['text'][:50]}...")
