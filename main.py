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
)
from src.mcp import message_bus
from src.config import settings


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 60)
    print("  多 Agent 开发团队")
    print("=" * 60)
    print("\n👋 你好，我是项目总监，负责协调团队完成你的项目。")
    print("\n📋 团队成员：")
    print("   - 产品经理：需求分析、PRD 输出")
    print("   - 架构师：技术架构设计")
    print("   - 研发效能组长：统筹开发任务")
    print("   - 前端开发工程师：实现页面和交互")
    print("   - 后端开发工程师：实现接口和逻辑")
    print("   - 测试工程师：功能测试、Bug 发现")
    print("   - 运维工程师：部署配置、Docker")
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
    
    # 创建产品经理
    product_manager = ProductManagerAgent()
    director.add_team_member("ProductManager", product_manager)
    print("   ✓ 产品经理 已就位")
    
    # 创建架构师
    architect = ArchitectAgent()
    director.add_team_member("Architect", architect)
    print("   ✓ 架构师 已就位")
    
    # 创建研发效能组长
    tech_lead = TechLeadAgent()
    director.add_team_member("TechLead", tech_lead)
    print("   ✓ 研发效能组长 已就位")
    
    # 创建前端开发
    frontend_dev = FrontendDeveloperAgent(name="FrontendDev")
    tech_lead.add_frontend_dev("FrontendDev", frontend_dev)
    print("   ✓ 前端开发工程师 已就位")
    
    # 创建后端开发
    backend_dev = BackendDeveloperAgent(name="BackendDev")
    tech_lead.add_backend_dev("BackendDev", backend_dev)
    print("   ✓ 后端开发工程师 已就位")
    
    # 创建测试工程师
    tester = TesterAgent()
    director.add_team_member("Tester", tester)
    print("   ✓ 测试工程师 已就位")
    
    # 创建运维工程师
    devops = DevOpsAgent()
    director.add_team_member("DevOps", devops)
    print("   ✓ 运维工程师 已就位")
    
    print("\n✅ 团队组建完成！\n")


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

    # 创建项目总监
    director = ProjectDirector()
    
    # 初始化团队
    init_team(director)

    # 打印欢迎信息
    print_banner()

    # 启动消息总线（后台运行）
    # asyncio.create_task(run_message_bus())

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
                else:
                    print(f"\n❓ 未知命令：{user_input}，输入 /help 查看帮助")
                    continue

            # 调用项目总监
            print("\n🤖 项目总监：", end="", flush=True)
            response = director.invoke(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\n\n🤖 项目总监：感谢使用，再见！\n")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")


if __name__ == "__main__":
    main()
