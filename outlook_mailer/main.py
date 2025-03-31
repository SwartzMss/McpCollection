#!/usr/bin/env python3
import os
import re
import time
import httpx
import asyncio
import pytz
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    # 你依然可以导入相关的类型，比如:
    CallToolRequest,
    ListToolsRequest,
    # 其余类型如有需要也可以导入
)

###############################################################################
# 自定义异常类（如果原版 MCP 已移除 McpError / ErrorCode）
###############################################################################
class McpError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(f"[MCP Error {code}] {message}")
        self.code = code
        self.message = message

class ErrorCode:
    MethodNotFound = -32601
    ConfigurationError = -32000

###############################################################################
# OutlookMailSearcher：查询指定主题、邮件正文中的验证码
###############################################################################
class OutlookMailSearcher:
    def __init__(self, subject: str, code_length: int, logger, access_token: str, refresh_token: str):
        self.subject = subject
        self.code_length = code_length
        self.logger = logger
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")

    def refresh_token(self):
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        refresh_response = httpx.post(token_url, data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": "https://login.microsoftonline.com/common/oauth2/nativeclient",
            "scope": "Mail.ReadBasic Mail.Read Mail.ReadWrite offline_access"
        })
        new_access_token_data = refresh_response.json()
        self.access_token = new_access_token_data.get("access_token")

    def search_email_by_subject(self, max_attempts=6, wait_time=10):
        url = "https://graph.microsoft.com/v1.0/me/messages?$orderby=receivedDateTime DESC&$top=3"

        for attempt in range(max_attempts):
            time.sleep(wait_time)
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = httpx.get(url, headers=headers)

            if response.status_code == 401:
                self.refresh_token()
                continue

            if response.status_code != 200:
                self.logger("Failed to fetch emails")
                continue

            emails = response.json().get("value", [])
            for email in emails:
                # 匹配subject和bodyPreview不为空
                if self.subject in email.get("subject", "") and email.get("bodyPreview", ""):
                    email_date = email.get("receivedDateTime")
                    if email_date:
                        email_datetime = datetime.fromisoformat(email_date.rstrip('Z'))
                        email_datetime = email_datetime.replace(tzinfo=pytz.utc)
                        current_datetime = datetime.now(pytz.utc)

                        time_diff = current_datetime - email_datetime
                        if time_diff > timedelta(minutes=1):
                            self.logger("Email is too old.")
                            continue

                    html_content = email["body"]["content"]
                    soup = BeautifulSoup(html_content, "html.parser")
                    text = soup.get_text()
                    codes = re.findall(rf"(?<!\d)\d{{{self.code_length}}}(?!\d)", text)
                    if codes:
                        return codes[0]

        self.logger("Reached maximum attempts, no new email found.")
        return None


class OutlookMailServer:
    def __init__(self):
        load_dotenv()
        self.server = Server(
            {
                "name": "outlook-mail-server",
                "version": "1.0.0"
            },
            {
                "capabilities": {
                    "tools": {}
                }
            }
        )

        # 旧版 set_request_handler 改为直接对 request_handlers 赋值
        self.server.request_handlers["tools/list"] = self.handle_list_tools
        self.server.request_handlers["tools/call"] = self.handle_call_tool

        self.server.onerror = lambda error: print(f"[MCP Error] {error}")

    async def handle_list_tools(self, request):
        """
        当客户端发来 method = "tools/list" 时，MCP会调用此函数
        """
        return {
            "tools": [
                {
                    "name": "search_verification_code",
                    "description": "Search for verification code in recent Outlook emails",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Email subject to search for"
                            },
                            "code_length": {
                                "type": "integer",
                                "description": "Length of the verification code",
                                "default": 6
                            }
                        },
                        "required": ["subject"]
                    }
                }
            ]
        }

    async def handle_call_tool(self, request):
        """
        当客户端发来 method = "tools/call" 时，MCP会调用此函数
        """
        name = request.params.get("name")  # 这里取决于你具体的请求结构
        arguments = request.params.get("arguments", {})

        if name != "search_verification_code":
            raise McpError(
                ErrorCode.MethodNotFound,
                f"Unknown tool: {name}"
            )

        subject = arguments.get("subject")
        code_length = arguments.get("code_length", 6)

        access_token = os.getenv("ACCESS_TOKEN")
        refresh_token = os.getenv("REFRESH_TOKEN")

        if not all([access_token, refresh_token]):
            raise McpError(
                ErrorCode.ConfigurationError,
                "Missing required environment variables: ACCESS_TOKEN and REFRESH_TOKEN"
            )

        searcher = OutlookMailSearcher(
            subject=subject,
            code_length=code_length,
            logger=print,
            access_token=access_token,
            refresh_token=refresh_token
        )

        code = searcher.search_email_by_subject()

        # 返回内容
        return {
            "content": [
                {
                    "type": "text",
                    "text": code if code else "No verification code found"
                }
            ]
        }

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            # 也可以传 None（如果 MCP 允许）
            await self.server.run(read_stream, write_stream, initialization_options=None)


if __name__ == "__main__":
    server = OutlookMailServer()
    asyncio.run(server.run())
