import os
import sys
import time
import subprocess
import asyncio
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from cookie_store import cookie_store
from scheduler import scheduler_manager


class MusicAppController:
    QQ_MUSIC_PATHS = [
        r"C:\Program Files (x86)\Tencent\QQMusic\QQMusic.exe",
        r"C:\Program Files\Tencent\QQMusic\QQMusic.exe",
        r"D:\Program Files (x86)\Tencent\QQMusic\QQMusic.exe",
        r"D:\Program Files\Tencent\QQMusic\QQMusic.exe",
    ]
    
    NETEASE_MUSIC_PATHS = [
        r"C:\Program Files (x86)\Netease\CloudMusic\cloudmusic.exe",
        r"C:\Program Files\Netease\CloudMusic\cloudmusic.exe",
        r"D:\Program Files (x86)\Netease\CloudMusic\cloudmusic.exe",
        r"D:\Program Files\Netease\CloudMusic\cloudmusic.exe",
    ]
    
    PROCESS_NAMES = {
        "qqmusic": "QQMusic.exe",
        "netease": "cloudmusic.exe"
    }
    
    def __init__(self, platform: str = "qqmusic"):
        self.platform = platform
        self.process: Optional[subprocess.Popen] = None
        self.executable_path: Optional[str] = None
        self._find_executable()
    
    def _get_paths(self) -> list:
        if self.platform == "netease":
            return self.NETEASE_MUSIC_PATHS
        return self.QQ_MUSIC_PATHS
    
    def _get_config_path(self) -> Optional[str]:
        if self.platform == "netease":
            return settings.NETEASEMUSIC_PATH
        return settings.QQMUSIC_PATH
    
    def _get_env_key(self) -> str:
        if self.platform == "netease":
            return "NETEASEMUSIC_PATH"
        return "QQMUSIC_PATH"
    
    def _find_executable(self) -> bool:
        config_path = self._get_config_path()
        if config_path and os.path.exists(config_path):
            self.executable_path = config_path
            print(f"[{self.platform}] Found at: {config_path}")
            return True
        
        for path in self._get_paths():
            if os.path.exists(path):
                self.executable_path = path
                print(f"[{self.platform}] Found at: {path}")
                return True
        
        print(f"[{self.platform}] Executable not found in default paths")
        print(f"[{self.platform}] Please set {self._get_env_key()} in .env file")
        return False
    
    def start(self) -> bool:
        if not self.executable_path:
            env_path = os.environ.get(self._get_env_key())
            if env_path and os.path.exists(env_path):
                self.executable_path = env_path
            else:
                print(f"[{self.platform}] No valid executable path found")
                return False
        
        try:
            self.process = subprocess.Popen(
                [self.executable_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[{self.platform}] Started (PID: {self.process.pid})")
            return True
        except Exception as e:
            print(f"[{self.platform}] Failed to start: {e}")
            return False
    
    def stop(self) -> bool:
        process_name = self.PROCESS_NAMES.get(self.platform, "unknown.exe")
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                print(f"[{self.platform}] Terminated gracefully")
                return True
            except subprocess.TimeoutExpired:
                self.process.kill()
                print(f"[{self.platform}] Killed forcefully")
                return True
            except Exception as e:
                print(f"[{self.platform}] Failed to stop: {e}")
                return False
        else:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", process_name],
                    capture_output=True,
                    timeout=10
                )
                print(f"[{self.platform}] Killed via taskkill")
                return True
            except Exception as e:
                print(f"[{self.platform}] Failed to kill via taskkill: {e}")
                return False
    
    def is_running(self) -> bool:
        process_name = self.PROCESS_NAMES.get(self.platform, "unknown.exe")
        
        if self.process and self.process.poll() is None:
            return True
        
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return process_name in result.stdout
        except:
            return False


class AutomationManager:
    def __init__(self):
        self.qqmusic = MusicAppController("qqmusic")
        self.netease = MusicAppController("netease")
        self.proxy_process: Optional[subprocess.Popen] = None
        self.running = False
        self.cycle_count = 0
        self.script_dir = Path(__file__).parent.absolute()
    
    def get_python_executable(self) -> str:
        venv_paths = [
            self.script_dir / "venv" / "Scripts" / "python.exe",
            self.script_dir / ".venv" / "Scripts" / "python.exe",
        ]
        
        for venv_python in venv_paths:
            if venv_python.exists():
                return str(venv_python)
        
        return sys.executable
    
    def start_proxy(self) -> bool:
        print("[Proxy] Starting MITM proxy as subprocess...")
        try:
            python_exe = self.get_python_executable()
            proxy_script = self.script_dir / "proxy_capture.py"
            log_file = self.script_dir / "logs" / "proxy.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            log_handle = open(log_file, 'a', encoding='utf-8')
            log_handle.write(f"\n{'='*50}\n")
            log_handle.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting proxy\n")
            log_handle.flush()
            
            self.proxy_process = subprocess.Popen(
                [python_exe, str(proxy_script)],
                stdout=log_handle,
                stderr=log_handle,
                cwd=str(self.script_dir)
            )
            
            time.sleep(5)
            
            if self.proxy_process.poll() is not None:
                print(f"[Proxy] Proxy process exited unexpectedly with code: {self.proxy_process.returncode}")
                return False
            
            print(f"[Proxy] Proxy started on {settings.PROXY_HOST}:{settings.PROXY_PORT}")
            print(f"[Proxy] Proxy PID: {self.proxy_process.pid}")
            print(f"[Proxy] Log file: {log_file}")
            return True
        except Exception as e:
            print(f"[Proxy] Error starting proxy: {e}")
            return False
    
    def stop_proxy(self) -> bool:
        if self.proxy_process:
            try:
                print("[Proxy] Stopping proxy process...")
                self.proxy_process.terminate()
                try:
                    self.proxy_process.wait(timeout=10)
                    print("[Proxy] Proxy terminated gracefully")
                except subprocess.TimeoutExpired:
                    self.proxy_process.kill()
                    print("[Proxy] Proxy killed forcefully")
            except Exception as e:
                print(f"[Proxy] Error stopping proxy: {e}")
            finally:
                self.proxy_process = None
        return True
    
    def clear_cookies(self) -> bool:
        try:
            cookie_file = settings.COOKIE_FILE
            if cookie_file.exists():
                cookie_file.unlink()
                print(f"[Cleanup] Deleted {cookie_file}")
            
            cookie_store.clear_all()
            print("[Cleanup] Cookie store cleared")
            return True
        except Exception as e:
            print(f"[Cleanup] Error clearing cookies: {e}")
            return False
    
    async def send_cookies(self, platform: str = "all") -> dict:
        print(f"[Send] Sending {platform} cookies to Meting-API...")
        result = await scheduler_manager.send_cookies_to_target(platform)
        
        if result.get('success'):
            print(f"[Send] Successfully sent cookies")
            for p, presult in result.get('platforms', {}).items():
                if presult.get('success'):
                    print(f"[Send] {p}: OK")
                else:
                    print(f"[Send] {p}: {presult.get('error', 'Unknown error')}")
        else:
            print(f"[Send] Failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def wait_for_cookies(self, platform: str = "all", timeout: int = 300) -> bool:
        print(f"[Wait] Waiting for {platform} cookies (timeout: {timeout}s)...")
        
        start_time = time.time()
        last_cookie_count = 0
        
        while time.time() - start_time < timeout:
            cookie_store.reload()
            
            qqmusic_valid = cookie_store.has_valid_qqmusic_cookies()
            netease_valid = cookie_store.has_valid_netease_cookies()
            
            if platform == "all":
                if qqmusic_valid or netease_valid:
                    print(f"[Wait] Valid cookies found!")
                    if qqmusic_valid:
                        cookies = cookie_store.get_all_cookies_flat("qqmusic")
                        print(f"[Wait] QQ Music UIN: {cookies.get('qqmusic_uin') or cookies.get('uin')}")
                    if netease_valid:
                        cookies = cookie_store.get_all_cookies_flat("netease")
                        print(f"[Wait] Netease MUSIC_U: {cookies.get('MUSIC_U', '')[:20]}...")
                    return True
            elif platform == "qqmusic":
                if qqmusic_valid:
                    cookies = cookie_store.get_all_cookies_flat("qqmusic")
                    print(f"[Wait] QQ Music cookies found!")
                    print(f"[Wait] UIN: {cookies.get('qqmusic_uin') or cookies.get('uin')}")
                    return True
            elif platform == "netease":
                if netease_valid:
                    cookies = cookie_store.get_all_cookies_flat("netease")
                    print(f"[Wait] Netease cookies found!")
                    print(f"[Wait] MUSIC_U: {cookies.get('MUSIC_U', '')[:20]}...")
                    return True
            
            all_cookies = cookie_store.get_all_cookies_flat()
            cookie_count = len(all_cookies)
            
            if cookie_count != last_cookie_count:
                print(f"[Wait] Captured {cookie_count} cookies...")
                last_cookie_count = cookie_count
            
            time.sleep(5)
        
        print("[Wait] Timeout - no valid cookies found")
        return False
    
    async def run_cycle(self, platform: str = "all") -> dict:
        print("\n" + "=" * 60)
        print(f"[Cycle] Starting cycle #{self.cycle_count + 1}")
        print(f"[Cycle] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[Cycle] Platform: {platform}")
        print("=" * 60)
        
        result = {
            "cycle": self.cycle_count + 1,
            "success": False,
            "error": None,
            "platform": platform
        }
        
        try:
            print("\n[Step 1/7] Starting proxy...")
            if not self.start_proxy():
                result["error"] = "Failed to start proxy"
                return result
            
            print("\n[Step 2/7] Waiting for proxy to stabilize (60s)...")
            for i in range(60, 0, -1):
                print(f"\r[Wait] {i} seconds remaining...", end="", flush=True)
                time.sleep(1)
            print("\r[Wait] Proxy ready!                    ")
            
            apps_started = []
            
            if platform in ["all", "qqmusic"]:
                print("\n[Step 3/7] Starting QQ Music...")
                if self.qqmusic.start():
                    apps_started.append("qqmusic")
                else:
                    print("[QQMusic] Failed to start, continuing...")
            
            if platform in ["all", "netease"]:
                print("\n[Step 4/7] Starting Netease Music...")
                if self.netease.start():
                    apps_started.append("netease")
                else:
                    print("[Netease] Failed to start, continuing...")
            
            if not apps_started:
                result["error"] = "No music apps started"
                self.stop_proxy()
                return result
            
            print("\n[Step 5/7] Waiting for cookies...")
            time.sleep(10)
            
            if not self.wait_for_cookies(platform=platform, timeout=300):
                result["error"] = "No valid cookies captured"
            else:
                print("\n[Step 6/7] Sending cookies...")
                send_result = await self.send_cookies(platform)
                result["success"] = send_result.get('success', False)
                result["send_result"] = send_result
            
            print("\n[Step 7/7] Stopping apps and cleaning up...")
            self.qqmusic.stop()
            self.netease.stop()
            self.stop_proxy()
            self.clear_cookies()
            
            self.cycle_count += 1
            result["cycle"] = self.cycle_count
            
        except Exception as e:
            result["error"] = str(e)
            print(f"[Error] {e}")
            self.qqmusic.stop()
            self.netease.stop()
            self.stop_proxy()
        
        print("\n" + "-" * 60)
        print(f"[Cycle] Cycle #{self.cycle_count} completed")
        print(f"[Cycle] Success: {result['success']}")
        if result.get('error'):
            print(f"[Cycle] Error: {result['error']}")
        print("-" * 60)
        
        return result
    
    async def run_forever(self, interval_hours: int = 24, platform: str = "all"):
        print("\n" + "=" * 60)
        print("Music Cookie Manager - Automation Mode")
        print("=" * 60)
        print(f"Interval: Every {interval_hours} hours")
        print(f"Platform: {platform}")
        print(f"Proxy: {settings.PROXY_HOST}:{settings.PROXY_PORT}")
        print(f"Target API: {settings.TARGET_API_URL or 'Not configured'}")
        print("=" * 60 + "\n")
        
        if not settings.TARGET_API_URL or not settings.TARGET_API_TOKEN:
            print("[Error] TARGET_API_URL and TARGET_API_TOKEN must be configured!")
            return
        
        self.running = True
        
        while self.running:
            await self.run_cycle(platform)
            
            if self.running:
                next_run = datetime.now() + timedelta(hours=interval_hours)
                print(f"\n[Sleep] Next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"[Sleep] Waiting {interval_hours} hours...\n")
                
                for _ in range(interval_hours * 3600):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
    
    def stop(self):
        print("\n[Stop] Stopping automation...")
        self.running = False
        self.qqmusic.stop()
        self.netease.stop()
        self.stop_proxy()


automation_manager = AutomationManager()


def signal_handler(sig, frame):
    print("\n[Signal] Received interrupt signal")
    automation_manager.stop()
    sys.exit(0)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Music Cookie Automation")
    parser.add_argument("--interval", type=int, default=24, help="Interval in hours (default: 24)")
    parser.add_argument("--once", action="store_true", help="Run only once")
    parser.add_argument("--platform", type=str, default="all", choices=["all", "qqmusic", "netease"],
                        help="Platform to capture cookies from (default: all)")
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.once:
        await automation_manager.run_cycle(platform=args.platform)
    else:
        await automation_manager.run_forever(interval_hours=args.interval, platform=args.platform)


if __name__ == "__main__":
    asyncio.run(main())
