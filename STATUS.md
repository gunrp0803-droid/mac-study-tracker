# 📌 프로젝트 작업 현황 및 세션 인계 문서 (STATUS.md)

> **⚠️ AI 에이전트 / 개발자 안내 (Agent Instruction)**
> 1. 이 폴더 (`/Users/dgsw50/Desktop/anything/study`)에서 새 세션이 시작되면, 유저 설명이 없어도 **`STATUS.md`와 `HANDOFF.md`를 먼저 읽고** 이어서 작업하세요.
> 2. **코드 수정 시**: 수정할 때마다 실행/테스트로 동작 검증하세요.
> 3. **작업 1개 끝낼 때마다** `STATUS.md`와 `HANDOFF.md`를 **반드시 갱신**하세요. (완료 항목·다음 할 일·변경 이력·함정)
> 4. **Mac 코드가 바뀔 때마다** `mac_tracker/`에서 GitHub(`gunrp0803-droid/mac-study-tracker`)에 **즉시 커밋하고 `git push`까지** 하세요. `windows_agent/`는 **절대 포함하지 마세요.**
> 5. 런타임 상태만 바뀐 `config.json`(누적 초·날짜 등)은 커밋하지 마세요. 코드·문서·의존성 변경만 커밋·푸시합니다.

---

## 📅 최종 업데이트 일시
- **시각**: 2026-07-26 11:19
- **작업 환경**: `/Users/dgsw50/Desktop/anything/study`
- **상세 과정 문서**: `HANDOFF.md` (반드시 함께 읽을 것)
- **오늘 목표 (수동)**: **2시간** (유저 요청으로 3→2 변경, Firebase `target_study_seconds=7200`)

---

## 🎯 프로젝트 개요
- **이름**: Study Flight Radar — 공부 연동 Windows 게임 PC 화면 잠금
- **Firebase**: `https://study-radar-72625-111d9-default-rtdb.firebaseio.com/`
- **GitHub (Mac only)**: `gunrp0803-droid/mac-study-tracker`

---

## 📂 구조

```text
Desktop/anything/study/
├── STATUS.md              # 이 파일 — 현황·다음 할 일
├── HANDOFF.md             # 실제 겪은 과정·함정·성공 절차 (AI 인수인계용)
├── README.md
├── study_tracker_plan.md
├── final_security_report.md
├── mac_tracker/           # GitHub 대상
└── windows_agent/         # 로컬 전용 (GitHub 제외)
```

---

## ✅ 완료된 작업

1. Firebase 구축·Mac/Windows config URL 동일 설정·실시간 동기화
2. Windows “Firebase URL 미설정” 버그 수정 (config를 exe/스크립트 옆 절대경로로 로드 + 기본 URL 자동 보정)
3. Mac 자정 리셋 실제 호출·목표 잠금 초기화 버그 수정
4. GitHub Mac-only 푸시 (`684d1f4`), Windows 미포함
5. **Windows PC 연동 성공 (2026-07-25)**:
   - `windows_agent` 폴더를 Windows에 복사
   - 탐색기에서 **`agent.py` 더블클릭**으로 실행 → 정상 동작 확인
   - (참고) PowerShell을 홈 폴더에서 쓰면 `agent.py` / `requirements.txt` not found — 폴더로 `cd` 필요
6. **세션 규칙 고정 (2026-07-25)**: 작업 1개마다 STATUS/HANDOFF 갱신 + Mac 코드 변경 시마다 GitHub 커밋·푸시(Windows 제외)
7. **목표 달성 → Windows 잠금 해제 검증·강화 (2026-07-25)**:
   - 기존에도 `today_study_seconds >= target_study_seconds`이면 해제됨을 확인
   - Mac: 달성 순간 Firebase 즉시 PUT + `goal_reached` 필드 추가
   - Windows: `should_lock()`로 판정 명확화(날짜·목표>0·공부≥목표/`goal_reached`)
   - 단위 테스트로 3시간(10800초) 경계 잠금/해제 PASS
   - ⚠️ Windows PC에는 수정된 `agent.py`를 **다시 복사**해야 반영됨
8. **목표 시간 잠금 규칙 명확화 (2026-07-25)**:
   - `공부 시작` 누르는 순간부터 목표 입력 잠금 (`🔒 잠김 (자정 해제)`)
   - **24시(자정)**에 공부시간 0 리셋 + 목표 다시 수정 가능 (`🔓 수정 가능`)
   - 자정 감지를 1초 워커에도 연결, 중복 리셋 방지
9. **Windows 완료 로그 스팸 수정 (2026-07-25)**:
   - 목표 달성 메시지가 2초마다 반복되던 문제 → **상태 전환 시 1회만** 출력
   - 미달성 진행 로그는 최대 1분 1회
   - ⚠️ Windows에 최신 `agent.py` **재복사 후 재실행** 필요
10. **Firebase 인스턴스 교체 (2026-07-26)**:
   - 기존 `study-radar-72625-default-rtdb`가 404를 반환해 새 Realtime Database 인스턴스로 변경
   - Mac/Windows 기본 URL과 설정 파일을 새 주소로 갱신

---

## 📌 다음 할 일 (Next)

- [ ] Windows PC에 최신 `windows_agent/agent.py` 재복사·재실행 (로그 스팸 수정 포함)
- [ ] (선택) Windows에서 `pyinstaller`로 `agent.exe` 만들어 콘솔 없이·부팅 자동 실행 강화
- [ ] (선택) Windows 시작 프로그램 등록이 의도대로인지 재부팅 후 확인
- [x] Mac 타이머·Windows 에이전트 기본 연동
- [x] 인수인계·커밋 워크플로 문서화
- [x] 3시간 달성 시 Windows 잠금 해제 로직 검증·강화
- [x] 목표 시간: 시작 시 잠금 / 자정에 수정 가능
- [x] Windows 목표 달성 콘솔 메시지 스팸 제거

일상 운영: Mac에서 `tracker.py` 켜고, Windows에서 `agent.py`(또는 exe) 켜 두면 됨.

잠금 해제 조건: **오늘 날짜 일치** AND **목표 > 0** AND (**공부시간 ≥ 목표** OR `goal_reached=true`). 기본 목표 3시간 = 10800초.

### 목표 시간 규칙
| 시점 | 목표 입력 |
|------|-----------|
| 하루 시작·자정 직후·아직 시작 전 | 수정 가능 |
| `공부 시작` 클릭 이후 (당일) | 수정 불가 |
| 다음 날 00:00 | 다시 수정 가능 |

---

## 🔁 작업 루프 (필수)

1. 작업 1개 수행 → 실행/테스트
2. **즉시** `STATUS.md` + `HANDOFF.md` 갱신 (study/ 원본 + `mac_tracker/` 복사본 동기화)
3. Mac 코드/문서가 바뀌었으면 `mac_tracker/`에서 **커밋 + `git push`** (Windows 제외)

---

## 💡 새 세션 체크리스트
1. `STATUS.md` + `HANDOFF.md` 읽기
2. Firebase 라이브: `curl -s "https://study-radar-72625-111d9-default-rtdb.firebaseio.com/study_status.json"`
3. Mac/Windows `config.json`의 `firebase_url` 확인
4. 수정 → 테스트 → **문서 갱신** → **Mac-only 커밋 + push**
5. push 전 Windows 코드 제외 재확인
