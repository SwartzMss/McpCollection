# Outlook Mail MCP 服务器

该项目实现了一个基于 MCP（Model Context Protocol）的服务器，用于通过 Microsoft Graph API 操作 Outlook 邮件。服务器通过 JSON-RPC 协议（使用 STDIN/STDOUT 通信）暴露了一系列工具，方便用户查询、管理和发送邮件

## 功能概述

服务器提供的主要工具包括：

- **get_email_by_subject**  
  根据邮件主题查询邮件内容。  
  **参数：**  
  - `subject`（字符串）：待查询的邮件主题。  
  - `count`（整数，默认值 1）：返回匹配邮件的数量（返回最新的几封邮件）。

- **get_email_by_id**  
  根据邮件的完整 `email_id` 获取邮件详细内容。  
  **参数：**  
  - `email_id`（字符串）：邮件的唯一标识。

- **list_recent_emails_by_number**  
  获取近期邮件主题列表（以编号形式返回），便于用户快速浏览。  
  **参数：**  
  - `max_count`（整数，默认值 5，取值范围 1~50）：返回的邮件数量。

- **list_recent_emails_by_time**  
  根据时间范围获取近期邮件主题列表（以编号形式返回）。  
  **参数：**  
  - `max_days`（整数，默认值 2，取值范围 1~30）：查询最近多少天内的邮件。

- **delete_email_by_id**  
  根据邮件的 `email_id` 删除指定邮件。  
  **参数：**  
  - `email_id`（字符串）：待删除邮件的唯一标识。

- **send_email**  
  发送邮件到指定收件人。  
  **参数：**  
  - `recipients`（字符串）：多个收件人邮箱地址，逗号分隔。  
  - `subject`（字符串）：邮件主题。  
  - `content`（字符串）：邮件正文内容。  
  - `content_type`（字符串，默认 "Text"，可选 "HTML"）：邮件内容类型。

## 运行环境

- Python 3.9+（推荐使用，理论上 3.7+ 也可）
- 微软 Graph API OAuth 相关配置（包含 client ID、client secret 等）
- MCP Python 库（可通过 `pyproject.toml` 或其他依赖管理工具自动安装）
- 能通过 **STDIN / STDOUT** 与 MCP 服务器进行 JSON-RPC 通信的客户端（MCP 兼容客户端）

## 使用步骤

1. **克隆仓库**  
   ```bash
   git clone https://github.com/SwartzMss/McpCollection.git
   cd McpCollection/mcp_server_outlook
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
- 运行模式(第一次先以运行模式，安装各种依赖性):
    ```bash   
    uv run main.py
    ```
- 调试模式:
    ```bash
    source .venv/Scripts/activate
    mcp dev main.py
    ```

## 使用说明
由于该 MCP 服务器使用 STDIN / STDOUT 进行 JSON-RPC 通信，你需要使用 MCP 兼容的客户端才能与之进行交互。大致流程如下：
1. **用于列出可用的工具**
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
- 按主题查询邮件：
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/call",
      "params": {
        "name": "get_email_by_subject",
        "arguments": {
          "subject": "会议通知",
          "count": 1
        }
      }
    }
    ```


## 其他注意事项
- 服务器需要在 .env 中读取 ACCESS_TOKEN、REFRESH_TOKEN、CLIENT_ID、CLIENT_SECRET 等环境变量，并使用它们对 Microsoft Graph 进行身份认证。

- 如果返回状态码为 401，则服务器会尝试用提供的 refresh_token 来刷新 access_token。

- 服务器会使用 max_days 过滤掉过老的邮件，并最多返回 max_count 条主题
