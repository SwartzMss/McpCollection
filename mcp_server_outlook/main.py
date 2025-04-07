from mcp.server.fastmcp import FastMCP
import os
import logging
import re
import httpx
from dotenv import load_dotenv
from mail import OutlookMailFetcher
from bs4 import BeautifulSoup
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
def get_email_by_subject(subject: str) -> str:
    """
    根据邮件主题查询邮件内容。

    参数：
      - subject: 邮件主题（字符串）如果存在重复的主题，则返回最新的一封邮件。

    返回值：
      返回查询到的邮件内容。
    """
    fetcher = OutlookMailFetcher(
        logger=logger,
        access_token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN")
    )
    try:
        # 获取最近的 50 封邮件
        emails = fetcher.fetch_emails()
        # 根据接收时间降序排序后，查找第一个主题匹配的邮件
        latest_email = next(
            (email for email in sorted(emails, key=lambda e: e.get("receivedDateTime", ""), reverse=True)
             if email.get("subject", "") == subject),
            None
        )
        if not latest_email:
            return f"No matching emails found for subject: {subject}"
        
        subj = latest_email.get("subject", "No Subject")
        content = latest_email.get("body", {}).get("content", "No Content")
        content_type = latest_email.get("body", {}).get("contentType", "text")
        if content_type.lower() == "html":
            # 使用 BeautifulSoup 解析 HTML 并提取纯文本
            content = BeautifulSoup(content, "html.parser").get_text()
        content = re.sub(r'\n\s*\n+', '\n\n', content).strip()  
        return f"Subject: {subj}\nContent:{content}"
    except Exception as e:
        logger.exception("Tool execution failed")
        return f"Error: {str(e)}"

@mcp.tool()
def get_email_by_id(email_id: str) -> str:
    """
    根据邮件的完整 email_id 获取邮件详细内容。

    参数：
      - email_id: 邮件的完整 id

    返回：
      返回邮件的详细内容。
    """
    fetcher = OutlookMailFetcher(
        logger=logger,
        access_token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN")
    )
    try:
        url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}"
        headers = {"Authorization": f"Bearer {fetcher.access_token}"}
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            email = response.json()
            subject = email.get("subject", "No Subject")
            content = email.get("body", {}).get("content", "No Content")
            content_type = email.get("body", {}).get("contentType", "text")
            if content_type.lower() == "html":
                # 将 HTML 转换为纯文本
                content = BeautifulSoup(content, "html.parser").get_text()
            content = re.sub(r'\n\s*\n+', '\n\n', content).strip()  
            return (
                f"Subject: {subject}\n"
                f"Content:{content}"
            )
        else:
            return (
                f"Failed to fetch email with id {email_id}. "
                f"Status code: {response.status_code}, Response: {response.text}"
            )
    except Exception as e:
        logger.exception("Tool execution failed")
        return f"Error: {str(e)}"



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
        emails = fetcher.fetch_emails()
        result_list = []
        for index, email in enumerate(emails):
            subj = email.get("subject", "")
            received_time_str = email.get("receivedDateTime", "")
            sender_info = email.get("sender", {}).get("emailAddress", {})
            email_id = email.get("id", "")
            sender_address = sender_info.get("address", "Unknown Email")
            result_list.append(
                f"{index+1}. {subj} (Received: {received_time_str}, Sender: {sender_address}, email_id: {email_id})"
            )
            if len(result_list) >= max_count:
                break
        if not result_list:
            return "No matching emails found"
        result = "\n".join(result_list)
        return "Recent Email Subjects (By Number):\n" + result
    except Exception as e:
        logger.exception("Tool execution failed")
        return f"Error: {str(e)}"


@mcp.tool()
def delete_email_by_id(email_id: str) -> str:
    """
    根据邮件 id 删除邮件。

    参数:
      - email_id: 邮件的完整 id

    返回:
      删除结果的反馈信息。如果成功删除邮件，返回成功提示；否则返回错误提示。
    """
    fetcher = OutlookMailFetcher(
        logger=logger,
        access_token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN")
    )
    try:
        result = fetcher.delete_email(email_id)
        if result:
            return f"Email with id {email_id} deleted successfully."
        else:
            return f"Failed to delete email with id {email_id}."
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
            received_time_str = email.get("receivedDateTime", "")
            email_id = email.get("id", "")
            sender_info = email.get("sender", {}).get("emailAddress", {})
            sender_address = sender_info.get("address", "Unknown Email")
            result_list.append(f"{index+1}. {subject} (Received: {received_time_str}, Sender: {sender_address}, email_id: {email_id})")
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
