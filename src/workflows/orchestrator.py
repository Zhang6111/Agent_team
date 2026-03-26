"""任务编排器 - 支持团队协作和工作流"""
from typing import Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import uuid
from datetime import datetime


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    """任务类型"""
    REQUIREMENT = "requirement"      # 需求分析
    DESIGN = "design"                 # 设计
    IMPLEMENTATION = "implementation" # 实现
    REVIEW = "review"                 # 审查
    TEST = "test"                     # 测试
    DEPLOY = "deploy"                 # 部署
    DOCUMENTATION = "documentation"   # 文档


@dataclass
class Task:
    """任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.IMPLEMENTATION
    assignee: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


class WorkflowEngine:
    """工作流引擎 - 编排多 Agent 协作"""

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.listeners: dict[str, list[Callable]] = {}
        self._execution_order: list[str] = []

    def create_task(
        self,
        name: str,
        description: str,
        task_type: TaskType = TaskType.IMPLEMENTATION,
        assignee: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
    ) -> Task:
        """创建任务"""
        task = Task(
            name=name,
            description=description,
            task_type=task_type,
            assignee=assignee,
            dependencies=dependencies or [],
        )
        self.tasks[task.id] = task
        return task

    def create_tasks_from_requirement(self, requirement: str) -> list[Task]:
        """根据需求自动创建任务序列"""
        tasks = []

        task1 = self.create_task(
            name="需求分析",
            description=f"分析需求：{requirement}",
            task_type=TaskType.REQUIREMENT,
            assignee="ProductManager",
        )
        tasks.append(task1)

        task2 = self.create_task(
            name="架构设计",
            description=f"设计技术架构",
            task_type=TaskType.DESIGN,
            assignee="Architect",
            dependencies=[task1.id],
        )
        tasks.append(task2)

        task3 = self.create_task(
            name="UI设计",
            description=f"设计用户界面",
            task_type=TaskType.DESIGN,
            assignee="UIDesigner",
            dependencies=[task1.id],
        )
        tasks.append(task3)

        task4 = self.create_task(
            name="后端开发",
            description=f"实现后端代码",
            task_type=TaskType.IMPLEMENTATION,
            assignee="BackendDev",
            dependencies=[task2.id],
        )
        tasks.append(task4)

        task5 = self.create_task(
            name="前端开发",
            description=f"实现前端代码",
            task_type=TaskType.IMPLEMENTATION,
            assignee="FrontendDev",
            dependencies=[task3.id],
        )
        tasks.append(task5)

        task6 = self.create_task(
            name="代码评审",
            description=f"审查代码质量",
            task_type=TaskType.REVIEW,
            assignee="CodeReviewer",
            dependencies=[task4.id, task5.id],
        )
        tasks.append(task6)

        task7 = self.create_task(
            name="测试",
            description=f"功能测试",
            task_type=TaskType.TEST,
            assignee="Tester",
            dependencies=[task6.id],
        )
        tasks.append(task7)

        task8 = self.create_task(
            name="部署",
            description=f"部署上线",
            task_type=TaskType.DEPLOY,
            assignee="DevOps",
            dependencies=[task7.id],
        )
        tasks.append(task8)

        return tasks

    def get_runnable_tasks(self) -> list[Task]:
        """获取可执行的任务（依赖已满足）"""
        runnable = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                self.tasks.get(dep_id)?.status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            if deps_met:
                runnable.append(task)
        return runnable

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_task_by_assignee(self, assignee: str) -> list[Task]:
        return [t for t in self.tasks.values() if t.assignee == assignee]

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """更新任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = status
        task.result = result
        task.error = error

        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.result = result
        elif status == TaskStatus.FAILED:
            task.completed_at = datetime.now()
            task.error = error

        self._notify(task)

    def _notify(self, task: Task) -> None:
        """通知监听器"""
        if task.assignee in self.listeners:
            for callback in self.listeners[task.assignee]:
                try:
                    callback(task)
                except Exception as e:
                    print(f"[Workflow] 通知失败：{e}")

    def subscribe(self, assignee: str, callback: Callable) -> None:
        """订阅任务通知"""
        if assignee not in self.listeners:
            self.listeners[assignee] = []
        self.listeners[assignee].append(callback)

    def get_progress(self) -> dict:
        """获取工作流进度"""
        total = len(self.tasks)
        if total == 0:
            return {"total": 0, "completed": 0, "running": 0, "progress": 0}

        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)

        return {
            "total": total,
            "completed": completed,
            "running": running,
            "progress": int(completed / total * 100),
        }

    def execute_workflow(
        self,
        execute_callback: Callable[[Task], str],
    ) -> list[dict]:
        """执行工作流"""
        results = []

        while True:
            runnable = self.get_runnable_tasks()
            if not runnable:
                break

            for task in runnable:
                print(f"[Workflow] 执行任务: {task.name} (分配给: {task.assignee})")
                self.update_status(task.id, TaskStatus.RUNNING)

                try:
                    result = execute_callback(task)
                    self.update_status(task.id, TaskStatus.COMPLETED, result)
                    results.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "assignee": task.assignee,
                        "status": "completed",
                        "result": result,
                    })
                except Exception as e:
                    self.update_status(task.id, TaskStatus.FAILED, error=str(e))
                    results.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "assignee": task.assignee,
                        "status": "failed",
                        "error": str(e),
                    })
                    return results

        return results


workflow_engine = WorkflowEngine()
