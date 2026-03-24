"""命令执行工具"""
import subprocess
import os
from typing import Optional


class CommandTools:
    """命令执行工具类"""

    @staticmethod
    def run_command(
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        shell: bool = True,
    ) -> tuple[int, str, str]:
        """
        执行命令

        Returns:
            (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)

    @staticmethod
    def run_command_stream(
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> tuple[int, str]:
        """
        执行命令并返回合并的输出

        Returns:
            (return_code, output)
        """
        returncode, stdout, stderr = CommandTools.run_command(
            command, cwd=cwd, timeout=timeout
        )
        output = stdout + stderr
        return returncode, output

    @staticmethod
    def check_command_exists(command: str) -> bool:
        """检查命令是否存在"""
        return shutil.which(command) is not None

    @staticmethod
    def get_current_directory() -> str:
        """获取当前工作目录"""
        return os.getcwd()

    @staticmethod
    def change_directory(dir_path: str) -> bool:
        """切换工作目录"""
        try:
            os.chdir(dir_path)
            return True
        except Exception as e:
            print(f"切换目录失败：{e}")
            return False


import shutil
