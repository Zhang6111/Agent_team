"""多 Agent 团队 - 交互式命令行工具（手动模式）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents import (
    FrontendDeveloperAgent,
    BackendDeveloperAgent,
    ProductManagerAgent,
    ArchitectAgent,
    TesterAgent,
    DevOpsAgent,
    UIDesignerAgent,
    DataEngineerAgent,
    CodeReviewerAgent,
    SecurityAuditorAgent,
    PerformanceOptimizerAgent,
    TechnicalWriterAgent,
)
from src.config import settings
from src.memory import session_memory


AGENTS = [
    ("1", "ProductManager", "产品经理 - 需求分析、PRD输出", ProductManagerAgent),
    ("2", "Architect", "架构师 - 技术架构设计", ArchitectAgent),
    ("3", "DataEngineer", "数据工程师 - 数据库设计", DataEngineerAgent),
    ("4", "UIDesigner", "UI设计师 - 页面布局、样式规范", UIDesignerAgent),
    ("5", "FrontendDev", "前端开发 - 前端实现", FrontendDeveloperAgent),
    ("6", "BackendDev", "后端开发 - 后端实现", BackendDeveloperAgent),
    ("7", "CodeReviewer", "代码评审 - 代码审查", CodeReviewerAgent),
    ("8", "Tester", "测试工程师 - 功能测试", TesterAgent),
    ("9", "SecurityAuditor", "安全审计 - 漏洞扫描", SecurityAuditorAgent),
    ("0", "PerformanceOptimizer", "性能优化 - 性能调优", PerformanceOptimizerAgent),
    ("-", "DevOps", "运维工程师 - 部署配置", DevOpsAgent),
    ("=", "TechnicalWriter", "技术文档 - 文档生成", TechnicalWriterAgent),
]

agent_instances = {}
current_agent_key = "1"


def print_banner():
    print("\n" + "=" * 60)
    print("  多 Agent 开发团队 - 手动模式")
    print("=" * 60)
    print("\n📋 可用 Agent (数字键快速切换)：")
    for key, name, desc, _ in AGENTS:
        marker = " ◄" if key == current_agent_key else ""
        print(f"   [{key}] {name} - {desc}{marker}")
    print("\n命令：")
    print("  1-9, 0, -, =   切换 Agent")
    print("  /help          显示帮助")
    print("  /list          列出所有 Agent")
    print("  /exit          退出程序")
    print("-" * 60)


def print_help():
    print("\n📖 使用说明：")
    print("  1. 按数字键切换到对应的 Agent")
    print("  2. 直接输入消息与当前 Agent 对话")
    print("  3. 每个 Agent 有自己的专业领域")
    print("\n💡 示例：")
    print("  - 切换到后端开发: 按 6")
    print("  - 让产品经理分析需求: 按 1，然后输入需求")
    print("  - 让前端开发写页面: 按 5，然后描述页面需求")
    print()


def get_current_agent():
    global current_agent_key
    for key, name, desc, cls in AGENTS:
        if key == current_agent_key:
            if name not in agent_instances:
                if name in ["FrontendDev", "BackendDev"]:
                    agent_instances[name] = cls(name=name, memory=session_memory)
                else:
                    agent_instances[name] = cls(memory=session_memory)
            return name, agent_instances[name]
    return None, None


def switch_agent(key):
    global current_agent_key
    for k, name, desc, _ in AGENTS:
        if k == key:
            current_agent_key = key
            print(f"\n🔄 已切换到: {name} ({desc})")
            return True
    print(f"\n❌ 无效的 Agent 键: {key}")
    return False


def main():
    try:
        settings.validate()
    except ValueError as e:
        print(f"\n❌ 配置错误：{e}")
        print("\n请在 .env 文件中设置 DEEPSEEK_API_KEY")
        sys.exit(1)

    print_banner()

    while True:
        try:
            current_name, current_agent = get_current_agent()
            user_input = input(f"\n[{current_name}] 你：").strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                cmd = user_input.lower()
                if cmd in ["/exit", "/quit", "/q"]:
                    print("\n👋 再见！\n")
                    break
                elif cmd == "/help":
                    print_help()
                    continue
                elif cmd == "/list":
                    print_banner()
                    continue
                elif cmd == "/memory":
                    print("\n🧠 当前记忆：")
                    print(session_memory.get_context_summary())
                    continue
                elif cmd == "/clear":
                    session_memory.clear_history()
                    print("\n🧹 记忆已清空")
                    continue
                else:
                    print(f"\n❓ 未知命令：{user_input}，输入 /help 查看帮助")
                    continue

            if len(user_input) == 1 and user_input in [k for k, _, _, _ in AGENTS]:
                switch_agent(user_input)
                continue

            session_memory.add_user_message(user_input)
            if not session_memory.current_task:
                session_memory.start_task(user_input)

            print(f"\n[{current_name}]：", end="", flush=True)
            response = current_agent.invoke(user_input)
            print(response)

            session_memory.add_ai_message(response)

        except KeyboardInterrupt:
            print("\n\n👋 再见！\n")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")


if __name__ == "__main__":
    main()
