"""MCP Client - 供 Agent 调用 MCP 工具"""
import asyncio
import json
from typing import Any, Optional


class EmbeddedMCPClient:
    """嵌入式 MCP 客户端 - 直接调用工具不启动独立进程"""

    def __init__(self):
        from src.tools import FileTools, CommandTools
        self.file_tools = FileTools()
        self.command_tools = CommandTools()

    def get_tools_schema(self) -> list[dict]:
        """获取工具 schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "创建或覆盖文件内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"},
                            "content": {"type": "string", "description": "文件内容"}
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "append_file",
                    "description": "追加内容到文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"},
                            "content": {"type": "string", "description": "追加的内容"}
                        },
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "file_exists",
                    "description": "检查文件是否存在",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_directory",
                    "description": "创建目录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "目录路径"}
                        },
                        "required": ["dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出目录内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "目录路径"}
                        },
                        "required": ["dir_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "执行系统命令",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "要执行的命令"},
                            "cwd": {"type": "string", "description": "工作目录"},
                            "timeout": {"type": "integer", "description": "超时时间（秒）"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_directory",
                    "description": "获取当前工作目录",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
        ]

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """
        调用工具（同步版本）

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        args = arguments or {}

        if name == "read_file":
            return self.file_tools.read_file(args.get("file_path", ""))
        elif name == "write_file":
            return {"success": self.file_tools.write_file(args.get("file_path", ""), args.get("content", ""))}
        elif name == "append_file":
            return {"success": self.file_tools.append_file(args.get("file_path", ""), args.get("content", ""))}
        elif name == "file_exists":
            return self.file_tools.file_exists(args.get("file_path", ""))
        elif name == "create_directory":
            return {"success": self.file_tools.create_directory(args.get("dir_path", ""))}
        elif name == "list_directory":
            return self.file_tools.list_directory(args.get("dir_path", ""))
        elif name == "run_command":
            returncode, stdout, stderr = self.command_tools.run_command(
                args.get("command", ""),
                cwd=args.get("cwd"),
                timeout=args.get("timeout", 60)
            )
            return {"returncode": returncode, "stdout": stdout, "stderr": stderr}
        elif name == "get_current_directory":
            return self.command_tools.get_current_directory()
        else:
            raise ValueError(f"Unknown tool: {name}")


embedded_mcp_client = EmbeddedMCPClient()
