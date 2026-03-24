"""多 Agent 团队 - 项目总监命令行工具"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents import ProjectDirector
from src.config import settings


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 60)
    print("  多 Agent 开发团队 - 项目总监")
    print("=" * 60)
    print("\n你好，我是项目总监，负责协调团队完成你的项目。")
    print("输入你的需求，我会帮你分析并完成。")
    print("\n命令：")
    print("  /help  - 显示帮助")
    print("  /exit  - 退出程序")
    print("-" * 60)


def print_help():
    """打印帮助信息"""
    print("\n可用命令：")
    print("  /help   - 显示此帮助信息")
    print("  /exit   - 退出程序")
    print("\n如何提问：")
    print("  直接输入你的需求即可，例如：")
    print("  - '帮我创建一个 Python 项目，实现待办事项管理'")
    print("  - '分析一下这个需求：做一个电商网站'")
    print("  - '帮我写一个快速排序算法'")
    print()


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
                else:
                    print(f"\n未知命令：{user_input}，输入 /help 查看帮助")
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
