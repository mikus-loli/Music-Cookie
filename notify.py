import httpx
from config import settings


class Notifier:
    def __init__(self):
        self._enabled = settings.MIOTIFY_ENABLED
        self._url = settings.MIOTIFY_URL or ""
        self._token = settings.MIOTIFY_TOKEN or ""
        self._api_url = ""
        self._init()

    def _init(self):
        if not self._enabled or not self._url or not self._token:
            return
        url = self._url.rstrip("/")
        if url.endswith("/message"):
            self._api_url = url
        else:
            self._api_url = f"{url}/message"

    @property
    def available(self) -> bool:
        return self._enabled and bool(self._url) and bool(self._token) and bool(self._api_url)

    async def send(self, title: str, message: str, priority: int = 5) -> bool:
        if not self.available:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self._api_url,
                    json={
                        "title": title,
                        "message": message,
                        "priority": priority
                    },
                    headers={
                        "Content-Type": "application/json",
                        "X-Gotify-Key": self._token
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"[Notify] Failed to send notification: {e}")
            return False

    async def cookie_captured(self, platform: str, uin: str = "", success: bool = True) -> bool:
        if success:
            if platform == "qqmusic":
                title = "🎵 QQ音乐 Cookie 已抓取"
                msg = f"成功抓取 QQ 音乐 Cookie\nUIN: {uin}"
            else:
                title = "🎵 网易云音乐 Cookie 已抓取"
                msg = f"成功抓取网易云音乐 Cookie\nMUSIC_U: {uin[:20] if uin else '未知'}..."
        else:
            if platform == "qqmusic":
                title = "❌ QQ音乐 Cookie 抓取失败"
                msg = "未捕获到有效的 QQ 音乐 Cookie，请检查客户端是否已登录并配置代理。"
            else:
                title = "❌ 网易云音乐 Cookie 抓取失败"
                msg = "未捕获到有效的网易云音乐 Cookie，请检查客户端是否已登录并配置代理。"
        return await self.send(title, msg, priority=8 if not success else 5)

    async def cookie_sent(self, platform: str, success: bool = True, detail: str = "") -> bool:
        if success:
            if platform == "qqmusic":
                title = "✅ QQ音乐 Cookie 已发送"
            else:
                title = "✅ 网易云音乐 Cookie 已发送"
            msg = f"Cookie 已成功发送到 Meting-API\n{detail}"
        else:
            if platform == "qqmusic":
                title = "⚠️ QQ音乐 Cookie 发送失败"
            else:
                title = "⚠️ 网易云音乐 Cookie 发送失败"
            msg = f"发送到 Meting-API 失败\n{detail}"
        return await self.send(title, msg, priority=3 if success else 8)

    async def cycle_start(self, cycle: int) -> bool:
        return await self.send(
            "🔄 自动化周期开始",
            f"第 {cycle} 次 Cookie 抓取周期已启动",
            priority=3
        )

    async def cycle_end(self, cycle: int, success: bool, summary: str = "") -> bool:
        if success:
            title = "✅ 自动化周期完成"
            msg = f"第 {cycle} 次周期已完成\n{summary}"
            priority = 3
        else:
            title = "⚠️ 自动化周期结束"
            msg = f"第 {cycle} 次周期已结束，部分任务失败\n{summary}"
            priority = 8
        return await self.send(title, msg, priority=priority)

    async def error(self, error_msg: str) -> bool:
        return await self.send(
            "🚨 系统错误",
            error_msg,
            priority=10
        )


notifier = Notifier()
