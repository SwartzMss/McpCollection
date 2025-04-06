from mcp.server.fastmcp import FastMCP
import os
import logging
from dotenv import load_dotenv
from mail import OutlookMailFetcher

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("outlook_mailer")

# Initialize FastMCP service
mcp = FastMCP(
    name="Outlook Mail MCP Server",
    description="Tool for Outlook emails",
    dependencies=["httpx", "pytz", "python-dotenv"]
)

@mcp.tool()
def list_recent_emails_by_number(max_count: int = 5) -> str:
    """
    获取邮件主题列表，以编号形式返回（按数量限制）。
    
    参数：
      - max_count: 返回的邮件数量（1~50）
    """
    max_count = min(max(1, max_count), 50)
    fetcher = OutlookMailFetcher(
        logger=logger,
        access_token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN")
    )
    try:
        result = fetcher.filter_emails_by_number(max_count=max_count)
        if not result:
            return "No matching emails found"
        return "Recent Email Subjects (By Number):\n" + result
    except Exception as e:
        logger.exception("Tool execution failed")
        return f"Error: {str(e)}"


@mcp.tool()
def list_recent_emails_by_time(max_days: int = 2) -> str:
    """
    获取最近 max_days 天内的邮件主题列表，并以编号形式返回。
    
    参数：
      - max_days: 搜索最近多少天内的邮件（1~30）
    """
    max_days = min(max(1, max_days), 30)
    fetcher = OutlookMailFetcher(
        logger=logger,
        access_token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN")
    )
    try:
        emails = fetcher.fetch_emails()
        recent_emails = fetcher.filter_emails_by_time(emails, max_days)
        if not recent_emails:
            return "No matching emails found"
        result_list = []
        for index, email in enumerate(recent_emails):
            subject = email.get("subject", "")
            result_list.append(f"{index+1}. {subject}")
        result = "\n".join(result_list)
        return f"Recent Email Subjects (Last {max_days} Days):\n" + result
    except Exception as e:
        logger.exception("Tool execution failed")
        return f"Error: {str(e)}"

@mcp.tool()
def send_email(recipients: str, subject: str, content: str, content_type: str = "Text") -> str:
    """
    发送邮件到指定收件人。
    
    参数：
      - recipients: 用逗号分隔的收件人邮箱地址列表。
      - subject: 邮件主题。
      - content: 邮件正文内容。
      - content_type: 邮件内容类型，默认 "Text"，可选 "HTML"。
    """
    recipient_list = [email.strip() for email in recipients.split(",") if email.strip()]
    if not recipient_list:
        return "Error: No valid recipient email addresses provided."

    fetcher = OutlookMailFetcher(
        logger=logger,
        access_token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN")
    )
    try:
        success = fetcher.send_email(
            recipients=recipient_list, 
            subject=subject, 
            content=content, 
            content_type=content_type
        )
        if success:
            return "Email sent successfully"
        else:
            return "Failed to send email"
    except Exception as e:
        logger.exception("Tool execution failed")
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run()
