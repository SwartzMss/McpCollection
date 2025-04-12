import subprocess
import psutil  # 用于获取本地磁盘和管理子进程
import logging
from pydantic import BaseModel, Field
from typing import Optional, List
import sys
import re
import time

# 配置日志，只写入 stderr，避免污染标准输出（stdout）
logger = logging.getLogger("rg_search")
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    ch = logging.StreamHandler(sys.stderr)  # 修改为 sys.stderr
    ch.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(fmt)
    logger.addHandler(ch)


class RGSearchParams(BaseModel):
    query: str = Field(..., description="Search pattern (supports regex or fixed string)")
    path: Optional[str] = Field(".", description="Starting search directory")
    ignore_case: bool = Field(True, description="Ignore case sensitivity (default: True)")
    case_sensitive: bool = Field(False, description="Force case-sensitive search")
    fixed_strings: bool = Field(False, description="Use fixed string matching (do not interpret as regex)")
    word_regexp: bool = Field(False, description="Match whole words only")
    glob: Optional[List[str]] = Field(None, description="File filtering patterns (glob format), e.g., ['*.py', '!*.log']")
    hidden: bool = Field(False, description="Include hidden files in search")
    no_ignore: bool = Field(False, description="Do not use .gitignore, .ignore, etc.")
    follow: bool = Field(False, description="Follow symbolic links")
    max_filesize: Optional[str] = Field(None, description="Maximum file size (e.g., '10M')")
    line_number: bool = Field(True, description="Include line numbers in output")
    column: bool = Field(False, description="Include column numbers in output")
    context: Optional[int] = Field(None, description="Show context lines before and after matches")
    before_context: Optional[int] = Field(None, description="Show lines before matches")
    after_context: Optional[int] = Field(None, description="Show lines after matches")
    only_matching: bool = Field(False, description="Output only the matching parts instead of full lines")
    json_output: bool = Field(False, description="Output results in JSON format")
    stats: bool = Field(False, description="Show statistics after search completes")
    line_buffered: bool = Field(False, description="Buffer output line by line")
    max_columns: Optional[int] = Field(None, description="Limit the maximum number of characters per line")
    threads: Optional[int] = Field(None, description="Number of threads to use")
    files_only: bool = Field(False, description="Only search for filenames (do not search file contents)")

    # 新增：限制最大返回的行数，防止输出过多
    max_output_lines: Optional[int] = Field(
        1000, 
        description="Maximum number of lines to return from the search output (default: 1000)."
    )


def build_rg_command(params: RGSearchParams) -> List[str]:
    """
    Build the command line argument list for calling rg.exe based on the parameters.
    """
    cmd = ["rg.exe"]

    if params.files_only:
        cmd.append("--files")

        if params.query:

            option = "-g" if params.case_sensitive else "--iglob"

            cmd.extend([option, params.query])

    else:
        if params.fixed_strings:
            cmd.append("--fixed-strings")
        if params.word_regexp:
            cmd.append("--word-regexp")

        if params.case_sensitive:
            cmd.append("--case-sensitive")
        elif not params.ignore_case:
            pass
        else:
            cmd.append("--ignore-case")

        if params.hidden:
            cmd.append("--hidden")
        if params.no_ignore:
            cmd.append("--no-ignore")
        if params.follow:
            cmd.append("--follow")
        if params.only_matching:
            cmd.append("--only-matching")
        if params.json_output:
            cmd.append("--json")
        if params.stats:
            cmd.append("--stats")
        if params.line_buffered:
            cmd.append("--line-buffered")
        if params.column:
            cmd.append("--column")
        if params.threads is not None:
            cmd.extend(["--threads", str(params.threads)])
        if params.max_columns is not None:
            cmd.extend(["--max-columns", str(params.max_columns)])
        if params.context is not None:
            cmd.extend(["-C", str(params.context)])
        if params.before_context is not None:
            cmd.extend(["-B", str(params.before_context)])
        if params.after_context is not None:
            cmd.extend(["-A", str(params.after_context)])
        if params.max_filesize:
            cmd.extend(["--max-filesize", params.max_filesize])

        cmd.append(params.query)

    if params.glob:
        for pattern in params.glob:
            cmd.extend(["-g", pattern])

    if params.path:
        cmd.append(params.path)

    return cmd


def run_command(cmd: List[str], timeout: int, max_output_lines: int = 1000) -> str:
    """
    Execute the given command and return its output.
    If output exceeds `max_output_lines`, it will be truncated.
    Handles different types of errors appropriately.

    Args:
        cmd: Command to execute as list of arguments
        timeout: Maximum execution time in seconds
        max_output_lines: Max lines to return from the search output

    Returns:
        str: Command output or error message
    """
    def clean_error_message(err: str) -> str:
        """Remove debug info and normalize error messages"""
        # 移除代码文件引用（如 rg_search.py:104）
        err = re.sub(r'\w+\.py:\d+:\s*', '', err)
        # 合并重复错误
        errors = list(set(err.splitlines()))
        return '\n'.join(e for e in errors if e.strip())

    def kill_process_tree(pid: int):
        """Terminate a process and all its children"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            parent.kill()
        except psutil.NoSuchProcess:
            pass
        except Exception as ex:
            logger.error(f"Process termination failed: {str(ex)}")

    logger.info(f"Executing: {subprocess.list2cmdline(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
            shell=False
        )

        # 手动按行读取 stdout
        collected_lines = []
        truncated = False

        start_time = time.time()
        while True:
            # 超时检查
            if time.time() - start_time > timeout:
                logger.error(f"Command timed out after {timeout} seconds")
                kill_process_tree(process.pid)
                return f"Error: Operation timed out after {timeout} seconds"

            line = process.stdout.readline()
            if not line:
                # 说明 stdout 读完
                break
            collected_lines.append(line)
            if len(collected_lines) >= max_output_lines:
                # 超过最大行数，截断输出
                kill_process_tree(process.pid)
                truncated = True
                break

        # 此时子进程要么自然结束，要么已被 kill；可以安全读取剩下的 stderr
        stderr_data = process.stderr.read()
        stderr_data = clean_error_message(stderr_data)

        # 处理和过滤常见的 os error
        if "os error 2" in stderr_data.lower():
            logger.warning("Some file or path not found (os error 2)")
        if "os error 5" in stderr_data.lower():
            logger.warning("Permission denied for some locations (os error 5)")

        # 过滤已处理的错误类型
        filtered_errors = [
            line for line in stderr_data.split('\n')
            if line.strip() and
            not any(err in line.lower() for err in ["os error 2", "os error 5"])
        ]
        if filtered_errors:
            logger.warning(f"Command warnings: {' | '.join(filtered_errors)}")

        # 如果发生截断，则在输出末尾附加提醒
        output_text = "".join(collected_lines)
        if truncated:
            output_text += "\n[Output truncated due to exceeding max_output_lines limit]\n"

        return output_text

    except FileNotFoundError:
        logger.error("ripgrep (rg.exe) not found")
        return "Error: ripgrep executable not found in PATH"
    except Exception as ex:
        logger.error(f"Unexpected error: {str(ex)}")
        return f"Error: {str(ex)}"


def rg_search(params: RGSearchParams, timeout: int = 30) -> str:
    """
    封装：使用给定参数构建命令并执行搜索，
    返回结果或错误信息（必要时截断）。
    """
    cmd = build_rg_command(params)
    result = run_command(cmd, timeout=timeout, max_output_lines=params.max_output_lines or 1000)
    return result

