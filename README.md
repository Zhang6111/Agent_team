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

## 快速开始

### 方式一：Python 命令行（基础版）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
# 编辑 .env 文件，设置 DEEPSEEK_API_KEY

# 3. 运行
python main.py
```

### 方式二：Node.js TUI 界面（推荐）

```bash
# 1. 启动 Python 后端
python server.py

# 2. 安装 Node.js 依赖
cd cli
npm install

# 3. 启动 TUI 界面
node src/index.js
```

连接远程服务器：
```bash
node src/index.js --host your-server-ip
```

## 可用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/exit` | 退出程序 |
| `/team` | 查看团队成员 |

## 技术栈

- **LangChain** - Agent 框架
- **MCP** - Agent 间通信协议
- **DeepSeek API** - LLM 服务
- **Python 3.12+** - 运行环境

## 项目结构

```
Agent_team/
├── main.py                 # 主入口
├── requirements.txt        # 依赖列表
├── .env                    # 环境变量
│
├── src/
│   ├── agents/             # Agent 定义
│   │   ├── base_agent.py   # 基类
│   │   ├── director.py     # 项目总监
│   │   ├── product_manager.py
│   │   ├── architect.py
│   │   ├── tech_lead.py
│   │   ├── frontend_dev.py
│   │   ├── backend_dev.py
│   │   ├── tester.py
│   │   └── devops.py
│   │
│   ├── mcp/                # MCP 通信层
│   │   ├── messages.py     # 消息模型
│   │   └── bus.py          # 消息总线
│   │
│   ├── tools/              # 工具函数
│   │   ├── file_tools.py   # 文件操作
│   │   └── command_tools.py # 命令执行
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

## 后续计划

- [ ] 多实例开发组（前后端多 Agent 并行开发）
- [ ] 更强大的 MCP 通信（持久化、消息路由）
- [ ] Agent 记忆系统（长期记忆、上下文管理）
- [ ] 工具增强（更多内置工具）
- [ ] Web UI 界面
- [ ] API 服务模式

## License

MIT
