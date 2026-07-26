import os
import sys
import time
import datetime
import threading
import json
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import requests

# 설정 파일 경로 (스크립트 위치 기준 — 실행 cwd와 무관)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_FIREBASE_URL = "https://study-radar-72625-111d9-default-rtdb.firebaseio.com/"

class StudyTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Study Tracker (Mac)")
        self.root.geometry("450x480")
        self.root.resizable(False, False)
        
        # 스타일 테마 (Modern Dark Blue & Teal)
        self.bg_color = "#121214"
        self.card_color = "#1a1a1e"
        self.accent_color = "#00adb5"
        self.text_color = "#eeeeee"
        self.dim_text = "#8a8a93"
        self.error_color = "#ff5555"
        self.success_color = "#00e676"
        
        self.root.configure(bg=self.bg_color)
        
        # macOS의 기본 상단 애플리케이션 메뉴바 설정 (복사/붙여넣기 완벽 지원용)
        self.setup_macos_menu()
        
        # 기본 변수 설정
        self.firebase_url = ""
        self.target_hours = 3.0  # 기본 목표 시간: 3시간 (실수형으로 보관하되, UI는 hh:mm 노출)
        self.accumulated_seconds = 0
        self.is_tracking = False
        self.current_active_app = "대기 중"
        self.discord_active_seconds = 0
        self.target_locked_date = ""
        self.is_target_locked = False
        self.current_date = datetime.date.today().isoformat()
        self._goal_synced = False  # 목표 달성 직후 Firebase 즉시 동기화했는지
        self._midnight_reset_pending = False  # 자정 리셋 중복 예약 방지
        
        # 차단할 프로그램 목록 (소문자 기준 블랙리스트)
        # 스포티파이(Spotify)는 제외하고 순수 오락 목적만 가진 프로그램을 차단합니다.
        self.blocked_apps = [
            "among us",               # 어몽어스 게임
            "feather launcher",       # 마인크래프트 페더 런처
            "jujutsuphanpara",        # 주술회전 팬텀 퍼레이드 게임
            "league of legends",      # 리그 오브 레전드 게임
            "leagueoflegends",        # 리그 오브 레전드 프로세스명 대비
            "riot client",            # 라이엇 클라이언트 (롤 런처)
            "riotclient",             # 라이엇 클라이언트 프로세스명 대비
            "series comic viewer"     # 네이버 시리즈 만화 뷰어 (오락용 뷰어)
        ]
        
        # 차단할 딴짓 사이트 키워드 (유튜브, 인스타, 페북, 틱톡, 트위터/X, 넷플릭스, 트위치 등)
        self.blocked_websites = [
            "youtube.com", "youtu.be",
            "instagram.com",
            "facebook.com",
            "tiktok.com",
            "twitter.com", "x.com",
            "netflix.com",
            "twitch.tv"
        ]
        
        self.load_config()
        self.setup_ui()
        
        # 실시간 백그라운드 워커 시작
        self.running = True
        self.worker_thread = threading.Thread(target=self.tracking_worker, daemon=True)
        self.worker_thread.start()
        
        # Firebase 백그라운드 동기화 스레드 (10초 주기)
        self.sync_thread = threading.Thread(target=self.firebase_sync_worker, daemon=True)
        self.sync_thread.start()

    def load_config(self):
        """설정 파일에서 Firebase URL 및 오늘 누적 시간을 불러옵니다."""
        today_date = datetime.date.today().isoformat()
        self.current_date = today_date
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.firebase_url = (config.get("firebase_url") or "").strip()
                    self.target_hours = config.get("target_hours", 3.0)

                    saved_date = config.get("last_date", "")
                    self.target_locked_date = config.get("target_locked_date", "")

                    # 오늘 날짜와 저장된 날짜가 같으면 누적 공부 시간 및 목표 시간 고정 상태 복원
                    if saved_date == today_date:
                        self.accumulated_seconds = config.get("accumulated_seconds", 0)
                        # 오늘 이미 '공부 시작'으로 잠근 경우에만 목표 입력 잠금 유지
                        if self.target_locked_date == today_date:
                            self.is_target_locked = True
                        else:
                            self.is_target_locked = False
                            self.target_locked_date = ""
                        target_seconds = int(float(self.target_hours) * 3600)
                        self._goal_synced = self.accumulated_seconds >= target_seconds
                    else:
                        # 날짜가 바뀜(자정 이후 재실행) → 공부시간 0 + 목표 다시 수정 가능
                        self.accumulated_seconds = 0
                        self.target_locked_date = ""
                        self.is_target_locked = False
                        self._goal_synced = False
                        self._persist_new_day_unlock = True
            except Exception as e:
                print(f"설정 불러오기 실패: {e}")

        if not self.firebase_url:
            self.firebase_url = DEFAULT_FIREBASE_URL

        if getattr(self, "_persist_new_day_unlock", False):
            self._persist_new_day_unlock = False
            self.save_config()

    def apply_target_lock_ui(self, locked):
        """목표 시간 입력창 잠금/해제 UI를 한곳에서 적용합니다."""
        if locked:
            self.target_entry.config(state="disabled", disabledbackground="#1e1e22", disabledforeground=self.dim_text)
            self.target_lock_label.config(
                text=" 🔒 잠김 (자정 해제)",
                fg=self.accent_color,
                font=("Helvetica", 9, "bold"),
            )
        else:
            self.target_entry.config(state="normal", bg="#222226", fg=self.text_color)
            self.target_lock_label.config(
                text=" 🔓 수정 가능",
                fg=self.dim_text,
                font=("Helvetica", 9, "normal"),
            )

    def lock_daily_target(self, hours):
        """공부 시작 시 오늘 목표를 확정하고 자정까지 수정 불가로 잠급니다."""
        today_str = datetime.date.today().isoformat()
        self.target_hours = hours
        self.target_locked_date = today_str
        self.is_target_locked = True
        self.apply_target_lock_ui(True)

    def unlock_daily_target(self):
        """자정(또는 날짜 변경) 시 목표 시간 입력을 다시 열어줍니다."""
        self.target_locked_date = ""
        self.is_target_locked = False
        self.apply_target_lock_ui(False)

    def save_config(self):
        """현재 설정을 파일에 저장합니다."""
        config = {
            "firebase_url": self.firebase_url,
            "target_hours": self.target_hours,
            "accumulated_seconds": self.accumulated_seconds,
            "last_date": datetime.date.today().isoformat(),
            "target_locked_date": self.target_locked_date
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def format_hours_to_str(self, float_hours):
        """float 타입의 시간을 hh:mm 형태로 이쁘게 파싱합니다. (예: 2.5 -> 02:30)"""
        hrs = int(float_hours)
        mins = int(round((float_hours - hrs) * 60))
        return f"{hrs:02d}:{mins:02d}"

    def parse_str_to_hours(self, time_str):
        """hh:mm 또는 h:mm 형식의 문자열을 float 시간으로 변환합니다. (예: '2:30' -> 2.5)"""
        try:
            time_str = time_str.strip()
            if ":" in time_str:
                parts = time_str.split(":")
                if len(parts) == 2:
                    hrs = int(parts[0])
                    mins = int(parts[1])
                    if hrs >= 0 and 0 <= mins < 60:
                        return hrs + (mins / 60.0)
            else:
                # 숫자 하나만 적은 하위 호환용 (예: '3' -> 3.0)
                val = float(time_str)
                if val >= 0:
                    return val
        except ValueError:
            pass
        return None

    def setup_macos_menu(self):
        """macOS 운영체제 표준 가상 메뉴바를 활성화하여 복사(Cmd+C), 붙여넣기(Cmd+V) 및 백스페이스 편집 등의 기본 동작을 OS 수준에서 완벽 보장합니다."""
        try:
            menubar = tk.Menu(self.root)
            # 편집(Edit) 메뉴 구성
            editmenu = tk.Menu(menubar, tearoff=0)
            editmenu.add_command(label="Cut", accelerator="Cmd+X", command=lambda: self.root.focus_get().event_generate("<<Cut>>"))
            editmenu.add_command(label="Copy", accelerator="Cmd+C", command=lambda: self.root.focus_get().event_generate("<<Copy>>"))
            editmenu.add_command(label="Paste", accelerator="Cmd+V", command=lambda: self.root.focus_get().event_generate("<<Paste>>"))
            editmenu.add_command(label="Select All", accelerator="Cmd+A", command=lambda: self.root.focus_get().event_generate("<<SelectAll>>"))
            menubar.add_cascade(label="Edit", menu=editmenu)
            self.root.config(menu=menubar)
        except Exception as e:
            print(f"메뉴바 바인딩 오류: {e}")

    def setup_ui(self):
        """현대적인 다크 모드 GUI 구성"""
        # 타이틀 영역
        title_label = tk.Label(self.root, text="STUDY FLIGHT RADAR", font=("Helvetica", 16, "bold"), bg=self.bg_color, fg=self.accent_color)
        title_label.pack(pady=15)
        
        # 메인 카드 프레임
        card = tk.Frame(self.root, bg=self.card_color, bd=0)
        card.pack(fill="both", expand=True, padx=20, pady=5)
        
        # 타이머 표시기
        self.timer_label = tk.Label(card, text="00:00:00", font=("Helvetica", 42, "bold"), bg=self.card_color, fg=self.text_color)
        self.timer_label.pack(pady=12)
        
        # 상태 표시 및 현재 감지된 활성 앱
        self.status_label = tk.Label(card, text="공부 대기 중 ⏸️", font=("Helvetica", 12, "bold"), bg=self.card_color, fg=self.dim_text)
        self.status_label.pack(pady=2)
        
        self.app_detect_label = tk.Label(card, text="감지된 앱: 없음", font=("Helvetica", 10), bg=self.card_color, fg=self.dim_text)
        self.app_detect_label.pack(pady=5)
        
        # 구분선
        separator = tk.Frame(card, height=1, bg="#2a2a30")
        separator.pack(fill="x", padx=30, pady=10)
        
        # 목표 및 Firebase 설정 입력 영역
        input_frame = tk.Frame(card, bg=self.card_color)
        input_frame.pack(fill="x", padx=30)
        
        # 목표 시간 입력창 (가이드 텍스트 hh:mm 제공)
        tk.Label(input_frame, text="오늘 목표 (시간:분):", bg=self.card_color, fg=self.text_color, font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        
        target_sub_frame = tk.Frame(input_frame, bg=self.card_color)
        target_sub_frame.grid(row=0, column=1, sticky="e", pady=5)
        
        self.target_entry = tk.Entry(target_sub_frame, bg="#222226", fg=self.text_color, insertbackground=self.text_color, bd=0, width=10, font=("Helvetica", 10))
        # 기존 저장값을 hh:mm 형태로 이쁘게 변환해 디폴트 삽입
        self.target_entry.insert(0, self.format_hours_to_str(self.target_hours))
        self.target_entry.pack(side="left")
        
        self.target_lock_label = tk.Label(
            target_sub_frame,
            text=" 🔒 잠김 (자정 해제)" if self.is_target_locked else " 🔓 수정 가능",
            bg=self.card_color,
            fg=self.accent_color if self.is_target_locked else self.dim_text,
            font=("Helvetica", 9, "bold" if self.is_target_locked else "normal")
        )
        self.target_lock_label.pack(side="left", padx=(2, 0))

        if self.is_target_locked:
            self.apply_target_lock_ui(True)
        
        # Firebase URL 입력창
        tk.Label(input_frame, text="Firebase URL:", bg=self.card_color, fg=self.text_color, font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.url_entry = tk.Entry(input_frame, bg="#222226", fg=self.text_color, insertbackground=self.text_color, bd=0, width=22, font=("Helvetica", 10))
        self.url_entry.insert(0, self.firebase_url)
        self.url_entry.grid(row=1, column=1, sticky="e", pady=5)
        
        # 연동 상태 표시등
        self.db_status_label = tk.Label(card, text="● 클라우드 미연동", font=("Helvetica", 9), bg=self.card_color, fg=self.error_color)
        self.db_status_label.pack(pady=8)
        
        # 하단 컨트롤 버튼 영역
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill="x", side="bottom", pady=15, padx=20)
        
        # 스타일리시한 시작/정지 버튼 (전체 너비)
        self.start_btn = tk.Button(
            btn_frame, text="공부 시작 🔥", font=("Helvetica", 11, "bold"),
            bg=self.accent_color, fg=self.bg_color, activebackground="#008a90", activeforeground=self.bg_color,
            relief="flat", bd=0, height=2, command=self.toggle_tracking
        )
        self.start_btn.pack(fill="x", expand=True)
        
        # 타이머 초기화 업데이트 한번 실행
        self.update_timer_display()

    def toggle_tracking(self):
        """공부 추적 시작 / 일시 정지 토글"""
        if not self.is_tracking:
            # Firebase URL 검증
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("입력 오류", "Firebase Realtime DB URL을 입력해 주세요.")
                return
            
            if not url.startswith("http"):
                url = "https://" + url
            self.firebase_url = url
            
            today_str = datetime.date.today().isoformat()
            
            # 오늘 처음 '공부 시작'을 누른 순간부터 목표 시간 잠금 (자정까지 수정 불가)
            if not self.is_target_locked:
                parsed_hours = self.parse_str_to_hours(self.target_entry.get().strip())
                if parsed_hours is None or parsed_hours <= 0:
                    messagebox.showerror("입력 오류", "목표 시간 형식이 올바르지 않습니다.\n'02:30' 이나 '3:00' 형태로 0시간보다 크게 입력해 주세요.")
                    return
                
                self.lock_daily_target(parsed_hours)
            
            self.is_tracking = True
            self.start_btn.config(text="일시 정지 ⏸️", bg="#44444a", fg=self.text_color)
            self.status_label.config(text="열공 중! 측정 중입니다 🔥", fg=self.success_color)
            self.save_config()
        else:
            self.is_tracking = False
            self.start_btn.config(text="공부 시작 🔥", bg=self.accent_color, fg=self.bg_color)
            self.status_label.config(text="공부 일시 정지 중 ⏸️", fg=self.dim_text)
            self.save_config()

    def reset_accumulated_time(self):
        """오늘 누적 공부 시간을 00:00:00으로 강제 초기화하고 클라우드에도 실시간 동기화합니다."""
        if self.is_tracking:
            messagebox.showwarning("초기화 불가능", "현재 공부 타이머가 작동 중입니다.\n일시 정지 버튼을 누르신 후에 초기화를 진행해 주세요.")
            return
        
        # 정말 리셋할 것인지 컨펌 윈도우 팝업
        confirm = messagebox.askyesno("공부 시간 초기화", "정말로 오늘의 누적 공부 시간을 00:00:00으로 초기화하시겠습니까?\n(클라우드 동기화 상태도 즉시 0초로 리셋되어 윈도우 PC가 바로 잠기게 됩니다.)")
        if confirm:
            self.accumulated_seconds = 0
            self.update_timer_display()
            self.status_label.config(text="오늘 공부량이 초기화되었습니다 🔄", fg=self.dim_text)
            self.save_config()
            
            # Firebase에 실시간 0초 상태 덮어씌우기 (즉시 동기화)
            if self.firebase_url:
                # 메인 UI 지연 방지를 위해 리셋 통신은 백그라운드 스레드로 처리
                threading.Thread(target=self.immediate_firebase_reset, daemon=True).start()

    def build_study_status_payload(self, today_study_seconds=None, is_study_active=None):
        """Windows 에이전트가 잠금/해제에 쓰는 study_status 페이로드를 만듭니다."""
        today_str = datetime.date.today().isoformat()
        if today_study_seconds is None:
            today_study_seconds = self.accumulated_seconds
        if is_study_active is None:
            is_study_active = self.is_tracking
        target_seconds = int(float(self.target_hours) * 3600)
        study_seconds = int(today_study_seconds)
        return {
            "date": today_str,
            "today_study_seconds": study_seconds,
            "target_study_seconds": target_seconds,
            "goal_reached": target_seconds > 0 and study_seconds >= target_seconds,
            "is_study_active": bool(is_study_active),
            "last_updated": time.time(),
        }

    def push_study_status(self, payload, success_text="● 클라우드 동기화 완료"):
        """Firebase study_status를 즉시 PUT합니다. 성공 여부를 반환합니다."""
        if not self.firebase_url:
            return False
        try:
            base_url = self.firebase_url.rstrip("/")
            url = f"{base_url}/study_status.json"
            response = requests.put(url, json=payload, timeout=5)
            if response.status_code == 200:
                self.root.after(0, lambda: self.db_status_label.config(text=success_text, fg=self.success_color))
                return True
            self.root.after(0, lambda: self.db_status_label.config(text="● 동기화 오류 (응답 에러)", fg=self.error_color))
            return False
        except Exception as e:
            self.root.after(0, lambda: self.db_status_label.config(text="● 통신 불가 (연결 끊김)", fg=self.error_color))
            print(f"Sync 에러: {e}")
            return False

    def immediate_firebase_reset(self):
        """데이터 초기화 시 즉각 Firebase에 리셋 요청을 보내 동기화합니다."""
        payload = self.build_study_status_payload(today_study_seconds=0, is_study_active=False)
        ok = self.push_study_status(payload, success_text="● 클라우드 초기화 리셋 완료")
        if not ok:
            self.root.after(0, lambda: self.db_status_label.config(text="● 리셋 통신 실패", fg=self.error_color))

    def immediate_firebase_goal_sync(self):
        """목표 달성 순간 Windows 잠금이 바로 풀리도록 Firebase에 즉시 업로드합니다."""
        payload = self.build_study_status_payload()
        if self.push_study_status(payload, success_text="● 목표 달성 → 윈도우 잠금 해제 전송"):
            self.save_config()

    def get_macos_idle_time(self):
        """pynput 감지기 대신, macOS 전용 내장 IOKit 시스템 호출을 이용해 마우스/키보드의 '맥북 전체 유휴(비활동) 시간'을 초 단위로 즉시 가져옵니다."""
        try:
            cmd = "ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print $NF/1000000000; exit}'"
            idle_seconds = float(subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip())
            return idle_seconds
        except Exception:
            return 0.0

    def get_active_window_macos(self):
        """AppleScript를 호출하여 현재 macOS 최상단(Active) 앱 프로세스 이름을 가져옵니다."""
        try:
            cmd = "osascript -e 'tell application \"System Events\" to name of first application process whose frontmost is true'"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
            return output
        except Exception:
            return "알 수 없음"

    def close_distracting_browser_tabs(self):
        """Chrome, Safari, 네이버 웨일 브라우저에서 유튜브, 인스타, 넷플릭스 등 딴짓 사이트 탭을 실시간 탐지하여 강제로 종료합니다."""
        keywords_condition = " or ".join([f'tabURL contains "{kw}"' for kw in self.blocked_websites])
        
        chrome_script = f"""
        tell application "Google Chrome"
            if it is running then
                try
                    set windowList to every window
                    repeat with aWindow in windowList
                        set tabList to every tab of aWindow
                        repeat with aTab in tabList
                            set tabURL to URL of aTab
                            if {keywords_condition} then
                                close aTab
                            end if
                        end repeat
                    end repeat
                end try
            end if
        end tell
        """

        safari_script = f"""
        tell application "Safari"
            if it is running then
                try
                    set windowList to every window
                    repeat with aWindow in windowList
                        set tabList to every tab of aWindow
                        repeat with aTab in tabList
                            set tabURL to URL of aTab
                            if {keywords_condition} then
                                close aTab
                            end if
                        end repeat
                    end repeat
                end try
            end if
        end tell
        """

        whale_script = f"""
        tell application "Naver Whale"
            if it is running then
                try
                    set windowList to every window
                    repeat with aWindow in windowList
                        set tabList to every tab of aWindow
                        repeat with aTab in tabList
                            set tabURL to URL of aTab
                            if {keywords_condition} then
                                close aTab
                            end if
                        end repeat
                    end repeat
                end try
            end if
        end tell
        """
        
        try:
            subprocess.run(["osascript", "-e", chrome_script], capture_output=True, text=True, timeout=2)
            subprocess.run(["osascript", "-e", safari_script], capture_output=True, text=True, timeout=2)
            subprocess.run(["osascript", "-e", whale_script], capture_output=True, text=True, timeout=2)
        except Exception as e:
            print(f"딴짓 탭 종료 실행 실패: {e}")

    def check_app_blocked(self, app_name):
        """현재 켜져 있는 앱이 블랙리스트(차단 대상)에 속하는지 체크합니다."""
        if app_name == "알 수 없음":
            return False
        app_name_lower = app_name.lower()
        for blocked in self.blocked_apps:
            if blocked in app_name_lower:
                return True
        return False

    def kill_blocked_app(self, app_name):
        """차단 대상 프로그램이 전면으로 켜졌을 때 해당 프로세스를 운영체제 수준에서 즉시 강제 종료시킵니다."""
        try:
            # killall 명령어를 사용해 해당 전면 프로그램의 프로세스를 즉각 강제 폭파합니다.
            subprocess.run(["killall", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[보안 차단] 차단 대상 앱 강제 처형 성공: {app_name}")
        except Exception as e:
            print(f"[보안 차단] 앱 처형 에러 ({app_name}): {e}")

    def update_timer_display(self):
        """시간 데이터를 hh:mm:ss 형식으로 라벨에 노출 (메인 스레드 안전성 보장)"""
        hrs = self.accumulated_seconds // 3600
        mins = (self.accumulated_seconds % 3600) // 60
        secs = self.accumulated_seconds % 60
        self.timer_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")

    def tracking_worker(self):
        """1초 주기로 백그라운드에서 동작하며 실제 공부 조건에 부합하는지 감시하고 타이머를 올립니다."""
        while self.running:
            # 자정 날짜 변경을 1초 단위로도 감지 (목표 잠금 해제 + 공부시간 초기화)
            today_str = datetime.date.today().isoformat()
            if today_str != self.current_date and not self._midnight_reset_pending:
                self._midnight_reset_pending = True
                self.root.after(0, self.reset_for_new_day)
                time.sleep(1)
                continue

            target_seconds = int(self.target_hours * 3600)
            is_goal_reached = self.accumulated_seconds >= target_seconds
            
            if self.is_tracking:
                # 1. 활성 앱 모니터링
                active_app = self.get_active_window_macos()
                self.current_active_app = active_app
                
                # 디스코드 연속 5분 사용 제한 체크 (잡담 방지)
                if "discord" in active_app.lower():
                    self.discord_active_seconds += 1
                    if self.discord_active_seconds >= 300: # 5분 (300초)
                        self.discord_active_seconds = 0
                        self.root.after(0, lambda: self.status_label.config(text="🚨 디스코드 5분 초과로 강제 종료!", fg=self.error_color))
                        self.kill_blocked_app("Discord")
                else:
                    self.discord_active_seconds = 0
                
                # 메인 UI 요소 업데이트는 thread-safety를 위해 root.after로 전달
                self.root.after(0, lambda a=active_app: self.app_detect_label.config(text=f"감지된 앱: {a}"))
                
                # 2. 2초 주기로 딴짓 웹 사이트 탭 강제 강제 종료 실행 (유튜브, 인스타, 페북 등 저격)
                if self.accumulated_seconds % 2 == 0 and not is_goal_reached:
                    self.close_distracting_browser_tabs()

                # 3. 자리비움 체크 (ioreg 기반 시스템 비활동 시간 측정 - 권한 우회 및 안정성 100%)
                idle_time = self.get_macos_idle_time()
                is_idle = idle_time > 300  # 5분(300초) 이상 조작 없음
                
                # 4. 차단 대상 프로그램 실행 중인지 여부 체크
                is_blocked = self.check_app_blocked(active_app)
                
                if is_idle:
                    # 자리 비움으로 인한 강제 일시 정지 (이것은 기존처럼 멈추고 안내)
                    self.is_tracking = False
                    self.root.after(0, lambda: messagebox.showwarning("자리비움 감지", "5분 이상 움직임이 없어 공부 타이머가 일시 정지되었습니다.\n공부를 다시 시작하면 '공부 시작'을 눌러주세요."))
                    self.root.after(0, lambda: self.pause_by_system("자리비움으로 일시정지 ⏸️"))
                elif is_blocked:
                    # ⚠️ 차단 대상 앱 가동 감지!
                    if not is_goal_reached:
                        # 아직 목표 시간을 채우지 않았다면 -> 타이머를 멈추지 않고, 딴짓 앱만 번개처럼 강제 폭파 종료시킵니다!
                        self.root.after(0, lambda a=active_app: self.status_label.config(text=f"🚨 차단 대상 앱 [{a}] 강제 종료 완료!", fg=self.error_color))
                        self.kill_blocked_app(active_app)
                    else:
                        # 목표 시간을 다 채운 이후에는 정상 허용하여 아무 앱이나 다 켤 수 있게 둡니다.
                        self.accumulated_seconds += 1
                        self.root.after(0, self.update_timer_display)
                else:
                    # 모든 조건 통과 시 1초 누적
                    self.accumulated_seconds += 1
                    self.root.after(0, self.update_timer_display)
                    
                    # 오늘 목표 달성 여부 실시간 체크 → 달성 직후 Firebase 즉시 전송(Windows 잠금 해제)
                    if self.accumulated_seconds >= target_seconds:
                        self.root.after(0, lambda: self.status_label.config(text="오늘 목표 달성 성공! 🎉", fg=self.success_color))
                        if not self._goal_synced:
                            self._goal_synced = True
                            threading.Thread(target=self.immediate_firebase_goal_sync, daemon=True).start()
            else:
                # [공부 타이머가 일시정지 되어 있을 때의 보안 감시 로직]
                # 목표를 채우지 못했다면 일시정지 상태여도 게임, 디스코드, 딴짓 탭 차단 작동!
                if not is_goal_reached:
                    active_app = self.get_active_window_macos()
                    
                    # 1. 블랙리스트 프로그램이 활성화되면 즉시 종료
                    if self.check_app_blocked(active_app):
                        self.root.after(0, lambda a=active_app: self.status_label.config(text=f"🚨 [미완수 잠금] 일시정지 중 딴짓 불가! [{a}] 종료", fg=self.error_color))
                        self.kill_blocked_app(active_app)
                    
                    # 2. 디스코드 감지되면 즉시 종료 (일시정지 중에는 즉시 차단!)
                    if "discord" in active_app.lower():
                        self.root.after(0, lambda: self.status_label.config(text="🚨 [미완수 잠금] 일시정지 중 디스코드 사용 불가!", fg=self.error_color))
                        self.kill_blocked_app("Discord")
                        
                    # 3. 딴짓 웹사이트 차단 (일시정지 중에는 2초 주기로 작동)
                    if int(time.time()) % 2 == 0:
                        self.close_distracting_browser_tabs()
            
            time.sleep(1)

    def pause_by_system(self, reason_text):
        """자리를 비웠거나 다른 앱을 켰을 때 시스템이 타이머를 중지시킴 (메인 스레드에서만 실행)"""
        self.start_btn.config(text="공부 시작 🔥", bg=self.accent_color, fg=self.bg_color)
        self.status_label.config(text=reason_text, fg=self.error_color)
        self.save_config()

    def reset_for_new_day(self):
        """자정(24시) 정각: 공부시간 0초 초기화 + 목표 시간 다시 수정 가능 + Windows 재잠금."""
        self.accumulated_seconds = 0
        self.is_tracking = False
        self._goal_synced = False
        self._midnight_reset_pending = False
        self.current_date = datetime.date.today().isoformat()
        self.unlock_daily_target()
        self.start_btn.config(text="공부 시작 🔥", bg=self.accent_color, fg=self.bg_color)
        self.update_timer_display()
        self.status_label.config(
            text="🚨 자정 초기화! 공부시간 리셋 · 목표 다시 수정 가능",
            fg=self.error_color,
        )
        self.save_config()

        # 즉시 Firebase에도 오늘 0초 상태 전송하여 윈도우 PC 및 클라우드 즉시 재잠금
        if self.firebase_url:
            threading.Thread(target=self.immediate_firebase_reset, daemon=True).start()

    def firebase_sync_worker(self):
        """10초 주기로 Firebase Realtime Database에 오늘의 공부 누적량과 목표량 상태를 실시간 업로드합니다."""
        while self.running:
            # 자정 날짜 변경 감지 → 당일 리셋 (공부시간 + 목표 잠금 해제 + Windows 재잠금)
            today_str = datetime.date.today().isoformat()
            if today_str != self.current_date:
                if not self._midnight_reset_pending:
                    self._midnight_reset_pending = True
                    self.root.after(0, self.reset_for_new_day)
                time.sleep(1)
                continue

            if self.firebase_url:
                payload = self.build_study_status_payload()
                if payload["goal_reached"]:
                    self._goal_synced = True
                if self.push_study_status(payload):
                    self.save_config()

            time.sleep(10)

    def onClose(self):
        """창을 닫을 때 리소스 정리 및 데이터 최종 저장"""
        self.running = False
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudyTrackerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.onClose)
    root.mainloop()
