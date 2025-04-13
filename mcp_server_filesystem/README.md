# 文件系统 MCP 服务器

该项目实现了一个基于 MCP（Model Context Protocol）的服务器，用于进行文件系统操作。服务器通过 JSON-RPC 协议（使用 STDIN/STDOUT 通信）暴露了一系列工具，方便用户进行文件读写、目录管理等操作。

## 功能概述

服务器提供的主要工具包括：

- **read_file**  
  读取文件内容。  
  **参数：**  
  - `path`（字符串）：要读取的文件路径。

- **write_file**  
  写入文件内容。  
  **参数：**  
  - `path`（字符串）：要写入的文件路径。
  - `content`（字符串）：要写入的内容。

- **list_directory**  
  列出目录内容。  
  **参数：**  
  - `path`（字符串，可选）：要列出的目录路径，默认为当前目录。

- **create_directory**  
  创建新目录。  
  **参数：**  
  - `path`（字符串）：要创建的目录路径。

- **move_file**  
  移动文件或目录。  
  **参数：**  
  - `source`（字符串）：源文件/目录路径。
  - `destination`（字符串）：目标路径。

- **get_file_info**  
  获取文件详细信息。  
  **参数：**  
  - `path`（字符串）：文件路径。

## 运行环境

- Python 3.9+（推荐使用，理论上 3.7+ 也可）
- MCP Python 库（可通过 `pyproject.toml` 或其他依赖管理工具自动安装）
- 能通过 **STDIN / STDOUT** 与 MCP 服务器进行 JSON-RPC 通信的客户端（MCP 兼容客户端）

## 使用步骤

1. **克隆仓库**  
   ```bash
   git clone https://github.com/SwartzMss/McpCollection.git
   cd McpCollection/mcp_server_filesystem
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
     - 文件操作结果通过 JSON-RPC 返回

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
     - 显示文件操作的详细过程

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
    例如，读取文件：
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/call",
      "params": {
        "name": "read_file",
        "arguments": {
          "path": "C:/example.txt"
        }
      }
    }
    ```

## 其他注意事项

- 所有文件操作都使用 UTF-8 编码
- 路径可以使用相对路径或绝对路径
- 文件操作可能会受到操作系统权限限制
- 建议在使用前确保有足够的文件系统权限 