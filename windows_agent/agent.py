import os
import sys
import time
import datetime
import json
import requests
import subprocess

try:
    import ctypes
    import winreg
except ImportError:
    ctypes = None
    winreg = None

# 설정 파일 경로
CONFIG_FILE = "config.json"

class WindowsStudyAgent:
    def __init__(self):
        self.firebase_url = ""
        self.running = True
        self.check_interval = 2.0  # 2초마다 클라우드 데이터 확인 및 잠금 처리
        
        print("=========================================")
        print("   STUDY RADAR - Windows Locking Agent   ")
        print("=========================================")
        self.load_config()

        # Windows 환경 전용 고급 보안 설정 적용
        if sys.platform == "win32":
            self.register_to_startup()
            self.start_watchdog()

    def load_config(self):
        """설정 파일에서 Firebase URL을 불러옵니다."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.firebase_url = config.get("firebase_url", "")
                    print(f"[설정] Firebase URL이 정상 로드되었습니다.\nURL: {self.firebase_url}")
            except Exception as e:
                print(f"[오류] 설정을 불러올 수 없습니다: {e}")
        else:
            # 기본 설정 템플릿 생성
            default_config = {
                "firebase_url": "YOUR_FIREBASE_DB_URL"
            }
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump(default_config, f, indent=4)
                print(f"[알림] {CONFIG_FILE} 템플릿 파일이 생성되었습니다. Firebase DB URL을 수정해주세요.")
            except Exception as e:
                print(f"[오류] 기본 설정 파일 생성 실패: {e}")

    def register_to_startup(self):
        """Windows 레지스트리에 프로그램을 시작 프로그램으로 등록합니다."""
        if winreg is None:
            return

        try:
            if getattr(sys, 'frozen', False):
                executable_path = sys.executable
            else:
                executable_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "StudyRadarAgent", 0, winreg.REG_SZ, executable_path)
            winreg.CloseKey(key)
            print("[설정] Windows 시작 프로그램(레지스트리)에 성공적으로 등록되었습니다.")
        except Exception as e:
            print(f"[오류] 시작 프로그램 등록 실패: {e}")

    def start_watchdog(self):
        """본 프로세스(Main)를 감시할 이중 감시(Watchdog) 프로세스를 백그라운드에 띄웁니다."""
        try:
            own_pid = os.getpid()
            if getattr(sys, 'frozen', False):
                args = [sys.executable, "--watchdog", str(own_pid)]
            else:
                args = [sys.executable, os.path.abspath(sys.argv[0]), "--watchdog", str(own_pid)]
            
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW # 창 숨김 플래그
                
            self.watchdog_sub = subprocess.Popen(
                args,
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[보안] 이중 감시(Watchdog) 프로세스를 기동했습니다. (감시 대상 PID: {own_pid})")
        except Exception as e:
            print(f"[오류] Watchdog 프로세스 생성 실패: {e}")

    def lock_workstation(self):
        """Windows API를 호출하여 컴퓨터 화면을 잠금 상태로 강제 전환합니다."""
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔒 [경고] 공부 목표 미달성으로 인해 화면을 잠급니다!")
            ctypes.windll.user32.LockWorkStation()
        except Exception as e:
            print(f"[오류] 화면 잠금 실패: {e}")

    def run(self):
        if not self.firebase_url or "YOUR_FIREBASE_DB_URL" in self.firebase_url:
            print("[오류] Firebase URL이 세팅되지 않았습니다. config.json 파일을 열고 URL을 올바르게 수정해 주세요.")
            time.sleep(5)
            return

        print("\n[알림] 공부 차단 감시 데몬이 실행되었습니다.")
        print("[감시 중] 맥북에서 공부 목표를 달성할 때까지 이 윈도우 PC는 사용하실 수 없습니다.\n")

        # 혹시 모를 오프라인 상태 연속 감지 카운트 (인터넷선 뽑기 방지용)
        offline_count = 0

        while self.running:
            # Watchdog 생존 여부 실시간 확인 (죽어있으면 다시 기동)
            if sys.platform == "win32" and hasattr(self, 'watchdog_sub') and self.watchdog_sub.poll() is not None:
                print("🚨 [보안 경고] Watchdog 프로세스가 의도치 않게 종료되었습니다. 즉시 재실행합니다!")
                self.start_watchdog()

            today_str = datetime.date.today().isoformat()
            base_url = self.firebase_url.rstrip('/')
            url = f"{base_url}/study_status.json"

            try:
                # 1. Firebase에서 현재 공부 정보 가져오기
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    offline_count = 0
                    data = response.json()
                    
                    if data is None:
                        # 데이터가 빈 경우 (아직 한번도 맥북에서 타이머를 켜지 않았음)
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ 클라우드 데이터가 비어 있습니다. (맥북에서 타이머를 실행해 주세요.)")
                        # 안전을 위해 최초 실행 및 동기화 전에는 잠그지 않되 경고만 하거나,
                        # 강력하게 막고 싶으면 아래 주석을 해제하여 첫 기록 전에도 잠금을 걸 수 있습니다.
                        self.lock_workstation()
                    else:
                        date = data.get("date", "")
                        today_study_seconds = data.get("today_study_seconds", 0)
                        target_study_seconds = data.get("target_study_seconds", 0)
                        
                        # 2. 오늘 공부 완료 상태 판정
                        if date == today_str:
                            remaining = target_study_seconds - today_study_seconds
                            if remaining > 0:
                                # 오늘 날짜이고, 아직 공부 잔여 시간이 남은 상태 -> 강제 잠금
                                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚨 공부 진행 중 ({today_study_seconds // 60}분 / {target_study_seconds // 60}분). {remaining // 60}분 더 필요합니다.")
                                self.lock_workstation()
                            else:
                                # 오늘 공부 목표 완료! 정상 사용 허가
                                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🎉 [완료] 오늘 공부 목표 달성이 확인되었습니다! 즐겜하세요!")
                        else:
                            # Firebase에 기록된 날짜가 오늘이 아님 -> 즉 오늘은 아직 아침이라 맥북 타이머를 한 번도 안 켰거나, 어제 공부 완료 후 리셋 안 됨.
                            # 하루가 바뀌었으므로 당연히 0분 공부한 상태로 판정되어 잠가야 합니다.
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🚨 새 날이 밝았습니다. 오늘 공부를 한 번도 시작하지 않았습니다.")
                            self.lock_workstation()
                else:
                    print(f"[에러] 서버 응답 코드 오류 ({response.status_code}). 통신 오류 발생.")
                    offline_count += 1

            except Exception as e:
                # 3. 우회 차단 (인터넷 연결 해제 꼼수 차단)
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 네트워크 통신 불가 ({e})")
                offline_count += 1

            # 만약 3회(6초) 이상 계속 네트워크 연결이 실패한다면,
            # 인터넷 연결을 강제로 끊어 우회하려 한다고 간주하고 잠가 버립니다. (인터넷 끊기 꼼수 원천 차단!)
            if offline_count >= 3:
                print("🚨 [인터넷 우회 감지] 네트워크 차단 상태가 장기화되었습니다. 보안 조치로 화면을 잠급니다!")
                self.lock_workstation()

            time.sleep(self.check_interval)

def run_watchdog_loop(parent_pid):
    """지정된 부모 PID(Main 프로세스)의 생존을 감시하다가, 부모가 죽으면 메인 프로세스를 즉각 재실행합니다."""
    print(f"[Watchdog] 감시 루프 기동 완료. (감시 대상 PID: {parent_pid})")
    
    while True:
        process_exists = False
        if sys.platform == "win32" and ctypes is not None:
            try:
                PROCESS_QUERY_INFORMATION = 0x0400
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, parent_pid)
                if handle:
                    exit_code = ctypes.c_ulong()
                    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                    STILL_ACTIVE = 259
                    if exit_code.value == STILL_ACTIVE:
                        process_exists = True
                    ctypes.windll.kernel32.CloseHandle(handle)
            except Exception:
                process_exists = False
        else:
            try:
                os.kill(parent_pid, 0)
                process_exists = True
            except OSError:
                process_exists = False

        if not process_exists:
            print(f"[Watchdog Warning] 메인 프로세스(PID: {parent_pid})가 종료된 것을 감지했습니다! 즉시 메인 프로세스를 부활시킵니다.")
            try:
                if getattr(sys, 'frozen', False):
                    args = [sys.executable]
                else:
                    args = [sys.executable, os.path.abspath(sys.argv[0])]
                
                creation_flags = 0
                if sys.platform == "win32":
                    creation_flags = 0x00000010 # CREATE_NEW_CONSOLE
                    
                subprocess.Popen(args, creationflags=creation_flags)
                print("[Watchdog Success] 메인 프로세스 부활 완료. 감시를 종료합니다.")
            except Exception as e:
                print(f"[Watchdog Error] 메인 프로세스 부활 실패: {e}")
            break
            
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--watchdog":
        parent_pid = int(sys.argv[2])
        run_watchdog_loop(parent_pid)
    else:
        agent = WindowsStudyAgent()
        try:
            agent.run()
        except KeyboardInterrupt:
            print("\n[알림] 제어 감시가 수동으로 중단되었습니다.")
