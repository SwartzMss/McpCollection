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
    CallToolRequest,
    ListToolsRequest,
)


class McpError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(f"[MCP Error {code}] {message}")
        self.code = code
        self.message = message


class ErrorCode:
    MethodNotFound = -32601
    ConfigurationError = -32000


class OutlookMailFetcher:
    def __init__(self, logger, access_token: str, refresh_token: str):
        self.logger = logger
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")

    def refresh_token_request(self):
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        response = httpx.post(token_url, data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": "https://login.microsoftonline.com/common/oauth2/nativeclient",
            "scope": "Mail.ReadBasic Mail.Read Mail.ReadWrite offline_access"
        })
        data = response.json()
        self.access_token = data.get("access_token")

    def list_recent_emails(self, max_count=5, max_days=2):
        """
        Fetch at most 'max_count' recent emails within the last 'max_days' days.
        Return a list of subjects.
        """
        url = "https://graph.microsoft.com/v1.0/me/messages?$orderby=receivedDateTime DESC&$top=20"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # We'll do a few retries if token is invalid
        attempts = 3
        for attempt in range(attempts):
            response = httpx.get(url, headers=headers)
            if response.status_code == 401:
                self.refresh_token_request()
                continue

            if response.status_code != 200:
                self.logger(f"Failed to fetch emails, status code={response.status_code}")
                return []

            emails = response.json().get("value", [])
            break
        else:
            # If we never broke out, means all attempts failed
            self.logger("Unable to fetch emails after multiple attempts.")
            return []

        result = []
        now_utc = datetime.now(pytz.utc)
        cutoff = now_utc - timedelta(days=max_days)

        for email in emails:
            # Filter out anything older than 'max_days' days
            email_date_str = email.get("receivedDateTime")
            if not email_date_str:
                continue
            email_dt = datetime.fromisoformat(email_date_str.rstrip("Z")).replace(tzinfo=pytz.utc)
            if email_dt < cutoff:
                continue

            subj = email.get("subject", "")
            result.append(subj)
            if len(result) >= max_count:
                break

        return result


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

        # Register handlers
        self.server.request_handlers["tools/list"] = self.handle_list_tools
        self.server.request_handlers["tools/call"] = self.handle_call_tool

        self.server.onerror = lambda error: print(f"[MCP Error] {error}")

    async def handle_list_tools(self, request):
        return {
            "tools": [
                {
                    "name": "list_recent_emails",
                    "description": "Fetch recent email subjects within the last X days, up to Y messages",
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
                        },
                        "required": []
                    }
                }
            ]
        }

    async def handle_call_tool(self, request):
        """
        Called when method == "tools/call".
        We only define one tool: "list_recent_emails".
        """
        name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        if name != "list_recent_emails":
            raise McpError(
                ErrorCode.MethodNotFound,
                f"Unknown tool: {name}"
            )

        max_count = arguments.get("max_count", 5)
        max_days = arguments.get("max_days", 2)

        access_token = os.getenv("ACCESS_TOKEN")
        refresh_token = os.getenv("REFRESH_TOKEN")

        if not all([access_token, refresh_token]):
            raise McpError(
                ErrorCode.ConfigurationError,
                "Missing environment variables: ACCESS_TOKEN and REFRESH_TOKEN"
            )

        fetcher = OutlookMailFetcher(
            logger=print,
            access_token=access_token,
            refresh_token=refresh_token
        )
        subjects = fetcher.list_recent_emails(
            max_count=max_count,
            max_days=max_days
        )

        if subjects:
            text_output = "\n".join(subjects)
        else:
            text_output = "No recent emails found."

        return {
            "content": [
                {
                    "type": "text",
                    "text": text_output
                }
            ]
        }

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, initialization_options=None)


if __name__ == "__main__":
    server = OutlookMailServer()
    asyncio.run(server.run())
