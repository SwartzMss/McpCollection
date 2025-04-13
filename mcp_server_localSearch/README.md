# 本地搜索 MCP 服务器

该项目实现了一个基于 MCP（Model Context Protocol）的服务器，用于进行本地文件搜索。服务器通过 JSON-RPC 协议（使用 STDIN/STDOUT 通信）暴露了一系列工具，方便用户使用 ripgrep (rg.exe) 进行高效的文件内容搜索和文件名搜索。

## 功能概述

服务器提供的主要工具包括：

- **search_rg**  
  使用 ripgrep (rg.exe) 进行文件内容或文件名搜索。  
  **参数：**  
  - `path`（字符串，可选）：搜索起始路径，默认为当前目录。如果为默认值且无结果，会自动搜索所有本地磁盘。
  - `query`（字符串）：搜索内容或文件名关键词。
  - `files_only`（布尔值）：是否只搜索文件名（不搜索内容）。
  - `ignore_case`（布尔值）：是否忽略大小写，默认为 true。
  - `case_sensitive`（布尔值）：是否强制区分大小写。
  - `fixed_strings`（布尔值）：是否将 query 视为固定字符串（关闭正则解析）。
  - `word_regexp`（布尔值）：是否整词匹配。
  - `glob`（字符串数组）：文件过滤模式，例如 `["*.py", "!*.log"]`。
  - `hidden`（布尔值）：是否包含隐藏文件。
  - `no_ignore`（布尔值）：是否忽略 .gitignore 等文件。
  - `max_filesize`（字符串）：跳过大于指定大小的文件，如 "50M"。
  - `threads`（整数）：自定义搜索线程数。
  - `context`（整数）：显示匹配行前后的上下文行数。
  - `before_context`（整数）：显示匹配行前的上下文行数。
  - `after_context`（整数）：显示匹配行后的上下文行数。

## 运行环境

- Python 3.9+（推荐使用，理论上 3.7+ 也可）
- ripgrep (rg.exe) 需要安装在系统 PATH 中
- MCP Python 库（可通过 `pyproject.toml` 或其他依赖管理工具自动安装）
- 能通过 **STDIN / STDOUT** 与 MCP 服务器进行 JSON-RPC 通信的客户端（MCP 兼容客户端）

## 使用步骤

1. **克隆仓库**  
   ```bash
   git clone https://github.com/SwartzMss/McpCollection.git
   cd McpCollection/mcp_server_localSearch
   ```

2. **安装依赖**  
   ```bash
   pip install -r requirements.txt
   ```

3. **运行服务器**  
   - **运行模式**（第一次先以运行模式，安装各种依赖性）：
     ```bash   
     uv run main.py
     ```
     在运行模式下，服务器会：
     - 只输出必要的错误信息
     - 通过 STDIN/STDOUT 与 MCP 客户端通信
     - 自动处理 JSON-RPC 请求
     - 保持静默运行，除非发生严重错误

   - **调试模式**：
     ```bash
     source .venv/Scripts/activate
     mcp dev main.py
     ```
     在调试模式下，服务器会：
     - 打印详细的日志信息
     - 显示所有 JSON-RPC 请求和响应
     - 在发生错误时显示完整的堆栈跟踪
     - 支持交互式命令行输入测试

## 使用说明

由于该 MCP 服务器使用 STDIN / STDOUT 进行 JSON-RPC 通信，你需要使用 MCP 兼容的客户端才能与之进行交互。大致流程如下：

1. **列出可用的工具**
    客户端发送请求：
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "tools/list"
    }
    ```
    服务器返回所有工具的名称、描述及参数信息

2. **调用具体工具**
    例如，搜索包含特定内容的文件：
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/call",
      "params": {
        "name": "search_rg",
        "arguments": {
          "query": "error",
          "path": "C:/logs",
          "glob": ["*.log"],
          "ignore_case": true
        }
      }
    }
    ```

## 其他注意事项

- 搜索内容时，ripgrep 可能受到 .gitignore 等文件的影响
- 搜索系统文件/隐藏文件时可能需要管理员权限
- 当 path 为默认值且无结果时，会自动搜索所有本地磁盘，可能耗时较长
- 特殊字符（如反斜杠、正则符号）需要正确转义
- Windows 路径中的反斜杠需要双写，如 "C:\\\\Users"
- 正则表达式中的特殊字符也需要转义，如 "\\d" 代替 "\d"