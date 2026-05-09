import asyncio
import httpx
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED, JobEvent
from cookie_store import cookie_store
from config import settings


class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.last_execution: Optional[datetime] = None
        self.execution_count: int = 0
        self.error_count: int = 0
        self._setup_listeners()
    
    def _setup_listeners(self):
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)
    
    def _on_job_error(self, event: JobEvent):
        self.error_count += 1
        print(f"[Scheduler] Job error: {event.exception}")
    
    def _on_job_missed(self, event: JobEvent):
        print(f"[Scheduler] Job missed at {event.scheduled_run_time}")
    
    def extract_qqmusic_cookie(self) -> dict:
        all_cookies = cookie_store.get_all_cookies_flat(platform="qqmusic")
        
        uin = all_cookies.get('qqmusic_uin') or all_cookies.get('uin', '')
        qqmusic_key = all_cookies.get('qqmusic_key', '')
        refresh_token = all_cookies.get('psrf_qqrefresh_token', '')
        access_token = all_cookies.get('psrf_qqaccess_token', '')
        openid = all_cookies.get('psrf_qqopenid', '')
        qm_keyst = all_cookies.get('qm_keyst', '')
        guid = all_cookies.get('qqmusic_guid', '')
        
        if not uin or not qqmusic_key:
            return None
        
        cookie_parts = [f"uin={uin}", f"qqmusic_key={qqmusic_key}"]
        
        if qm_keyst:
            cookie_parts.append(f"qm_keyst={qm_keyst}")
        if refresh_token:
            cookie_parts.append(f"psrf_qqrefresh_token={refresh_token}")
        if access_token:
            cookie_parts.append(f"psrf_qqaccess_token={access_token}")
        if openid:
            cookie_parts.append(f"psrf_qqopenid={openid}")
        if guid:
            cookie_parts.append(f"qqmusic_guid={guid}")
        
        cookie_string = '; '.join(cookie_parts)
        
        return {
            'platform': 'tencent',
            'uin': uin,
            'qqmusic_key': qqmusic_key,
            'cookie_string': cookie_string,
            'refresh_token': refresh_token,
            'has_refresh_token': bool(refresh_token)
        }
    
    def extract_netease_cookie(self) -> dict:
        all_cookies = cookie_store.get_all_cookies_flat(platform="netease")
        
        music_u = all_cookies.get('MUSIC_U', '')
        music_a = all_cookies.get('MUSIC_A', '')
        csrf = all_cookies.get('__csrf', '')
        remember_me = all_cookies.get('__remember_me', '')
        
        if not music_u:
            return None
        
        cookie_parts = [f"MUSIC_U={music_u}"]
        
        if music_a:
            cookie_parts.append(f"MUSIC_A={music_a}")
        if csrf:
            cookie_parts.append(f"__csrf={csrf}")
        if remember_me:
            cookie_parts.append(f"__remember_me={remember_me}")
        
        cookie_string = '; '.join(cookie_parts)
        
        return {
            'platform': 'netease',
            'music_u': music_u,
            'music_a': music_a,
            'csrf': csrf,
            'cookie_string': cookie_string
        }
    
    async def send_cookies_to_target(self, platform: str = "all") -> dict:
        if not settings.TARGET_API_URL:
            print("[Scheduler] No target API URL configured, skipping send")
            return {"success": False, "error": "No target API URL configured"}
        
        if not settings.TARGET_API_TOKEN:
            print("[Scheduler] No target API token configured, skipping send")
            return {"success": False, "error": "No target API token configured"}
        
        results = {"success": True, "platforms": {}}
        
        if platform in ["all", "qqmusic"]:
            qqmusic_result = await self._send_qqmusic_cookie()
            results["platforms"]["qqmusic"] = qqmusic_result
            if not qqmusic_result.get("success"):
                results["success"] = False
        
        if platform in ["all", "netease"]:
            netease_result = await self._send_netease_cookie()
            results["platforms"]["netease"] = netease_result
            if not netease_result.get("success"):
                results["success"] = False
        
        return results
    
    async def _send_qqmusic_cookie(self) -> dict:
        meting_cookie = self.extract_qqmusic_cookie()
        
        if not meting_cookie:
            print("[Scheduler] No valid QQ Music cookies found (missing uin or qqmusic_key)")
            return {"success": False, "error": "No valid QQ Music cookies"}
        
        payload = {
            "platform": "tencent",
            "cookie": meting_cookie['cookie_string'],
            "note": f"Auto-synced from Music-Cookie-Manager",
            "isActive": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.TARGET_API_TOKEN}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.TARGET_API_URL,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                
                self.last_execution = datetime.now()
                self.execution_count += 1
                
                print(f"[Scheduler] Successfully sent QQ Music cookie to {settings.TARGET_API_URL}")
                print(f"[Scheduler] UIN: {meting_cookie['uin']}, Has refresh token: {meting_cookie['has_refresh_token']}")
                
                if result.get('success') and result.get('data'):
                    data = result['data']
                    print(f"[Scheduler] Cookie ID: {data.get('id', 'N/A')}")
                    if data.get('userInfo'):
                        user_info = data['userInfo']
                        print(f"[Scheduler] User: {user_info.get('nickname', 'N/A')}, VIP: {user_info.get('isVip', False)}")
                
                return {
                    "success": True,
                    "platform": "qqmusic",
                    "uin": meting_cookie['uin'],
                    "has_refresh_token": meting_cookie['has_refresh_token'],
                    "response_status": response.status_code,
                    "data": result.get('data')
                }
                
        except httpx.HTTPStatusError as e:
            self.error_count += 1
            error_detail = e.response.text
            try:
                error_json = e.response.json()
                error_detail = error_json.get('message', error_detail)
            except:
                pass
            print(f"[Scheduler] QQ Music HTTP error: {e.response.status_code} - {error_detail}")
            return {"success": False, "platform": "qqmusic", "error": f"HTTP {e.response.status_code}: {error_detail}"}
            
        except httpx.RequestError as e:
            self.error_count += 1
            print(f"[Scheduler] QQ Music Request error: {str(e)}")
            return {"success": False, "platform": "qqmusic", "error": str(e)}
            
        except Exception as e:
            self.error_count += 1
            print(f"[Scheduler] QQ Music Unexpected error: {str(e)}")
            return {"success": False, "platform": "qqmusic", "error": str(e)}
    
    async def _send_netease_cookie(self) -> dict:
        netease_cookie = self.extract_netease_cookie()
        
        if not netease_cookie:
            print("[Scheduler] No valid Netease Music cookies found (missing MUSIC_U)")
            return {"success": False, "error": "No valid Netease Music cookies"}
        
        payload = {
            "platform": "netease",
            "cookie": netease_cookie['cookie_string'],
            "note": f"Auto-synced from Music-Cookie-Manager",
            "isActive": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.TARGET_API_TOKEN}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.TARGET_API_URL,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                
                self.last_execution = datetime.now()
                self.execution_count += 1
                
                print(f"[Scheduler] Successfully sent Netease Music cookie to {settings.TARGET_API_URL}")
                print(f"[Scheduler] MUSIC_U: {netease_cookie['music_u'][:20]}...")
                
                if result.get('success') and result.get('data'):
                    data = result['data']
                    print(f"[Scheduler] Cookie ID: {data.get('id', 'N/A')}")
                    if data.get('userInfo'):
                        user_info = data['userInfo']
                        print(f"[Scheduler] User: {user_info.get('nickname', 'N/A')}, VIP: {user_info.get('isVip', False)}")
                
                return {
                    "success": True,
                    "platform": "netease",
                    "music_u": netease_cookie['music_u'],
                    "response_status": response.status_code,
                    "data": result.get('data')
                }
                
        except httpx.HTTPStatusError as e:
            self.error_count += 1
            error_detail = e.response.text
            try:
                error_json = e.response.json()
                error_detail = error_json.get('message', error_detail)
            except:
                pass
            print(f"[Scheduler] Netease Music HTTP error: {e.response.status_code} - {error_detail}")
            return {"success": False, "platform": "netease", "error": f"HTTP {e.response.status_code}: {error_detail}"}
            
        except httpx.RequestError as e:
            self.error_count += 1
            print(f"[Scheduler] Netease Music Request error: {str(e)}")
            return {"success": False, "platform": "netease", "error": str(e)}
            
        except Exception as e:
            self.error_count += 1
            print(f"[Scheduler] Netease Music Unexpected error: {str(e)}")
            return {"success": False, "platform": "netease", "error": str(e)}
    
    async def scheduled_send_task(self):
        print(f"[Scheduler] Running scheduled task at {datetime.now().isoformat()}")
        result = await self.send_cookies_to_target()
        print(f"[Scheduler] Task result: {result}")
        return result
    
    def setup_daily_schedule(self, hour: int = None, minute: int = None):
        hour = hour if hour is not None else settings.SCHEDULE_HOUR
        minute = minute if minute is not None else settings.SCHEDULE_MINUTE
        
        trigger = CronTrigger(hour=hour, minute=minute)
        
        self.scheduler.add_job(
            self.scheduled_send_task,
            trigger=trigger,
            id="daily_cookie_send",
            name="Daily Cookie Send Task",
            replace_existing=True,
            misfire_grace_time=3600
        )
        
        print(f"[Scheduler] Scheduled daily task at {hour:02d}:{minute:02d}")
    
    def add_custom_schedule(self, job_id: str, cron_expression: str, job_func):
        trigger = CronTrigger.from_crontab(cron_expression)
        self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600
        )
    
    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            print("[Scheduler] Scheduler started")
    
    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            print("[Scheduler] Scheduler stopped")
    
    def get_status(self) -> dict:
        jobs = self.scheduler.get_jobs()
        return {
            "running": self.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None
                }
                for job in jobs
            ],
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count,
            "error_count": self.error_count
        }
    
    async def run_once(self):
        return await self.scheduled_send_task()


scheduler_manager = SchedulerManager()
