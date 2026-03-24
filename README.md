# 多 Agent 开发团队

基于 LangChain 和 MCP (Model Context Protocol) 的多 Agent 协作系统，模拟完整的软件开发团队。

## 团队架构

```
总控调度层
└── 项目总监 (ProjectDirector) - 用户交互接口，协调团队

产品设计层
├── 产品经理 (ProductManagerAgent) - 需求分析、PRD 输出
└── UI 设计师 (UIDesignerAgent) - 页面布局、样式规范

架构数据层
├── 架构师 (ArchitectAgent) - 技术架构设计
└── 数据工程师 (DataEngineerAgent) - 数据库设计

研发执行层
├── 研发效能组长 (TechLeadAgent) - 统筹开发任务
├── 前端开发 (FrontendDeveloperAgent) - 前端实现
├── 后端开发 (BackendDeveloperAgent) - 后端实现
└── 代码评审 (CodeReviewerAgent) - 代码审查

质量保障层
├── 测试工程师 (TesterAgent) - 功能测试、Bug 发现
├── 故障修复 (BugFixerAgent) - Bug 修复
├── 安全审计 (SecurityAuditorAgent) - 漏洞扫描
└── 性能优化 (PerformanceOptimizerAgent) - 性能调优

工程交付层
├── 运维工程师 (DevOpsAgent) - 部署配置、Docker
└── 技术文档 (TechnicalWriterAgent) - 文档生成
```

共 **15 个 Agent**，覆盖软件开发的完整流程。

## 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

编辑 `.env` 文件：

```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEFAULT_MODEL=deepseek-chat
```

### 3. 启动 CLI（推荐）

```bash
# 终端 1 - 启动 Python 后端
python server.py

# 终端 2 - 启动 CLI
cd cli
npm install
npm link
agent-team
```

### 4. 使用 CLI

```bash
# 本地连接
agent-team

# 连接远程服务器
agent-team --host 192.168.1.100

# 指定工作目录
agent-team --workdir D:\projects\my-app
```

### 5. 命令行模式（备选）

```bash
python main.py
```

## CLI 界面

```
  ███╗   ███╗ █████╗  ██████╗██████╗ ██╗██████╗ 
  ████╗ ████║██╔══██╗██╔════╝██╔══██╗██║██╔══██╗
  ██╔████╔██║███████║██║     ██████╔╝██║██║  ██║
  ██║╚██╔╝██║██╔══██║██║     ██╔══██╗██║██║  ██║
  ██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║██║██████╔╝
  ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝ 

  Multi-Agent Team CLI  v1.0.0
  工作目录：D:\projects\my-app
  后端地址：http://localhost:8000
  ● 已连接

────────────────────────────────────────────────────────────────────────
ℹ️  输入你的需求，按 Enter 发送...

> 创建一个 Python 博客项目
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/exit`, `/quit`, `/q` | 退出程序 |
| `/clear`, `/cls` | 清屏 |

## CLI 参数

| 参数 | 说明 |
|------|------|
| `--host <hostname>` | 指定后端 API 地址 |
| `--workdir <directory>` | 指定工作目录 |
| `--help`, `-h` | 显示帮助 |

## 技术栈

- **LangChain** - Agent 框架
- **MCP** - Agent 间通信协议
- **FastAPI** - 后端 API 服务器
- **DeepSeek API** - LLM 服务
- **Python 3.12+** - 运行环境
- **Node.js 16+** - CLI 运行环境

## 项目结构

```
Agent_team/
├── main.py                 # Python 命令行入口
├── server.py               # FastAPI 服务器
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量
│
├── cli/                    # Node.js CLI
│   ├── src/
│   │   └── index.js        # CLI 主程序
│   ├── package.json
│   └── README.md
│
├── src/
│   ├── agents/             # Agent 定义 (15 个)
│   │   ├── base_agent.py   # 基类
│   │   ├── director.py     # 项目总监
│   │   ├── tech_lead.py    # 研发效能组长
│   │   ├── frontend_dev.py # 前端开发
│   │   ├── backend_dev.py  # 后端开发
│   │   ├── product_manager.py
│   │   ├── architect.py
│   │   ├── data_engineer.py
│   │   ├── ui_designer.py
│   │   ├── tester.py
│   │   ├── bug_fixer.py
│   │   ├── security_auditor.py
│   │   ├── performance_optimizer.py
│   │   ├── devops.py
│   │   ├── technical_writer.py
│   │   └── code_reviewer.py
│   │
│   ├── mcp/                # MCP 通信层
│   │   ├── messages.py     # 消息模型
│   │   └── bus.py          # 消息总线
│   │
│   ├── memory/             # 记忆系统
│   │   └── session.py      # 会话记忆
│   │
│   ├── tools/              # 工具函数
│   │   ├── file_tools.py   # 文件操作
│   │   └── command_tools.py # 命令执行
│   │
│   ├── cli/                # CLI 执行器
│   │   └── executor.py
│   │
│   └── config/             # 配置
│       ├── settings.py     # 设置
│       └── prompts.py      # 提示词
│
└── examples/               # 示例脚本
```

## MCP 通信

Agent 之间通过 MCP (Model Context Protocol) 进行通信：

- **MessageBus** - 消息总线，管理所有通信
- **Message** - 消息模型，包含类型、优先级、内容
- **TaskPayload** - 任务负载
- **ResponsePayload** - 响应负载

## 核心功能

### 1. 会话记忆系统

- 保存对话历史，支持多轮对话
- 记录任务上下文
- 跟踪文件操作记录

### 2. 文件操作

- 自动创建文件
- 修改现有文件（需确认）
- 删除文件（需确认）

### 3. 命令执行

- 运行 shell 命令（需确认）
- 支持超时控制
- 捕获输出和错误

### 4. 团队协作

- 项目总监统一协调
- Agent 间通过消息总线通信
- 任务逐级派发

## API 接口

### HTTP API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/team` | GET | 获取团队状态 |
| `/chat` | POST | 发送消息 |
| `/execute` | POST | 执行操作 |

### WebSocket

| 端点 | 说明 |
|------|------|
| `/ws` | 实时状态推送 |

## 使用示例

### 创建项目

```
> 创建一个 Python 博客项目

📋 创建文件：backend/main.py
✅ 已创建 backend/main.py
📋 创建文件：backend/requirements.txt
✅ 已创建 backend/requirements.txt
📋 创建文件：frontend/package.json
✅ 已创建 frontend/package.json

🤖 Agent: 博客项目已创建完成！
  - 后端使用 FastAPI
  - 前端使用 Vue 3
  - 数据库使用 SQLite
```

### 添加功能

```
> 给项目添加用户登录功能

📋 创建文件：backend/auth.py
✅ 已创建 backend/auth.py
📋 运行命令：pip install python-jose
✅ 已完成

🤖 Agent: 用户登录功能已添加
```

## 后续计划

- [ ] 多实例开发组（前后端多 Agent 并行开发）
- [ ] 更强大的 MCP 通信（持久化、消息路由）
- [ ] 长期记忆系统（向量数据库）
- [ ] 更多内置工具
- [ ] Web UI 界面

## License

MIT
