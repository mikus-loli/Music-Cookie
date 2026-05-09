import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel
from config import settings


class CookieRecord(BaseModel):
    platform: str = "qqmusic"
    cookies: Dict[str, str]
    source_host: str
    captured_at: str
    updated_at: str


class CookieStore:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._data_lock = threading.Lock()
        self._ensure_data_dir()
        self._cookies: Dict[str, CookieRecord] = {}
        self._load_from_file()
    
    def _ensure_data_dir(self) -> None:
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_from_file(self) -> None:
        if settings.COOKIE_FILE.exists():
            try:
                with open(settings.COOKIE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if 'platform' not in value:
                            value['platform'] = 'qqmusic'
                        self._cookies[key] = CookieRecord(**value)
                print(f"[Store] Loaded {len(self._cookies)} cookie records")
            except Exception as e:
                print(f"[Store] Error loading cookies: {e}")
                self._cookies = {}
    
    def _save_to_file(self) -> None:
        try:
            data = {
                key: value.model_dump() 
                for key, value in self._cookies.items()
            }
            with open(settings.COOKIE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Store] Error saving cookies: {e}")
    
    def save_cookies(self, source_host: str, cookies: Dict[str, str], platform: str = "qqmusic") -> None:
        with self._data_lock:
            now = datetime.now().isoformat()
            key = f"{platform}_{source_host}"
            
            if key in self._cookies:
                record = self._cookies[key]
                record.cookies.update(cookies)
                record.updated_at = now
            else:
                record = CookieRecord(
                    platform=platform,
                    cookies=cookies,
                    source_host=source_host,
                    captured_at=now,
                    updated_at=now
                )
                self._cookies[key] = record
            
            self._save_to_file()
            print(f"[Store] Saved {len(cookies)} {platform} cookies from {source_host}")
    
    def get_cookies(self, source_host: Optional[str] = None) -> Dict[str, Any]:
        with self._data_lock:
            if source_host:
                if source_host in self._cookies:
                    return self._cookies[source_host].model_dump()
                return {}
            return {
                key: value.model_dump() 
                for key, value in self._cookies.items()
            }
    
    def get_cookies_by_platform(self, platform: str) -> Dict[str, CookieRecord]:
        with self._data_lock:
            return {
                key: record for key, record in self._cookies.items()
                if record.platform == platform
            }
    
    def get_all_cookies_flat(self, platform: str = None) -> Dict[str, str]:
        with self._data_lock:
            all_cookies = {}
            for record in self._cookies.values():
                if platform is None or record.platform == platform:
                    all_cookies.update(record.cookies)
            return all_cookies
    
    def get_cookie_string(self, source_host: Optional[str] = None, platform: str = None) -> str:
        if source_host:
            cookies = self.get_cookies(source_host).get('cookies', {})
        else:
            cookies = self.get_all_cookies_flat(platform)
        return '; '.join(f"{k}={v}" for k, v in cookies.items())
    
    def delete_cookies(self, source_host: str) -> bool:
        with self._data_lock:
            if source_host in self._cookies:
                del self._cookies[source_host]
                self._save_to_file()
                return True
            return False
    
    def clear_all(self) -> None:
        with self._data_lock:
            self._cookies.clear()
            self._save_to_file()
    
    def reload(self) -> None:
        with self._data_lock:
            self._cookies.clear()
            self._load_from_file()
    
    def update_cookies(self, source_host: str, cookies: Dict[str, str]) -> bool:
        with self._data_lock:
            if source_host in self._cookies:
                record = self._cookies[source_host]
                record.cookies.update(cookies)
                record.updated_at = datetime.now().isoformat()
                self._save_to_file()
                return True
            return False
    
    def has_valid_qqmusic_cookies(self) -> bool:
        cookies = self.get_all_cookies_flat(platform="qqmusic")
        return bool(cookies.get('qqmusic_uin') or cookies.get('uin')) and bool(cookies.get('qqmusic_key'))
    
    def has_valid_netease_cookies(self) -> bool:
        cookies = self.get_all_cookies_flat(platform="netease")
        return bool(cookies.get('MUSIC_U'))


cookie_store = CookieStore()
