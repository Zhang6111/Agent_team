"""项目总监 Agent - 用户交互的唯一接口"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.config import SystemPrompts


# 项目总监的系统提示词
DIRECTOR_PROMPT = """你是一个项目总监，负责与用户直接沟通并协调团队完成项目。

你的职责：
1. 理解用户的项目需求和目标
2. 分析需求并制定项目计划
3. 协调团队成员（产品经理、开发工程师、测试工程师、设计师）完成各自任务
4. 向用户汇报项目进展和结果
5. 确保最终交付物符合用户期望

沟通风格：
- 专业、清晰、有条理
- 主动询问不清楚的需求
- 及时汇报进展

团队成员：
- 产品经理 (ProductManager)：负责需求分析、功能规划
- 开发工程师 (Developer)：负责编写代码、技术实现
- 测试工程师 (Tester)：负责测试、质量保证
- 设计师 (Designer)：负责 UI/UX 设计

当需要团队成员协助时，你会调用相应的 Agent 完成任务，然后整合结果反馈给用户。"""


class ProjectDirector(BaseAgent):
    """
    项目总监 Agent
    
    这是用户直接交互的唯一接口，负责：
    - 理解用户需求
    - 协调团队完成任务
    - 反馈最终结果
    """

    def __init__(self, model: Optional[str] = None):
        """
        初始化项目总监

        Args:
            model: 使用的模型名称，默认使用配置中的 DEFAULT_MODEL
        """
        super().__init__(
            name="项目总监",
            role="Project Director",
            system_prompt=DIRECTOR_PROMPT,
            model=model,
        )

        # 内部团队成员（后续实现）
        self._team_members = {}

    def add_team_member(self, name: str, agent: BaseAgent) -> None:
        """
        添加团队成员

        Args:
            name: 成员名称
            agent: Agent 实例
        """
        self._team_members[name] = agent

    def get_team_member(self, name: str) -> Optional[BaseAgent]:
        """
        获取团队成员

        Args:
            name: 成员名称

        Returns:
            对应的 Agent，如果不存在则返回 None
        """
        return self._team_members.get(name)

    @property
    def team_members(self) -> list:
        """获取所有团队成员名称"""
        return list(self._team_members.keys())

    def delegate_task(self, member_name: str, task: str) -> str:
        """
        委派任务给团队成员

        Args:
            member_name: 成员名称
            task: 任务描述

        Returns:
            成员的响应
        """
        member = self.get_team_member(member_name)
        if not member:
            return f"团队成员 '{member_name}' 不存在"
        return member.invoke(task)
