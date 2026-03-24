"""CLI 执行器 - 解析并执行 Agent 的操作指令"""
import os
import json
import subprocess
from typing import Optional, Any
from pathlib import Path
from enum import Enum


class ActionType(Enum):
    """操作类型"""
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    RUN_COMMAND = "run_command"
    READ_FILE = "read_file"
    LIST_DIR = "list_dir"
    MESSAGE = "message"  # 仅显示消息


class CLIExecutor:
    """
    CLI 执行器
    
    解析 Agent 的操作指令并执行
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化执行器

        Args:
            base_dir: 基础工作目录，默认为当前目录
        """
        self.base_dir = base_dir or os.getcwd()
        self.pending_actions: list[dict] = []
        self.executed_actions: list[dict] = []

    def parse_agent_response(self, response: str) -> list[dict]:
        """
        解析 Agent 响应，提取操作指令

        Agent 响应格式示例：
        ```json
        {
            "actions": [
                {"type": "create_file", "path": "main.py", "content": "..."},
                {"type": "run_command", "command": "python main.py"}
            ],
            "message": "任务完成"
        }
        ```

        Args:
            response: Agent 响应

        Returns:
            操作列表
        """
        actions = []
        
        # 尝试提取 JSON
        try:
            # 查找 JSON 块
            if "```json" in response:
                start = response.index("```json") + 7
                end = response.index("```", start)
                json_str = response[start:end].strip()
                data = json.loads(json_str)
                actions = data.get("actions", [])
            elif response.strip().startswith("{"):
                # 直接是 JSON
                data = json.loads(response)
                actions = data.get("actions", [])
        except (json.JSONDecodeError, ValueError):
            # 不是 JSON 格式，返回原始消息
            actions = [{"type": "message", "content": response}]
        
        return actions

    def execute_action(
        self, action: dict, auto_confirm: bool = False
    ) -> tuple[bool, Any]:
        """
        执行单个操作

        Args:
            action: 操作字典
            auto_confirm: 是否自动确认

        Returns:
            (成功标志，结果)
        """
        action_type = action.get("type")
        
        try:
            if action_type == ActionType.CREATE_FILE.value:
                return self._create_file(action, auto_confirm)
            elif action_type == ActionType.MODIFY_FILE.value:
                return self._modify_file(action, auto_confirm)
            elif action_type == ActionType.DELETE_FILE.value:
                return self._delete_file(action, auto_confirm)
            elif action_type == ActionType.RUN_COMMAND.value:
                return self._run_command(action, auto_confirm)
            elif action_type == ActionType.READ_FILE.value:
                return self._read_file(action)
            elif action_type == ActionType.LIST_DIR.value:
                return self._list_dir(action)
            elif action_type == ActionType.MESSAGE.value:
                return self._show_message(action)
            else:
                return False, f"未知操作类型：{action_type}"
        except Exception as e:
            return False, f"执行失败：{str(e)}"

    def _create_file(self, action: dict, auto_confirm: bool = False) -> tuple[bool, Any]:
        """创建文件"""
        path = action.get("path")
        content = action.get("content", "")
        
        if not path:
            return False, "缺少文件路径"
        
        # 构建完整路径
        full_path = os.path.join(self.base_dir, path)
        
        # 确认
        if not auto_confirm:
            print(f"\n📝 创建文件：{path}")
            print(f"   大小：{len(content)} 字节")
        
        # 创建目录
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 写入文件
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return True, f"文件已创建：{full_path}"

    def _modify_file(self, action: dict, auto_confirm: bool = False) -> tuple[bool, Any]:
        """修改文件"""
        path = action.get("path")
        content = action.get("content")
        diff = action.get("diff")
        
        if not path:
            return False, "缺少文件路径"
        
        full_path = os.path.join(self.base_dir, path)
        
        if not os.path.exists(full_path):
            return False, f"文件不存在：{path}"
        
        # 确认
        if not auto_confirm:
            print(f"\n✏️  修改文件：{path}")
            if diff:
                print(f"   变更：\n{diff}")
        
        # 写入新内容
        if content:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        return True, f"文件已修改：{full_path}"

    def _delete_file(self, action: dict, auto_confirm: bool = False) -> tuple[bool, Any]:
        """删除文件"""
        path = action.get("path")
        
        if not path:
            return False, "缺少文件路径"
        
        full_path = os.path.join(self.base_dir, path)
        
        if not os.path.exists(full_path):
            return False, f"文件不存在：{path}"
        
        # 确认
        if not auto_confirm:
            print(f"\n🗑️  删除文件：{path}")
        
        os.remove(full_path)
        return True, f"文件已删除：{full_path}"

    def _run_command(
        self, action: dict, auto_confirm: bool = False
    ) -> tuple[bool, Any]:
        """运行命令"""
        command = action.get("command")
        cwd = action.get("cwd", self.base_dir)
        timeout = action.get("timeout", 60)
        
        if not command:
            return False, "缺少命令"
        
        # 确认
        if not auto_confirm:
            print(f"\n▶️  运行命令：{command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                return True, output
            else:
                return False, f"命令执行失败：\n{output}"
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, f"命令执行异常：{str(e)}"

    def _read_file(self, action: dict) -> tuple[bool, Any]:
        """读取文件"""
        path = action.get("path")
        
        if not path:
            return False, "缺少文件路径"
        
        full_path = os.path.join(self.base_dir, path)
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"读取失败：{str(e)}"

    def _list_dir(self, action: dict) -> tuple[bool, Any]:
        """列出目录"""
        path = action.get("path", ".")
        full_path = os.path.join(self.base_dir, path)
        
        try:
            items = os.listdir(full_path)
            return True, items
        except Exception as e:
            return False, f"列出目录失败：{str(e)}"

    def _show_message(self, action: dict) -> tuple[bool, Any]:
        """显示消息"""
        content = action.get("content", "")
        print(f"\n{content}")
        return True, content

    def execute_actions(
        self, actions: list[dict], auto_confirm: bool = False
    ) -> list[dict]:
        """
        执行一系列操作

        Args:
            actions: 操作列表
            auto_confirm: 是否自动确认

        Returns:
            执行结果列表
        """
        results = []
        
        for action in actions:
            action_type = action.get("type", "unknown")
            success, result = self.execute_action(action, auto_confirm)
            
            results.append({
                "type": action_type,
                "success": success,
                "result": result,
            })
            
            self.executed_actions.append({
                "action": action,
                "success": success,
                "result": result,
            })
        
        return results

    def get_execution_summary(self) -> dict:
        """获取执行摘要"""
        total = len(self.executed_actions)
        success = sum(1 for a in self.executed_actions if a["success"])
        
        return {
            "total": total,
            "success": success,
            "failed": total - success,
            "actions": self.executed_actions,
        }

    def reset(self) -> None:
        """重置执行记录"""
        self.pending_actions.clear()
        self.executed_actions.clear()
