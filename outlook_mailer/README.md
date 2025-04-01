# Outlook Mail MCP 服务器

该项目实现了一个简单的 MCP（Model Context Protocol）服务器，用于在用户请求时从 Outlook 上获取近期邮件（仅返回邮件主题）。它基于 [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/) 实现。

## 功能

1. **列出工具 (List Tools)**  
   服务器对外暴露了一个 `list_recent_emails` 工具，用于获取最近若干天内的邮件主题。

2. **获取最近邮件**  
   当调用 `list_recent_emails` 工具时，可以指定：
   - `max_count`（默认 5）：最大邮件条数  
   - `max_days`（默认 2）：向前追溯的天数  

## 运行环境

- Python 3.9+（推荐使用，理论上 3.7+ 也可）
- 微软 Graph API OAuth 相关配置（包含 client ID、client secret 等）
- MCP Python 库（可通过 `pyproject.toml` 或其他依赖管理工具自动安装）
- 能通过 **STDIN / STDOUT** 与 MCP 服务器进行 JSON-RPC 通信的客户端（MCP 兼容客户端）

## 使用步骤

1. **克隆仓库**  
   ```bash
   git clone https://github.com/SwartzMss/McpCollection.git
   cd McpCollection/outlook_mailer
   ```

2. **创建并配置 .env 文件**  
    .env 文件中需要包含 Microsoft Graph 的相关凭证和 Token。例如：
    ```bash
    CLIENT_ID=00000000-0000-0000-0000-000000000000
    CLIENT_SECRET=yourclientsecret
    ACCESS_TOKEN=youraccesstoken
    REFRESH_TOKEN=yourrefreshtoken
    ```
3. **安装运行** 
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *main.py*.


## 使用说明
由于该 MCP 服务器使用 STDIN / STDOUT 进行 JSON-RPC 通信，你需要使用 MCP 兼容的客户端才能与之进行交互。大致流程如下：
1. **客户端 发送请求, 用于列出可用的工具**  
    ```json
    {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
    }
    ```
2. **服务器 响应**  
    ```json
    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
            {
                "name": "list_recent_emails",
                "description": "Fetch recent email subjects ...",
                "inputSchema": {
                "type": "object",
                "properties": {
                    "max_count": {
                    "type": "integer",
                    "description": "Maximum number of emails to return",
                    "default": 5
                    },
                    "max_days": {
                    "type": "integer",
                    "description": "How many days back to fetch",
                    "default": 2
                    }
                }
                }
            }
            ]
        }
    }
    ```
    3. **客户端 调用工具**  
    ```json
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "list_recent_emails",
            "arguments": {
            "max_count": 5,
            "max_days": 2
            }
        }
    }
    ```
    4. **服务器 返回邮件主题**  
    ```json
    {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "content": [
            {
                "type": "text",
                "text": "Subject1\nSubject2\nSubject3"
            }
            ]
        }
    }
    ```

## 其他注意事项
- 服务器需要在 .env 中读取 ACCESS_TOKEN、REFRESH_TOKEN、CLIENT_ID、CLIENT_SECRET 等环境变量，并使用它们对 Microsoft Graph 进行身份认证。

- 如果返回状态码为 401，则服务器会尝试用提供的 refresh_token 来刷新 access_token。

- 服务器会使用 max_days 过滤掉过老的邮件，并最多返回 max_count 条主题
