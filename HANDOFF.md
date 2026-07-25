# 📌 Study Flight Radar — 세션 인수인계 / 과정 정리 (HANDOFF.md)

> **AI 에이전트**: 이 폴더에서 새 세션을 시작하면 **먼저 `STATUS.md`와 이 파일(`HANDOFF.md`)을 읽고** 이어서 작업하세요.  
> **작업 1개 끝낼 때마다** `STATUS.md` + `HANDOFF.md`를 **반드시 갱신**하세요. (한 번에 몰아서 쓰지 말 것)  
> **Mac 코드가 수정될 때마다** `mac_tracker/` → GitHub `gunrp0803-droid/mac-study-tracker`에 **즉시 커밋 + `git push`**. `windows_agent/`는 **절대 올리지 말 것**.

---

## 1. 프로젝트가 무엇인가

맥북에서 하루 공부 목표를 채우지 않으면, 집 Windows 게임 PC 화면을 Firebase를 통해 원격으로 잠근다 (`LockWorkStation`).

| 구분 | 역할 | 경로 |
|------|------|------|
| Mac 타이머 | 공부 시간 측정 → Firebase 업로드 | `Desktop/anything/study/mac_tracker/` |
| Windows 에이전트 | Firebase 감시 → 목표 미달 시 화면 잠금 | `Desktop/anything/study/windows_agent/` |
| 클라우드 허브 | 실시간 DB | `https://study-radar-72625-default-rtdb.firebaseio.com/` |

- GitHub (Mac만): `https://github.com/gunrp0803-droid/mac-study-tracker`
- **Windows 코드는 GitHub에 올리지 않음** (`mac_tracker/.gitignore`에 `windows_agent/` 등록)

---

## 2. 2026-07-25에 실제로 겪은 일 (중요)

### 증상
Windows에서 에이전트를 켜면 **"Firebase URL이 설정되지 않았다"**고 나옴.  
Mac / Firebase / `windows_agent/config.json`에는 URL이 **이미 정상**이었다.

### 진짜 원인
예전 `agent.py`는 `config.json`을 **현재 작업 폴더(cwd)** 기준으로 찾았다.  
시작 프로그램·다른 경로에서 실행하면 exe 옆 config를 못 찾고, `YOUR_FIREBASE_DB_URL` 템플릿을 새로 만들어 오류가 났다.

### 수정 내용 (이미 반영됨)
- Windows: config를 **스크립트/exe가 있는 폴더** 기준으로 읽음. 없거나 템플릿이면 기본 URL로 자동 보정.
- Mac: 자정 리셋이 실제로 호출되도록 연결, 목표 잠금 상태 초기화 버그 수정, config 경로 안정화.
- GitHub: Mac `tracker.py`만 푸시 (`684d1f4`). Windows는 미포함.

---

## 3. Windows에 다시 올린 실제 과정 (유저가 성공한 방법)

### 1단계 — 폴더 복사
Mac의 `Desktop/anything/study/windows_agent/` 전체를 Windows PC로 복사·붙여넣기.

필수 파일:
- `agent.py`
- `config.json` (안에 Firebase URL 있어야 함)
- `requirements.txt`
- `README.md` (선택)

### 2단계 — 흔한 실수 (반드시 피할 것)
PowerShell이 `C:\Users\gunrp` 같은 **홈 폴더**에 있으면:

```text
ERROR: Could not open requirements file: ... 'requirements.txt'
ERROR: Script file 'agent.py' does not exist.
```

→ 파일이 없어서가 아니라, **지금 있는 폴더가 틀려서**다.  
`windows_agent` 폴더로 들어간 뒤 명령을 실행하거나, 아래 3단계처럼 더블클릭한다.

### 3단계 — 실행 (이번에 성공한 방법)
탐색기에서 `windows_agent` 폴더를 연 다음 **`agent.py`를 더블클릭**.

전제:
- Windows에 Python이 설치되어 있을 것
- 가능하면 미리 `pip install requests` (또는 해당 폴더에서 `pip install -r requirements.txt`)
- **`agent.py`와 `config.json`이 같은 폴더**에 있을 것

성공 시: 검은 콘솔에 Firebase URL 로드 메시지가 나오고, 공부 목표 미달이면 화면이 잠긴다.

### (선택) exe로 빌드하는 방법
`windows_agent` 폴더에서 PowerShell을 연 뒤:

```powershell
cd <windows_agent가_있는_경로>
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconsole --onefile agent.py
copy config.json dist\
.\dist\agent.exe
```

주의: 명령은 **반드시 `windows_agent` 안에서** 실행.  
홈 폴더(`C:\Users\...`)에서 `pyinstaller ... agent.py` 하면 또 "agent.py does not exist"가 난다.

---

## 4. Mac 쪽 현재 상태

- 경로: `/Users/dgsw50/Desktop/anything/study/mac_tracker/`
- 실행: `tracker.py` (venv 또는 `python3 tracker.py`)
- Firebase에 10초마다 `study_status` 업로드
- 오늘 목표 잠금, 자정 리셋, 딴짓 앱/사이트 차단 동작

확인용:

```bash
curl -s "https://study-radar-72625-default-rtdb.firebaseio.com/study_status.json"
```

---

## 5. 새 AI 세션이 바로 해야 할 일

1. `STATUS.md` + `HANDOFF.md` 읽기
2. Mac `config.json` / Windows `config.json` / Firebase 라이브 데이터 확인
3. 유저 요청에 맞춰 수정 → **실행/테스트**
4. **작업 1개마다** `STATUS.md` + `HANDOFF.md` 갱신 (`study/` 원본과 `mac_tracker/` 복사본 동기화)
5. **Mac 코드/문서 변경 시마다** `mac_tracker/`에서 **커밋 + `git push`** (`windows_agent/` 제외). 런타임 `config.json` 상태값은 커밋하지 않음. GitHub에는 **Mac만**

### 커밋·푸시 위치
```bash
cd ~/Desktop/anything/study/mac_tracker
# Windows 제외 확인 후
git add <변경된 Mac 파일들>
git commit -m "..."
git push
```
원격: `https://github.com/gunrp0803-droid/mac-study-tracker`

---

## 6. 자주 묻는 오해

| 오해 | 사실 |
|------|------|
| Windows에 URL이 없다 | Mac·원본 config에는 이미 있음. 경로/cwd 문제였음. |
| `pip install -r requirements.txt`가 홈에서 실패 | `windows_agent`로 `cd` 안 해서임. |
| GitHub에 Windows도 올려야 한다 | **올리지 말 것.** 로컬 `windows_agent/`만 유지. |
| exe만 있어야 한다 | `agent.py` 더블클릭으로도 동작 확인됨 (Python 설치 시). |

---

## 7. 관련 문서

| 파일 | 용도 |
|------|------|
| `STATUS.md` | AI 세션 자동 인계 (최신 할 일·완료 현황) |
| `HANDOFF.md` | 이 파일 — 실제 겪은 과정·함정·성공 절차 |
| `README.md` | 전체 시스템 세팅 매뉴얼 |
| `windows_agent/README.md` | Windows 에이전트 설치 상세 |
| `study_tracker_plan.md` | 기획·아키텍처 |
| `final_security_report.md` | 보안·우회 방지 점검 |

---

## 8. 변경 이력 (요약)

- **2026-07-25**: Firebase URL “미설정” 버그 수정, Mac 자정 리셋 수정, GitHub Mac-only 푸시, Windows에 폴더 복사 후 `agent.py` 더블클릭으로 연동 성공 → 본 문서 작성.
- **2026-07-25 (이어짐)**: 작업 1개마다 STATUS/HANDOFF 갱신 + Mac 코드 변경 시마다 GitHub 커밋·푸시(Windows 제외) 규칙을 인수인계에 고정. `mac_tracker/`에 STATUS·HANDOFF 복사본 추가.
- **2026-07-25 (목표 해제)**: 3시간(목표) 달성 시 Windows 잠금이 풀리는 경로를 재검토. 기본 비교 로직은 이미 올바름. Mac은 달성 즉시 Firebase 동기화 + `goal_reached` 전송, Windows는 `should_lock()`으로 해제 판정 강화. Windows에는 최신 `agent.py` 재배포 필요.

---

## 9. 잠금 해제 판정 (중요)

| 조건 | 결과 |
|------|------|
| `date == 오늘` AND `target_study_seconds > 0` AND (`today_study_seconds >= target` OR `goal_reached`) | **잠금 해제** |
| 그 외 (미달·날짜 불일치·목표 없음·데이터 없음·오프라인 3회+) | **잠금** |

기본 목표 3시간 → `target_study_seconds = 10800`. Mac이 10800초를 찍는 순간 즉시 Firebase PUT → Windows는 최대 약 2초 내 해제.
