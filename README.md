# MCP Collection
[![Render PlantUML Diagrams](https://github.com/SwartzMss/McpCollection/actions/workflows/plantuml-render.yml/badge.svg)](https://github.com/SwartzMss/McpCollection/actions/workflows/plantuml-render.yml)


这是一个 MCP（Model Context Protocol）相关的项目集合仓库，包含多个子项目。  
在本仓库中，你可以找到以下内容：

---

## 目录

1. [mcp_server_outlook](#mcp_server_outlook)
2. [mcp_server_filesystem](#mcp_server_filesystem)
3. [mcp_server_localSearch](#mcp_server_localsearch)
4. [mcp_client_chatbot](#mcp_client_chatbot)

---

## mcp_server_outlook
通过 [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/) 提供完整的 Outlook 邮件管理功能，包括：
- 邮件列表查询（按数量或时间范围）
- 邮件内容获取（按主题或 ID）
- 邮件发送和回复
- 邮件删除
- 邮件搜索

支持 HTML 和纯文本格式的邮件内容处理。具体信息查看[README](mcp_server_outlook/README.md)。  

## mcp_server_filesystem
提供基本的文件系统操作功能，包括文件读写、目录管理、文件移动等操作。支持 Windows 系统，无需指定可操作目录。具体信息查看[README](mcp_server_filesystem/README.md)。

## mcp_server_localSearch
基于 ripgrep (rg.exe) 的本地文件搜索服务，支持文件内容搜索和文件名搜索。提供丰富的搜索选项，如大小写敏感、正则表达式、文件过滤等。具体信息查看[README](mcp_server_localSearch/README.md)。

## mcp_client_chatbot 
主要用于与大语言模型 (LLM) 进行交互，并通过调用各种工具 (Tool) 完成任务。
具体信息查看[README](mcp_client_chatbot/README.md)。  
[点击观看项目介绍视频](https://www.bilibili.com/video/BV1XVZUYrELX)

## 许可

本项目采用 [MIT 许可](LICENSE)。
