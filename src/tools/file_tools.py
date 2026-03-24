"""文件操作工具"""
import os
import shutil
from pathlib import Path
from typing import Optional


class FileTools:
    """文件操作工具类"""

    @staticmethod
    def read_file(file_path: str, encoding: str = "utf-8") -> str:
        """读取文件内容"""
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
        """写入文件内容"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入文件失败：{e}")
            return False

    @staticmethod
    def append_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
        """追加内容到文件"""
        try:
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"追加文件失败：{e}")
            return False

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(file_path)

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败：{e}")
            return False

    @staticmethod
    def create_directory(dir_path: str) -> bool:
        """创建目录"""
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败：{e}")
            return False

    @staticmethod
    def delete_directory(dir_path: str, recursive: bool = False) -> bool:
        """删除目录"""
        try:
            if recursive:
                shutil.rmtree(dir_path)
            else:
                os.rmdir(dir_path)
            return True
        except Exception as e:
            print(f"删除目录失败：{e}")
            return False

    @staticmethod
    def list_directory(dir_path: str) -> list[str]:
        """列出目录内容"""
        try:
            return os.listdir(dir_path)
        except Exception as e:
            print(f"列出目录失败：{e}")
            return []

    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        """复制文件"""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"复制文件失败：{e}")
            return False

    @staticmethod
    def move_file(src: str, dst: str) -> bool:
        """移动文件"""
        try:
            shutil.move(src, dst)
            return True
        except Exception as e:
            print(f"移动文件失败：{e}")
            return False

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）"""
        return os.path.getsize(file_path)

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名"""
        return Path(file_path).suffix

    @staticmethod
    def search_files(
        dir_path: str, pattern: str = "*", recursive: bool = False
    ) -> list[str]:
        """搜索文件"""
        import fnmatch

        results = []
        if recursive:
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        results.append(os.path.join(root, file))
        else:
            for file in os.listdir(dir_path):
                if fnmatch.fnmatch(file, pattern):
                    results.append(os.path.join(dir_path, file))
        return results
