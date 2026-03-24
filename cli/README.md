# Multi-Agent Team CLI

基于 Blessed 的终端 TUI 界面，连接 Python 后端 API。

## 安装

### 1. 安装 Node.js 依赖

```bash
cd cli
npm install
```

### 2. 启动 Python 后端

```bash
# 在项目根目录
python server.py
```

后端将在 http://localhost:8000 启动

### 3. 启动 CLI

```bash
cd cli
node src/index.js
```

或者连接到远程服务器：

```bash
node src/index.js --host 192.168.1.100
```

## 界面说明

```
┌─────────────────────────────────────────────────────────┐
│           🤖 Multi-Agent Team CLI                       │
├──────────────────┬──────────────────────────────────────┤
│ Agent 状态        │ 实时日志                              │
│                  │                                      │
│ 🟢 ProjectDir    │ [10:00:00] 正在启动...              │
│ ⚪ ProductMgr    │ [10:00:01] 已连接到后端 API          │
│ 🟢 Developer     │ [10:00:02] 发送：创建项目            │
│ ⚪ Tester        │ [10:00:05] Agent: 好的，我来创建...  │
│                  │                                      │
├──────────────────┴──────────────────────────────────────┤
│ Ctrl+C 退出 | Ctrl+L 清屏 | /help 查看命令              │
├─────────────────────────────────────────────────────────┤
│ 输入消息 (Enter 发送): [________________]               │
└─────────────────────────────────────────────────────────┘
```

## 命令

| 命令 | 说明 |
|------|------|
| `/clear` | 清空日志 |
| `/status` | 显示状态 |
| `/help` | 显示帮助 |
| `/exit` | 退出程序 |
| `Ctrl+C` | 强制退出 |
| `Ctrl+L` | 清屏 |

## 配置

编辑 `src/index.js` 修改默认连接地址：

```javascript
const DEFAULT_API_URL = 'http://localhost:8000';
const DEFAULT_WS_URL = 'ws://localhost:8000/ws';
```

## 部署

### 本地开发

```bash
# 终端 1 - 启动后端
python server.py

# 终端 2 - 启动 CLI
cd cli && node src/index.js
```

### 远程服务器

1. 在服务器上启动 Python 后端
2. 本地运行 CLI 并指定服务器地址

```bash
node src/index.js --host your-server-ip
```

## 故障排查

### 无法连接到后端

检查后端是否启动：
```bash
curl http://localhost:8000/health
```

### WebSocket 连接失败

检查防火墙是否开放 8000 端口。

### TUI 显示异常

确保终端支持 Unicode 和颜色。
