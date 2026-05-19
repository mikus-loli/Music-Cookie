# Music Cookie Manager 使用教程

## 目录

- [系统概述](#系统概述)
- [环境准备](#环境准备)
- [安装配置](#安装配置)
- [客户端代理设置](#客户端代理设置)
- [运行方式](#运行方式)
- [自动化流程详解](#自动化流程详解)
- [Miotify 通知配置](#miotify-通知配置)
- [Web 管理后台](#web-管理后台)
- [API 接口说明](#api-接口说明)
- [常见问题](#常见问题)

---

## 系统概述

Music Cookie Manager 是一个自动抓取 QQ 音乐和网易云音乐客户端 Cookie 的工具。它通过 MITM 代理拦截客户端网络请求，提取登录凭证，并自动发送到 [Meting-API](https://github.com/mikus-loli/Meting-API) 进行统一管理。

### 核心功能

| 功能 | 说明 |
|------|------|
| 多平台支持 | QQ音乐 + 网易云音乐 |
| 自动抓取 | MITM 代理拦截客户端请求中的 Cookie |
| 自动发送 | 提取后自动 POST 到 Meting-API |
| 定时循环 | 每24小时自动执行一次完整流程 |
| 通知推送 | 支持 Miotify 实时推送执行状态 |
| Web 管理 | 可视化管理界面，查看/管理 Cookie |

### 工作流程

```
启动代理 (60s等待)
    │
    ├─► QQ音乐流程 ──────────────────────────────►
    │   1. 启动 QQ 音乐客户端
    │   2. 等待60秒应用初始化
    │   3. 等待有效 Cookie (最长300秒)
    │   4. 发送 Cookie 到 Meting-API
    │   5. 关闭 QQ 音乐客户端
    │
    ├─► 网易云音乐流程 ──────────────────────────►
    │   1. 启动网易云音乐客户端
    │   2. 等待60秒应用初始化
    │   3. 等待有效 Cookie (最长300秒)
    │   4. 发送 Cookie 到 Meting-API
    │   5. 关闭网易云音乐客户端
    │
    └─► 停止代理 → 清理文件 → 等待24小时 → 循环
```

---

## 环境准备

### 系统要求

- Windows 操作系统
- Python 3.9+
- **Visual C++ 生成工具**（编译 mitmproxy 依赖必需）
- QQ音乐客户端（已登录）
- 网易云音乐客户端（已登录，可选）

### 1. 安装 Visual C++ 生成工具（必需）

`mitmproxy` 的某些底层依赖（`zstandard`、`cffi`）需要 C++ 编译器才能安装。

**方式一：安装 Visual Studio Build Tools（推荐）**

1. 访问 [Visual Studio 下载页面](https://visualstudio.microsoft.com/zh-hans/downloads/)
2. 展开 **"所有下载"** → 找到 **"Visual Studio 2022 生成工具"** → 下载
3. 运行安装程序，勾选 **"C++ 生成工具"** 工作负荷
4. 确保包含以下组件：
   - MSVC v143 - VS 2022 C++ x64/x86 生成工具
   - Windows 11 SDK (最新版本)
   - C++ CMake 工具（可选）

**方式二：使用预编译 wheel（绕过编译）**

如果不想安装 C++ 环境，可以直接安装预编译好的 wheel 包：

```bash
# 激活虚拟环境后
pip install zstandard --only-binary :all:
pip install cffi --only-binary :all:
pip install mitmproxy --only-binary :all:
```

> 如果部分包没有对应 Python 版本的预编译 wheel，此方法会失败，建议还是安装 C++ 生成工具。

**方式三：使用精简版依赖（不需要 C++ 环境）**

如果完全不想安装 C++ 环境和 mitmproxy：

```bash
pip install -r requirements-lite.txt
```

> 注意：精简版不包含 mitmproxy，**自动化模式 (`automate.py`) 无法使用**，但其他功能正常（API 服务、Web 管理后台、定时发送已存储的 Cookie）。

### 2. 安装 Python

如果尚未安装 Python，请从 [python.org](https://www.python.org/downloads/) 下载安装。

> **重要**：安装时勾选 "Add Python to PATH"。

### 3. 创建虚拟环境（推荐）

```powershell
# 在项目目录打开终端
cd D:\miku\QQMusic-Cookie

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

---

## 安装配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

> 如果安装 mitmproxy 遇到问题，可使用精简版依赖：
> ```bash
> pip install -r requirements-lite.txt
> ```

依赖说明：

| 依赖 | 版本 | 用途 |
|------|------|------|
| mitmproxy | 10.4.2 | MITM 代理抓包 |
| fastapi | 0.109.0 | Web API 服务 |
| uvicorn | 0.27.0 | ASGI 服务器 |
| apscheduler | 3.10.4 | 定时任务调度 |
| httpx | 0.26.0 | HTTP 客户端 |
| pydantic | 2.5.3 | 数据验证 |

### 2. 配置 .env 文件

```bash
# 复制配置模板
copy .env.example .env
```

打开 `.env` 文件，填写以下关键配置：

```ini
# ===== 必填配置 =====

# Meting-API 地址（你的 Meting-API 服务地址）
TARGET_API_URL=https://meting.mikus.ink/admin/cookies

# Meting-API Token（在 Meting-API 管理后台获取，以 mapi_ 开头）
TARGET_API_TOKEN=mapi_your_token_here

# ===== 可选配置 =====

# QQ音乐客户端路径（留空则自动检测）
QQMUSIC_PATH=C:\QQMusic\QQMusic.exe

# 网易云音乐客户端路径（留空则自动检测）
NETEASEMUSIC_PATH=C:\Program Files\Netease\CloudMusic\cloudmusic.exe

# Miotify 通知（详见下方通知配置章节）
MIOTIFY_ENABLED=false
MIOTIFY_URL=http://localhost:8080
MIOTIFY_TOKEN=

# 代理配置（一般无需修改）
PROXY_HOST=127.0.0.1
PROXY_PORT=8080

# API 服务配置
API_HOST=0.0.0.0
API_PORT=5000
API_TOKEN=your_api_token
```

### 3. 安装 MITM 证书

MITM 代理需要安装 SSL 证书才能解密 HTTPS 流量。

**步骤：**

1. 启动代理（任选一种方式）：
   ```bash
   python main.py --proxy-only
   ```

2. 打开浏览器访问 `http://mitm.it`

3. 下载 Windows 证书：
   - 点击 **Windows** 图标下载 `mitmproxy-ca-cert.p12`

4. 安装证书：
   - 双击下载的证书文件
   - 选择 **"本地计算机"**
   - 选择 **"将所有证书放入下列存储"**
   - 点击 **"浏览"** → 选择 **"受信任的根证书颁发机构"**
   - 完成安装

> 或者通过命令行安装：
> ```bash
> certutil -addstore root %USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer
> ```

---

## 客户端代理设置

代理抓包需要客户端将所有网络请求发送到 MITM 代理。

### QQ音乐客户端

1. 打开 QQ音乐客户端
2. 点击右上角 **菜单**（三条横线图标）
3. 选择 **设置**
4. 找到 **网络设置** 或 **代理设置**
5. 选择 **自定义代理**
6. 填写：
   - 类型：**HTTP 代理**
   - 服务器地址：`127.0.0.1`
   - 端口：`8080`
7. 点击 **保存** 或 **确定**

### 网易云音乐客户端

1. 打开网易云音乐客户端
2. 点击右上角 **设置**（齿轮图标）
3. 找到 **工具** 或 **代理设置**
4. 选择 **自定义代理**
5. 填写：
   - 类型：**HTTP 代理**
   - 服务器地址：`127.0.0.1`
   - 端口：`8080`
6. 点击 **保存** 或 **确定**

> **注意**：两个客户端都需要先登录账号，否则捕获的 Cookie 无效。

---

## 运行方式

### 方式一：双击运行（最简单）

| 文件 | 功能 |
|------|------|
| `run_automate.bat` | 24小时自动化循环 |
| `run_once.bat` | 执行一次 |

直接双击对应的 `.bat` 文件即可启动。

### 方式二：命令行运行

#### 自动化模式（推荐）

```bash
# 每24小时循环一次，抓取所有平台
python automate.py --interval 24

# 只抓取 QQ音乐
python automate.py --interval 24 --platform qqmusic

# 只抓取 网易云音乐
python automate.py --interval 24 --platform netease

# 执行一次后退出
python automate.py --once
python automate.py --once --platform qqmusic
```

**参数说明：**

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `--interval` | 数字 | 24 | 循环间隔（小时） |
| `--once` | - | - | 仅执行一次 |
| `--platform` | all / qqmusic / netease | all | 目标平台 |

#### 手动模式

```bash
# 完整服务（代理 + API + 定时任务）
python main.py

# 仅启动 API 服务
python main.py --api-only

# 仅启动代理抓包
python main.py --proxy-only

# 手动发送已存储的 Cookie 到 Meting-API
python main.py --send-now

# 查看当前 Cookie 状态
python main.py --status
```

### 自动化运行输出示例

```
============================================
 Music Cookie Manager - Automation Mode
============================================

[Info] Found virtual environment, activating...

Starting automation...

[qqmusic] Found at: C:\QQMusic\QQMusic.exe
[netease] Found at: C:\CloudMusic\cloudmusic.exe

============================================================
Music Cookie Manager - Automation Mode
============================================================
Interval: Every 24 hours
Platform: all
Proxy: 127.0.0.1:8080
Target API: https://meting.mikus.ink/admin/cookies
============================================================


============================================================
[Cycle] Starting cycle #1
[Cycle] Time: 2026-05-15 17:05:49
[Cycle] Platform: all
============================================================

[Step 1] Starting proxy...
[Proxy] Starting MITM proxy as subprocess...
[Proxy] Proxy started on 127.0.0.1:8080
[Proxy] Proxy PID: 3792

[Step 2] Waiting for proxy to stabilize (60s)...
[Wait] 58 seconds remaining...
[Wait] Proxy ready!

[Step 2.1] Processing qqmusic...

==================================================
[QQMUSIC] Starting qqmusic cycle...
==================================================

[qqmusic] Starting app...
[qqmusic] Started (PID: 5180)
[qqmusic] Waiting for app to initialize (60s)...
[qqmusic] 30 seconds remaining...
[qqmusic] App ready!
[qqmusic] Waiting for cookies (timeout: 300s)...
[Wait] Captured 7 cookies...
[Wait] QQ Music cookies found!
[Wait] UIN: 3166326944

[qqmusic] Sending cookies...
[Scheduler] Successfully sent QQ Music cookie
[Scheduler] UIN: 3166326944, Has refresh token: True
[Scheduler] Cookie ID: mozisrejxvu3jtsig

[qqmusic] Stopping app...
[qqmusic] Terminated gracefully

[Step 2.2] Processing netease...
... (同上流程)

[Step 3] Stopping proxy and cleaning up...

------------------------------------------------------------
[Cycle] Cycle #1 completed
[Cycle] Success: True
------------------------------------------------------------

[Sleep] Next run at: 2026-05-16 17:08:02
[Sleep] Waiting 24 hours...
```

---

## 自动化流程详解

### 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    自动化流程 (每24小时)                      │
└─────────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌────────────┐
  │ 启动代理  │────▶│ 等待60秒   │
  └──────────┘     └─────┬──────┘
                         │
  ┌───────────────────────┘
  │
  ▼
  ┌─────────────────────────────────────────────────────────┐
  │                    QQ音乐处理流程                        │
  │                                                         │
  │  ┌─────────────┐   ┌────────────┐   ┌─────────────┐     │
  │  │ 启动 QQ音乐  │──▶│ 等待60秒   │──▶│ 等待Cookie  │     │
  │  │             │   │ 应用初始化  │   │ (最长300秒) │     │
  │  └─────────────┘   └────────────┘   └──────┬──────┘     │
  │                                            │            │
  │                                     ┌──────▼──────┐     │
  │                                     │  找到有效   │     │
  │                                     │  Cookie?    │     │
  │                                     └──┬──────┬───┘     │
  │                                   NO    │      │  YES   │
  │                                    │     │      │        │
  │                              ┌─────▼──┐ ┌─▼────────┐    │
  │                              │ 发送失败 │ │ 发送成功  │    │
  │                              │  通知   │ │  POST    │    │
  │                              └────────┘ │ Meting-API│   │
  │                                         └─────┬─────┘    │
  │                                               │          │
  │                                         ┌─────▼─────┐    │
  │                                         │  通知结果  │    │
  │                                         └─────┬─────┘    │
  │                                               │          │
  │                                         ┌─────▼─────┐    │
  │                                         │ 关闭QQ音乐 │    │
  │                                         └───────────┘    │
  └─────────────────────────────────────────────────────────┘
                         │
  ┌───────────────────────┘
  │
  ▼
  ┌─────────────────────────────────────────────────────────┐
  │                   网易云音乐处理流程                      │
  │                  (与 QQ音乐相同)                         │
  └─────────────────────────────────────────────────────────┘
                         │
  ┌───────────────────────┘
  │
  ▼
  ┌──────────┐     ┌────────────┐     ┌──────────┐
  │ 停止代理  │────▶│  清理文件   │────▶│ 等待24小时 │
  └──────────┘     └────────────┘     └────┬─────┘
                                           │
                                           └──▶ 循环
```

### 各阶段说明

| 阶段 | 说明 | 耗时 |
|------|------|------|
| 启动代理 | 启动 MITM 代理子进程，绑定 127.0.0.1:8080 | ~5秒 |
| 等待稳定 | 等待代理完全启动并准备接收连接 | 60秒 |
| 启动客户端 | 启动 QQ音乐/网易云音乐 EXE | ~3秒 |
| 应用初始化 | 等待客户端加载 UI、连接网络、发送请求 | 60秒 |
| 等待 Cookie | 轮询检查是否捕获到有效登录凭证 | 最长300秒 |
| 发送 Cookie | POST 到 Meting-API 保存 | ~3秒 |
| 关闭客户端 | 优雅关闭客户端进程 | ~5秒 |
| 清理文件 | 删除临时 cookie 文件 | ~1秒 |
| 等待循环 | 休眠至下次执行 | 24小时 |

### 定时执行

- 脚本会每24小时自动执行一次完整流程
- 执行时间取决于首次启动时间（例如首次 17:00 启动，下次也是 17:00）
- 按 `Ctrl+C` 可随时停止

---

## Miotify 通知配置

Miotify 是一个轻量级消息推送服务器，兼容 Gotify API。配置后可以实时收到 Cookie 抓取和发送的状态推送。

### 1. 部署 Miotify

```bash
git clone https://github.com/mikus-loli/Miotify
cd Miotify
docker-compose up -d
```

服务默认运行在 `http://localhost:8080`。

### 2. 获取 App Token

1. 浏览器打开 `http://localhost:8080`
2. 使用默认账号登录（admin / admin）
3. 点击 **Apps** → **Create Application**
4. 输入应用名称（如 "Cookie Manager"）
5. 创建后会生成一个 App Token（UUID 格式），复制保存

### 3. 配置 .env

```ini
MIOTIFY_ENABLED=true
MIOTIFY_URL=http://localhost:8080
MIOTIFY_TOKEN=你的App_Token_（UUID格式）
```

### 4. 通知类型

| 通知 | 标题 | 场景 |
|------|------|------|
| 🔄 自动化周期开始 | 第 N 次 Cookie 抓取周期已启动 | 每个周期开始时 |
| 🎵 QQ音乐 Cookie 已抓取 | 成功抓取 QQ 音乐 Cookie | UIN 已获取 |
| ❌ QQ音乐 Cookie 抓取失败 | 未捕获到有效的 QQ 音乐 Cookie | 超时或未找到 |
| ✅ QQ音乐 Cookie 已发送 | Cookie 已成功发送到 Meting-API | POST 成功 |
| ⚠️ QQ音乐 Cookie 发送失败 | 发送到 Meting-API 失败 | 网络错误等 |
| ✅ 自动化周期完成 | 所有平台处理完毕 | 周期结束汇总 |
| 🚨 系统错误 | 异常错误详情 | 脚本异常 |

---

## Web 管理后台

### 启动管理后台

```bash
python main.py --api-only
```

浏览器访问 `http://localhost:5000/admin`

### 功能模块

| 模块 | 路径 | 功能 |
|------|------|------|
| 仪表盘 | `/admin` | Cookie 状态概览、统计信息 |
| Cookie 管理 | `/admin/cookies` | 查看/添加/删除 Cookie |
| 定时任务 | `/admin/scheduler` | 配置/触发定时同步 |
| 系统设置 | `/admin/settings` | API 配置和系统参数 |

### Cookie 状态检查

```bash
python main.py --status
```

输出示例：

```
QQ Music Cookie Status
========================================
  UIN: 3166326944
  Key: Q_H_L_63k3NLuJcvgUCi...
  Refresh Token: Yes
  Status: Valid
```

---

## API 接口说明

### 认证方式

需要认证的接口使用 Bearer Token：

```bash
curl -H "Authorization: Bearer your_token" http://localhost:5000/api/meting
```

### 接口列表

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 服务运行状态 |
| GET | `/health` | 否 | 健康检查 |
| GET | `/api/meting` | 是 | 获取完整 Cookie 数据 |
| GET | `/api/meting/simple` | 是 | 获取简化 Cookie 数据 |
| POST | `/api/cookies` | 是 | 手动添加 Cookie |
| POST | `/api/send` | 是 | 发送 Cookie 到 Meting-API |
| DELETE | `/api/cookies` | 是 | 清空所有 Cookie |

### Cookie 格式

#### QQ音乐

**最简格式**（基本播放功能）：
```
uin=你的QQ号; qqmusic_key=Q_H_L_开头的key
```

**完整格式**（支持自动续期）：
```
uin=你的QQ号; qqmusic_key=Q_H_L_...; qm_keyst=Q_H_L_...; psrf_qqrefresh_token=...; psrf_qqaccess_token=...; qqmusic_guid=...
```

#### 网易云音乐

```
MUSIC_U=用户token; MUSIC_A=认证key; __csrf=csrf值
```

### 发送到 Meting-API 的数据格式

**QQ音乐：**
```json
{
  "platform": "tencent",
  "cookie": "uin=3166326944; qqmusic_key=Q_H_L_63k3...; psrf_qqrefresh_token=...",
  "note": "Auto-synced from Music-Cookie-Manager",
  "isActive": true
}
```

**网易云音乐：**
```json
{
  "platform": "netease",
  "cookie": "MUSIC_U=00FD08B3B2141E00C258...; __csrf=...",
  "note": "Auto-synced from Music-Cookie-Manager",
  "isActive": true
}
```

---

## 常见问题

### Q: 安装依赖报错 `error: Microsoft Visual C++ 14.0 or greater is required`？

A: `mitmproxy` 的底层依赖 `zstandard` 和 `cffi` 需要 C++ 编译器。三种解决方案：

1. **安装 Visual Studio 2022 生成工具**（推荐，一劳永逸）
   - 下载：https://visualstudio.microsoft.com/zh-hans/downloads/
   - 安装时勾选 **"C++ 生成工具"** 工作负荷
   - 约 3-5 GB 磁盘空间

2. **使用预编译包绕过编译**
   ```bash
   pip install zstandard --only-binary :all:
   pip install cffi --only-binary :all:
   pip install -r requirements.txt --only-binary :all:
   ```

3. **使用轻量版依赖**（不需要 mitmproxy）
   ```bash
   pip install -r requirements-lite.txt
   ```
   > 注意：轻量版无法使用自动化代理抓包，但 API 服务和手动模式正常。

### Q: 自动化模式无法启动 QQ音乐/网易云音乐？

A: 两种解决方式：
1. 在 `.env` 中设置正确的路径：
   ```ini
   QQMUSIC_PATH=C:\你的安装路径\QQMusic\QQMusic.exe
   NETEASEMUSIC_PATH=C:\你的安装路径\CloudMusic\cloudmusic.exe
   ```
2. 将客户端安装到默认路径，脚本会自动检测

### Q: Cookie 抓不到？

A: 按以下顺序排查：
1. **客户端是否已登录**：确保 QQ音乐和网易云音乐已登录账号
2. **代理是否配置**：客户端设置中确认代理为 `127.0.0.1:8080`
3. **证书是否安装**：确认 MITM 证书已安装到受信任的根证书颁发机构
4. **查看代理日志**：打开 `logs/proxy.log` 查看有没有捕获到请求

### Q: 证书安装后客户端还是报错？

A: 部分客户端有独立的证书存储。可以尝试：
1. 以管理员身份运行客户端
2. 在客户端设置中关闭 SSL 验证（如果有此选项）
3. 检查 Windows 防火墙是否阻止了代理端口

### Q: 发送 Cookie 到 Meting-API 失败？

A: 检查配置：
1. `TARGET_API_URL` 是否正确（确保是完整的 Cookie 接口地址）
2. `TARGET_API_TOKEN` 是否正确（应是以 `mapi_` 开头的 token）
3. 网络是否能访问 Meting-API 服务器

### Q: 网易云音乐抓不到 Cookie？

A: 因为需要 HTTP 代理。注意：
1. 网易云音乐的代理设置比较隐蔽，需要在设置中仔细查找
2. 如果客户端不支持 HTTP 代理，可以尝试使用系统代理或 Proxifier

### Q: WinError 32 文件被占用？

A: 这是代理进程和清理操作同时访问 cookie 文件引起的。最新版本已添加重试机制，一般不会遇到此问题。如果仍然出现，不影响功能运行。

### Q: 等待24小时后报错？

A: 这是因为后台进程的 event loop 问题。现在已经将代理改为子进程模式，每个周期都是全新进程，不会出现此问题。

### Q: 如何只运行一次后立即关闭？

A: 使用 `--once` 参数：
```bash
python automate.py --once
```

### Q: 如何查看详细日志？

A: 代理日志保存在 `logs/proxy.log`，可以查看所有抓包记录。
```

---

## 项目结构

```
QQMusic-Cookie/
├── automate.py          # 自动化脚本（主入口）
├── main.py              # 手动模式主程序
├── config.py            # 配置管理（读取 .env）
├── proxy_capture.py     # MITM 代理抓包
├── cookie_store.py      # Cookie 存储和读取
├── scheduler.py         # 定时任务和发送逻辑
├── notify.py            # Miotify 通知模块
├── api_server.py        # REST API 服务
├── run_automate.bat     # 一键自动化启动
├── run_once.bat         # 一键单次执行
├── requirements.txt     # Python 依赖
├── requirements-lite.txt# 精简版依赖
├── .env.example         # 配置模板
├── .env                 # 你的配置文件（需手动创建）
├── static/              # Web 管理后台前端
├── data/                # Cookie 数据存储
└── logs/                # 代理运行日志
```
