# macOS Study Support Tracker (맥 전용 학습 보조 프로그램) 🍏🚀

macOS 환경에서 학습에 집중할 수 있도록 돕는 백그라운드 학습 시간 측정 및 집중 서포트 프로그램입니다. 
공부 중 유휴 시간(자리비움)을 실시간 감지하여 타이머를 일시정지하고, 공부 도중 학습을 방해하는 특정 오락용 프로그램이나 웹사이트 탭을 감지 시 조용히 정리하여 몰입을 유도합니다. 오늘의 학습 누적 시간은 Firebase Realtime Database와 실시간 연동되어 동기화 및 백업됩니다.

## ✨ 주요 기능
1. **스마트 타이머 및 다크 테마 GUI 🎨**
   - Tkinter를 활용한 미려한 Modern Dark Blue & Teal 테마의 UI를 제공합니다.
   - macOS 시스템 가상 메뉴바 연동으로 입력창 내 복사(Cmd+C)/붙여넣기(Cmd+V) 및 백스페이스 편집 등의 단축키를 완벽히 지원합니다.
2. **ioreg 기반 스마트 자리비움 감지 ⏸️**
   - macOS 전용 IOKit 시스템 호출을 활용하여 마우스/키보드의 비활동(유휴) 시간을 초 단위로 측정합니다. 5분 이상 시스템 조작이 없으면 공부 타이머를 일시 정지하여 불필요한 공회전을 방지합니다.
3. **학습 방해 프로그램 제어 (블랙리스트) 🚨**
   - 스포티파이(`Spotify`)와 같은 업무/학습용 음악 스트리밍 앱은 정상 허용하되, 사전에 등록된 오락 목적의 프로그램이 실행될 경우 감지하여 정리를 유도합니다.
4. **산만함 방지 브라우저 탭 제어 🌐**
   - Chrome, Safari, 네이버 웨일 브라우저에서 유튜브, 인스타그램, 페이스북, 틱톡, 트위터(X), 넷플릭스, 트위치 등 집중을 분산시키는 웹 사이트 접속 시 실시간 탐지하여 해당 탭만 지능적으로 닫습니다.
5. **Firebase 실시간 클라우드 동기화 ☁️**
   - 10초 주기로 Firebase Realtime Database에 공부 시작 상태, 오늘 누적 공부 시간(초), 목표 달성 상태를 실시간 업로드 및 동기화합니다.
6. **당일 목표 시간 고정(잠금) 시스템 🔒**
   - 의지 약화로 인한 목표 시간 단축을 방지하기 위해, 하루 목표 시간을 입력하고 공부를 시작하면 당일 동안은 목표 시간을 수정할 수 없도록 자동 잠금(`🔒 잠김`)됩니다. (자정이 지나 새 날짜가 되면 자동 해제)

## 🛠️ 시작하기

### 1. 패키지 설치
프로젝트 루트 디렉토리에서 아래 명령어로 필요한 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

### 2. 실행 방법
```bash
python tracker.py
```

### 3. 주요 설정
- 실행 후 화면의 **오늘 목표 (시간:분)** 입력창에 `02:30` 또는 `3:00` 과 같은 형식으로 목표 시간을 지정합니다.
- 공부를 시작하는 순간 당일 목표 시간이 고정(`🔒 잠김`)되어 그 날 하루 동안 임의 수정을 방지합니다.
- 연동할 **Firebase URL**을 입력해 클라우드와 실시간 상태를 동기화할 수 있습니다.
- 설정 값과 공부 누적 시간은 `config.json` 파일에 로컬로 자동 보관되어 프로그램 재실행 시 복원됩니다.

---

## ⚙️ 프로그램 커스터마이징 가이드

프로그램 제어 목록이나 제한 시간은 코드 내에서 아주 쉽게 원하는 대로 수정할 수 있습니다.

### 1. 🚫 블랙리스트 애플리케이션 변경하기
공부할 때 차단하고 싶은 게임, 소셜 미디어 앱이 있다면 `tracker.py` 파일의 약 44번째 라인 부근의 `self.blocked_apps` 리스트를 수정해 주세요.

```python
        # tracker.py 파일 약 44번째 줄
        self.blocked_apps = [
            "among us",               # 어몽어스 게임
            "feather launcher",       # 마인크래프트 페더 런처
            "jujutsuphanpara",        # 주술회전 팬텀 퍼레이드 게임
            "league of legends",      # 리그 오브 레전드 게임
            "leagueoflegends",        # 리그 오브 레전드 프로세스명 대비
            "riot client",            # 라이엇 클라이언트 (롤 런처)
            "riotclient",             # 라이엇 클라이언트 프로세스명 대비
            "series comic viewer",    # 네이버 시리즈 만화 뷰어
            "steam",                  # (예시 추가) 스팀 클라이언트 차단 시
        ]
```
* **팁**: 차단하려는 앱의 이름을 **영어 소문자**로 입력해 주시면 대소문자 구분 없이 감지하여 처리합니다.
* **프로세스 이름 확인법**: 차단하려는 앱을 켠 상태에서 Study Tracker의 메인 화면에 표시되는 **`감지된 앱: [앱이름]`** 부분을 보고 프로세스명을 그대로 추가하면 가장 정확합니다.

### 2. 💬 디스코드(Discord) 연속 사용 제한 시간 조절하기
디스코드는 소통 목적으로 사용할 수 있도록 허용되어 있으나, 연속으로 5분(300초) 동안 켜두고 사용하면 잡담 방지를 위해 감지 후 정리를 유도합니다. 
제한 시간을 늘리거나 줄이고 싶다면 `tracker.py` 파일의 약 415번째 라인 부근을 수정해 주세요.

```python
                # tracker.py 파일 약 415번째 줄
                if "discord" in active_app.lower():
                    self.discord_active_seconds += 1
                    if self.discord_active_seconds >= 300: # 5분 (초 단위로 수정 가능, 예: 10분 = 600)
                        self.discord_active_seconds = 0
                        self.root.after(0, lambda: self.status_label.config(text="🚨 디스코드 5분 초과로 강제 종료!", fg=self.error_color))
                        self.kill_blocked_app("Discord")
```
* 디스코드 시간제한을 아예 없애고 싶으시다면 이 부분의 코드 블록 전체를 주석 처리 또는 삭제하시면 됩니다.

### 3. 🌐 차단 브라우저 탭(웹 사이트) 변경하기
차단하고 싶은 딴짓 웹 사이트 목록은 `tracker.py` 파일의 약 57번째 라인 부근의 `self.blocked_websites`를 수정하시면 됩니다.

```python
        # tracker.py 파일 약 57번째 줄
        self.blocked_websites = [
            "youtube.com", "youtu.be",
            "instagram.com",
            "facebook.com",
            "tiktok.com",
            "twitter.com", "x.com",
            "netflix.com",
            "twitch.tv"
        ]
```

---
*Developed as part of BIND-assignment.*
