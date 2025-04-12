from mcp.server.fastmcp import FastMCP
import psutil  # search_rg 中会用到
from rg_search import RGSearchParams, build_rg_command, run_command
import logging

mcp = FastMCP(
    name="rg.exe File Search Service",
    description="MCP service for comprehensive file search based on ripgrep (rg.exe)."
)

@mcp.tool()
def search_rg(params: dict, timeout: int = 30) -> str:
    """
    使用 rg.exe 进行通用文本或文件名搜索的服务。

    [主要用途]
    1. **内容搜索**：
       - 通过 `query` 指定要搜索的文本（支持正则、固定字符串、整词等）
       - 常用于在多个文件中查找关键字、分析日志异常、批量检索信息

    2. **文件名搜索**：
       - 当 `files_only=True` 时，将在指定路径下按文件名匹配 `query`
       - 例如查询带有 "config" 字样的文件，可设置 `{"query": "config", "files_only": true}`
       - 若要只匹配特定后缀（如 *.yaml），可结合 `glob` 参数

    [关键参数说明]
    - `path`: 搜索起始路径（默认为当前目录）。若结果为空且为默认 "."，则自动遍历本地所有磁盘。
    - `query`: 待搜索的内容或文件名关键词（必填）
      - 在“内容搜索”模式下，支持正则表达式或固定字符串
      - 在“文件名搜索”模式下，当 `files_only=True`，则将 `query` 视为文件名的一部分（大小写敏感/不敏感依赖于 `case_sensitive` 与 `ignore_case` 设置）
    - `glob`: 进一步过滤文件，类似 `-g` 参数（可使用 `["*.py", "!*.log"]` 等）
    - `ignore_case`: 是否忽略大小写（默认 True），`case_sensitive` 则强制区分大小写
    - `fixed_strings`: 是否视 `query` 为固定字符串（关闭正则解析）
    - `word_regexp`: 是否整词匹配（相当于自动加 `\b` 边界）
    - `files_only`: 是否只搜索文件名（而不搜索内容）
    - `hidden`: 是否包含隐藏文件
    - `max_filesize`: 跳过大于指定大小的文件（如 "50M"）
    - `threads`: 自定义搜索线程数

    [返回结果]
    - 成功：返回匹配到的文本内容或文件列表（根据参数不同格式也不同）
    - 失败：以"Error:"开头的错误描述
    - 超时：以"Error: Operation timed out..."返回

    [注意事项]
    1. 当 `files_only=True` 时，ripgrep 默认列出所有文件；因此代码里进行了特殊处理，使之仅显示文件名中包含 `query` 的项（若需更多复杂规则，请使用 `glob` 或自行实现逻辑）。
    2. 搜索内容时，ripgrep 可能被 `.gitignore` / `.ignore` 文件影响（可用 `no_ignore=True` 覆盖）。
    3. 搜索系统文件/隐藏文件时，可能需要管理员权限或者显式启用 `hidden=True`。
    4. 不支持统计空文件夹或列出目录，如需此功能应使用操作系统命令（如 `dir`、`find` 等）或文件系统 API。
    5. 当 `path` 为 "." 且无结果时，工具会自动尝试搜索所有本地盘符，可能耗时较长。
    6. 特殊字符（如反斜杠、正则符号）需要转义，示例：Windows 路径需写成 `"C:\\\\Users"`，正则里要写 `\\d` 代替 `\d`。

    [调用示例]
    1. 在日志文件中按正则搜索时间戳：
       ```json
       {
         "query": "2023-\\d{2}-\\d{2} \\d{2}:\\d{2}",
         "glob": ["*.log"],
         "ignore_case": true
       }
       ```
    2. 搜索包含 "rustdesk" 字样的文件名（不区分大小写），在 E 盘下：
       ```json
       {
         "query": "rustdesk",
         "path": "E:\\\\",
         "files_only": true
       }
       ```
    """
    try:
        logging.getLogger("rg_search").info("Parsing input parameters...")
        # Validate and parse input parameters using RGSearchParams model
        rg_params = RGSearchParams(**params)
        cmd = build_rg_command(rg_params)
        logging.getLogger("rg_search").info("Starting search...")
        output = run_command(cmd, timeout=timeout)

        # 当输出为空且路径为默认 '.' 时，尝试对所有本地盘符搜索
        if not output.strip() and (not rg_params.path or rg_params.path.strip() == "."):
            logging.getLogger("rg_search").info("No result from initial search; searching all local drives...")
            drives = [p.device for p in psutil.disk_partitions() if p.fstype and p.device[0].isalpha()]
            if not drives:
                logging.getLogger("rg_search").error("No local disks detected.")
                return "No local disks detected."

            results = []
            for drive in drives:
                if not drive.endswith("\\"):
                    drive = drive + "\\"
                logging.getLogger("rg_search").info(f"Searching drive {drive}...")
                rg_params.path = drive
                cmd = build_rg_command(rg_params)
                drive_output = run_command(cmd, timeout=timeout)
                results.append(f"Drive {drive}:\n{drive_output}")
            output = "\n".join(results)

        logging.getLogger("rg_search").info("Search complete.")
        return output
    except Exception as ex:
        logging.getLogger("rg_search").error(f"Error during search: {str(ex)}")
        return f"Error: {str(ex)}"


if __name__ == "__main__":
    mcp.run()
