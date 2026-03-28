"""DevOps Agent - 部署、CI/CD、环境配置"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


DEVOPS_PROMPT = """你是经验丰富的 DevOps 工程师，负责系统部署、CI/CD 和环境配置。

你的职责：
1. 编写容器化配置文件（Dockerfile、docker-compose.yml）
2. 配置 CI/CD 流水线
3. 编写部署脚本
4. 配置监控和日志
5. 优化构建和部署效率

工作流程：
1. 分析项目架构，确定部署方案
2. 根据技术栈创建配置文件
3. 编写自动化脚本
4. 测试部署流程

重要原则：
- 根据用户指定的技术栈配置部署方案
- 如果用户未指定，主动询问或根据项目文件判断
- 支持任意技术栈的部署

支持的技术示例：
- 容器化：Docker, Podman, Kubernetes
- CI/CD：GitHub Actions, GitLab CI, Jenkins, CircleCI
- 云平台：AWS, Azure, GCP, 阿里云, 腾讯云
- 配置管理：Ansible, Terraform, Helm
- 监控：Prometheus, Grafana, ELK

可用工具：
- read_file: 读取现有配置
- write_file: 创建配置文件
- list_directory: 查看项目结构
- run_command: 执行构建/部署命令

注意：
- 不要预设技术栈，根据用户需求或项目文件判断
- 执行破坏性命令前需谨慎
- 确保系统在生产环境下稳定运行"""


class DevOpsAgent(BaseAgent):
    """DevOps Agent"""

    def __init__(self, name: str = "DevOps", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="DevOps Engineer",
            system_prompt=DEVOPS_PROMPT,
            model=model,
            memory=memory,
        )

        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        message_bus.subscribe(self.name, self._handle_message)

    def _handle_message(self, message: Message) -> None:
        if message.type == MessageType.TASK and message.receiver == self.name:
            payload = message.content
            if isinstance(payload, dict):
                task_payload = TaskPayload(**payload)
                print(f"\n[新任务] {self.name} 收到：{task_payload.description}")

    def send_response(
        self,
        task_id: str,
        success: bool,
        result: any = None,
        error_message: Optional[str] = None,
    ) -> None:
        payload = ResponsePayload(
            task_id=task_id,
            success=success,
            result=result,
            error_message=error_message,
        )
        message = Message(
            type=MessageType.RESPONSE,
            sender=self.name,
            receiver=None,
            content=payload.model_dump(),
        )
        message_bus.publish_sync(message)

    def create_dockerfile(self, content: str, file_path: str = "Dockerfile") -> bool:
        return self.file_tools.write_file(file_path, content)

    def create_docker_compose(self, content: str, file_path: str = "docker-compose.yml") -> bool:
        return self.file_tools.write_file(file_path, content)

    def run_command(self, command: str, timeout: Optional[int] = None) -> tuple[int, str]:
        return self.command_tools.run_command_stream(command, timeout=timeout)
