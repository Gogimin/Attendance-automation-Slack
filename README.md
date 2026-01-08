# 슬랙 출석체크 자동화 시스템 📊

> 슬랙 API와 구글 스프레드시트 API를 활용한 **완전 자동화된 출석 관리 시스템**

**더블클릭 한 번으로 실행 가능!** 🚀

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Educational-orange.svg)](LICENSE)

---

## 📖 프로젝트 개요

이 프로젝트는 슬랙(Slack) 메신저를 활용한 출석체크를 완전 자동화하는 웹 기반 시스템입니다.

### 🎯 해결하는 문제
- 슬랙 스레드에서 수동으로 출석자를 일일이 확인하고 엑셀에 입력하는 번거로움
- 반복적인 출석 체크 작업의 자동화 필요성
- 여러 워크스페이스/그룹을 관리해야 하는 복잡성

### ✨ 제공하는 솔루션
- 슬랙 댓글 자동 분석 및 출석자 파싱
- 구글 스프레드시트 자동 업데이트
- 예약된 시간에 자동 실행
- 웹 UI를 통한 직관적인 관리
- EXE 파일로 배포하여 비개발자도 쉽게 사용

---

## 🌟 주요 기능

### 1️⃣ 다중 워크스페이스 지원
- 여러 슬랙 워크스페이스를 하나의 프로그램으로 관리
- 워크스페이스별 독립적인 설정 (Slack Bot Token, 스프레드시트 ID 등)
- 웹 UI에서 드롭다운으로 간편하게 전환

### 2️⃣ 슬랙 API 연동
- **출석 스레드 자동 감지**: "출석", "출석체크" 키워드로 최신 스레드 자동 검색
- **유연한 패턴 인식**: "이름/출석했습니다", "이름 출석", "이름 입실" 등 다양한 형식 지원
- **슬랙 링크 파싱**: 슬랙 URL을 붙여넣으면 자동으로 Thread TS 추출
- **출석 스레드 자동 생성**: 예약된 시간에 출석 체크 스레드 자동 게시

### 3️⃣ 구글 스프레드시트 연동
- 학생/구성원 명단 자동 읽기
- O/X/△ 문자로 출석 상태 표시
- 출석자 자동 O 표시, 미출석자 자동 X 표시
- 배치 업데이트로 빠른 처리

### 4️⃣ 알림 기능
- 출석체크 스레드에 완료 댓글 자동 작성
- 담당자에게 상세 DM 전송 (출석률, 출석자 명단, 미출석자 명단)

### 5️⃣ 자동 실행 스케줄 🆕
- **매주 특정 요일/시간에 출석 스레드 자동 생성**
- **매주 특정 요일/시간에 출석 자동 집계**
- 한국 시간대 (KST, UTC+9) 지원
- 워크스페이스별 독립적인 스케줄 설정
- 자동 열 증가 모드: 매주 다음 열로 자동 이동 (H → I → J → ...)
- 웹 UI에서 간편하게 스케줄 관리

### 6️⃣ Flask 웹 UI
- 직관적이고 아름다운 그라데이션 디자인
- 실시간 진행 상황 표시
- 출석 통계 대시보드
- 워크스페이스 관리 (추가/삭제)
- 스케줄 설정 UI

### 7️⃣ EXE 빌드 지원
- Python 설치 없이 실행 가능한 독립 실행 파일
- PyInstaller를 사용한 원클릭 빌드
- 다른 컴퓨터에 쉽게 배포

## 🚀 빠른 시작

### 1. 패키지 설치 (최초 1회만)

```bash
conda activate auto
pip install -r requirements.txt
```

### 2. 프로그램 실행

**방법 A: Python으로 직접 실행 (개발/테스트)**
```
실행.bat 더블클릭
```

**방법 B: EXE 파일로 빌드 (배포)**
```
빌드.bat 더블클릭
```
→ `dist/슬랙출석체크/슬랙출석체크.exe` 생성
→ EXE 파일 더블클릭으로 실행!

브라우저가 자동으로 열리고 `http://127.0.0.1:5000`에서 앱이 실행됩니다.

---

## 📁 프로젝트 구조

```
SLACK_CHECK/
├── 실행.bat                      # Flask 앱 실행 (개발/테스트용)
├── 빌드.bat                      # EXE 파일 빌드
├── 아이콘빌드.bat                # 아이콘 포함 빌드
├── app_flask.py                  # Flask 메인 애플리케이션
├── build_exe.py                  # 빌드 스크립트
├── attendance_app.spec           # PyInstaller 설정 파일
├── requirements.txt              # Python 패키지 의존성
│
├── README.md                     # 📖 이 파일 (프로젝트 소개)
├── CLAUDE.md                     # 📋 프로젝트 계획 및 진행 상황
├── 워크스페이스 추가.md          # 📝 워크스페이스 추가 가이드
├── 서버 배포.md                  # 🚀 서버 배포 가이드
├── 프로젝트 구조.md              # 🗂️ 상세 프로젝트 구조
├── 추가 기능 제안.md             # 💡 향후 개선 제안
│
├── src/                          # 소스 코드
│   ├── __init__.py
│   ├── slack_handler.py          # Slack API 처리
│   ├── sheets_handler.py         # Google Sheets API 처리
│   ├── parser.py                 # 출석 댓글 파싱 로직
│   ├── utils.py                  # 유틸리티 함수 (링크 파싱, 열 변환 등)
│   └── workspace_manager.py      # 워크스페이스 관리자
│
├── templates/                    # Flask HTML 템플릿
│   └── index.html                # 메인 웹 UI
│
├── static/                       # 정적 파일 (CSS, JS)
│   ├── css/
│   │   └── style.css             # 웹 UI 스타일
│   └── js/
│       └── app.js                # 프론트엔드 JavaScript
│
├── workspaces/                   # 워크스페이스 설정
│   ├── README.md                 # 워크스페이스 추가 가이드
│   └── [워크스페이스명]/         # 각 워크스페이스 폴더
│       ├── config.json           # 슬랙/구글 시트 설정
│       └── credentials.json      # 구글 서비스 계정 키
│
├── img/                          # 이미지 및 아이콘 (README 용도)
│
└── .gitignore                    # Git 제외 파일 목록
```

### 핵심 파일 설명

| 파일 | 설명 |
|------|------|
| [app_flask.py](app_flask.py) | Flask 웹 서버 메인 파일, API 엔드포인트, 스케줄러 관리 |
| [src/slack_handler.py](src/slack_handler.py) | Slack API 연동 (메시지 읽기, 댓글 수집, DM 전송) |
| [src/sheets_handler.py](src/sheets_handler.py) | Google Sheets API 연동 (명단 읽기, 출석 업데이트) |
| [src/parser.py](src/parser.py) | 출석 댓글 파싱 (정규표현식 패턴 매칭) |
| [src/workspace_manager.py](src/workspace_manager.py) | 다중 워크스페이스 관리 |
| [src/utils.py](src/utils.py) | 유틸리티 함수 (슬랙 링크 파싱, 열 변환) |

---

## ⚙️ 설치 및 설정 가이드

### 1. 필수 요구사항

| 항목 | 요구사항 |
|------|----------|
| Python | 3.11 이상 |
| 환경 | Conda 또는 venv |
| Slack | 워크스페이스 관리자 권한 |
| Google | 구글 클라우드 프로젝트 |

### 2. Slack 앱 설정 🔧

#### Step 1: Slack 앱 생성
1. [Slack API 페이지](https://api.slack.com/apps)에서 **Create New App** 클릭
2. **From scratch** 선택
3. 앱 이름과 워크스페이스 선택

#### Step 2: Bot Token Scopes 추가
**OAuth & Permissions** 메뉴에서 다음 권한 추가:

| Scope | 설명 | 필수 여부 |
|-------|------|-----------|
| `channels:history` | 채널 메시지 읽기 | ✅ 필수 |
| `channels:read` | 채널 정보 읽기 | ✅ 필수 |
| `channels:join` | 퍼블릭 채널 자동 참여 | ✅ 필수 |
| `users:read` | 사용자 정보 읽기 | ✅ 필수 |
| `users:read.email` | 이메일로 사용자 찾기 | ✅ 필수 |
| `chat:write` | 메시지 작성 | ✅ 필수 |
| `im:write` | DM 전송 | ✅ 필수 |

#### Step 3: 워크스페이스에 설치
1. **Install to Workspace** 버튼 클릭
2. 권한 승인
3. **Bot User OAuth Token** 복사 (xoxb-로 시작)
4. ~~출석체크 채널에 봇 초대 (`@봇이름` 멘션)~~ → `channels:join` 권한으로 자동 참여!

### 3. Google Sheets API 설정 📊

#### Step 1: Google Cloud 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성

#### Step 2: Google Sheets API 활성화
1. **API 및 서비스** → **라이브러리**
2. "Google Sheets API" 검색 후 활성화

#### Step 3: 서비스 계정 생성
1. **API 및 서비스** → **사용자 인증 정보**
2. **사용자 인증 정보 만들기** → **서비스 계정**
3. 서비스 계정 이름 입력 후 생성
4. 생성된 서비스 계정 클릭 → **키** 탭
5. **키 추가** → **새 키 만들기** → **JSON** 선택
6. 다운로드한 JSON 파일 저장

#### Step 4: 스프레드시트 공유
1. 구글 스프레드시트 열기
2. **공유** 버튼 클릭
3. 서비스 계정 이메일 추가 (JSON 파일의 `client_email` 값)
4. **편집자** 권한 부여

### 4. 워크스페이스 설정 📂

#### 워크스페이스 폴더 구조
```
workspaces/
└── [워크스페이스명]/
    ├── config.json          # 슬랙/구글 시트 설정
    └── credentials.json     # 구글 서비스 계정 키
```

#### config.json 예시

```json
{
  "name": "학교A",
  "slack_bot_token": "xoxb-YOUR-SLACK-BOT-TOKEN-HERE",
  "slack_channel_id": "C01234ABCDE",
  "spreadsheet_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCdE",
  "sheet_name": "출석현황",
  "name_column": "B",
  "start_row": 4,
  "notification_user_id": "",
  "auto_schedule": {
    "enabled": false,
    "create_thread_day": "",
    "create_thread_time": "",
    "create_thread_message": "📢 출석 스레드입니다.\n\n\"이름/출석했습니다\" 형식으로 댓글 달아주세요!",
    "check_attendance_day": "",
    "check_attendance_time": "",
    "check_attendance_column": "K",
    "check_completion_message": "[자동] 출석 체크를 완료했습니다.\n출석: {present}명 / 미출석: {absent}명",
    "auto_column_enabled": false,
    "start_column": "H",
    "end_column": "O"
  }
}
```

#### 설정 항목 설명

| 항목 | 설명 | 예시 |
|------|------|------|
| `name` | 워크스페이스 표시 이름 | "학교A" |
| `slack_bot_token` | Slack Bot Token (xoxb-로 시작) | "xoxb-YOUR-TOKEN-HERE" |
| `slack_channel_id` | 출석체크 채널 ID | "C01234ABCDE" |
| `spreadsheet_id` | 구글 스프레드시트 ID | "1AbCdEfG..." |
| `sheet_name` | 시트 이름 | "출석현황" |
| `name_column` | 이름 열 (A, B, C...) | "B" |
| `start_row` | 명단 시작 행 (1-based) | 4 |

💡 **자세한 워크스페이스 추가 방법**: [워크스페이스 추가.md](워크스페이스%20추가.md) 참조

---

## 🎯 사용 방법

### 기본 출석체크 플로우

#### 1️⃣ 프로그램 실행
```bash
# 실행.bat 더블클릭 또는
conda activate auto
python app_flask.py
```
→ 브라우저가 자동으로 열리고 `http://127.0.0.1:5000` 접속

#### 2️⃣ 워크스페이스 선택
- 상단 드롭다운에서 출석체크할 워크스페이스 선택

#### 3️⃣ 출석 스레드 선택
**방법 A: 자동 감지**
- "스레드 자동 감지" 버튼 클릭
- 최신 "출석" 키워드가 포함된 메시지 자동 검색

**방법 B: 수동 입력**
- 슬랙 스레드 링크 복사하여 붙여넣기
- 또는 Thread TS 직접 입력 (예: `1760337471.753399`)

#### 4️⃣ 출석 체크 설정
- **열 선택**: 출석을 표시할 열 입력 (예: K, L, M)
- **옵션 선택**:
  - ✅ 미출석자 자동 X 표시
  - ✅ 스레드에 완료 댓글 작성
  - ✅ 담당자에게 DM 전송

#### 5️⃣ 출석체크 실행
- "출석체크 시작" 버튼 클릭
- 실시간 진행 상황 확인
- 결과 확인:
  - 출석자 명단
  - 미출석자 명단
  - 출석률 통계

---

### 자동 스케줄 설정

#### 예약 실행 설정 방법

1. **"스케줄 설정" 탭 클릭**
2. **출석 스레드 생성 설정**
   - 요일 선택 (예: 토요일)
   - 시간 입력 (예: 09:00)
   - 메시지 작성 (예: "📢 출석 체크 시작!")
3. **출석 집계 설정**
   - 요일 선택 (예: 토요일)
   - 시간 입력 (예: 21:00)
   - 출석 체크할 열 선택 (예: K)
4. **자동 열 증가 모드** (선택사항)
   - 활성화 시 매주 다음 열로 자동 이동 (H → I → J → ...)
   - 시작 열, 끝 열 설정
5. **알림 수신자 설정**
   - User ID 또는 이메일 주소 입력
6. **저장** 버튼 클릭

#### 스케줄 예시

**매주 토요일 오전 9시에 출석 스레드 생성 → 오후 9시에 자동 집계**
```
출석 스레드 생성: 토요일 09:00
출석 집계: 토요일 21:00
자동 열 증가: H → I → J → ... → O
```

---

## 📦 EXE 빌드

### 빌드 방법

```
빌드.bat 더블클릭
```

또는 터미널에서:
```bash
conda activate auto
python build_exe.py
```

### 빌드 결과

```
dist/슬랙출석체크/
├── 슬랙출석체크.exe        # 메인 실행 파일
├── templates/              # HTML 템플릿
├── static/                 # CSS, JS 파일
├── workspaces/             # 워크스페이스 설정
└── ... (기타 의존성 파일들)
```

### 배포하기

1. `dist/슬랙출석체크/` 폴더 전체를 복사
2. 다른 컴퓨터에 붙여넣기
3. `슬랙출석체크.exe` 더블클릭
4. 완료! (Python 설치 필요 없음)

## 💡 자주 묻는 질문 (FAQ)

### Q1. Python이 없어도 실행 가능한가요?
**A:** 네! EXE 파일로 빌드하면 Python 설치 없이 실행 가능합니다.
```
빌드.bat 더블클릭 → dist/슬랙출석체크/슬랙출석체크.exe 실행
```

### Q2. 여러 학교/워크스페이스를 관리할 수 있나요?
**A:** 네! `workspaces/` 폴더에 여러 워크스페이스를 추가하고 웹 UI에서 드롭다운으로 선택하면 됩니다.
각 워크스페이스는 독립적인 설정을 가집니다.

### Q3. 자동 스케줄이 실행되지 않아요.
**A:** 다음을 확인하세요:
- 프로그램이 실행 중인지 확인 (프로그램 종료 시 스케줄 중단)
- 스케줄 설정이 올바른지 확인 (요일, 시간)
- 한국 시간대(KST)가 적용되는지 확인

### Q4. 슬랙 링크를 붙여넣었는데 인식이 안돼요.
**A:** 슬랙 링크는 다음 형식이어야 합니다:
```
https://workspace.slack.com/archives/C1234567890/p1760337471753399
```
또는 Thread TS를 직접 입력하세요: `1760337471.753399`

### Q5. 출석 체크가 누락되는 학생이 있어요.
**A:** 다음을 확인하세요:
- 슬랙 댓글 형식: "이름/출석했습니다" 또는 "이름 출석"
- 구글 시트의 이름 철자와 댓글의 이름 철자가 일치하는지 확인
- 댓글 작성 시간이 스레드 생성 이후인지 확인

### Q6. 서버로 배포할 수 있나요?
**A:** 네! [서버 배포.md](서버%20배포.md) 문서를 참조하세요.
AWS, GCP, Azure 등에서 24시간 실행 가능합니다.

---

## 🔧 문제 해결 (Troubleshooting)

### ❌ Slack API 권한 오류
**증상**: "missing_scope" 또는 "not_authed" 오류

**해결 방법**:
1. [Slack API 페이지](https://api.slack.com/apps)에서 앱 설정 확인
2. **OAuth & Permissions** → Bot Token Scopes 확인
3. 필요한 권한이 모두 추가되었는지 확인
4. 앱을 워크스페이스에 재설치
5. Bot Token을 다시 복사하여 `config.json` 업데이트

### ❌ Google Sheets 접근 오류
**증상**: "The caller does not have permission" 오류

**해결 방법**:
1. `credentials.json` 파일 경로 확인
2. 서비스 계정 이메일 확인 (JSON 파일의 `client_email`)
3. 구글 스프레드시트 **공유** 설정에서 서비스 계정 이메일 추가
4. **편집자** 권한 부여 확인

### ❌ 워크스페이스가 웹에 표시되지 않음
**증상**: 드롭다운에 워크스페이스가 없음

**해결 방법**:
1. 워크스페이스 폴더 구조 확인:
   ```
   workspaces/
   └── [워크스페이스명]/
       ├── config.json
       └── credentials.json
   ```
2. `config.json` 파일이 올바른 JSON 형식인지 확인
3. 필수 필드가 모두 포함되었는지 확인
4. 프로그램 재시작

### ❌ EXE 빌드 실패
**증상**: PyInstaller 오류

**해결 방법**:
```bash
# 1. PyInstaller 재설치
pip uninstall pyinstaller
pip install pyinstaller

# 2. 모든 패키지 재설치
pip install -r requirements.txt

# 3. 캐시 삭제 후 재빌드
python build_exe.py
```

### ❌ 출석 파싱 오류
**증상**: 댓글이 있는데 출석자가 0명으로 표시

**해결 방법**:
1. 댓글 형식 확인: "이름/출석" 또는 "이름 출석"
2. 봇 메시지는 자동으로 제외됨
3. Thread TS가 올바른지 확인 (원본 메시지가 아닌 댓글 Thread TS)

---

## 📚 관련 문서

| 문서 | 설명 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | 📋 프로젝트 계획 및 진행 상황 (TASK 목록) |
| [워크스페이스 추가.md](워크스페이스%20추가.md) | 📝 새 워크스페이스 추가 가이드 |
| [서버 배포.md](서버%20배포.md) | 🚀 클라우드 서버 배포 가이드 (AWS, GCP, Azure) |
| [프로젝트 구조.md](프로젝트%20구조.md) | 🗂️ 상세 프로젝트 구조 및 모듈 설명 |
| [추가 기능 제안.md](추가%20기능%20제안.md) | 💡 향후 개선 사항 및 기능 제안 |
| [workspaces/README.md](workspaces/README.md) | 📂 워크스페이스 폴더 구조 및 설정 방법 |

---

## 🎉 완료된 기능

### ✅ 핵심 기능
- [x] 다중 워크스페이스 지원
- [x] Slack API 연동 (댓글 수집, DM 전송, 메시지 작성)
- [x] Google Sheets API 연동 (명단 읽기, 출석 업데이트)
- [x] 출석 댓글 파싱 (정규표현식 기반)
- [x] 웹 UI (Flask)

### ✅ 고급 기능
- [x] 출석 스레드 자동 감지
- [x] 슬랙 링크 자동 파싱
- [x] 미출석자 자동 X 표시
- [x] 알림 기능 (스레드 댓글, DM)
- [x] 통계 대시보드

### ✅ 자동화 기능 🆕
- [x] 자동 실행 스케줄 (APScheduler)
- [x] 출석 스레드 자동 생성
- [x] 출석 자동 집계
- [x] 자동 열 증가 모드
- [x] 한국 시간대 (KST) 지원

### ✅ 배포 및 관리
- [x] EXE 빌드 (PyInstaller)
- [x] 워크스페이스 추가/삭제 (웹 UI)
- [x] 예약 현황 조회

---

## 🚧 향후 개선 사항

### 우선순위 높음
- [ ] 로깅 시스템 (실행 이력 저장)
- [ ] 출석률 추이 그래프
- [ ] 아이콘 추가 (브랜딩)

### 우선순위 중간
- [ ] 출석 통계 CSV 내보내기
- [ ] 이메일 알림 기능
- [ ] 다크 모드

### 우선순위 낮음
- [ ] 모바일 반응형 UI
- [ ] 다국어 지원 (영어)

💡 더 많은 아이디어는 [추가 기능 제안.md](추가%20기능%20제안.md)를 참조하세요.

---

## 📊 기술 스택

### Backend
- **Flask** 3.0.0 - 웹 프레임워크
- **APScheduler** 3.10.4 - 자동 실행 스케줄러
- **pytz** - 한국 시간대 (KST) 지원

### APIs
- **slack-sdk** 3.26.1 - Slack Web API
- **google-api-python-client** 2.108.0 - Google Sheets API
- **google-auth** 2.25.2 - Google 인증

### Frontend
- **HTML5**, **CSS3** - 그라데이션 디자인
- **JavaScript (Vanilla)** - 프론트엔드 로직

### Build & Deploy
- **PyInstaller** 6.3.0 - EXE 빌드
- **Python** 3.11+ - 메인 언어

### 전체 의존성
자세한 패키지 목록은 [requirements.txt](requirements.txt)를 참조하세요.

---

## 🏗️ 프로젝트 아키텍처

```
┌─────────────────┐
│   웹 UI (Flask) │ ← 사용자 인터페이스
└────────┬────────┘
         │
    ┌────┴─────────────────┐
    │                      │
┌───▼───────┐      ┌──────▼──────┐
│  Slack    │      │   Google    │
│  Handler  │      │   Sheets    │
│           │      │   Handler   │
└───────────┘      └─────────────┘
    │                      │
    │                      │
┌───▼──────────────────────▼───┐
│   APScheduler (자동 실행)     │
└──────────────────────────────┘
```

---

## 👥 기여

이 프로젝트는 교육용으로 제작되었습니다.
기여, 이슈, 피드백은 언제나 환영합니다!

---

## 📄 라이선스

이 프로젝트는 교육 목적으로 자유롭게 사용 가능합니다.

---

## 🙏 감사의 말

- **Slack API** - 강력한 메시징 플랫폼 제공
- **Google Sheets API** - 스프레드시트 자동화 지원
- **Flask** - 간편한 웹 프레임워크
- **APScheduler** - 안정적인 스케줄링 라이브러리

---

<div align="center">

**Made with ❤️ using Python & Flask**

**v2.5** - 완전 자동화된 출석 관리 시스템 🎉

[⬆ 맨 위로 이동](#슬랙-출석체크-자동화-시스템-)

</div>
