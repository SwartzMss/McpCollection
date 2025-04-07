# outlook_mail_fetcher.py

import os
import httpx
from datetime import datetime, timedelta
import pytz

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
            "scope": "Mail.ReadBasic Mail.Read Mail.ReadWrite Mail.Send offline_access"
        })
        data = response.json()
        new_token = data.get("access_token")
        self.access_token = new_token

        from dotenv import set_key, find_dotenv
        dotenv_path = find_dotenv()
        if dotenv_path:
            set_key(dotenv_path, "ACCESS_TOKEN", new_token)
            self.logger("ACCESS_TOKEN has been updated in the .env file.")
        else:
            self.logger("Could not locate the .env file. ACCESS_TOKEN update failed.")

    def fetch_emails(self):
        """
        从 Microsoft Graph API 获取邮件数据，不进行过滤。(50条)
        """
        url = "https://graph.microsoft.com/v1.0/me/messages?$orderby=receivedDateTime DESC&$top=50"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        attempts = 3
        for attempt in range(attempts):
            response = httpx.get(url, headers=headers)
            if response.status_code == 401:
                self.refresh_token_request()
                continue

            if response.status_code != 200:
                self.logger(f"Failed to fetch emails, status code={response.status_code}")
                return []
            return response.json().get("value", [])
        self.logger.error("Unable to fetch emails after multiple attempts.")
        return []

    def reply_email(self, email_id: str, comment: str) -> bool:
        """
        回复指定邮件。
        
        参数：
        - email_id: 要回复邮件的 id。
        - comment: 回复的正文内容。
        
        返回值：
        - True 表示回复成功，False 表示回复失败。
        """
        url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/reply"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        mail_data = {"comment": comment}
        attempts = 3
        for attempt in range(attempts):
            response = httpx.post(url, headers=headers, json=mail_data)
            if response.status_code == 401:
                self.refresh_token_request()
                continue
            if response.status_code in (200, 202):
                return True
            else:
                self.logger(f"Failed to reply email, status code={response.status_code}, response: {response.text}")
                return False
        return False

    def filter_emails_by_time(self, emails, max_days=2):
        """
        根据 max_days 参数过滤出最近 max_days 天内的邮件。
        """
        now_utc = datetime.now(pytz.utc)
        cutoff = now_utc - timedelta(days=max_days)
        filtered_emails = []
        for email in emails:
            email_date_str = email.get("receivedDateTime")
            if not email_date_str:
                continue
            email_dt = datetime.fromisoformat(email_date_str.rstrip("Z")).replace(tzinfo=pytz.utc)
            if email_dt >= cutoff:
                filtered_emails.append(email)
        return filtered_emails


    def send_email(self, recipients: list, subject: str, content: str, content_type: str = "Text"):
        """
        发送邮件
        参数：
        - recipients: 收件人的邮箱地址列表。
        - subject: 邮件主题。
        - content: 邮件正文内容。
        - content_type: 内容格式，默认 "Text"，可选 "HTML"。
        返回 True 表示发送成功，否则返回 False。
        """
        url = "https://graph.microsoft.com/v1.0/me/sendMail"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        recipients_formatted = [{"emailAddress": {"address": email}} for email in recipients]

        mail_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": content_type,
                    "content": content
                },
                "toRecipients": recipients_formatted
            }
        }

        attempts = 3
        for attempt in range(attempts):
            response = httpx.post(url, headers=headers, json=mail_data)
            if response.status_code == 401:
                self.refresh_token_request()
                continue

            if response.status_code in (202, 200):
                return True
            else:
                self.logger(f"Failed to send email, status code={response.status_code}, response: {response.text}")
                return False
        return False

    def delete_email(self, email_id: str) -> bool:
        """
        删除指定 id 的邮件。
        
        参数：
        - email_id: 要删除邮件的完整 id
        返回值：
        - True 表示删除成功，False 表示删除失败
        """
        url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = httpx.delete(url, headers=headers)
        if response.status_code == 204:
            return True
        elif response.status_code == 401:
            # 如果未授权，刷新 token 后重试
            self.refresh_token_request()
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = httpx.delete(url, headers=headers)
            return response.status_code == 204
        else:
            self.logger(f"Failed to delete email, status code={response.status_code}, response: {response.text}")
            return False
