# Music Cookie Manager

QQ音乐和网易云音乐客户端Cookie抓取工具，专为 [Meting-API](https://github.com/mikus-loli/Meting-API) 优化。

## 功能特性

- 🎵 **多平台支持**：支持QQ音乐和网易云音乐Cookie抓取
- 🔀 **顺序执行**：先QQ音乐后网易云，独立处理每个平台
- 🎨 **管理后台**：现代化响应式Web管理界面
- 🔐 **安全认证**：Token认证保护API访问
- ⏰ **定时同步**：自动定时发送Cookie到Meting-API
- 🔄 **自动续期**：支持refresh_token自动续期
- 🤖 **全自动化**：自动启动应用、抓取、发送、关闭的完整流程

## 快速开始

### 0. 安装 Visual C++ 生成工具（必需）

`mitmproxy` 依赖 `zstandard`、`cffi` 需要 C++ 编译器。安装 [Visual Studio 2022 生成工具](https://visualstudio.microsoft.com/zh-hans/downloads/)，勾选 **"C++ 生成工具"** 工作负荷。

> 如不想安装 C++ 环境，可尝试预编译安装：
> ```bash
> pip install zstandard --only-binary :all:
> pip install cffi --only-binary :all:
> pip install mitmproxy --only-binary :all:
> ```

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# API安全Token
API_TOKEN=your_secure_token_here

# Meting-API 配置
TARGET_API_URL=http://localhost:3000/admin/cookies
TARGET_API_TOKEN=mapi_xxxxxxxx...

# QQ音乐路径（可选，自动检测）
QQMUSIC_PATH=C:\Program Files (x86)\Tencent\QQMusic\QQMusic.exe

# 网易云音乐路径（可选，自动检测）
NETEASEMUSIC_PATH=C:\Program Files\Netease\CloudMusic\cloudmusic.exe
```

### 3. 安装MITM证书

```bash
# 启动代理后访问
http://mitm.it

# Windows安装证书到"受信任的根证书颁发机构"
```

### 4. 配置客户端代理

**QQ音乐**：设置 → 网络代理 → 自定义代理 → `127.0.0.1:8080`

**网易云音乐**：设置 → 代理设置 → 自定义代理 → HTTP → `127.0.0.1:8080`

## 运行模式

### 自动化模式（推荐）

全自动循环：启动应用 → 抓取Cookie → 发送 → 关闭 → 等待 → 循环

```bash
# 双击运行
run_automate.bat

# 或命令行
python automate.py --interval 24

# 仅抓取QQ音乐
python automate.py --platform qqmusic

# 仅抓取网易云音乐
python automate.py --platform netease

# 抓取所有平台
python automate.py --platform all
```

**参数说明**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--interval` | 执行间隔（小时） | 24 |
| `--once` | 仅执行一次 | - |
| `--platform` | 平台选择：`all`/`qqmusic`/`netease` | all |

### 手动模式

```bash
# 完整服务（代理+API+定时任务）
python main.py

# 仅API服务
python main.py --api-only

# 仅代理抓包
python main.py --proxy-only

# 立即发送Cookie
python main.py --send-now

# 查看状态
python main.py --status
```

## 自动化流程

```
┌─────────────────────────────────────────────────────────────┐
│                    自动化流程 (每24小时)                      │
└─────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────┐
  │  启动代理     │────▶│  等待稳定60s  │
  └──────────────┘     └───────┬──────┘
                               │
        ┌──────────────────────┘
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │                    QQ音乐处理流程                        │
  │  ┌────────────┐   ┌────────────┐   ┌────────────┐       │
  │  │ 启动QQ音乐  │──▶│ 等待Cookie │──▶│ 发送Cookie │       │
  │  └────────────┘   └────────────┘   └─────┬──────┘       │
  │                                          │              │
  │                                    ┌─────▼──────┐       │
  │                                    │ 关闭QQ音乐  │       │
  │                                    └────────────┘       │
  └─────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┘
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │                   网易云音乐处理流程                      │
  │  ┌────────────┐   ┌────────────┐   ┌────────────┐       │
  │  │ 启动网易云  │──▶│ 等待Cookie │──▶│ 发送Cookie │       │
  │  └────────────┘   └────────────┘   └─────┬──────┘       │
  │                                          │              │
  │                                    ┌─────▼──────┐       │
  │                                    │ 关闭网易云  │       │
  │                                    └────────────┘       │
  └─────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┘
        ▼
  ┌──────────────┐     ┌──────────────┐
  │  停止代理     │────▶│  等待24小时   │
  └──────────────┘     └───────┬──────┘
                               │
                               └──────────────▶ 循环
```

## 管理后台

启动服务后访问 `http://localhost:5000/admin` 进入管理后台。

### 功能模块

| 模块 | 功能 |
|------|------|
| 仪表盘 | Cookie状态、统计信息、快速操作 |
| Cookie管理 | 查看、添加、删除Cookie |
| 定时任务 | 配置定时同步、手动触发 |
| 系统设置 | API配置、快速操作 |

## API接口

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 服务状态 |
| GET | `/health` | 否 | 健康检查 |
| GET | `/api/meting` | 是 | 获取完整Cookie |
| GET | `/api/meting/simple` | 是 | 获取简化Cookie |
| POST | `/api/cookies` | 是 | 添加Cookie |
| POST | `/api/send` | 是 | 发送Cookie到Meting-API |
| DELETE | `/api/cookies` | 是 | 清空所有Cookie |

### 认证方式

所有 `/api/meting` 端点需要 Bearer Token 认证：

```bash
curl -H "Authorization: Bearer your_token" http://localhost:5000/api/meting
```

## Cookie 格式说明

### QQ音乐

**最简格式**：
```
uin=你的QQ号; qqmusic_key=Q_H_L_开头的key
```

**完整格式（支持自动续期）**：
```
uin=你的QQ号; qqmusic_key=Q_H_L_xxx; qm_keyst=Q_H_L_xxx; psrf_qqrefresh_token=刷新token
```

### 网易云音乐

**格式**：
```
MUSIC_U=用户token; __csrf=csrf值
```

## 发送数据格式

### QQ音乐

```json
{
  "platform": "tencent",
  "cookie": "uin=3166326944; qqmusic_key=Q_H_L_63k3...; psrf_qqrefresh_token=...",
  "note": "Auto-synced from Music-Cookie-Manager",
  "isActive": true
}
```

### 网易云音乐

```json
{
  "platform": "netease",
  "cookie": "MUSIC_U=xxx; __csrf=xxx",
  "note": "Auto-synced from Music-Cookie-Manager",
  "isActive": true
}
```

## 项目结构

```
QQMusic-Cookie/
├── automate.py          # 自动化脚本
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── api_server.py        # REST API服务
├── proxy_capture.py     # MITM代理抓包
├── cookie_store.py      # Cookie存储
├── scheduler.py         # 定时任务
├── run_automate.bat     # 自动化启动脚本
├── run_once.bat         # 单次执行脚本
├── static/              # 前端静态文件
├── data/                # 数据目录
├── logs/                # 日志目录
├── requirements.txt     # 完整依赖
└── .env.example         # 配置示例
```

## 安全建议

1. **设置API_TOKEN**：防止Cookie被未授权访问
2. **使用HTTPS**：生产环境建议配置反向代理
3. **限制访问IP**：通过防火墙限制API访问来源
4. **定期更换Token**：提高安全性

## 常见问题

### Q: 自动化模式无法启动应用？
A: 检查 `.env` 中的 `QQMUSIC_PATH` 和 `NETEASEMUSIC_PATH` 是否正确，或确保应用安装在默认路径。

### Q: Cookie抓取失败？
A: 
1. 确保已安装MITM证书
2. 确保客户端已配置代理 `127.0.0.1:8080`
3. 确保客户端已登录账号

### Q: 发送失败？
A: 检查 `TARGET_API_URL` 和 `TARGET_API_TOKEN` 配置是否正确。

### Q: 网易云音乐抓取不到Cookie？
A: 
1. 网易云音乐需要在设置中配置代理
2. 确保已登录账号
3. 检查代理日志 `logs/proxy.log`

## License

MIT
