from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Music Cookie Manager"
    DEBUG: bool = False
    
    PROXY_HOST: str = "127.0.0.1"
    PROXY_PORT: int = 8080
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 5000
    API_TOKEN: Optional[str] = None
    
    SCHEDULE_HOUR: int = 8
    SCHEDULE_MINUTE: int = 0
    
    TARGET_API_URL: Optional[str] = None
    TARGET_API_TOKEN: Optional[str] = None
    
    QQMUSIC_PATH: Optional[str] = None
    NETEASEMUSIC_PATH: Optional[str] = None
    
    MIOTIFY_ENABLED: bool = False
    MIOTIFY_URL: Optional[str] = None
    MIOTIFY_TOKEN: Optional[str] = None
    
    DATA_DIR: Path = Path("data")
    COOKIE_FILE: Path = Path("data/cookies.json")
    
    QQ_MUSIC_DOMAINS: list = [
        "y.qq.com",
        "c.y.qq.com", 
        "u.y.qq.com",
        "m.y.qq.com",
        "api.y.qq.com",
        "szu6.y.qq.com",
        "szu.y.qq.com",
        "shu6.y.qq.com",
        "stat.y.qq.com",
        "u6.y.qq.com",
        "dldir.y.qq.com",
        "qpic.y.qq.com",
        "c6.y.qq.com",
        "music-file.y.qq.com",
        "xui.ptlogin2.qq.com",
        "ssl.ptlogin2.qq.com",
        "ptlogin2.qq.com",
        "ui.ptlogin2.qq.com",
        "graph.qq.com",
        "openmobile.qq.com",
        "qun.qq.com",
        "mqun.qq.com",
        "connect.qq.com",
        "login.qq.com",
        "t.qq.com",
        "qzone.qq.com",
        "vip.qq.com",
        "qq.com",
    ]
    
    NETEASE_MUSIC_DOMAINS: list = [
        "music.163.com",
        "interface.music.163.com",
        "api.music.163.com",
        "m.music.163.com",
        "music.126.net",
        "interface3.music.163.com",
        "interface.music.163.com",
        "clientlog.music.163.com",
        "clientlog3.music.163.com",
        "p1.music.126.net",
        "p2.music.126.net",
        "m7.music.126.net",
        "m8.music.126.net",
        "mam.netease.com",
        "client.music.163.com",
        "music.163.com.00.bg.mp",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
