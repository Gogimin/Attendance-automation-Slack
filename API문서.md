# API 문서 - 슬랙 출석체크 자동화

> **Base URL:** `http://127.0.0.1:5000`
>
> **Last Updated:** 2025-11-06

---

## 📋 목차

1. [출석 체크 API](#1-출석-체크-api)
2. [과제 체크 API](#2-과제-체크-api)
3. [워크스페이스 관리 API](#3-워크스페이스-관리-api)
4. [스케줄 관리 API](#4-스케줄-관리-api)
5. [스레드 검색 API](#5-스레드-검색-api)
6. [에러 코드](#6-에러-코드)

---

## 1. 출석 체크 API

### 1.1 출석 체크 실행

**Endpoint:** `POST /api/run-attendance`

**설명:** Slack 스레드에서 출석 댓글을 수집하고 Google Sheets에 자동으로 기록합니다.

#### Request Body
```json
{
  "workspace": "workspace_name",
  "thread_ts": "1234567890.123456",
  "column": "K",
  "mark_absent": true,
  "send_thread_reply": true,
  "send_dm": true,
  "thread_user": "U12345ABCD"
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|-----|------|-----|--------|------|
| `workspace` | string | ✅ | - | 워크스페이스 이름 |
| `thread_ts` | string | ✅ | - | Thread Timestamp 또는 Slack URL |
| `column` | string | ❌ | "K" | 출석을 기록할 열 (A-Z) |
| `mark_absent` | boolean | ❌ | true | 미출석자 X 표시 여부 |
| `send_thread_reply` | boolean | ❌ | true | 스레드 댓글 작성 여부 |
| `send_dm` | boolean | ❌ | true | DM 전송 여부 |
| `thread_user` | string | ❌ | null | 스레드 작성자 User ID (DM 수신자) |

#### Response (성공)
```json
{
  "success": true,
  "result": {
    "total_students": 50,
    "present": 45,
    "absent": 5,
    "matched_names": ["홍길동", "김철수", ...],
    "absent_names": ["이영희", "박민수", ...],
    "unmatched_names": ["닉네임1"],
    "success_count": 50,
    "column": "K",
    "notifications": ["스레드 댓글 작성 완료", "DM 전송 완료"]
  }
}
```

#### Response (실패)
```json
{
  "success": false,
  "error": "워크스페이스를 찾을 수 없습니다."
}
```

#### 예제 (cURL)
```bash
curl -X POST http://127.0.0.1:5000/api/run-attendance \
  -H "Content-Type: application/json" \
  -d '{
    "workspace": "test_workspace",
    "thread_ts": "1234567890.123456",
    "column": "K",
    "mark_absent": true
  }'
```

#### 예제 (Python)
```python
import requests

response = requests.post(
    'http://127.0.0.1:5000/api/run-attendance',
    json={
        'workspace': 'test_workspace',
        'thread_ts': '1234567890.123456',
        'column': 'K',
        'mark_absent': True,
        'send_thread_reply': True,
        'send_dm': True,
        'thread_user': 'U12345ABCD'
    }
)

result = response.json()
print(f"출석: {result['result']['present']}명")
print(f"미출석: {result['result']['absent']}명")
```

---

## 2. 과제 체크 API

### 2.1 과제 체크 실행

**Endpoint:** `POST /api/run-assignment`

**설명:** Slack 과제 스레드에서 제출자를 수집하고 Google Sheets에 기록합니다.

#### Request Body
```json
{
  "workspace": "workspace_name",
  "thread_ts": "1234567890.123456",
  "column": "D",
  "mark_absent": true
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|-----|------|-----|--------|------|
| `workspace` | string | ✅ | - | 워크스페이스 이름 |
| `thread_ts` | string | ✅ | - | 과제 스레드 TS 또는 URL |
| `column` | string | ❌ | "D" | 과제 제출을 기록할 열 |
| `mark_absent` | boolean | ❌ | true | 미제출자 X 표시 여부 |

#### Response
```json
{
  "success": true,
  "result": {
    "total_students": 50,
    "submitted": ["홍길동", "김철수", ...],
    "not_submitted": ["이영희", "박민수", ...],
    "submitted_count": 40,
    "not_submitted_count": 10,
    "column": "D",
    "success_count": 50
  }
}
```

---

### 2.2 과제 체크 기록 조회

**Endpoint:** `GET /api/assignment-history/<workspace_name>`

**설명:** 특정 워크스페이스의 과제 체크 기록을 조회합니다.

#### Path Parameters
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|-----|------|
| `workspace_name` | string | ✅ | 워크스페이스 이름 |

#### Query Parameters
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|-----|--------|------|
| `limit` | integer | ❌ | 20 | 최대 조회 개수 (최대 100) |

#### Response
```json
{
  "success": true,
  "history": [
    {
      "id": "20251106123456",
      "timestamp": "2025-11-06 12:34:56",
      "thread_ts": "1234567890.123456",
      "thread_link": "https://slack.com/...",
      "column": "D",
      "total_students": 50,
      "submitted_count": 40,
      "not_submitted_count": 10,
      "submitted_list": ["홍길동", ...],
      "not_submitted_list": ["이영희", ...]
    }
  ]
}
```

#### 예제
```bash
curl http://127.0.0.1:5000/api/assignment-history/test_workspace?limit=10
```

---

## 3. 워크스페이스 관리 API

### 3.1 워크스페이스 목록 조회

**Endpoint:** `GET /api/workspaces`

**설명:** 모든 워크스페이스 목록을 조회합니다.

#### Response
```json
{
  "success": true,
  "workspaces": [
    {
      "name": "테스트 워크스페이스",
      "folder_name": "test_workspace",
      "channel_id": "C12345ABCD",
      "spreadsheet_id": "1ABC...",
      "sheet_name": "Sheet1"
    }
  ]
}
```

---

### 3.2 워크스페이스 추가

**Endpoint:** `POST /api/workspaces/add`

**설명:** 새로운 워크스페이스를 추가합니다.

#### Request Body
```json
{
  "workspace_name": "test_workspace",
  "display_name": "테스트 워크스페이스",
  "slack_bot_token": "xoxb-...",
  "slack_channel_id": "C12345ABCD",
  "assignment_channel_id": "C67890EFGH",
  "spreadsheet_id": "1ABC...",
  "sheet_name": "Sheet1",
  "assignment_sheet_name": "과제실습 모니터링",
  "name_column": "B",
  "start_row": 4,
  "credentials_json": {
    "type": "service_account",
    "project_id": "...",
    "private_key": "...",
    "client_email": "..."
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|-----|------|-----|--------|------|
| `workspace_name` | string | ✅ | - | 워크스페이스 폴더명 (영문, 숫자, _만) |
| `display_name` | string | ✅ | - | 화면에 표시될 이름 |
| `slack_bot_token` | string | ✅ | - | Slack Bot Token (xoxb-...) |
| `slack_channel_id` | string | ✅ | - | 출석 체크 채널 ID |
| `assignment_channel_id` | string | ❌ | slack_channel_id | 과제 체크 채널 ID |
| `spreadsheet_id` | string | ✅ | - | Google Sheets ID |
| `sheet_name` | string | ❌ | "Sheet1" | 출석 시트 이름 |
| `assignment_sheet_name` | string | ❌ | "과제실습 모니터링" | 과제 시트 이름 |
| `name_column` | string | ❌ | "B" | 이름 열 |
| `start_row` | integer | ❌ | 4 | 데이터 시작 행 |
| `credentials_json` | object | ✅ | - | Google Service Account JSON |

#### Response
```json
{
  "success": true,
  "message": "테스트 워크스페이스가 추가되었습니다.",
  "workspace_name": "test_workspace"
}
```

---

### 3.3 워크스페이스 삭제

**Endpoint:** `POST /api/workspaces/delete`

**설명:** 워크스페이스를 삭제합니다.

#### Request Body
```json
{
  "workspace_name": "test_workspace"
}
```

#### Response
```json
{
  "success": true,
  "message": "test_workspace 워크스페이스가 삭제되었습니다."
}
```

---

### 3.4 워크스페이스 수정

**Endpoint:** `POST /api/workspaces/edit/<workspace_name>`

**설명:** 워크스페이스 설정을 수정합니다.

#### Request Body
```json
{
  "display_name": "새로운 이름",
  "slack_channel_id": "C12345ABCD",
  "assignment_channel_id": "C67890EFGH",
  "sheet_name": "Sheet1",
  "assignment_sheet_name": "과제실습 모니터링",
  "name_column": "B",
  "start_row": 4,
  "notification_user_id": "U12345ABCD"
}
```

**참고:** 모든 필드는 선택사항입니다. 제공된 필드만 업데이트됩니다.

#### Response
```json
{
  "success": true,
  "message": "워크스페이스 정보가 업데이트되었습니다.",
  "updated_config": { ... }
}
```

---

### 3.5 워크스페이스 상세 정보 조회

**Endpoint:** `GET /api/workspaces/info/<workspace_name>`

**설명:** 워크스페이스의 상세 정보를 조회합니다.

#### Response
```json
{
  "success": true,
  "workspace": {
    "name": "test_workspace",
    "display_name": "테스트 워크스페이스",
    "slack_channel_id": "C12345ABCD",
    "assignment_channel_id": "C67890EFGH",
    "spreadsheet_id": "1ABC...",
    "sheet_name": "Sheet1",
    "assignment_sheet_name": "과제실습 모니터링",
    "name_column": "B",
    "start_row": 4,
    "notification_user_id": "U12345ABCD"
  }
}
```

---

### 3.6 동명이인 정보 조회

**Endpoint:** `GET /api/duplicate-names/<workspace_name>`

**설명:** 워크스페이스의 동명이인 설정을 조회합니다.

#### Response
```json
{
  "success": true,
  "duplicate_names": {
    "홍길동": [
      {
        "email": "hong1@example.com",
        "user_id": "U12345",
        "display_name": "홍길동(1반)",
        "sheet_row": 5,
        "note": "1반"
      },
      {
        "email": "hong2@example.com",
        "user_id": "U67890",
        "display_name": "홍길동(2반)",
        "sheet_row": 25,
        "note": "2반"
      }
    ]
  }
}
```

---

### 3.7 동명이인 정보 저장

**Endpoint:** `POST /api/duplicate-names/<workspace_name>`

**설명:** 동명이인 정보를 저장합니다. 이메일을 자동으로 Slack User ID로 변환합니다.

#### Request Body
```json
{
  "duplicate_names": {
    "홍길동": [
      {
        "email": "hong1@example.com",
        "display_name": "홍길동(1반)",
        "sheet_row": 5,
        "note": "1반"
      },
      {
        "email": "hong2@example.com",
        "display_name": "홍길동(2반)",
        "sheet_row": 25,
        "note": "2반"
      }
    ]
  }
}
```

#### Response (성공)
```json
{
  "success": true,
  "message": "동명이인 정보가 저장되었습니다.",
  "converted_data": {
    "홍길동": [
      {
        "email": "hong1@example.com",
        "user_id": "U12345",
        "display_name": "홍길동(1반)",
        "sheet_row": 5,
        "note": "1반"
      }
    ]
  }
}
```

#### Response (실패 - User ID 변환 실패)
```json
{
  "success": false,
  "error": "일부 이메일을 User ID로 변환할 수 없습니다.",
  "details": [
    "홍길동 - hong1@example.com: User ID를 찾을 수 없습니다."
  ]
}
```

---

## 4. 스케줄 관리 API

### 4.1 워크스페이스 스케줄 조회

**Endpoint:** `GET /api/schedule/<workspace_name>`

**설명:** 특정 워크스페이스의 스케줄 설정을 조회합니다.

#### Response
```json
{
  "success": true,
  "schedule": {
    "enabled": true,
    "schedules": [
      {
        "day": "토요일",
        "create_thread_time": "09:00",
        "check_attendance_time": "18:00",
        "check_attendance_column": "K"
      }
    ],
    "create_thread_message": "@channel\n출석 스레드입니다.",
    "check_completion_message": "[자동] 출석 체크 완료"
  },
  "notification_user_id": "U12345ABCD"
}
```

---

### 4.2 전체 스케줄 현황 조회

**Endpoint:** `GET /api/schedules/all`

**설명:** 모든 워크스페이스의 스케줄 현황을 조회합니다.

#### Response
```json
{
  "success": true,
  "schedules": [
    {
      "workspace_name": "테스트 워크스페이스",
      "folder_name": "test_workspace",
      "day": "토요일",
      "create_thread_time": "09:00",
      "check_attendance_time": "18:00",
      "check_attendance_column": "K",
      "notification_user_id": "U12345ABCD",
      "enabled": true
    }
  ],
  "total": 1
}
```

---

### 4.3 스케줄 저장

**Endpoint:** `POST /api/schedule`

**설명:** 자동 출석 체크 스케줄을 저장합니다.

#### Request Body
```json
{
  "workspace": "test_workspace",
  "notification_user_id": "U12345ABCD",
  "schedule": {
    "enabled": true,
    "schedules": [
      {
        "day": "토요일",
        "create_thread_time": "09:00",
        "check_attendance_time": "18:00",
        "check_attendance_column": "K"
      },
      {
        "day": "일요일",
        "create_thread_time": "10:00",
        "check_attendance_time": "19:00",
        "check_attendance_column": "L"
      }
    ],
    "create_thread_message": "@channel\n출석 스레드입니다.",
    "check_completion_message": "[자동] 출석 체크 완료",
    "auto_column_enabled": false,
    "start_column": "H",
    "end_column": "O"
  }
}
```

| 필드 | 설명 |
|-----|------|
| `enabled` | 스케줄 활성화 여부 |
| `schedules` | 스케줄 목록 (여러 개 가능) |
| `day` | 요일 (월요일, 화요일, ..., 일요일) |
| `create_thread_time` | 스레드 생성 시간 (HH:MM) |
| `check_attendance_time` | 출석 체크 시간 (HH:MM) |
| `check_attendance_column` | 출석 기록 열 |
| `auto_column_enabled` | 자동 열 증가 사용 여부 |
| `start_column` ~ `end_column` | 자동 열 범위 |

#### Response
```json
{
  "success": true,
  "message": "스케줄이 저장되었습니다."
}
```

**참고:** 스케줄 저장 시 APScheduler가 자동으로 재시작됩니다.

---

### 4.4 스케줄 삭제

**Endpoint:** `POST /api/schedule/delete`

**설명:** 특정 스케줄 항목을 삭제합니다.

#### Request Body
```json
{
  "workspace": "test_workspace",
  "schedule_index": 0
}
```

| 필드 | 설명 |
|-----|------|
| `schedule_index` | 삭제할 스케줄의 인덱스 (0부터 시작) |

#### Response
```json
{
  "success": true,
  "message": "스케줄이 삭제되었습니다.",
  "deleted_schedule": {
    "day": "토요일",
    "create_thread_time": "09:00",
    "check_attendance_time": "18:00",
    "check_attendance_column": "K"
  }
}
```

---

### 4.5 스케줄 활성화/비활성화

**Endpoint:** `POST /api/schedule/toggle`

**설명:** 스케줄을 활성화하거나 비활성화합니다.

#### Request Body
```json
{
  "workspace": "test_workspace"
}
```

#### Response
```json
{
  "success": true,
  "message": "스케줄이 활성화되었습니다.",
  "enabled": true
}
```

---

## 5. 스레드 검색 API

### 5.1 최신 출석 스레드 자동 감지

**Endpoint:** `POST /api/find-thread`

**설명:** Slack 채널에서 "출석" 키워드가 포함된 최신 메시지를 자동으로 찾습니다.

#### Request Body
```json
{
  "workspace": "test_workspace"
}
```

#### Response
```json
{
  "success": true,
  "thread_ts": "1234567890.123456",
  "thread_text": "출석 스레드입니다. 댓글로 출석해주세요!",
  "thread_user": "U12345ABCD"
}
```

#### 예제
```python
import requests

response = requests.post(
    'http://127.0.0.1:5000/api/find-thread',
    json={'workspace': 'test_workspace'}
)

result = response.json()
if result['success']:
    thread_ts = result['thread_ts']
    print(f"찾은 스레드: {thread_ts}")
```

---

## 6. 에러 코드

### HTTP 상태 코드

| 코드 | 설명 |
|-----|------|
| `200` | 성공 |
| `400` | 잘못된 요청 (파라미터 오류) |
| `404` | 리소스를 찾을 수 없음 |
| `500` | 서버 내부 오류 |

### 에러 응답 형식

```json
{
  "success": false,
  "error": "에러 메시지"
}
```

### 주요 에러 메시지

| 에러 메시지 | 원인 | 해결 방법 |
|-----------|------|----------|
| `워크스페이스를 찾을 수 없습니다.` | 존재하지 않는 워크스페이스 | 워크스페이스 이름 확인 |
| `Thread TS 형식이 올바르지 않습니다.` | 잘못된 Thread TS | Slack URL 또는 TS 형식 확인 |
| `슬랙 연결에 실패했습니다.` | Slack Bot Token 오류 | Token 유효성 확인 |
| `구글 시트 연결에 실패했습니다.` | Google Sheets 권한 오류 | 서비스 계정 공유 확인 |
| `유효하지 않은 워크스페이스 이름입니다.` | 경로 탐색 시도 감지 | 영문, 숫자, _ 만 사용 |

---

## 7. 공통 규칙

### Thread TS 형식

다음 형식 모두 지원:
```
1. Thread TS: "1234567890.123456"
2. Slack URL: "https://[workspace].slack.com/archives/[channel]/p[ts]"
```

### 열 형식

- A-Z 단일 문자만 지원
- 대소문자 구분 없음 (자동 변환)
- 예: "K", "k" → 모두 K열로 처리

### 워크스페이스 이름 규칙

- 영문, 숫자, 언더스코어(_)만 사용 가능
- 최대 50자
- `.`, `/`, `\`, null byte 금지
- 예: `test_workspace`, `class_2024_01`

---

## 8. 사용 예제

### Python으로 전체 출석 체크 플로우

```python
import requests

BASE_URL = "http://127.0.0.1:5000"

# 1. 최신 출석 스레드 찾기
response = requests.post(f"{BASE_URL}/api/find-thread", json={
    "workspace": "test_workspace"
})
thread_data = response.json()
thread_ts = thread_data['thread_ts']
thread_user = thread_data['thread_user']

print(f"출석 스레드 발견: {thread_ts}")

# 2. 출석 체크 실행
response = requests.post(f"{BASE_URL}/api/run-attendance", json={
    "workspace": "test_workspace",
    "thread_ts": thread_ts,
    "column": "K",
    "mark_absent": True,
    "send_thread_reply": True,
    "send_dm": True,
    "thread_user": thread_user
})

result = response.json()

if result['success']:
    print(f"✅ 출석 체크 완료!")
    print(f"  - 출석: {result['result']['present']}명")
    print(f"  - 미출석: {result['result']['absent']}명")
else:
    print(f"❌ 실패: {result['error']}")
```

### JavaScript로 워크스페이스 관리

```javascript
// 워크스페이스 목록 조회
fetch('http://127.0.0.1:5000/api/workspaces')
  .then(res => res.json())
  .then(data => {
    console.log('워크스페이스 목록:', data.workspaces);
  });

// 워크스페이스 추가
fetch('http://127.0.0.1:5000/api/workspaces/add', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    workspace_name: 'new_workspace',
    display_name: '새 워크스페이스',
    slack_bot_token: 'xoxb-...',
    slack_channel_id: 'C12345',
    spreadsheet_id: '1ABC...',
    credentials_json: { ... }
  })
})
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      console.log('✅ 워크스페이스 추가 완료!');
    }
  });
```

---

## 9. 보안 고려사항

### 1. 경로 탐색 방어
```
❌ 위험: workspace_name = "../../../etc/passwd"
✅ 방어: validate_workspace_name()로 검증
```

### 2. 민감정보 보호
- Slack Bot Token: 환경변수 또는 안전한 저장소 사용
- Google Credentials: 파일 권한 600으로 제한
- Secret Key: 환경변수 사용 권장

### 3. 에러 처리
- 프로덕션: 일반적인 에러 메시지만 반환
- 개발 모드: 상세 스택 트레이스 제공

---

## 10. 개발 팁

### API 테스트용 cURL 모음

```bash
# 출석 체크
curl -X POST http://127.0.0.1:5000/api/run-attendance \
  -H "Content-Type: application/json" \
  -d '{"workspace":"test","thread_ts":"1234567890.123456"}'

# 과제 체크
curl -X POST http://127.0.0.1:5000/api/run-assignment \
  -H "Content-Type: application/json" \
  -d '{"workspace":"test","thread_ts":"1234567890.123456"}'

# 워크스페이스 목록
curl http://127.0.0.1:5000/api/workspaces

# 스케줄 현황
curl http://127.0.0.1:5000/api/schedules/all

# 스레드 찾기
curl -X POST http://127.0.0.1:5000/api/find-thread \
  -H "Content-Type: application/json" \
  -d '{"workspace":"test"}'
```

---

**문서 버전:** 1.0.0
**마지막 업데이트:** 2025-11-06
**문의:** GitHub Issues
