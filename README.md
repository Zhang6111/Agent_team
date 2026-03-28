# 多 Agent 开发团队

基于 LangChain 和 MCP (Model Context Protocol) 的多 Agent 协作系统，支持任意编程语言和框架。

## 特性

- **手动模式**：用户直接与指定 Agent 对话，按需切换
- **多语言支持**：不预设技术栈，根据用户描述自动适配
- **独立模型配置**：每个 Agent 可配置不同的 LLM 模型
- **即时响应**：单 Agent 调用，无超时问题

## 团队架构

```
产品设计层
├── 产品经理 (ProductManager) - 需求分析、PRD 输出
└── UI 设计师 (UIDesigner) - 页面布局、样式规范

架构数据层
├── 架构师 (Architect) - 技术架构设计
└── 数据工程师 (DataEngineer) - 数据库设计

研发执行层
├── 前端开发 (FrontendDev) - 前端实现
├── 后端开发 (BackendDev) - 后端实现
└── 代码评审 (CodeReviewer) - 代码审查

质量保障层
├── 测试工程师 (Tester) - 功能测试
├── 安全审计 (SecurityAuditor) - 漏洞扫描
└── 性能优化 (PerformanceOptimizer) - 性能调优

工程交付层
├── 运维工程师 (DevOps) - 部署配置、Docker
└── 技术文档 (TechnicalWriter) - 文档生成
```

共 **12 个 Agent**，覆盖软件开发的完整流程。

## 快速开始

### 1. 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# CLI 依赖（可选）
cd cli && npm install && npm link
```

### 2. 配置 API Key

编辑 `.env` 文件：

```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEFAULT_MODEL=deepseek-chat
```

### 3. 配置 Agent 模型（可选）

编辑 `agents.yaml` 文件，为每个 Agent 配置独立模型：

```yaml
agents:
  ProductManager:
    model: deepseek-reasoner
    temperature: 0.5
    max_tokens: 8192

  FrontendDev:
    model: deepseek-chat
    temperature: 0.3
    max_tokens: 8192
```

### 4. 启动 CLI

**方式一：Python CLI**

```bash
python main.py
```

**方式二：Node.js CLI（推荐）**

```bash
# 终端 1 - 启动后端
python server.py

# 终端 2 - 启动 CLI
agent-team
```

## 使用方式

### Agent 切换

```
按数字键切换 Agent：
  [1] ProductManager      [7] CodeReviewer
  [2] Architect           [8] Tester
  [3] DataEngineer        [9] SecurityAuditor
  [4] UIDesigner          [0] PerformanceOptimizer
  [5] FrontendDev         [-] DevOps
  [6] BackendDev          [=] TechnicalWriter
```

### 使用示例

```
[ProductManager] 你：我要用 Java Spring Boot 实现一个博客系统
[ProductManager]：好的，我来分析需求并输出 PRD...

[Architect] 你：（按 2 切换）
[Architect]：好的，我来设计 Java Spring Boot 架构...

[BackendDev] 你：（按 6 切换）帮我实现用户登录 API
[BackendDev]：好的，我用 Java Spring Boot 实现登录接口...
```

### CLI 命令

| 命令 | 说明 |
|------|------|
| `1-9, 0, -, =` | 切换 Agent |
| `/agents` | 列出所有 Agent |
| `/status` | 查看状态 |
| `/clear` | 清屏 |
| `/exit` | 退出 |

### CLI 参数

| 参数 | 说明 |
|------|------|
| `--host <hostname>` | 指定后端 API 地址 |
| `--workdir <directory>` | 指定工作目录 |

## 支持的技术栈

### 后端
- Python: FastAPI, Django, Flask
- Java: Spring Boot, Quarkus
- Node.js: Express, NestJS
- Go: Gin, Echo, Fiber
- Rust: Actix-web, Axum
- C#: ASP.NET Core

### 前端
- React, Vue, Angular, Svelte
- Next.js, Nuxt.js
- Flutter, React Native
- Electron, Tauri
- WPF, WinUI, SwiftUI

### 数据库
- MySQL, PostgreSQL, SQLite
- MongoDB, Redis
- Elasticsearch

## 配置文件

### .env（全局默认配置）

```bash
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEFAULT_MODEL=deepseek-chat
TEMPERATURE=0.7
MAX_TOKENS=4096
```

### agents.yaml（Agent 独立配置）

```yaml
default:
  base_url: https://api.deepseek.com
  api_key: ${DEEPSEEK_API_KEY}

agents:
  ProductManager:
    model: deepseek-reasoner
    temperature: 0.5
    max_tokens: 8192

  BackendDev:
    model: deepseek-chat
    temperature: 0.3
    max_tokens: 8192

  # 支持混合使用不同 API
  # FrontendDev:
  #   model: gpt-4
  #   base_url: https://api.openai.com/v1
  #   api_key: sk-xxx
```

## API 接口

### HTTP API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/agents` | GET | 获取 Agent 列表 |
| `/chat` | POST | 与指定 Agent 对话 |
| `/execute` | POST | 执行操作指令 |

### WebSocket

| 端点 | 说明 |
|------|------|
| `/ws` | 实时状态推送 |

## 项目结构

```
Agent_team/
├── main.py                 # Python CLI 入口
├── server.py               # FastAPI 服务器
├── agents.yaml             # Agent 模型配置
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量
│
├── cli/                    # Node.js CLI
│   ├── src/index.js        # CLI 主程序
│   └── package.json
│
└── src/
    ├── agents/             # Agent 定义 (12 个)
    │   ├── base_agent.py   # 基类
    │   ├── product_manager.py
    │   ├── architect.py
    │   ├── frontend_dev.py
    │   ├── backend_dev.py
    │   └── ...
    │
    ├── mcp/                # MCP 通信层
    │   ├── messages.py
    │   └── bus.py
    │
    ├── memory/             # 记忆系统
    │   └── session.py
    │
    ├── tools/              # 工具函数
    │   ├── file_tools.py
    │   └── command_tools.py
    │
    └── config/             # 配置
        ├── settings.py
        └── prompts.py
```

## 核心功能

### 1. 手动模式

- 用户直接选择 Agent 对话
- 数字键快速切换
- 单 Agent 调用，无超时问题

### 2. 多语言支持

- 不预设技术栈
- 根据用户描述自动适配
- 支持任意编程语言和框架

### 3. 会话记忆

- 保存对话历史
- 记录任务上下文
- 跟踪文件操作

### 4. 文件操作

- 创建、修改、删除文件
- 支持命令执行
- 自动确认模式

## 后续计划

- [ ] Agent 间协作通信
- [ ] 长期记忆系统（向量数据库）
- [ ] 更多内置工具
- [ ] Web UI 界面

## License

MIT
