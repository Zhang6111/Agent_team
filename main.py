"""多 Agent 团队 - 项目总监命令行工具"""
import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents import (
    ProjectDirector,
    TechLeadAgent,
    FrontendDeveloperAgent,
    BackendDeveloperAgent,
    ProductManagerAgent,
    ArchitectAgent,
    TesterAgent,
    DevOpsAgent,
    UIDesignerAgent,
    DataEngineerAgent,
    CodeReviewerAgent,
    BugFixerAgent,
    SecurityAuditorAgent,
    PerformanceOptimizerAgent,
    TechnicalWriterAgent,
)
from src.mcp import message_bus
from src.config import settings
from src.memory import session_memory


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 60)
    print("  多 Agent 开发团队")
    print("=" * 60)
    print("\n👋 你好，我是项目总监，负责协调团队完成你的项目。")
    print("\n📋 团队成员：")
    print("   【总控调度层】")
    print("     - 项目总监：用户需求接口、任务分发")
    print("   【产品设计层】")
    print("     - 产品经理：需求分析、PRD 输出")
    print("     - UI 设计师：页面布局、样式规范")
    print("   【架构数据层】")
    print("     - 架构师：技术架构设计")
    print("     - 数据工程师：数据库设计")
    print("   【研发执行层】")
    print("     - 研发效能组长：统筹开发任务")
    print("     - 前端开发：页面实现")
    print("     - 后端开发：接口实现")
    print("     - 代码评审：代码审查")
    print("   【质量保障层】")
    print("     - 测试工程师：功能测试")
    print("     - 故障修复：Bug 修复")
    print("     - 安全审计：漏洞扫描")
    print("     - 性能优化：性能调优")
    print("   【工程交付层】")
    print("     - 运维工程师：部署配置")
    print("     - 技术文档：文档生成")
    print("\n💬 输入你的需求，我会帮你分析并完成。")
    print("\n命令：")
    print("  /help  - 显示帮助")
    print("  /exit  - 退出程序")
    print("  /team  - 查看团队成员")
    print("-" * 60)


def print_help():
    """打印帮助信息"""
    print("\n📖 可用命令：")
    print("  /help   - 显示此帮助信息")
    print("  /exit   - 退出程序")
    print("  /team   - 查看团队成员")
    print("\n💡 如何提问：")
    print("  直接输入你的需求即可，例如：")
    print("  - '帮我创建一个 Python 项目，实现待办事项管理'")
    print("  - '分析一下这个需求：做一个电商网站'")
    print("  - '帮我写一个快速排序算法'")
    print("  - '创建一个简单的登录页面'")
    print()


def init_team(director: ProjectDirector) -> None:
    """初始化团队"""
    print("\n🔧 正在组建团队...")
    
    # 产品设计层
    product_manager = ProductManagerAgent(memory=session_memory)
    director.add_team_member("ProductManager", product_manager)
    print("   ✓ 产品经理 已就位")
    
    ui_designer = UIDesignerAgent(memory=session_memory)
    director.add_team_member("UIDesigner", ui_designer)
    print("   ✓ UI 设计师 已就位")
    
    # 架构数据层
    architect = ArchitectAgent(memory=session_memory)
    director.add_team_member("Architect", architect)
    print("   ✓ 架构师 已就位")
    
    data_engineer = DataEngineerAgent(memory=session_memory)
    director.add_team_member("DataEngineer", data_engineer)
    print("   ✓ 数据工程师 已就位")
    
    # 研发执行层
    tech_lead = TechLeadAgent(memory=session_memory)
    director.add_team_member("TechLead", tech_lead)
    print("   ✓ 研发效能组长 已就位")
    
    frontend_dev = FrontendDeveloperAgent(name="FrontendDev", memory=session_memory)
    tech_lead.add_frontend_dev("FrontendDev", frontend_dev)
    print("   ✓ 前端开发 已就位")
    
    backend_dev = BackendDeveloperAgent(name="BackendDev", memory=session_memory)
    tech_lead.add_backend_dev("BackendDev", backend_dev)
    print("   ✓ 后端开发 已就位")
    
    code_reviewer = CodeReviewerAgent(memory=session_memory)
    director.add_team_member("CodeReviewer", code_reviewer)
    print("   ✓ 代码评审 已就位")
    
    # 质量保障层
    tester = TesterAgent(memory=session_memory)
    director.add_team_member("Tester", tester)
    print("   ✓ 测试工程师 已就位")
    
    bug_fixer = BugFixerAgent(memory=session_memory)
    director.add_team_member("BugFixer", bug_fixer)
    print("   ✓ 故障修复 已就位")
    
    security_auditor = SecurityAuditorAgent(memory=session_memory)
    director.add_team_member("SecurityAuditor", security_auditor)
    print("   ✓ 安全审计 已就位")
    
    performance_optimizer = PerformanceOptimizerAgent(memory=session_memory)
    director.add_team_member("PerformanceOptimizer", performance_optimizer)
    print("   ✓ 性能优化 已就位")
    
    # 工程交付层
    devops = DevOpsAgent(memory=session_memory)
    director.add_team_member("DevOps", devops)
    print("   ✓ 运维工程师 已就位")
    
    technical_writer = TechnicalWriterAgent(memory=session_memory)
    director.add_team_member("TechnicalWriter", technical_writer)
    print("   ✓ 技术文档 已就位")
    
    print("\n✅ 团队组建完成！共 15 名成员\n")


async def run_message_bus():
    """运行消息总线"""
    await message_bus.run()


def main():
    """主函数"""
    # 验证配置
    try:
        settings.validate()
    except ValueError as e:
        print(f"\n❌ 配置错误：{e}")
        print("\n请在 .env 文件中设置 DEEPSEEK_API_KEY")
        sys.exit(1)

    # 创建项目总监（传入记忆系统）
    director = ProjectDirector(memory=session_memory)
    
    # 初始化团队
    init_team(director)

    # 打印欢迎信息
    print_banner()

    # 对话循环
    while True:
        try:
            user_input = input("\n👤 你：").strip()

            if not user_input:
                continue

            # 处理命令
            if user_input.startswith("/"):
                cmd = user_input.lower()
                if cmd in ["/exit", "/quit", "/q"]:
                    print("\n🤖 项目总监：感谢使用，再见！\n")
                    break
                elif cmd == "/help":
                    print_help()
                    continue
                elif cmd == "/team":
                    print(f"\n📋 团队成员：{director.team_members}")
                    continue
                elif cmd == "/memory":
                    # 查看当前记忆
                    print("\n🧠 当前记忆：")
                    print(session_memory.get_context_summary())
                    continue
                elif cmd == "/clear":
                    # 清空记忆
                    session_memory.clear_history()
                    print("\n🧹 记忆已清空")
                    continue
                else:
                    print(f"\n❓ 未知命令：{user_input}，输入 /help 查看帮助")
                    continue

            # 添加到记忆
            session_memory.add_user_message(user_input)
            
            # 如果是第一个消息，设为当前任务
            if not session_memory.current_task:
                session_memory.start_task(user_input)

            # 调用项目总监
            print("\n🤖 项目总监：", end="", flush=True)
            response = director.invoke(user_input)
            print(response)
            
            # 添加到记忆
            session_memory.add_ai_message(response)

        except KeyboardInterrupt:
            print("\n\n🤖 项目总监：感谢使用，再见！\n")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")


if __name__ == "__main__":
    main()
