"""MCP Server - 将工具封装为 MCP 服务"""
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.lifecycle import lifespan
import asyncio
import json

from src.tools import FileTools, CommandTools


class MCPToolsServer:
    """MCP 工具服务器"""

    def __init__(self):
        self.server = Server("tools-server")
        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        self._setup_handlers()

    def _setup_handlers(self):
        """设置工具处理器"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出所有可用工具"""
            return [
                Tool(
                    name="read_file",
                    description="读取文件内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径（相对或绝对路径）",
                            },
                            "encoding": {
                                "type": "string",
                                "description": "文件编码，默认 utf-8",
                                "default": "utf-8",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="write_file",
                    description="创建或覆盖文件内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径",
                            },
                            "content": {
                                "type": "string",
                                "description": "文件内容",
                            },
                            "encoding": {
                                "type": "string",
                                "description": "文件编码，默认 utf-8",
                                "default": "utf-8",
                            },
                        },
                        "required": ["file_path", "content"],
                    },
                ),
                Tool(
                    name="append_file",
                    description="追加内容到文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径",
                            },
                            "content": {
                                "type": "string",
                                "description": "追加的内容",
                            },
                        },
                        "required": ["file_path", "content"],
                    },
                ),
                Tool(
                    name="file_exists",
                    description="检查文件是否存在",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="delete_file",
                    description="删除文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="create_directory",
                    description="创建目录",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dir_path": {
                                "type": "string",
                                "description": "目录路径",
                            },
                        },
                        "required": ["dir_path"],
                    },
                ),
                Tool(
                    name="delete_directory",
                    description="删除目录",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dir_path": {
                                "type": "string",
                                "description": "目录路径",
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "是否递归删除",
                                "default": False,
                            },
                        },
                        "required": ["dir_path"],
                    },
                ),
                Tool(
                    name="list_directory",
                    description="列出目录内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dir_path": {
                                "type": "string",
                                "description": "目录路径",
                            },
                        },
                        "required": ["dir_path"],
                    },
                ),
                Tool(
                    name="copy_file",
                    description="复制文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "src": {
                                "type": "string",
                                "description": "源文件路径",
                            },
                            "dst": {
                                "type": "string",
                                "description": "目标文件路径",
                            },
                        },
                        "required": ["src", "dst"],
                    },
                ),
                Tool(
                    name="move_file",
                    description="移动文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "src": {
                                "type": "string",
                                "description": "源文件路径",
                            },
                            "dst": {
                                "type": "string",
                                "description": "目标文件路径",
                            },
                        },
                        "required": ["src", "dst"],
                    },
                ),
                Tool(
                    name="get_file_size",
                    description="获取文件大小（字节）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="get_file_extension",
                    description="获取文件扩展名",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "文件路径",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="search_files",
                    description="搜索文件",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dir_path": {
                                "type": "string",
                                "description": "搜索目录",
                            },
                            "pattern": {
                                "type": "string",
                                "description": "文件名模式（如 *.py）",
                                "default": "*",
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "是否递归搜索",
                                "default": False,
                            },
                        },
                        "required": ["dir_path"],
                    },
                ),
                Tool(
                    name="run_command",
                    description="执行系统命令",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "要执行的命令",
                            },
                            "cwd": {
                                "type": "string",
                                "description": "工作目录（可选）",
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "超时时间（秒）",
                                "default": 60,
                            },
                        },
                        "required": ["command"],
                    },
                ),
                Tool(
                    name="get_current_directory",
                    description="获取当前工作目录",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict | None) -> list[TextContent]:
            """调用工具"""
            try:
                result = await self._execute_tool(name, arguments or {})
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]

    async def _execute_tool(self, name: str, arguments: dict) -> Any:
        """执行工具"""
        if name == "read_file":
            return self.file_tools.read_file(
                arguments["file_path"],
                arguments.get("encoding", "utf-8")
            )
        elif name == "write_file":
            success = self.file_tools.write_file(
                arguments["file_path"],
                arguments["content"],
                arguments.get("encoding", "utf-8")
            )
            return {"success": success}
        elif name == "append_file":
            success = self.file_tools.append_file(
                arguments["file_path"],
                arguments["content"]
            )
            return {"success": success}
        elif name == "file_exists":
            return self.file_tools.file_exists(arguments["file_path"])
        elif name == "delete_file":
            return {"success": self.file_tools.delete_file(arguments["file_path"])}
        elif name == "create_directory":
            return {"success": self.file_tools.create_directory(arguments["dir_path"])}
        elif name == "delete_directory":
            return {"success": self.file_tools.delete_directory(
                arguments["dir_path"],
                arguments.get("recursive", False)
            )}
        elif name == "list_directory":
            return self.file_tools.list_directory(arguments["dir_path"])
        elif name == "copy_file":
            return {"success": self.file_tools.copy_file(arguments["src"], arguments["dst"])}
        elif name == "move_file":
            return {"success": self.file_tools.move_file(arguments["src"], arguments["dst"])}
        elif name == "get_file_size":
            return self.file_tools.get_file_size(arguments["file_path"])
        elif name == "get_file_extension":
            return self.file_tools.get_file_extension(arguments["file_path"])
        elif name == "search_files":
            return self.file_tools.search_files(
                arguments["dir_path"],
                arguments.get("pattern", "*"),
                arguments.get("recursive", False)
            )
        elif name == "run_command":
            returncode, stdout, stderr = self.command_tools.run_command(
                arguments["command"],
                cwd=arguments.get("cwd"),
                timeout=arguments.get("timeout", 60)
            )
            return {
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        elif name == "get_current_directory":
            return self.command_tools.get_current_directory()
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def run(self):
        """运行 MCP 服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    """主入口"""
    server = MCPToolsServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
