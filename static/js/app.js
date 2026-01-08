// 전역 변수
let currentWorkspace = null;
let threadTS = null;
let threadUser = null;

// DOM 로드 완료 시
document.addEventListener('DOMContentLoaded', function() {
    loadWorkspaces();
    setupEventListeners();
    loadAllSchedules(); // 예약 현황 로드
    initializeToastContainer(); // Toast 컨테이너 초기화
    initializeEscapeKeyHandler(); // ESC 키 핸들러 초기화
});

// ========================================
// Toast 알림 시스템
// ========================================

function initializeToastContainer() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
}

function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) {
        initializeToastContainer();
        return showToast(message, type, duration);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const titles = {
        success: '성공',
        error: '오류',
        warning: '경고',
        info: '알림'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${titles[type] || titles.info}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast(this)">×</button>
    `;

    container.appendChild(toast);

    // 자동 제거
    if (duration > 0) {
        setTimeout(() => {
            closeToast(toast.querySelector('.toast-close'));
        }, duration);
    }
}

function closeToast(closeBtn) {
    const toast = closeBtn.closest('.toast');
    if (toast) {
        toast.classList.add('removing');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// ========================================
// ESC 키로 모달 닫기
// ========================================

function initializeEscapeKeyHandler() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' || e.keyCode === 27) {
            // 열려있는 모든 모달 찾기
            const openModals = document.querySelectorAll('.modal[style*="display: flex"]');
            if (openModals.length > 0) {
                // 가장 최근에 열린 모달 (마지막 모달) 닫기
                const lastModal = openModals[openModals.length - 1];

                // 모달 ID에 따라 적절한 닫기 함수 호출
                if (lastModal.id === 'add-workspace-modal') {
                    closeAddWorkspaceModal();
                } else if (lastModal.id === 'edit-workspace-modal') {
                    closeEditWorkspaceModal();
                } else if (lastModal.id === 'duplicate-names-modal') {
                    closeDuplicateNamesModal();
                } else if (lastModal.id === 'edit-schedule-modal') {
                    closeEditScheduleModal();
                } else {
                    // 기본 닫기 동작
                    lastModal.style.display = 'none';
                }
            }
        }
    });
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 워크스페이스 선택
    document.getElementById('workspace-select').addEventListener('change', onWorkspaceChange);

    // 워크스페이스 추가 버튼
    document.getElementById('add-workspace-btn').addEventListener('click', openAddWorkspaceModal);

    // 출석체크 열 드롭다운 선택 이벤트
    document.getElementById('column-select').addEventListener('change', function(e) {
        const selectedValue = e.target.value;
        if (selectedValue) {
            document.getElementById('column-input').value = selectedValue;
        }
    });

    // 과제체크 열 드롭다운 선택 이벤트
    document.getElementById('assignment-column-select').addEventListener('change', function(e) {
        const selectedValue = e.target.value;
        if (selectedValue) {
            document.getElementById('assignment-column').value = selectedValue;
        }
    });

    // 워크스페이스 삭제 버튼
    document.getElementById('delete-workspace-btn').addEventListener('click', deleteWorkspace);

    // 모달 닫기
    document.querySelector('.modal-close').addEventListener('click', closeAddWorkspaceModal);
    document.getElementById('cancel-add-workspace-btn').addEventListener('click', closeAddWorkspaceModal);

    // 워크스페이스 추가 제출
    document.getElementById('submit-add-workspace-btn').addEventListener('click', submitAddWorkspace);

    // Bot Token 파일 불러오기
    document.getElementById('load-token-btn').addEventListener('click', function() {
        document.getElementById('token-file-input').click();
    });

    document.getElementById('token-file-input').addEventListener('change', loadTokenFile);

    // Bot Token 초기화
    document.getElementById('clear-token-btn').addEventListener('click', function() {
        document.getElementById('new-bot-token').value = '';
    });

    // credentials 파일 불러오기
    document.getElementById('load-credentials-btn').addEventListener('click', function() {
        document.getElementById('credentials-file-input').click();
    });

    document.getElementById('credentials-file-input').addEventListener('change', loadCredentialsFile);

    // credentials 초기화
    document.getElementById('clear-credentials-btn').addEventListener('click', function() {
        document.getElementById('new-credentials').value = '';
    });

    // 스레드 모드 전환
    document.querySelectorAll('input[name="thread-mode"]').forEach(radio => {
        radio.addEventListener('change', onThreadModeChange);
    });

    // 스레드 찾기 버튼
    document.getElementById('find-thread-btn').addEventListener('click', findThread);

    // 수동 입력
    document.getElementById('thread-input').addEventListener('input', onManualInput);

    // 실행 버튼
    document.getElementById('run-btn').addEventListener('click', runAttendance);

    // 스케줄 활성화 토글
    document.getElementById('auto-schedule-enabled').addEventListener('change', toggleScheduleSettings);

    // 자동 열 증가 토글
    document.getElementById('auto-column-enabled').addEventListener('change', toggleAutoColumnSettings);

    // 스케줄 저장 버튼
    document.getElementById('save-schedule-btn').addEventListener('click', saveSchedule);

    // 예약 현황 새로고침 버튼
    document.getElementById('refresh-schedule-btn').addEventListener('click', loadAllSchedules);

    // 워크스페이스 수정 버튼
    document.getElementById('edit-workspace-btn').addEventListener('click', openEditWorkspaceModal);

    // 동명이인 관리 버튼
    document.getElementById('manage-duplicates-btn').addEventListener('click', openDuplicateNamesModal);

    // 워크스페이스 수정 모달 닫기
    const editWorkspaceModalClose = document.querySelectorAll('#edit-workspace-modal .modal-close')[0];
    if (editWorkspaceModalClose) {
        editWorkspaceModalClose.addEventListener('click', closeEditWorkspaceModal);
    }
    document.getElementById('cancel-edit-workspace-btn').addEventListener('click', closeEditWorkspaceModal);
    document.getElementById('save-edit-workspace-btn').addEventListener('click', saveEditWorkspace);

    // 동명이인 모달 닫기
    const duplicateModalClose = document.querySelectorAll('#duplicate-names-modal .modal-close')[0];
    if (duplicateModalClose) {
        duplicateModalClose.addEventListener('click', closeDuplicateNamesModal);
    }
    document.getElementById('cancel-duplicate-btn').addEventListener('click', closeDuplicateNamesModal);

    // 동명이인 그룹 추가
    document.getElementById('add-duplicate-group-btn').addEventListener('click', addDuplicateGroup);

    // 동명이인 저장
    document.getElementById('save-duplicate-btn').addEventListener('click', saveDuplicateNames);
}

// 워크스페이스 목록 로드
async function loadWorkspaces() {
    try {
        const response = await fetch('/api/workspaces');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('workspace-select');
            select.innerHTML = '<option value="">워크스페이스를 선택하세요...</option>';

            data.workspaces.forEach(ws => {
                const option = document.createElement('option');
                option.value = ws.folder_name;
                option.textContent = ws.name;
                option.dataset.channelId = ws.channel_id;
                option.dataset.sheetName = ws.sheet_name;
                select.appendChild(option);
            });

            if (data.workspaces.length === 0) {
                showError('워크스페이스가 없습니다. workspaces/ 폴더에 워크스페이스를 추가하세요.');
            }
        } else {
            showError('워크스페이스 로드 실패: ' + data.error);
        }
    } catch (error) {
        showError('워크스페이스 로드 오류: ' + error.message);
    }
}

// 워크스페이스 변경
function onWorkspaceChange(e) {
    const select = e.target;
    const selectedOption = select.options[select.selectedIndex];

    if (selectedOption.value) {
        currentWorkspace = selectedOption.value;

        // 워크스페이스 정보 표시
        const infoBox = document.getElementById('workspace-info');
        document.getElementById('channel-id').textContent = selectedOption.dataset.channelId;
        document.getElementById('sheet-name').textContent = selectedOption.dataset.sheetName;
        infoBox.style.display = 'block';

        // 삭제 버튼 표시
        document.getElementById('delete-workspace-btn').style.display = 'inline-block';

        // 워크스페이스 액션 버튼 표시
        document.getElementById('workspace-actions').style.display = 'block';

        // 스레드 정보 초기화
        resetThreadInfo();

        // 기존 스케줄 불러오기 (사용자가 볼 수 있도록)
        loadSchedule();

        // 시트 열 정보 로드
        loadSheetColumns(currentWorkspace);
    } else {
        currentWorkspace = null;
        document.getElementById('workspace-info').style.display = 'none';
        document.getElementById('delete-workspace-btn').style.display = 'none';
        document.getElementById('workspace-actions').style.display = 'none';

        // 열 드롭다운 초기화
        resetColumnDropdowns();
    }
}

// 스레드 모드 전환
function onThreadModeChange(e) {
    const mode = e.target.value;

    if (mode === 'auto') {
        document.getElementById('auto-detect-section').style.display = 'block';
        document.getElementById('manual-input-section').style.display = 'none';
    } else {
        document.getElementById('auto-detect-section').style.display = 'none';
        document.getElementById('manual-input-section').style.display = 'block';
    }

    resetThreadInfo();
}

// 스레드 찾기
async function findThread() {
    if (!currentWorkspace) {
        showError('워크스페이스를 먼저 선택하세요.');
        return;
    }

    const btn = document.getElementById('find-thread-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> 검색 중...';

    try {
        const response = await fetch('/api/find-thread', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({workspace: currentWorkspace})
        });

        const data = await response.json();

        if (data.success) {
            threadTS = data.thread_ts;
            threadUser = data.thread_user;

            document.getElementById('thread-ts').value = threadTS;
            document.getElementById('thread-user').value = threadUser;
            document.getElementById('thread-text').textContent = data.thread_text;
            document.getElementById('thread-ts-display').textContent = 'Thread TS: ' + threadTS;
            document.getElementById('thread-found').style.display = 'block';

            hideError();
        } else {
            showError('스레드 찾기 실패: ' + data.error);
        }
    } catch (error) {
        showError('스레드 찾기 오류: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔍 최신 출석 스레드 찾기';
    }
}

// 수동 입력
function onManualInput(e) {
    const input = e.target.value.trim();
    if (input) {
        threadTS = input;
        document.getElementById('thread-ts').value = input;
        threadUser = null; // 수동 입력 시 DM 불가
        hideError();
    }
}

// 출석체크 실행
async function runAttendance() {
    // 유효성 검사
    if (!currentWorkspace) {
        showError('워크스페이스를 선택하세요.');
        return;
    }

    const threadInput = document.getElementById('thread-ts').value;
    if (!threadInput) {
        showError('스레드를 선택하거나 입력하세요.');
        return;
    }

    const column = document.getElementById('column-input').value.trim().toUpperCase();
    if (!column) {
        showError('열을 입력하세요.');
        return;
    }

    // 진행 상황 표시
    showProgress();
    hideError();
    hideResult();

    // 설정 수집
    const settings = {
        workspace: currentWorkspace,
        thread_ts: threadInput,
        column: column,
        mark_absent: document.getElementById('mark-absent').checked,
        send_thread_reply: document.getElementById('send-thread-reply').checked,
        send_dm: document.getElementById('send-dm').checked,
        thread_user: document.getElementById('thread-user').value
    };

    // 실행 버튼 비활성화
    const runBtn = document.getElementById('run-btn');
    runBtn.disabled = true;

    try {
        // 진행 단계 시뮬레이션
        updateProgress(10, '슬랙 연결 중...');
        await sleep(500);

        updateProgress(25, '댓글 수집 중...');
        const response = await fetch('/api/run-attendance', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
        });

        updateProgress(50, '출석 파싱 중...');
        await sleep(500);

        updateProgress(70, '구글 시트 업데이트 중...');
        const data = await response.json();

        updateProgress(90, '알림 전송 중...');
        await sleep(500);

        if (data.success) {
            updateProgress(100, '완료!');
            await sleep(300);
            showResult(data.result);
        } else {
            showError('출석체크 실패: ' + data.error);
            if (data.traceback) {
                console.error(data.traceback);
            }
        }
    } catch (error) {
        showError('출석체크 오류: ' + error.message);
    } finally {
        runBtn.disabled = false;
        hideProgress();
    }
}

// 진행 상황 표시
function showProgress() {
    document.getElementById('progress-section').style.display = 'block';
    updateProgress(0, '준비 중...');
}

function updateProgress(percent, text) {
    document.getElementById('progress-fill').style.width = percent + '%';
    document.getElementById('progress-text').textContent = text;
}

function hideProgress() {
    setTimeout(() => {
        document.getElementById('progress-section').style.display = 'none';
    }, 1000);
}

// 결과 표시
function showResult(result) {
    const section = document.getElementById('result-section');

    // 통계
    document.getElementById('stat-total').textContent = result.total_students;
    document.getElementById('stat-present').textContent = result.present;
    document.getElementById('stat-absent').textContent = result.absent;
    document.getElementById('stat-rate').textContent =
        (result.present / result.total_students * 100).toFixed(1) + '%';

    // 출석자 명단
    const presentList = document.getElementById('present-list');
    if (result.matched_names.length > 0) {
        presentList.innerHTML = result.matched_names
            .map(name => `<span class="name-tag">${name}</span>`)
            .join('');
    } else {
        presentList.innerHTML = '<em style="color: #888;">출석자가 없습니다</em>';
    }

    // 미출석자 명단
    const absentList = document.getElementById('absent-list');
    if (result.absent_names.length > 0) {
        absentList.innerHTML = result.absent_names
            .map(name => `<span class="name-tag">${name}</span>`)
            .join('');
        if (result.absent > result.absent_names.length) {
            absentList.innerHTML += `<span class="name-tag" style="opacity: 0.7;">... 외 ${result.absent - result.absent_names.length}명</span>`;
        }
    } else {
        absentList.innerHTML = '<em style="color: var(--color-success); font-weight: 600;">🎉 전원 출석!</em>';
    }

    // 명단에 없는 이름
    if (result.unmatched_names && result.unmatched_names.length > 0) {
        const unmatchedSection = document.getElementById('unmatched-section');
        const unmatchedList = document.getElementById('unmatched-list');
        unmatchedList.innerHTML = result.unmatched_names
            .map(name => `<span class="name-tag" style="background: var(--color-warning);">${name}</span>`)
            .join('');
        unmatchedSection.style.display = 'block';
    } else {
        document.getElementById('unmatched-section').style.display = 'none';
    }

    // 알림
    if (result.notifications && result.notifications.length > 0) {
        const notificationsSection = document.getElementById('notifications-section');
        const notificationsList = document.getElementById('notifications-list');
        notificationsList.innerHTML = '';
        result.notifications.forEach(notif => {
            const li = document.createElement('li');
            li.textContent = notif;
            notificationsList.appendChild(li);
        });
        notificationsSection.style.display = 'block';
    } else {
        document.getElementById('notifications-section').style.display = 'none';
    }

    section.style.display = 'block';
    section.scrollIntoView({behavior: 'smooth'});
}

function hideResult() {
    document.getElementById('result-section').style.display = 'none';
}

// 오류 표시
function showError(message) {
    const section = document.getElementById('error-section');
    document.getElementById('error-message').textContent = message;
    section.style.display = 'block';
    section.scrollIntoView({behavior: 'smooth'});
}

function hideError() {
    document.getElementById('error-section').style.display = 'none';
}

// 스레드 정보 초기화
function resetThreadInfo() {
    threadTS = null;
    threadUser = null;
    document.getElementById('thread-ts').value = '';
    document.getElementById('thread-user').value = '';
    document.getElementById('thread-found').style.display = 'none';
    document.getElementById('thread-input').value = '';
}

// 스케줄 폼 초기화 (기본값으로 리셋)
function resetScheduleForm() {
    // 자동 실행 비활성화
    const autoScheduleEnabled = document.getElementById('auto-schedule-enabled');
    if (autoScheduleEnabled) {
        autoScheduleEnabled.checked = false;
    }

    const scheduleSettings = document.getElementById('schedule-settings');
    if (scheduleSettings) {
        scheduleSettings.style.display = 'none';
    }

    // 스케줄 리스트 초기화
    const schedulesList = document.getElementById('schedules-list');
    if (schedulesList) {
        schedulesList.innerHTML = '';
    }

    currentSchedules = [];

    // 기본 메시지 초기화
    const threadMessage = document.getElementById('thread-message');
    if (threadMessage) {
        threadMessage.value = '@channel\n📢 출석 스레드입니다.\n\n"이름/출석했습니다" 형식으로 댓글 달아주세요!';
    }

    const completionMessage = document.getElementById('completion-message');
    if (completionMessage) {
        completionMessage.value = '[자동] 출석 체크를 완료했습니다.\n출석: {present}명 / 미출석: {absent}명';
    }

    // 자동 열 증가 초기화
    const autoColumnEnabled = document.getElementById('auto-column-enabled');
    if (autoColumnEnabled) {
        autoColumnEnabled.checked = false;
    }

    const autoColumnSettings = document.getElementById('auto-column-settings');
    if (autoColumnSettings) {
        autoColumnSettings.style.display = 'none';
    }

    const startColumn = document.getElementById('start-column');
    if (startColumn) {
        startColumn.value = 'H';
    }

    const endColumn = document.getElementById('end-column');
    if (endColumn) {
        endColumn.value = 'O';
    }

    // 알림 수신자 초기화
    const notificationUserId = document.getElementById('notification-user-id');
    if (notificationUserId) {
        notificationUserId.value = '';
    }
}

// 스케줄 활성화 토글
function toggleScheduleSettings(e) {
    const settings = document.getElementById('schedule-settings');
    if (e.target.checked) {
        settings.style.display = 'block';
    } else {
        settings.style.display = 'none';
    }
}

// 자동 열 증가 토글
function toggleAutoColumnSettings(e) {
    const settings = document.getElementById('auto-column-settings');
    if (e.target.checked) {
        settings.style.display = 'block';
    } else {
        settings.style.display = 'none';
    }
}

// 스케줄 정보 로드
async function loadSchedule() {
    if (!currentWorkspace) return;

    try {
        const response = await fetch(`/api/schedule/${currentWorkspace}`);
        const data = await response.json();

        if (data.success && data.schedule) {
            const schedule = data.schedule;

            // 활성화 상태
            document.getElementById('auto-schedule-enabled').checked = schedule.enabled || false;
            document.getElementById('schedule-settings').style.display = schedule.enabled ? 'block' : 'none';

            // 출석 스레드 생성
            document.getElementById('create-thread-day').value = schedule.create_thread_day || '';
            document.getElementById('create-thread-time').value = schedule.create_thread_time || '';
            document.getElementById('thread-message').value = schedule.create_thread_message || '';

            // 출석 집계
            document.getElementById('check-attendance-day').value = schedule.check_attendance_day || '';
            document.getElementById('check-attendance-time').value = schedule.check_attendance_time || '';
            document.getElementById('check-attendance-column').value = schedule.check_attendance_column || 'K';
            document.getElementById('completion-message').value = schedule.check_completion_message || '[자동] 출석 체크를 완료했습니다.\n출석: {present}명 / 미출석: {absent}명';

            // 자동 열 증가
            const autoColumnEnabled = schedule.auto_column_enabled || false;
            document.getElementById('auto-column-enabled').checked = autoColumnEnabled;
            document.getElementById('auto-column-settings').style.display = autoColumnEnabled ? 'block' : 'none';
            document.getElementById('start-column').value = schedule.start_column || 'H';
            document.getElementById('end-column').value = schedule.end_column || 'O';

            // 알림 수신자
            document.getElementById('notification-user-id').value = data.notification_user_id || '';
        }
    } catch (error) {
        console.error('스케줄 로드 오류:', error);
    }
}

// 스케줄 저장
async function saveSchedule() {
    if (!currentWorkspace) {
        showToast('워크스페이스를 먼저 선택하세요.', 'warning');
        return;
    }

    const btn = document.getElementById('save-schedule-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '💾 저장 중...';

    try {
        const enabled = document.getElementById('auto-schedule-enabled').checked;

        // 스케줄 목록 수집
        const schedules = [];
        const items = document.querySelectorAll('#schedules-list .schedule-item');

        items.forEach(function(item) {
            const day = item.querySelector('.schedule-day').value;
            const createTime = item.querySelector('.schedule-create-time').value;
            const checkTime = item.querySelector('.schedule-check-time').value;
            const column = item.querySelector('.schedule-column').value.trim().toUpperCase();

            if (day && createTime && checkTime && column) {
                schedules.push({
                    day: day,
                    create_thread_time: createTime,
                    check_attendance_time: checkTime,
                    check_attendance_column: column
                });
            }
        });

        const schedule = {
            enabled: enabled,
            schedules: schedules,
            create_thread_message: document.getElementById('thread-message').value || '@channel\n📢 출석 스레드입니다.\n\n"이름/출석했습니다" 형식으로 댓글 달아주세요!',
            check_completion_message: document.getElementById('completion-message').value || '[자동] 출석 체크를 완료했습니다.\n출석: {present}명 / 미출석: {absent}명',
            auto_column_enabled: document.getElementById('auto-column-enabled').checked,
            start_column: document.getElementById('start-column').value.trim().toUpperCase() || 'H',
            end_column: document.getElementById('end-column').value.trim().toUpperCase() || 'O'
        };

        const notification_user_id = document.getElementById('notification-user-id').value.trim();

        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                workspace: currentWorkspace,
                schedule: schedule,
                notification_user_id: notification_user_id
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('스케줄이 저장되었습니다!', 'success');
            loadAllSchedules();
        } else {
            showToast('스케줄 저장 실패: ' + data.error, 'error', 7000);
        }
    } catch (error) {
        showToast('스케줄 저장 오류: ' + error.message, 'error', 7000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// 예약 현황 로드 (새 버전 - 여러 스케줄 지원)
async function loadAllSchedules() {
    try {
        const response = await fetch('/api/schedules/all');
        const data = await response.json();

        const section = document.getElementById('schedule-status-section');
        const content = document.getElementById('schedule-status-content');

        if (data.success && data.schedules && data.schedules.length > 0) {
            section.style.display = 'block';

            const dayNames = {
                'mon': '월', 'tue': '화', 'wed': '수', 'thu': '목',
                'fri': '금', 'sat': '토', 'sun': '일'
            };

            // 워크스페이스별로 그룹화
            const grouped = {};
            data.schedules.forEach(function(schedule) {
                if (!grouped[schedule.workspace_name]) {
                    grouped[schedule.workspace_name] = [];
                }
                grouped[schedule.workspace_name].push(schedule);
            });

            let html = '';
            let globalScheduleIndex = 0;  // 전역 인덱스 추적

            for (const wsName in grouped) {
                const schedules = grouped[wsName];
                const folderName = schedules[0].folder_name;
                const isEnabled = schedules[0].enabled;

                // 비활성화된 경우 회색 배경
                const containerBgColor = isEnabled ? '#f9f9f9' : '#f0f0f0';
                const containerBorder = isEnabled ? '1px solid #ddd' : '1px solid #999';
                const opacity = isEnabled ? '1' : '0.7';

                html += '<div style="margin-bottom: 20px; padding: 15px; border: ' + containerBorder + '; border-radius: 10px; background: ' + containerBgColor + '; opacity: ' + opacity + ';">';
                html += '<div style="display: flex; justify-content: space-between; align-items: center;">';
                html += '<h3 style="margin: 0 0 10px 0;">' + wsName + ' <span style="font-size: 0.8rem; color: ' + (isEnabled ? '#28a745' : '#dc3545') + '; font-weight: bold;">(' + (isEnabled ? '✓ 활성' : '⏸️ 일시정지') + ')</span></h3>';
                html += '<div>';
                html += '<button class="btn btn-secondary" onclick="editScheduleFromStatus(\'' + folderName + '\')" style="padding: 5px 15px; margin-right: 5px;">✏️ 수정</button>';
                html += '<button class="btn ' + (isEnabled ? 'btn-warning' : 'btn-success') + '" onclick="toggleSchedule(\'' + folderName + '\')" style="padding: 5px 15px;">' + (isEnabled ? '⏸️ 일시정지' : '▶️ 활성화') + '</button>';
                html += '</div>';
                html += '</div>';

                schedules.forEach(function(schedule, localIndex) {
                    const day = dayNames[schedule.day] || schedule.day;
                    const itemBgColor = isEnabled ? 'white' : '#e8e8e8';
                    html += '<div style="padding: 10px; margin-top: 10px; background: ' + itemBgColor + '; border-radius: 5px; display: flex; justify-content: space-between; align-items: center;">';
                    html += '<div>';
                    html += '<strong>' + day + '요일</strong><br>';
                    html += '스레드 생성: ' + schedule.create_thread_time + ' | 집계: ' + schedule.check_attendance_time + ' | 열: ' + schedule.check_attendance_column;
                    if (!isEnabled) {
                        html += '<br><small style="color: #999;">⏸️ 일시정지됨 (실행되지 않음)</small>';
                    }
                    html += '</div>';
                    html += '<button class="btn btn-danger" onclick="deleteScheduleItem(\'' + folderName + '\', ' + localIndex + ')" style="padding: 3px 10px;">🗑️ 삭제</button>';
                    html += '</div>';
                    globalScheduleIndex++;
                });

                html += '</div>';
            }

            content.innerHTML = html;
        } else {
            section.style.display = 'none';
        }
    } catch (error) {
        console.error('예약 현황 로드 오류:', error);
    }
}

// 스케줄 수정
function editSchedule(workspaceName) {
    // 워크스페이스 선택
    const select = document.getElementById('workspace-select');
    select.value = workspaceName;
    currentWorkspace = workspaceName;

    // 워크스페이스 정보 업데이트 (change 이벤트 트리거하지 않음)
    const selectedOption = select.options[select.selectedIndex];
    const infoBox = document.getElementById('workspace-info');
    document.getElementById('channel-id').textContent = selectedOption.dataset.channelId;
    document.getElementById('sheet-name').textContent = selectedOption.dataset.sheetName;
    infoBox.style.display = 'block';

    // 스레드 정보 초기화
    resetThreadInfo();

    // 저장된 스케줄 불러오기 (수정 모드에서만!)
    loadSchedule();

    // 스케줄 섹션으로 스크롤
    document.getElementById('auto-schedule-enabled').scrollIntoView({ behavior: 'smooth', block: 'center' });

    // 자동 실행 활성화 체크박스 강조
    setTimeout(() => {
        const checkbox = document.getElementById('auto-schedule-enabled');
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event('change'));

        // 깜빡임 효과
        const settings = document.getElementById('schedule-settings');
        settings.style.animation = 'highlight 1s ease';
        setTimeout(() => {
            settings.style.animation = '';
        }, 1000);
    }, 500);
}

// 스케줄 삭제
async function deleteSchedule(workspaceName, displayName) {
    if (!confirm(`"${displayName}" 워크스페이스의 자동 실행 스케줄을 삭제하시겠습니까?\n\n삭제 후 서버를 재시작해야 적용됩니다.`)) {
        return;
    }

    try {
        // 빈 스케줄로 저장 (enabled: false)
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace: workspaceName,
                schedule: {
                    enabled: false,
                    create_thread_day: '',
                    create_thread_time: '',
                    create_thread_message: '',
                    check_attendance_day: '',
                    check_attendance_time: '',
                    check_attendance_column: ''
                },
                notification_user_id: ''
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('✓ 스케줄이 삭제되었습니다!\n\n서버를 재시작하면 적용됩니다.');
            // 예약 현황 새로고침
            loadAllSchedules();
        } else {
            alert('스케줄 삭제 실패: ' + data.error);
        }
    } catch (error) {
        alert('스케줄 삭제 오류: ' + error.message);
    }
}

// 유틸리티
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// === 워크스페이스 관리 기능 ===

// Bot Token 파일 불러오기
function loadTokenFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = function(e) {
        try {
            let content = e.target.result.trim();

            // JSON 파일인 경우 bot_token 키 찾기
            if (file.name.endsWith('.json')) {
                try {
                    const json = JSON.parse(content);
                    // bot_token 또는 slack_bot_token 키 찾기
                    content = json.bot_token || json.slack_bot_token || json.token || content;
                } catch (jsonError) {
                    // JSON 파싱 실패 시 그대로 사용
                }
            }

            // xoxb- 토큰 형식 확인
            if (!content.startsWith('xoxb-')) {
                if (!confirm('⚠️ 올바른 Slack Bot Token 형식이 아닐 수 있습니다.\n(xoxb-로 시작해야 함)\n\n그래도 사용하시겠습니까?')) {
                    event.target.value = '';
                    return;
                }
            }

            // 입력 필드에 삽입
            document.getElementById('new-bot-token').value = content;
            showToast('Bot Token을 성공적으로 불러왔습니다!', 'success');
        } catch (error) {
            showToast('파일을 읽는 중 오류가 발생했습니다: ' + error.message, 'error', 7000);
        }
        // 파일 입력 초기화
        event.target.value = '';
    };

    reader.onerror = function() {
        showToast('파일을 읽는 중 오류가 발생했습니다.', 'error');
        event.target.value = '';
    };

    reader.readAsText(file);
}

// 워크스페이스 삭제
async function deleteWorkspace() {
    if (!currentWorkspace) {
        showError('삭제할 워크스페이스를 선택하세요.');
        return;
    }

    const select = document.getElementById('workspace-select');
    const selectedOption = select.options[select.selectedIndex];
    const displayName = selectedOption.textContent;

    // 확인 메시지
    if (!confirm(`정말로 "${displayName}" 워크스페이스를 삭제하시겠습니까?\n\n⚠️ 경고: 이 작업은 되돌릴 수 없습니다!\n- config.json\n- credentials.json\n모든 설정 파일이 영구적으로 삭제됩니다.`)) {
        return;
    }

    // 한 번 더 확인
    if (!confirm(`⚠️ 최종 확인\n\n"${displayName}" 워크스페이스의 모든 데이터를 삭제합니다.\n계속하시겠습니까?`)) {
        return;
    }

    const btn = document.getElementById('delete-workspace-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> 삭제 중...';

    try {
        const response = await fetch('/api/workspaces/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace_name: currentWorkspace
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('워크스페이스가 삭제되었습니다: ' + displayName, 'success');

            // 현재 선택 초기화
            currentWorkspace = null;

            // 워크스페이스 목록 새로고침
            await loadWorkspaces();

            // UI 초기화
            document.getElementById('workspace-info').style.display = 'none';
            document.getElementById('delete-workspace-btn').style.display = 'none';
            resetThreadInfo();
            resetScheduleForm();
            hideError();
            hideResult();
        } else {
            showToast('워크스페이스 삭제 실패: ' + data.error, 'error', 7000);
        }
    } catch (error) {
        showToast('워크스페이스 삭제 오류: ' + error.message, 'error', 7000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// credentials 파일 불러오기
function loadCredentialsFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 파일 확장자 검증
    if (!file.name.endsWith('.json')) {
        showToast('JSON 파일만 업로드할 수 있습니다.', 'warning');
        event.target.value = '';
        return;
    }

    const reader = new FileReader();

    reader.onload = function(e) {
        try {
            const content = e.target.result;
            // JSON 유효성 검사
            JSON.parse(content);
            // 유효하면 textarea에 삽입
            document.getElementById('new-credentials').value = content;
            showToast('파일을 성공적으로 불러왔습니다!', 'success');
        } catch (error) {
            showToast('JSON 파일 형식이 올바르지 않습니다: ' + error.message, 'error', 7000);
        }
        // 파일 입력 초기화 (같은 파일 재선택 가능하도록)
        event.target.value = '';
    };

    reader.onerror = function() {
        showToast('파일을 읽는 중 오류가 발생했습니다.', 'error');
        event.target.value = '';
    };

    reader.readAsText(file);
}

// 모달 열기
function openAddWorkspaceModal() {
    const modal = document.getElementById('add-workspace-modal');
    modal.style.display = 'flex';
    clearAddWorkspaceForm();
    setupModalFocusTrap(modal);
}

// 모달 닫기
function closeAddWorkspaceModal() {
    const modal = document.getElementById('add-workspace-modal');
    modal.style.display = 'none';
    clearAddWorkspaceForm();
}

// 폼 초기화
function clearAddWorkspaceForm() {
    document.getElementById('new-workspace-name').value = '';
    document.getElementById('new-display-name').value = '';
    document.getElementById('new-bot-token').value = '';
    document.getElementById('new-channel-id').value = '';
    document.getElementById('new-assignment-channel-id').value = '';
    document.getElementById('new-spreadsheet-id').value = '';
    document.getElementById('new-sheet-name').value = '출석현황';
    document.getElementById('new-assignment-sheet-name').value = '실습과제현황';
    document.getElementById('new-name-column').value = 'B';
    document.getElementById('new-start-row').value = '4';
    document.getElementById('new-credentials').value = '';
}

// 워크스페이스 추가 제출
async function submitAddWorkspace() {
    // 입력값 수집
    const workspaceName = document.getElementById('new-workspace-name').value.trim();
    const displayName = document.getElementById('new-display-name').value.trim();
    const botToken = document.getElementById('new-bot-token').value.trim();
    const channelId = document.getElementById('new-channel-id').value.trim();
    const assignmentChannelId = document.getElementById('new-assignment-channel-id').value.trim();
    const spreadsheetId = document.getElementById('new-spreadsheet-id').value.trim();
    const sheetName = document.getElementById('new-sheet-name').value.trim();
    const assignmentSheetName = document.getElementById('new-assignment-sheet-name').value.trim();
    const nameColumn = document.getElementById('new-name-column').value.trim();
    const startRow = parseInt(document.getElementById('new-start-row').value);
    const endColumn = document.getElementById('new-end-column').value.trim().toUpperCase();
    const credentialsText = document.getElementById('new-credentials').value.trim();

    // 유효성 검사
    if (!workspaceName) {
        showToast('워크스페이스 폴더 이름을 입력하세요.', 'warning');
        return;
    }

    // 폴더 이름 검증 (Windows 폴더명으로 사용할 수 없는 특수문자만 제외)
    const invalidChars = /[<>:"/\\|?*]/;
    if (invalidChars.test(workspaceName)) {
        showToast('워크스페이스 폴더 이름에 다음 문자는 사용할 수 없습니다: < > : " / \\ | ? *', 'warning', 7000);
        return;
    }

    if (workspaceName.trim().length === 0) {
        showToast('워크스페이스 폴더 이름을 입력하세요.', 'warning');
        return;
    }

    if (!displayName) {
        showToast('표시 이름을 입력하세요.', 'warning');
        return;
    }

    if (!botToken || !botToken.startsWith('xoxb-')) {
        showToast('올바른 Slack Bot Token을 입력하세요. (xoxb-로 시작해야 합니다)', 'warning', 6000);
        return;
    }

    if (!channelId || !channelId.startsWith('C')) {
        showToast('올바른 Channel ID를 입력하세요. (C로 시작해야 합니다)', 'warning', 6000);
        return;
    }

    if (!spreadsheetId) {
        showToast('Spreadsheet ID를 입력하세요.', 'warning');
        return;
    }

    if (!credentialsText) {
        showToast('Google Credentials JSON을 입력하세요.', 'warning');
        return;
    }

    // JSON 파싱 검증
    let credentialsJson;
    try {
        credentialsJson = JSON.parse(credentialsText);
    } catch (error) {
        showToast('Google Credentials JSON 형식이 올바르지 않습니다: ' + error.message, 'error', 7000);
        return;
    }

    // 버튼 비활성화
    const submitBtn = document.getElementById('submit-add-workspace-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading"></span> 추가 중...';

    try {
        const response = await fetch('/api/workspaces/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace_name: workspaceName,
                display_name: displayName,
                slack_bot_token: botToken,
                slack_channel_id: channelId,
                assignment_channel_id: assignmentChannelId,
                spreadsheet_id: spreadsheetId,
                sheet_name: sheetName,
                assignment_sheet_name: assignmentSheetName,
                name_column: nameColumn,
                start_row: startRow,
                end_column: endColumn,
                credentials_json: credentialsJson
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('워크스페이스가 추가되었습니다: ' + displayName, 'success');
            closeAddWorkspaceModal();
            // 워크스페이스 목록 새로고침
            await loadWorkspaces();
            // 새로 추가된 워크스페이스 자동 선택
            document.getElementById('workspace-select').value = workspaceName;
            currentWorkspace = workspaceName;
            // 워크스페이스 정보 표시
            const select = document.getElementById('workspace-select');
            const selectedOption = select.options[select.selectedIndex];
            const infoBox = document.getElementById('workspace-info');
            document.getElementById('channel-id').textContent = selectedOption.dataset.channelId;
            document.getElementById('sheet-name').textContent = selectedOption.dataset.sheetName;
            infoBox.style.display = 'block';
        } else {
            showToast('워크스페이스 추가 실패: ' + data.error, 'error', 7000);
        }
    } catch (error) {
        showToast('워크스페이스 추가 오류: ' + error.message, 'error', 7000);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// ===== 새로운 스케줄 관리 함수 (여러 요일 지원) =====

// 전역 변수: 현재 스케줄 목록
let currentSchedules = [];

// 페이지 로드시 이벤트 등록
(function() {
    const originalSetup = setupEventListeners;
    setupEventListeners = function() {
        originalSetup();

        // 스케줄 추가 버튼
        const addBtn = document.getElementById('add-schedule-btn');
        if (addBtn) addBtn.addEventListener('click', addScheduleItem);

        const editAddBtn = document.getElementById('edit-add-schedule-btn');
        if (editAddBtn) editAddBtn.addEventListener('click', addEditScheduleItem);

        // 수정 모달 닫기
        const editModalClose = document.querySelector('#edit-schedule-modal .modal-close');
        if (editModalClose) editModalClose.addEventListener('click', closeEditScheduleModal);

        const cancelEditBtn = document.getElementById('cancel-edit-schedule-btn');
        if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEditScheduleModal);

        const submitEditBtn = document.getElementById('submit-edit-schedule-btn');
        if (submitEditBtn) submitEditBtn.addEventListener('click', submitEditSchedule);

        // 수정 모달의 자동 열 증가 토글
        const editAutoToggle = document.getElementById('edit-auto-column-enabled');
        if (editAutoToggle) {
            editAutoToggle.addEventListener('change', function() {
                const settings = document.getElementById('edit-auto-column-settings');
                if (settings) settings.style.display = this.checked ? 'block' : 'none';
            });
        }
    };
})();

// 스케줄 아이템 추가 (메인 화면)
function addScheduleItem() {
    const container = document.getElementById('schedules-list');
    const index = container.children.length;

    // 출석 열 드롭다운 옵션 생성
    let columnOptions = '<option value="">열 선택...</option>';
    if (scheduleModalColumns && scheduleModalColumns.length > 0) {
        scheduleModalColumns.forEach(col => {
            columnOptions += `<option value="${col.letter}">${col.letter} - ${col.name}</option>`;
        });
    } else {
        // 열 정보가 없으면 기본 옵션 제공
        const defaultColumns = ['H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P'];
        defaultColumns.forEach(col => {
            columnOptions += `<option value="${col}">${col}</option>`;
        });
    }

    const scheduleHTML = '<div class="schedule-item" data-index="' + index + '" style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 8px; background: #f9f9f9;">' +
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">' +
        '<h4 style="margin: 0;">스케줄 #' + (index + 1) + '</h4>' +
        '<button type="button" class="btn btn-danger" onclick="removeScheduleItem(' + index + ')" style="padding: 5px 10px; font-size: 0.85rem;">🗑️ 삭제</button>' +
        '</div>' +
        '<div class="form-row">' +
        '<div class="form-group"><label>요일</label>' +
        '<select class="form-control schedule-day" data-index="' + index + '">' +
        '<option value="">선택...</option>' +
        '<option value="mon">월</option><option value="tue">화</option><option value="wed">수</option>' +
        '<option value="thu">목</option><option value="fri">금</option><option value="sat">토</option><option value="sun">일</option>' +
        '</select></div>' +
        '<div class="form-group"><label>스레드 생성 시간</label>' +
        '<input type="time" class="form-control schedule-create-time" data-index="' + index + '"></div>' +
        '<div class="form-group"><label>집계 시간</label>' +
        '<input type="time" class="form-control schedule-check-time" data-index="' + index + '"></div>' +
        '<div class="form-group"><label>출석 열</label>' +
        '<select class="form-control schedule-column" data-index="' + index + '" style="max-width: 150px;">' +
        columnOptions +
        '</select></div>' +
        '</div></div>';

    container.insertAdjacentHTML('beforeend', scheduleHTML);
    currentSchedules.push({});
}

// 스케줄 아이템 삭제
function removeScheduleItem(index) {
    const item = document.querySelector('.schedule-item[data-index="' + index + '"]');
    if (item) {
        item.remove();
        currentSchedules.splice(index, 1);
        reindexScheduleItems();
    }
}

// 스케줄 인덱스 재정렬
function reindexScheduleItems() {
    const items = document.querySelectorAll('#schedules-list .schedule-item');
    currentSchedules = [];
    items.forEach(function(item, newIndex) {
        item.dataset.index = newIndex;
        item.querySelector('h4').textContent = '스케줄 #' + (newIndex + 1);
        item.querySelector('.schedule-day').dataset.index = newIndex;
        item.querySelector('.schedule-create-time').dataset.index = newIndex;
        item.querySelector('.schedule-check-time').dataset.index = newIndex;
        item.querySelector('.schedule-column').dataset.index = newIndex;
        item.querySelector('button').setAttribute('onclick', 'removeScheduleItem(' + newIndex + ')');
        currentSchedules.push({});
    });
}

// 스케줄 아이템 추가 (수정 모달)
function addEditScheduleItem() {
    const container = document.getElementById('edit-schedules-list');
    const index = container.children.length;

    // 출석 열 드롭다운 옵션 생성
    let columnOptions = '<option value="">열 선택...</option>';
    if (scheduleModalColumns && scheduleModalColumns.length > 0) {
        scheduleModalColumns.forEach(col => {
            columnOptions += `<option value="${col.letter}">${col.letter} - ${col.name}</option>`;
        });
    } else {
        // 열 정보가 없으면 기본 옵션 제공
        const defaultColumns = ['H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P'];
        defaultColumns.forEach(col => {
            columnOptions += `<option value="${col}">${col}</option>`;
        });
    }

    const scheduleHTML = '<div class="schedule-item" data-index="' + index + '" style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 8px; background: #f9f9f9;">' +
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">' +
        '<h4 style="margin: 0;">스케줄 #' + (index + 1) + '</h4>' +
        '<button type="button" class="btn btn-danger" onclick="removeEditScheduleItem(' + index + ')" style="padding: 5px 10px; font-size: 0.85rem;">🗑️ 삭제</button>' +
        '</div>' +
        '<div class="form-row">' +
        '<div class="form-group"><label>요일</label>' +
        '<select class="form-control edit-schedule-day" data-index="' + index + '">' +
        '<option value="">선택...</option>' +
        '<option value="mon">월</option><option value="tue">화</option><option value="wed">수</option>' +
        '<option value="thu">목</option><option value="fri">금</option><option value="sat">토</option><option value="sun">일</option>' +
        '</select></div>' +
        '<div class="form-group"><label>스레드 생성 시간</label>' +
        '<input type="time" class="form-control edit-schedule-create-time" data-index="' + index + '"></div>' +
        '<div class="form-group"><label>집계 시간</label>' +
        '<input type="time" class="form-control edit-schedule-check-time" data-index="' + index + '"></div>' +
        '<div class="form-group"><label>출석 열</label>' +
        '<select class="form-control edit-schedule-column" data-index="' + index + '" style="max-width: 150px;">' +
        columnOptions +
        '</select></div>' +
        '</div></div>';

    container.insertAdjacentHTML('beforeend', scheduleHTML);
}

// 수정 모달 스케줄 아이템 삭제
function removeEditScheduleItem(index) {
    const item = document.querySelector('#edit-schedules-list .schedule-item[data-index="' + index + '"]');
    if (item) {
        item.remove();
        reindexEditScheduleItems();
    }
}

// 수정 모달 스케줄 인덱스 재정렬
function reindexEditScheduleItems() {
    const items = document.querySelectorAll('#edit-schedules-list .schedule-item');
    items.forEach(function(item, newIndex) {
        item.dataset.index = newIndex;
        item.querySelector('h4').textContent = '스케줄 #' + (newIndex + 1);
        item.querySelector('.edit-schedule-day').dataset.index = newIndex;
        item.querySelector('.edit-schedule-create-time').dataset.index = newIndex;
        item.querySelector('.edit-schedule-check-time').dataset.index = newIndex;
        item.querySelector('.edit-schedule-column').dataset.index = newIndex;
        item.querySelector('button').setAttribute('onclick', 'removeEditScheduleItem(' + newIndex + ')');
    });
}

// 예약 현황에서 수정 버튼 클릭
function editScheduleFromStatus(workspaceName) {
    openEditScheduleModal(workspaceName);
}

// 스케줄 아이템 삭제
async function deleteScheduleItem(workspaceName, scheduleIndex) {
    if (!confirm('이 스케줄을 삭제하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch('/api/schedule/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace: workspaceName,
                schedule_index: scheduleIndex
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('스케줄이 삭제되었습니다!', 'success');
            // 예약 현황 새로고침
            loadAllSchedules();
        } else {
            showToast('오류: ' + data.error, 'error', 7000);
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error', 7000);
    }
}

// 스케줄 활성화/비활성화 토글
async function toggleSchedule(workspaceName) {
    try {
        const response = await fetch('/api/schedule/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace: workspaceName
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            // 예약 현황 새로고침
            loadAllSchedules();
        } else {
            showToast('오류: ' + data.error, 'error', 7000);
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error', 7000);
    }
}

// 전역 변수: 스케줄 모달용 열 정보
let scheduleModalColumns = [];

// 스케줄 수정 모달 열기
async function openEditScheduleModal(workspaceName) {
    try {
        const response = await fetch('/api/schedule/' + workspaceName);
        const data = await response.json();

        if (!data.success) {
            alert('스케줄 로드 실패');
            return;
        }

        // 워크스페이스의 열 정보 가져오기
        const columnsResponse = await fetch(`/api/workspaces/${workspaceName}/sheet-columns`);
        const columnsData = await columnsResponse.json();

        if (columnsData.success && columnsData.columns) {
            scheduleModalColumns = columnsData.columns;
        } else {
            scheduleModalColumns = [];
        }

        const schedule = data.schedule || {};

        document.getElementById('edit-workspace-name').value = workspaceName;
        document.getElementById('edit-workspace-display').value = workspaceName;
        document.getElementById('edit-thread-message').value = schedule.create_thread_message || '';
        document.getElementById('edit-completion-message').value = schedule.check_completion_message || '';
        document.getElementById('edit-auto-column-enabled').checked = schedule.auto_column_enabled || false;
        document.getElementById('edit-schedule-start-column').value = schedule.start_column || 'H';
        document.getElementById('edit-schedule-end-column').value = schedule.end_column || 'O';
        document.getElementById('edit-schedule-notification-user-id').value = data.notification_user_id || '';

        const editAutoSettings = document.getElementById('edit-auto-column-settings');
        if (editAutoSettings) editAutoSettings.style.display = schedule.auto_column_enabled ? 'block' : 'none';

        const schedulesContainer = document.getElementById('edit-schedules-list');
        schedulesContainer.innerHTML = '';

        const schedules = schedule.schedules || [];
        schedules.forEach(function(sched, index) {
            addEditScheduleItem();
            document.querySelector('.edit-schedule-day[data-index="' + index + '"]').value = sched.day || '';
            document.querySelector('.edit-schedule-create-time[data-index="' + index + '"]').value = sched.create_thread_time || '';
            document.querySelector('.edit-schedule-check-time[data-index="' + index + '"]').value = sched.check_attendance_time || '';
            document.querySelector('.edit-schedule-column[data-index="' + index + '"]').value = sched.check_attendance_column || '';
        });

        document.getElementById('edit-schedule-modal').style.display = 'flex';
    } catch (error) {
        alert('스케줄 로드 오류: ' + error.message);
    }
}

// 스케줄 수정 모달 닫기
function closeEditScheduleModal() {
    document.getElementById('edit-schedule-modal').style.display = 'none';
}

// 스케줄 수정 제출
async function submitEditSchedule() {
    const workspaceName = document.getElementById('edit-workspace-name').value;
    const btn = document.getElementById('submit-edit-schedule-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '💾 저장 중...';

    try {
        const schedules = [];
        const items = document.querySelectorAll('#edit-schedules-list .schedule-item');

        items.forEach(function(item) {
            const day = item.querySelector('.edit-schedule-day').value;
            const createTime = item.querySelector('.edit-schedule-create-time').value;
            const checkTime = item.querySelector('.edit-schedule-check-time').value;
            const column = item.querySelector('.edit-schedule-column').value.trim().toUpperCase();

            if (day && createTime && checkTime && column) {
                schedules.push({
                    day: day,
                    create_thread_time: createTime,
                    check_attendance_time: checkTime,
                    check_attendance_column: column
                });
            }
        });

        const schedule = {
            enabled: schedules.length > 0,
            schedules: schedules,
            create_thread_message: document.getElementById('edit-thread-message').value,
            check_completion_message: document.getElementById('edit-completion-message').value,
            auto_column_enabled: document.getElementById('edit-auto-column-enabled').checked,
            start_column: document.getElementById('edit-schedule-start-column').value.trim().toUpperCase(),
            end_column: document.getElementById('edit-schedule-end-column').value.trim().toUpperCase()
        };

        const notification_user_id = document.getElementById('edit-schedule-notification-user-id').value.trim();

        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                workspace: workspaceName,
                schedule: schedule,
                notification_user_id: notification_user_id
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('스케줄이 수정되었습니다!', 'success');
            closeEditScheduleModal();
            loadAllSchedules();
        } else {
            showToast('스케줄 수정 실패: ' + data.error, 'error', 7000);
        }
    } catch (error) {
        showToast('스케줄 수정 오류: ' + error.message, 'error', 7000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// ========================================
// 워크스페이스 수정 기능
// ========================================

async function openEditWorkspaceModal() {
    const workspaceName = document.getElementById('workspace-select').value;
    if (!workspaceName) {
        showToast('워크스페이스를 먼저 선택하세요.', 'warning');
        return;
    }

    const modal = document.getElementById('edit-workspace-modal');

    // 기존 정보 로드
    try {
        const response = await fetch(`/api/workspaces/info/${workspaceName}`);
        const data = await response.json();

        if (data.success) {
            const workspace = data.workspace;

            // 모달에 정보 표시 (null 체크)
            const setValueSafe = (id, value) => {
                const element = document.getElementById(id);
                if (element) {
                    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
                        element.value = value || '';
                    } else {
                        element.textContent = value || '';
                    }
                } else {
                    console.warn(`Element not found: ${id}`);
                }
            };

            setValueSafe('edit-workspace-name-hidden', workspaceName);
            setValueSafe('edit-workspace-folder-name', workspace.name);
            setValueSafe('edit-workspace-display-name', workspace.display_name);
            setValueSafe('edit-slack-channel-id', workspace.slack_channel_id);
            setValueSafe('edit-assignment-channel-id', workspace.assignment_channel_id);
            setValueSafe('edit-sheet-name', workspace.sheet_name || 'Sheet1');
            setValueSafe('edit-assignment-sheet-name', workspace.assignment_sheet_name || '실습과제현황');
            setValueSafe('edit-name-column', workspace.name_column || 'B');
            setValueSafe('edit-start-row', workspace.start_row || 4);
            setValueSafe('edit-end-column', workspace.end_column || 'P');
            setValueSafe('edit-notification-user-id', workspace.notification_user_id);

            // 모달 표시
            if (modal) {
                modal.style.display = 'flex';
                setupModalFocusTrap(modal);
            } else {
                console.error('Modal not found: edit-workspace-modal');
                showToast('워크스페이스 수정 모달을 찾을 수 없습니다. 페이지를 새로고침해주세요.', 'error');
            }
        } else {
            alert('워크스페이스 정보 로드 실패: ' + data.error);
        }
    } catch (error) {
        alert('오류: ' + error.message);
    }
}

function closeEditWorkspaceModal() {
    document.getElementById('edit-workspace-modal').style.display = 'none';
}

async function saveEditWorkspace() {
    const workspaceName = document.getElementById('edit-workspace-name-hidden').value;
    const displayName = document.getElementById('edit-workspace-display-name').value.trim();
    const slackChannelId = document.getElementById('edit-slack-channel-id').value.trim();
    const assignmentChannelId = document.getElementById('edit-assignment-channel-id').value.trim();
    const sheetName = document.getElementById('edit-sheet-name').value.trim();
    const assignmentSheetName = document.getElementById('edit-assignment-sheet-name').value.trim();
    const nameColumn = document.getElementById('edit-name-column').value.trim();
    const startRow = parseInt(document.getElementById('edit-start-row').value);
    const endColumn = document.getElementById('edit-end-column').value.trim().toUpperCase();
    const notificationUserId = document.getElementById('edit-notification-user-id').value.trim();

    // 필수 항목 검증
    if (!displayName) {
        showToast('표시 이름은 필수입니다.', 'warning');
        return;
    }
    if (!slackChannelId) {
        showToast('Slack Channel ID (출석)는 필수입니다.', 'warning');
        return;
    }
    if (!sheetName) {
        showToast('시트 이름 (출석)은 필수입니다.', 'warning');
        return;
    }
    if (!assignmentSheetName) {
        showToast('시트 이름 (과제)은 필수입니다.', 'warning');
        return;
    }
    if (!nameColumn) {
        showToast('이름 열은 필수입니다.', 'warning');
        return;
    }
    if (isNaN(startRow) || startRow < 1) {
        showToast('시작 행은 1 이상의 숫자여야 합니다.', 'warning');
        return;
    }

    const btn = document.getElementById('save-edit-workspace-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ 저장 중...';

    try {
        const response = await fetch(`/api/workspaces/edit/${workspaceName}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                display_name: displayName,
                slack_channel_id: slackChannelId,
                assignment_channel_id: assignmentChannelId,
                sheet_name: sheetName,
                assignment_sheet_name: assignmentSheetName,
                name_column: nameColumn,
                start_row: startRow,
                end_column: endColumn,
                notification_user_id: notificationUserId
            })
        });

        const data = await response.json();

        if (data.success) {
            showToast('워크스페이스 정보가 수정되었습니다!', 'success');
            closeEditWorkspaceModal();

            // 워크스페이스 목록 새로고침
            loadWorkspaces();
        } else {
            showToast('오류: ' + data.error, 'error', 7000);
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error', 7000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// ========================================
// 동명이인 관리 기능
// ========================================

let currentDuplicateNames = {};

function openDuplicateNamesModal() {
    const workspaceName = document.getElementById('workspace-select').value;
    if (!workspaceName) {
        showToast('워크스페이스를 먼저 선택하세요.', 'warning');
        return;
    }

    const modal = document.getElementById('duplicate-names-modal');
    document.getElementById('duplicate-workspace-name').value = workspaceName;
    document.getElementById('duplicate-workspace-display').textContent = workspaceName;

    // 기존 동명이인 정보 로드
    loadDuplicateNames(workspaceName);

    modal.style.display = 'flex';
    setupModalFocusTrap(modal);
}

function closeDuplicateNamesModal() {
    document.getElementById('duplicate-names-modal').style.display = 'none';
    currentDuplicateNames = {};
}

async function loadDuplicateNames(workspaceName) {
    try {
        const response = await fetch(`/api/duplicate-names/${workspaceName}`);
        const data = await response.json();

        if (data.success) {
            currentDuplicateNames = data.duplicate_names || {};
            renderDuplicateNamesList();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('동명이인 정보 로드 실패:', error);
        alert('❌ 동명이인 정보를 불러올 수 없습니다:\n\n' + error.message);
    }
}

function renderDuplicateNamesList() {
    const container = document.getElementById('duplicate-names-list');
    container.innerHTML = '';

    const groupNames = Object.keys(currentDuplicateNames);

    if (groupNames.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">등록된 동명이인이 없습니다.</p>';
        return;
    }

    groupNames.forEach(groupName => {
        const group = currentDuplicateNames[groupName];
        const groupDiv = document.createElement('div');
        groupDiv.className = 'duplicate-group';
        groupDiv.style.cssText = 'border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 8px; background: #f9f9f9;';

        let groupHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0;">📋 ${groupName}</h4>
                <button type="button" class="btn btn-danger" onclick="removeDuplicateGroup('${groupName}')" style="padding: 5px 10px; font-size: 0.85rem;">🗑️ 그룹 삭제</button>
            </div>
        `;

        group.forEach((person, idx) => {
            const userIdHint = person.user_id ? `<small style="color: #666;">User ID: ${person.user_id}</small>` : '';

            groupHTML += `
                <div style="margin-bottom: 10px; padding: 15px; background: white; border-radius: 5px; border: 1px solid #e0e0e0;">
                    <div class="form-row" style="margin-bottom: 10px;">
                        <div class="form-group" style="flex: 2;">
                            <label>슬랙 이메일 📧</label>
                            <input type="email" class="form-control duplicate-email" data-group="${groupName}" data-idx="${idx}" value="${person.email || ''}" placeholder="예: hong@igini.co.kr">
                            ${userIdHint}
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label>표시 이름</label>
                            <input type="text" class="form-control duplicate-display-name" data-group="${groupName}" data-idx="${idx}" value="${person.display_name || ''}" placeholder="홍길동_컴공">
                        </div>
                        <div class="form-group" style="flex: 0.8;">
                            <label>시트 행</label>
                            <input type="number" class="form-control duplicate-sheet-row" data-group="${groupName}" data-idx="${idx}" value="${person.sheet_row || ''}" placeholder="5" min="1">
                        </div>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: flex-end;">
                        <div style="flex: 1;">
                            <label>비고 📝</label>
                            <input type="text" class="form-control duplicate-note" data-group="${groupName}" data-idx="${idx}" value="${person.note || ''}" placeholder="예: 컴퓨터공학과 3학년">
                        </div>
                        <button type="button" class="btn btn-danger" onclick="removeDuplicatePerson('${groupName}', ${idx})" style="padding: 8px 15px; white-space: nowrap;">삭제</button>
                    </div>
                </div>
            `;
        });

        groupHTML += `
            <button type="button" class="btn btn-secondary" onclick="addDuplicatePerson('${groupName}')" style="margin-top: 5px; font-size: 0.85rem;">➕ ${groupName} 추가</button>
        `;

        groupDiv.innerHTML = groupHTML;
        container.appendChild(groupDiv);
    });
}

function addDuplicateGroup() {
    const groupName = prompt('동명이인 그룹 이름을 입력하세요 (예: 홍길동):');
    if (!groupName || groupName.trim() === '') {
        return;
    }

    const trimmedName = groupName.trim();

    if (currentDuplicateNames[trimmedName]) {
        alert('이미 존재하는 그룹입니다.');
        return;
    }

    currentDuplicateNames[trimmedName] = [
        {
            email: '',
            user_id: '',
            display_name: '',
            sheet_row: null,
            note: ''
        }
    ];

    renderDuplicateNamesList();
}

function removeDuplicateGroup(groupName) {
    if (!confirm(`"${groupName}" 그룹을 삭제하시겠습니까?`)) {
        return;
    }

    delete currentDuplicateNames[groupName];
    renderDuplicateNamesList();
}

function addDuplicatePerson(groupName) {
    if (!currentDuplicateNames[groupName]) {
        currentDuplicateNames[groupName] = [];
    }

    currentDuplicateNames[groupName].push({
        email: '',
        user_id: '',
        display_name: '',
        sheet_row: null,
        note: ''
    });

    renderDuplicateNamesList();
}

function removeDuplicatePerson(groupName, idx) {
    if (!confirm('이 항목을 삭제하시겠습니까?')) {
        return;
    }

    currentDuplicateNames[groupName].splice(idx, 1);

    // 그룹이 비어있으면 그룹도 삭제
    if (currentDuplicateNames[groupName].length === 0) {
        delete currentDuplicateNames[groupName];
    }

    renderDuplicateNamesList();
}

async function saveDuplicateNames() {
    const btn = document.getElementById('save-duplicate-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ 저장 중...';

    try {
        // 입력값 수집
        const groupNames = Object.keys(currentDuplicateNames);
        const updatedData = {};

        groupNames.forEach(groupName => {
            updatedData[groupName] = [];

            const emailInputs = document.querySelectorAll(`.duplicate-email[data-group="${groupName}"]`);
            const displayNameInputs = document.querySelectorAll(`.duplicate-display-name[data-group="${groupName}"]`);
            const sheetRowInputs = document.querySelectorAll(`.duplicate-sheet-row[data-group="${groupName}"]`);
            const noteInputs = document.querySelectorAll(`.duplicate-note[data-group="${groupName}"]`);

            for (let i = 0; i < emailInputs.length; i++) {
                const email = emailInputs[i].value.trim();
                const displayName = displayNameInputs[i].value.trim();
                const sheetRow = parseInt(sheetRowInputs[i].value);
                const note = noteInputs[i] ? noteInputs[i].value.trim() : '';

                if (email && displayName && sheetRow) {
                    updatedData[groupName].push({
                        email: email,
                        display_name: displayName,
                        sheet_row: sheetRow,
                        note: note
                    });
                }
            }

            // 빈 그룹 제거
            if (updatedData[groupName].length === 0) {
                delete updatedData[groupName];
            }
        });

        const workspaceName = document.getElementById('duplicate-workspace-name').value;

        const response = await fetch(`/api/duplicate-names/${workspaceName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                duplicate_names: updatedData
            })
        });

        const data = await response.json();

        // 응답 상태 확인
        if (!response.ok) {
            // 400, 500 등의 오류
            let errorMsg = '❌ 서버 오류 (' + response.status + '): ' + (data.error || '알 수 없는 오류');
            if (data.details && data.details.length > 0) {
                errorMsg += '\n\n상세 오류:\n' + data.details.join('\n');
            }
            alert(errorMsg);
            btn.disabled = false;
            btn.innerHTML = originalText;
            return;
        }

        if (data.success) {
            showToast('동명이인 정보가 저장되었습니다! 이메일이 User ID로 변환되었습니다.', 'success', 6000);

            // 변환된 데이터로 UI 업데이트
            if (data.converted_data) {
                currentDuplicateNames = data.converted_data;
                renderDuplicateNamesList();
            } else {
                closeDuplicateNamesModal();
            }
        } else {
            // 변환 오류가 있는 경우
            let errorMsg = data.error;
            if (data.details && data.details.length > 0) {
                errorMsg += '\n상세 오류:\n' + data.details.join('\n');
            }
            showToast(errorMsg, 'error', 10000);
        }
    } catch (error) {
        showToast('저장 오류: ' + error.message, 'error', 7000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}


// ========================================
// 탭 시스템
// ========================================

// setupEventListeners 함수에 탭 시스템 초기화 추가
(function() {
    const originalSetup = setupEventListeners;
    setupEventListeners = function() {
        originalSetup();

        // 탭 전환 이벤트 등록
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.dataset.tab;

                // 모든 탭 비활성화
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

                // 모든 탭 컨텐츠 숨기기
                document.querySelectorAll('.tab-content').forEach(c => {
                    c.classList.remove('active');
                    c.style.display = 'none';
                });

                // 선택한 탭 활성화
                this.classList.add('active');

                // 선택한 탭 컨텐츠 보이기
                const targetTab = document.getElementById(`${tabName}-tab`);
                if (targetTab) {
                    targetTab.classList.add('active');
                    targetTab.style.display = 'block';
                }

                // 탭별 초기화 함수 호출
                if (tabName === 'assignment') {
                    loadAssignmentWorkspaces();
                }
            });
        });

        // 과제 체크 실행 버튼 이벤트
        const runAssignmentBtn = document.getElementById('run-assignment-btn');
        if (runAssignmentBtn) {
            runAssignmentBtn.addEventListener('click', runAssignmentCheck);
        }

        // 과제체크 탭 워크스페이스 선택 이벤트
        const assignmentWorkspaceSelect = document.getElementById('assignment-workspace-select');
        if (assignmentWorkspaceSelect) {
            assignmentWorkspaceSelect.addEventListener('change', async function(e) {
                const workspace = e.target.value;
                if (!workspace) {
                    const container = document.getElementById('recent-assignment-history');
                    if (container) container.innerHTML = '';
                    resetColumnDropdowns();
                    return;
                }
                await loadRecentAssignmentHistory(workspace);
                // 과제체크 탭에서도 열 정보 로드
                loadSheetColumns(workspace);
            });
        }
    };
})();

// 과제체크 탭 워크스페이스 로드
async function loadAssignmentWorkspaces() {
    const select = document.getElementById('assignment-workspace-select');
    if (!select || select.options.length > 1) return;

    try {
        const response = await fetch('/api/workspaces');
        const data = await response.json();

        if (data.success) {
            data.workspaces.forEach(ws => {
                const option = document.createElement('option');
                option.value = ws.folder_name;
                option.textContent = ws.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('워크스페이스 로드 오류:', error);
    }
}

// 과제 체크 실행
async function runAssignmentCheck() {
    const workspace = document.getElementById('assignment-workspace-select').value;
    const threadInput = document.getElementById('assignment-thread-input').value.trim();
    const column = document.getElementById('assignment-column').value.trim().toUpperCase();
    const markAbsent = document.getElementById('assignment-mark-absent').checked;

    if (!workspace || !threadInput || !column) {
        showToast('모든 필드를 입력해주세요.', 'warning');
        return;
    }

    const btn = document.getElementById('run-assignment-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ 과제 체크 중...';

    try {
        const response = await fetch('/api/run-assignment', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                workspace: workspace,
                thread_ts: threadInput,
                column: column,
                mark_absent: markAbsent
            })
        });

        const data = await response.json();

        if (data.success) {
            displayAssignmentResult(data.result);
            loadRecentAssignmentHistory(workspace);
            showToast('과제 체크가 완료되었습니다!', 'success');
        } else {
            showToast(`오류: ${data.error}`, 'error', 7000);
        }
    } catch (error) {
        showToast(`오류: ${error.message}`, 'error', 7000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// 과제 체크 결과 표시
function displayAssignmentResult(result) {
    const resultSection = document.getElementById('assignment-result');
    resultSection.style.display = 'block';

    document.getElementById('result-column').textContent = result.column;
    document.getElementById('submitted-count').textContent = `${result.submitted_count}명`;
    document.getElementById('not-submitted-count').textContent = `${result.not_submitted_count}명`;

    const submittedList = document.getElementById('submitted-names');
    submittedList.innerHTML = result.submitted.length > 0
        ? result.submitted.map(name => `<li>✅ ${name}</li>`).join('')
        : '<li class="info-text">제출자가 없습니다.</li>';

    const notSubmittedList = document.getElementById('not-submitted-names');
    notSubmittedList.innerHTML = result.not_submitted.length > 0
        ? result.not_submitted.map(name => `<li>❌ ${name}</li>`).join('')
        : '<li class="info-text">모두 제출했습니다!</li>';

    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 최근 과제 체크 기록 로드
async function loadRecentAssignmentHistory(workspace) {
    try {
        const response = await fetch(`/api/assignment-history/${workspace}`);
        const data = await response.json();

        if (data.success) {
            const container = document.getElementById('recent-assignment-history');
            const history = data.history.slice(0, 5);

            if (history.length === 0) {
                container.innerHTML = '<p class="info-text">아직 과제 체크 기록이 없습니다.</p>';
                return;
            }

            container.innerHTML = history.map((record, index) => `
                <div class="history-item" style="cursor: pointer;" onclick="toggleHistoryDetail('recent-history-detail-${index}')">
                    <div class="history-header">🕐 ${record.timestamp}</div>
                    <div class="history-body">
                        <p><strong>열:</strong> ${record.column}열</p>
                        <p><strong>제출:</strong> ${record.submitted_count}명 / <strong>미제출:</strong> ${record.not_submitted_count}명</p>
                        <p style="font-size: 0.85rem; color: #888; margin-top: 5px;">▼ 클릭하여 상세 보기</p>
                    </div>
                    <div id="recent-history-detail-${index}" class="history-detail" style="display: none; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <h4 style="color: #28a745; margin-bottom: 10px;">✅ 제출자 (${record.submitted_count}명)</h4>
                                <ul style="max-height: 300px; overflow-y: auto; padding-left: 20px;">
                                    ${record.submitted_list && record.submitted_list.length > 0
                                        ? record.submitted_list.map(name => `<li>${name}</li>`).join('')
                                        : '<li style="color: #999;">제출자가 없습니다.</li>'}
                                </ul>
                            </div>
                            <div>
                                <h4 style="color: #dc3545; margin-bottom: 10px;">❌ 미제출자 (${record.not_submitted_count}명)</h4>
                                <ul style="max-height: 300px; overflow-y: auto; padding-left: 20px;">
                                    ${record.not_submitted_list && record.not_submitted_list.length > 0
                                        ? record.not_submitted_list.map(name => `<li>${name}</li>`).join('')
                                        : '<li style="color: #999;">모두 제출했습니다!</li>'}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('과제 기록 로드 오류:', error);
    }
}

// 과제 이력 상세 토글
function toggleHistoryDetail(detailId) {
    const detailElement = document.getElementById(detailId);
    if (detailElement) {
        if (detailElement.style.display === 'none') {
            detailElement.style.display = 'block';
        } else {
            detailElement.style.display = 'none';
        }
    }
}

// ========================================
// 시트 열 드롭다운 관리
// ========================================

// 시트 열 정보 로드
async function loadSheetColumns(workspaceName) {
    try {
        const response = await fetch(`/api/workspaces/${workspaceName}/sheet-columns`);
        const data = await response.json();

        if (data.success && data.columns) {
            // 스케줄 모달용 열 정보 저장
            scheduleModalColumns = data.columns;

            // 출석체크 열 드롭다운 채우기
            const columnSelect = document.getElementById('column-select');
            columnSelect.innerHTML = '<option value="">열을 선택하세요...</option>';

            data.columns.forEach(col => {
                const option = document.createElement('option');
                option.value = col.letter;
                option.textContent = `${col.letter} - ${col.name}`;
                columnSelect.appendChild(option);
            });

            // 과제체크 열 드롭다운 채우기 (과제 시트용)
            loadAssignmentSheetColumns(workspaceName);
        } else {
            showToast('시트 열 정보를 불러올 수 없습니다.', 'warning');
        }
    } catch (error) {
        console.error('시트 열 로드 오류:', error);
        // 오류가 나도 사용자 경험을 해치지 않도록 조용히 처리
    }
}

// 과제 시트의 열 정보 로드
async function loadAssignmentSheetColumns(workspaceName) {
    try {
        // 과제 시트는 별도의 API로 가져오기
        const response = await fetch(`/api/workspaces/${workspaceName}/assignment-sheet-columns`);
        const data = await response.json();

        if (data.success && data.columns) {
            const assignmentColumnSelect = document.getElementById('assignment-column-select');
            assignmentColumnSelect.innerHTML = '<option value="">열을 선택하세요...</option>';

            data.columns.forEach(col => {
                const option = document.createElement('option');
                option.value = col.letter;
                option.textContent = `${col.letter} - ${col.name}`;
                assignmentColumnSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('과제 시트 열 로드 오류:', error);
    }
}

// 열 드롭다운 초기화
function resetColumnDropdowns() {
    const columnSelect = document.getElementById('column-select');
    const assignmentColumnSelect = document.getElementById('assignment-column-select');

    if (columnSelect) {
        columnSelect.innerHTML = '<option value="">워크스페이스를 먼저 선택하세요...</option>';
    }

    if (assignmentColumnSelect) {
        assignmentColumnSelect.innerHTML = '<option value="">워크스페이스를 먼저 선택하세요...</option>';
    }
}

// ========================================
// 실시간 폼 유효성 검사
// ========================================

// 유효성 검사 규칙
const validationRules = {
    'new-bot-token': {
        validate: (value) => value.startsWith('xoxb-'),
        message: 'Bot Token은 xoxb-로 시작해야 합니다.'
    },
    'new-channel-id': {
        validate: (value) => value.startsWith('C'),
        message: 'Channel ID는 C로 시작해야 합니다.'
    },
    'new-assignment-channel-id': {
        validate: (value) => !value || value.startsWith('C'),
        message: 'Channel ID는 C로 시작해야 합니다.'
    },
    'column-input': {
        validate: (value) => /^[A-Z]{1,2}$/i.test(value),
        message: '올바른 열 이름을 입력하세요 (예: H, K, AB)'
    },
    'assignment-column': {
        validate: (value) => /^[A-Z]{1,2}$/i.test(value),
        message: '올바른 열 이름을 입력하세요 (예: D, E, AA)'
    }
};

// 필드에 유효성 검사 추가
function setupFormValidation() {
    Object.keys(validationRules).forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field) return;

        const rule = validationRules[fieldId];

        // 입력 이벤트 리스너
        field.addEventListener('input', function() {
            validateField(field, rule);
        });

        // blur 이벤트에서도 검증
        field.addEventListener('blur', function() {
            if (field.value.trim()) {
                validateField(field, rule);
            }
        });
    });
}

// 개별 필드 검증
function validateField(field, rule) {
    const value = field.value.trim();

    // 값이 비어있으면 검증 스타일 제거
    if (!value) {
        clearFieldValidation(field);
        return true;
    }

    const isValid = rule.validate(value);

    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        removeFieldError(field);
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        showFieldError(field, rule.message);
    }

    return isValid;
}

// 필드 검증 스타일 제거
function clearFieldValidation(field) {
    field.classList.remove('is-valid', 'is-invalid');
    removeFieldError(field);
}

// 오류 메시지 표시
function showFieldError(field, message) {
    removeFieldError(field);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    errorDiv.id = `${field.id}-error`;

    field.parentNode.appendChild(errorDiv);
}

// 오류 메시지 제거
function removeFieldError(field) {
    const existingError = document.getElementById(`${field.id}-error`);
    if (existingError) {
        existingError.remove();
    }
}

// DOM 로드 시 폼 검증 설정 추가
document.addEventListener('DOMContentLoaded', function() {
    setupFormValidation();
});

// ========================================
// 로딩 인디케이터
// ========================================

// 전체 화면 로딩 표시
function showLoadingOverlay(message = '처리 중입니다...') {
    // 기존 오버레이 제거
    hideLoadingOverlay();

    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div class="spinner-container">
            <div class="spinner spinner-large"></div>
            <div class="loading-text">${message}</div>
        </div>
    `;

    document.body.appendChild(overlay);
}

// 전체 화면 로딩 숨기기
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// 버튼 로딩 상태 설정
function setButtonLoading(button, isLoading, loadingText = '처리 중...') {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="spinner"></span>${loadingText}`;
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
    }
}

// ========================================
// 키보드 접근성
// ========================================

// 모달 포커스 트랩 설정
function setupModalFocusTrap(modal) {
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    // 첫 번째 요소에 포커스
    if (firstFocusable) {
        setTimeout(() => firstFocusable.focus(), 100);
    }

    // 탭 키 트랩
    modal.addEventListener('keydown', function(e) {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
            // Shift + Tab
            if (document.activeElement === firstFocusable) {
                lastFocusable.focus();
                e.preventDefault();
            }
        } else {
            // Tab
            if (document.activeElement === lastFocusable) {
                firstFocusable.focus();
                e.preventDefault();
            }
        }
    });
}

// 모달 열기 시 포커스 트랩 적용 (기존 모달 열기 함수 개선)
function openModalWithFocus(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        setupModalFocusTrap(modal);
    }
}

// ========================================
// 결과 복사 기능
// ========================================

// 출석 체크 결과 복사
function copyAttendanceResult() {
    const total = document.getElementById('stat-total').textContent;
    const present = document.getElementById('stat-present').textContent;
    const absent = document.getElementById('stat-absent').textContent;
    const rate = document.getElementById('stat-rate').textContent;

    const presentList = document.getElementById('present-list').textContent;
    const absentList = document.getElementById('absent-list').textContent;

    const text = `📊 출석 체크 결과

✅ 출석: ${present}명
❌ 미출석: ${absent}명
📈 출석률: ${rate}
👥 총 인원: ${total}명

✅ 출석자:
${presentList || '(없음)'}

❌ 미출석자:
${absentList || '(없음)'}`;

    copyToClipboard(text);
}

// 클립보드에 복사
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('결과가 클립보드에 복사되었습니다!', 'success', 3000);
        }).catch(err => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// 폴백 복사 방법 (구형 브라우저)
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '-9999px';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showToast('결과가 클립보드에 복사되었습니다!', 'success', 3000);
    } catch (err) {
        showToast('복사에 실패했습니다. 브라우저가 지원하지 않습니다.', 'error');
    }

    document.body.removeChild(textArea);
}
