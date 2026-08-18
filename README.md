# Study Tracker

macOS에서 공부 시간을 기록하고 Firebase Realtime Database와 동기화하는 간단한 타이머입니다.
공부 중 자리비움, 차단 앱, 차단 웹사이트를 감지하면 타이머를 일시 정지하거나 해당 항목을 종료합니다.

## 기능

- `hh:mm` 또는 시간 숫자로 일일 목표 설정
- 공부 시간 누적 및 `config.json` 저장
- 5분 이상 키보드·마우스 입력이 없으면 자동 일시 정지
- 등록된 차단 앱 감지 및 종료
- Chrome, Safari, Naver Whale의 차단 웹사이트 탭 종료
- Discord 연속 사용 시간 제한
- Firebase Realtime Database에 10초마다 상태 동기화
- 목표 시간 달성 시 `goal_reached` 상태 전송
- 공부를 시작하면 당일 목표 수정 잠금
- 날짜가 바뀌면 누적 시간과 목표 잠금 초기화

## 실행 환경

- macOS
- Python 3.10 이상
- Tkinter
- Firebase Realtime Database

`tkinter`는 Python의 기본 GUI 모듈이며, 설치한 Python 배포판에 따라 별도로 포함되지 않을 수 있습니다.

## 설치 및 실행

```bash
cd mac_tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python tracker.py
```

## 초기 설정

프로그램을 실행한 뒤 다음 항목을 입력합니다.

1. 오늘 목표 시간을 입력합니다. 예: `02:30`, `3:00`
2. Firebase Realtime Database URL을 입력합니다.
3. `공부 시작`을 누릅니다.

공부를 시작하면 해당 날짜의 목표 시간이 잠깁니다. 다음 날이 되면 목표를 다시 수정할 수 있습니다.

설정과 오늘 누적 시간은 `config.json`에 저장됩니다. 이 파일에는 개인별 Firebase 주소와 실행 상태가 포함될 수 있으므로 공개 저장소에 올리지 않는 것을 권장합니다.

## macOS 권한

다음 기능을 사용하려면 macOS에서 권한을 허용해야 할 수 있습니다.

- 시스템 유휴 시간 확인: 손쉬운 사용 권한
- 현재 활성 앱 확인: 시스템 이벤트 자동화 권한
- 브라우저 탭 종료: 각 브라우저 자동화 권한

권한은 `시스템 설정 > 개인정보 보호 및 보안`에서 Python 또는 실행에 사용한 터미널 앱에 부여합니다.

## 차단 목록 수정

`tracker.py`의 `blocked_apps`에 앱 이름 일부를 소문자로 추가합니다. 앱 이름은 화면의 `감지된 앱` 항목에서 확인할 수 있습니다.

```python
self.blocked_apps = [
    "among us",
    "league of legends",
    "steam",
]
```

웹사이트 차단 목록은 `blocked_websites`에서 수정합니다.

```python
self.blocked_websites = [
    "youtube.com",
    "instagram.com",
    "netflix.com",
]
```

Discord 연속 사용 제한은 `tracking_worker`의 `300`초 값을 변경해 조절할 수 있습니다.

## 테스트

GUI를 실행하지 않고 순수 로직 테스트를 실행할 수 있습니다.

```bash
python -m unittest -v test_tracker.py
python -m py_compile tracker.py
```

## Firebase 데이터

프로그램은 `study_status` 경로에 다음 상태를 저장합니다.

```json
{
  "date": "2026-08-18",
  "today_study_seconds": 3600,
  "target_study_seconds": 10800,
  "goal_reached": false,
  "is_study_active": true,
  "last_updated": 1723939200
}
```

Firebase 보안 규칙은 공개 읽기·쓰기로 설정하지 말고, 실제 사용 환경에 맞게 인증과 접근 권한을 설정해야 합니다.
