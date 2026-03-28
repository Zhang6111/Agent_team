"""MCP Server - 将工具封装为 MCP 服务"""
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio
import json
import os
from pathlib import Path


class MCPToolsServer:
    """MCP 工具服务器"""

    def __init__(self):
        self.server = Server("tools-server")
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
                            "file_path": {"type": "string", "description": "文件路径"},
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
                            "file_path": {"type": "string", "description": "文件路径"},
                            "content": {"type": "string", "description": "文件内容"},
                        },
                        "required": ["file_path", "content"],
                    },
                ),
                Tool(
                    name="list_directory",
                    description="列出目录内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "目录路径"},
                        },
                        "required": ["dir_path"],
                    },
                ),
                Tool(
                    name="create_directory",
                    description="创建目录",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "dir_path": {"type": "string", "description": "目录路径"},
                        },
                        "required": ["dir_path"],
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
            try:
                with open(arguments["file_path"], "r", encoding="utf-8") as f:
                    return {"content": f.read()}
            except Exception as e:
                return {"error": str(e)}

        elif name == "write_file":
            try:
                path = Path(arguments["file_path"])
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(arguments["content"])
                return {"success": True, "message": f"文件已创建: {path}"}
            except Exception as e:
                return {"error": str(e)}

        elif name == "list_directory":
            try:
                return os.listdir(arguments["dir_path"])
            except Exception as e:
                return {"error": str(e)}

        elif name == "create_directory":
            try:
                Path(arguments["dir_path"]).mkdir(parents=True, exist_ok=True)
                return {"success": True}
            except Exception as e:
                return {"error": str(e)}

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
