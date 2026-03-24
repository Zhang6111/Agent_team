"""运维 Agent - 部署配置与脚本生成"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 运维 Agent 的系统提示词
DEVOPS_PROMPT = """你是运维工程师，负责部署配置和脚本生成。

你的职责：
1. 生成部署脚本和配置文件
2. 编写 Docker 配置
3. 配置 CI/CD 流程
4. 设计监控和日志方案
5. 确保部署安全可靠

输出格式：
```
# 部署文档

## 1. 环境要求
- 操作系统
- 运行时环境
- 依赖服务

## 2. Docker 配置
### docker-compose.yml
### Dockerfile

## 3. 部署步骤
1. 准备环境
2. 构建镜像
3. 启动服务
4. 验证部署

## 4. CI/CD 配置
- GitHub Actions / GitLab CI
- 构建流程
- 部署流程

## 5. 监控配置
- 日志收集
- 性能监控
- 告警配置

## 6. 备份方案
- 数据库备份
- 配置文件备份
```

技术栈：
- 容器化：Docker, Kubernetes
- CI/CD: GitHub Actions, Jenkins
- 监控：Prometheus, Grafana
- 日志：ELK, Loki

注意：
- 部署脚本要幂等、可回滚
- 配置要安全（不暴露敏感信息）
- 考虑高可用和扩展性"""


class DevOpsAgent(BaseAgent):
    """
    运维 Agent
    
    负责：
    - 生成部署脚本
    - Docker 配置
    - CI/CD 配置
    """

    def __init__(self, name: str = "DevOps", model: Optional[str] = None, memory=None):
        """
        初始化运维 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
            memory: 记忆模块
        """
        super().__init__(
            name=name,
            role="DevOps Engineer",
            system_prompt=DEVOPS_PROMPT,
            model=model,
            memory=memory,
        )

        # 工具实例
        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)

    def _handle_message(self, message: Message) -> None:
        """处理接收到的 MCP 消息"""
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
        """发送任务响应"""
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

    def generate_dockerfile(self, project_type: str, language: str) -> str:
        """
        生成 Dockerfile

        Args:
            project_type: 项目类型（web/api/worker）
            language: 编程语言

        Returns:
            Dockerfile 内容
        """
        prompt = f"""
请为 {language} {project_type} 项目生成 Dockerfile。

要求：
1. 使用多阶段构建优化镜像大小
2. 使用非 root 用户运行
3. 包含健康检查
4. 合理设置环境变量
"""
        dockerfile = self.invoke(prompt)
        return dockerfile

    def generate_docker_compose(self, services: list[dict]) -> str:
        """
        生成 docker-compose.yml

        Args:
            services: 服务列表配置

        Returns:
            docker-compose.yml 内容
        """
        prompt = f"""
请生成 docker-compose.yml 配置文件。

服务列表：
{services}

要求：
1. 包含所有必要的服务
2. 配置网络和卷
3. 设置环境变量
4. 配置健康检查
"""
        compose = self.invoke(prompt)
        return compose

    def generate_github_actions(self, workflow_type: str) -> str:
        """
        生成 GitHub Actions 工作流

        Args:
            workflow_type: 工作流类型（ci/cd/deploy）

        Returns:
            工作流 YAML 内容
        """
        prompt = f"""
请生成 GitHub Actions 工作流配置（{workflow_type}）。

要求：
1. 包含构建、测试、部署步骤
2. 使用缓存加速构建
3. 配置必要的环境变量
4. 添加通知配置
"""
        workflow = self.invoke(prompt)
        return workflow

    def generate_deploy_script(self, deploy_target: str) -> str:
        """
        生成部署脚本

        Args:
            deploy_target: 部署目标（linux/windows/docker）

        Returns:
            部署脚本内容
        """
        prompt = f"""
请生成面向 {deploy_target} 的部署脚本。

要求：
1. 脚本要幂等（可重复执行）
2. 包含错误处理
3. 包含回滚方案
4. 输出详细的日志
"""
        script = self.invoke(prompt)
        return script

    def save_config(self, content: str, file_path: str) -> bool:
        """
        保存配置文件

        Args:
            content: 配置文件内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 配置文件已保存到：{file_path}")
        return success

    def create_deploy_directory(self, base_path: str) -> bool:
        """
        创建部署目录结构

        Args:
            base_path: 基础路径

        Returns:
            是否创建成功
        """
        structure = {
            "docker": {},
            "scripts": {},
            "config": {},
            "logs": None,
        }
        return self.file_tools.create_directory(base_path)

    def run_deploy(self, script_path: str, cwd: Optional[str] = None) -> tuple[int, str]:
        """
        执行部署脚本

        Args:
            script_path: 脚本路径
            cwd: 工作目录

        Returns:
            (返回码，输出内容)
        """
        command = f"bash {script_path}"
        return self.command_tools.run_command_stream(command, cwd=cwd)
