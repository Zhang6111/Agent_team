"""MCP Client - 供 Agent 调用 MCP 工具"""
import os
from typing import Any, Optional
from pathlib import Path


class EmbeddedMCPClient:
    """嵌入式 MCP 客户端 - 直接调用工具不启动独立进程"""

    def __init__(self):
        pass

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
                    "name": "get_current_directory",
                    "description": "获取当前工作目录",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
        ]

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """调用工具（同步版本）"""
        args = arguments or {}

        if name == "read_file":
            try:
                with open(args.get("file_path", ""), "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return f"读取文件失败: {e}"

        elif name == "write_file":
            try:
                path = Path(args.get("file_path", ""))
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(args.get("content", ""))
                return f"✓ 文件已创建: {path}"
            except Exception as e:
                return f"写入文件失败: {e}"

        elif name == "append_file":
            try:
                with open(args.get("file_path", ""), "a", encoding="utf-8") as f:
                    f.write(args.get("content", ""))
                return f"✓ 内容已追加"
            except Exception as e:
                return f"追加文件失败: {e}"

        elif name == "file_exists":
            return os.path.exists(args.get("file_path", ""))

        elif name == "create_directory":
            try:
                Path(args.get("dir_path", "")).mkdir(parents=True, exist_ok=True)
                return f"✓ 目录已创建"
            except Exception as e:
                return f"创建目录失败: {e}"

        elif name == "list_directory":
            try:
                return os.listdir(args.get("dir_path", "."))
            except Exception as e:
                return f"列出目录失败: {e}"

        elif name == "get_current_directory":
            return os.getcwd()

        else:
            raise ValueError(f"Unknown tool: {name}")


embedded_mcp_client = EmbeddedMCPClient()
