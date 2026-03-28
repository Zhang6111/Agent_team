"""文件操作工具 - LangChain Tool 封装"""
import os
import shutil
from pathlib import Path
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool


class ReadFileInput(BaseModel):
    file_path: str = Field(description="文件路径")


class WriteFileInput(BaseModel):
    file_path: str = Field(description="文件路径")
    content: str = Field(description="文件内容")


class AppendFileInput(BaseModel):
    file_path: str = Field(description="文件路径")
    content: str = Field(description="追加内容")


class CreateDirectoryInput(BaseModel):
    dir_path: str = Field(description="目录路径")


class ListDirectoryInput(BaseModel):
    dir_path: str = Field(description="目录路径")


class DeleteFileInput(BaseModel):
    file_path: str = Field(description="文件路径")


class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "读取文件内容。参数: file_path - 文件路径"
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"读取文件失败: {e}"


class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = "创建或覆盖文件。参数: file_path - 文件路径, content - 文件内容"
    args_schema: Type[BaseModel] = WriteFileInput

    def _run(self, file_path: str, content: str) -> str:
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✓ 文件已创建: {file_path}"
        except Exception as e:
            return f"写入文件失败: {e}"


class AppendFileTool(BaseTool):
    name: str = "append_file"
    description: str = "追加内容到文件末尾。参数: file_path - 文件路径, content - 追加内容"
    args_schema: Type[BaseModel] = AppendFileInput

    def _run(self, file_path: str, content: str) -> str:
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content)
            return f"✓ 内容已追加到: {file_path}"
        except Exception as e:
            return f"追加文件失败: {e}"


class CreateDirectoryTool(BaseTool):
    name: str = "create_directory"
    description: str = "创建目录。参数: dir_path - 目录路径"
    args_schema: Type[BaseModel] = CreateDirectoryInput

    def _run(self, dir_path: str) -> str:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return f"✓ 目录已创建: {dir_path}"
        except Exception as e:
            return f"创建目录失败: {e}"


class ListDirectoryTool(BaseTool):
    name: str = "list_directory"
    description: str = "列出目录内容。参数: dir_path - 目录路径"
    args_schema: Type[BaseModel] = ListDirectoryInput

    def _run(self, dir_path: str) -> str:
        try:
            items = os.listdir(dir_path)
            return "\n".join(items)
        except Exception as e:
            return f"列出目录失败: {e}"


class DeleteFileTool(BaseTool):
    name: str = "delete_file"
    description: str = "删除文件。参数: file_path - 文件路径"
    args_schema: Type[BaseModel] = DeleteFileInput

    def _run(self, file_path: str) -> str:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return f"✓ 文件已删除: {file_path}"
            return f"文件不存在: {file_path}"
        except Exception as e:
            return f"删除文件失败: {e}"


def get_file_tools() -> list[BaseTool]:
    """获取所有文件操作工具"""
    return [
        ReadFileTool(),
        WriteFileTool(),
        AppendFileTool(),
        CreateDirectoryTool(),
        ListDirectoryTool(),
        DeleteFileTool(),
    ]
