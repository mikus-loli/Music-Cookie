import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path
from mitmproxy import http, ctx
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster

sys.path.insert(0, str(Path(__file__).parent))
from config import settings


class QQMusicAddon:
    QQ_MUSIC_COOKIE_KEYS = [
        'qqmusic_uin',
        'qqmusic_key',
        'qqmusic_guid',
        'qqmusic_gkey',
        'qm_keyst',
        'psrf_qqrefresh_token',
        'psrf_qqaccess_token',
        'psrf_qqopenid',
        'uin',
        'skey',
        'p_skey',
    ]
    
    def __init__(self, on_cookie_captured: Optional[Callable] = None):
        self.on_cookie_captured = on_cookie_captured
        self.captured_cookies = {}
        self.platform = "qqmusic"
    
    def is_target_request(self, host: str) -> bool:
        return any(domain in host for domain in settings.QQ_MUSIC_DOMAINS)
    
    def has_target_cookies(self, cookie_header: str) -> bool:
        if not cookie_header:
            return False
        cookie_lower = cookie_header.lower()
        return any(key.lower() in cookie_lower for key in self.QQ_MUSIC_COOKIE_KEYS)
    
    def extract_cookies(self, cookie_header: str) -> dict:
        cookies = {}
        if cookie_header:
            for item in cookie_header.split(';'):
                item = item.strip()
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookies[name.strip()] = value.strip()
        return cookies
    
    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.host
        cookie_header = flow.request.headers.get("Cookie", "")
        
        is_target_domain = self.is_target_request(host)
        has_target_cookies = self.has_target_cookies(cookie_header)
        
        if cookie_header and (is_target_domain or has_target_cookies):
            cookies = self.extract_cookies(cookie_header)
            
            target_cookies = {
                k: v for k, v in cookies.items()
                if any(key.lower() in k.lower() for key in self.QQ_MUSIC_COOKIE_KEYS)
            }
            
            if target_cookies:
                self.captured_cookies.update(target_cookies)
                
                capture_info = {
                    "platform": self.platform,
                    "host": host,
                    "url": flow.request.url,
                    "cookies": target_cookies,
                    "timestamp": datetime.now().isoformat()
                }
                
                ctx.log.info(f"[QQ Music] Captured {len(target_cookies)} cookies from {host}")
                
                if self.on_cookie_captured:
                    try:
                        self.on_cookie_captured(capture_info)
                    except Exception as e:
                        ctx.log.error(f"Callback error: {e}")


class NeteaseMusicAddon:
    NETEASE_COOKIE_KEYS = [
        'MUSIC_U',
        'MUSIC_A',
        '__csrf',
        '__remember_me',
        'NMTID',
        '_ntes_nnid',
        '_ntes_nuid',
        'WM_TID',
        'WM_NI',
        'WM_NIKE',
    ]
    
    def __init__(self, on_cookie_captured: Optional[Callable] = None):
        self.on_cookie_captured = on_cookie_captured
        self.captured_cookies = {}
        self.platform = "netease"
    
    def is_target_request(self, host: str) -> bool:
        return any(domain in host for domain in settings.NETEASE_MUSIC_DOMAINS)
    
    def has_target_cookies(self, cookie_header: str) -> bool:
        if not cookie_header:
            return False
        cookie_lower = cookie_header.lower()
        return any(key.lower() in cookie_lower for key in self.NETEASE_COOKIE_KEYS)
    
    def extract_cookies(self, cookie_header: str) -> dict:
        cookies = {}
        if cookie_header:
            for item in cookie_header.split(';'):
                item = item.strip()
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookies[name.strip()] = value.strip()
        return cookies
    
    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.host
        cookie_header = flow.request.headers.get("Cookie", "")
        
        is_target_domain = self.is_target_request(host)
        has_target_cookies = self.has_target_cookies(cookie_header)
        
        if cookie_header and (is_target_domain or has_target_cookies):
            cookies = self.extract_cookies(cookie_header)
            
            target_cookies = {
                k: v for k, v in cookies.items()
                if any(key.lower() in k.lower() for key in self.NETEASE_COOKIE_KEYS)
            }
            
            if target_cookies:
                self.captured_cookies.update(target_cookies)
                
                capture_info = {
                    "platform": self.platform,
                    "host": host,
                    "url": flow.request.url,
                    "cookies": target_cookies,
                    "timestamp": datetime.now().isoformat()
                }
                
                ctx.log.info(f"[Netease Music] Captured {len(target_cookies)} cookies from {host}")
                
                if self.on_cookie_captured:
                    try:
                        self.on_cookie_captured(capture_info)
                    except Exception as e:
                        ctx.log.error(f"Callback error: {e}")


class ProxyManager:
    def __init__(self, on_cookie_captured: Optional[Callable] = None, platform: str = "all"):
        self.qqmusic_addon = QQMusicAddon(on_cookie_captured)
        self.netease_addon = NeteaseMusicAddon(on_cookie_captured)
        self.proxy_process = None
        self._master = None
        self.platform = platform
    
    def get_captured_cookies(self, platform: str = None) -> dict:
        if platform == "qqmusic":
            return self.qqmusic_addon.captured_cookies.copy()
        elif platform == "netease":
            return self.netease_addon.captured_cookies.copy()
        return {
            "qqmusic": self.qqmusic_addon.captured_cookies.copy(),
            "netease": self.netease_addon.captured_cookies.copy()
        }
    
    def clear_captured_cookies(self) -> None:
        self.qqmusic_addon.captured_cookies.clear()
        self.netease_addon.captured_cookies.clear()
    
    async def start_proxy(self) -> None:
        opts = Options(
            listen_host=settings.PROXY_HOST,
            listen_port=settings.PROXY_PORT,
            ssl_insecure=True,
        )
        
        self._master = DumpMaster(opts)
        
        if self.platform in ["all", "qqmusic"]:
            self._master.addons.add(self.qqmusic_addon)
        if self.platform in ["all", "netease"]:
            self._master.addons.add(self.netease_addon)
        
        print(f"[Proxy] Starting MITM proxy on {settings.PROXY_HOST}:{settings.PROXY_PORT}")
        print(f"[Proxy] SSL insecure mode enabled")
        print(f"[Proxy] Platform: {self.platform}")
        print(f"[Proxy] Capturing QQ Music and Netease Music cookies")
        
        try:
            await self._master.run()
        except KeyboardInterrupt:
            print("[Proxy] Shutting down...")
            await self.shutdown()
    
    async def shutdown(self) -> None:
        if self._master:
            try:
                await self._master.done()
            except Exception as e:
                print(f"[Proxy] Error during shutdown: {e}")
            self._master = None
    
    def run_proxy_sync(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.start_proxy())
        except KeyboardInterrupt:
            pass
        finally:
            try:
                loop.run_until_complete(self.shutdown())
            except:
                pass
            loop.close()


def run_standalone():
    print("[Proxy] Running in standalone mode...")
    print(f"[Proxy] Listening on {settings.PROXY_HOST}:{settings.PROXY_PORT}")
    
    def save_cookies_to_file(capture_info: dict):
        cookie_file = settings.COOKIE_FILE
        cookie_file.parent.mkdir(parents=True, exist_ok=True)
        
        existing = {}
        if cookie_file.exists():
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except:
                existing = {}
        
        platform = capture_info.get('platform', 'unknown')
        host = capture_info.get('host', 'unknown')
        cookies = capture_info.get('cookies', {})
        
        platform_key = f"{platform}_{host}"
        
        if platform_key not in existing:
            existing[platform_key] = {
                'platform': platform,
                'cookies': {},
                'source_host': host,
                'captured_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        existing[platform_key]['cookies'].update(cookies)
        existing[platform_key]['updated_at'] = datetime.now().isoformat()
        
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        print(f"[Store] Saved {len(cookies)} {platform} cookies from {host}")
    
    manager = ProxyManager(on_cookie_captured=save_cookies_to_file, platform="all")
    manager.run_proxy_sync()


if __name__ == "__main__":
    run_standalone()
