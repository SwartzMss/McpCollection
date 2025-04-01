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

        attempts = 3
        for attempt in range(attempts):
            response = httpx.get(url, headers=headers)
            if response.status_code == 401:
                # 如果 access_token 过期，尝试刷新
                self.refresh_token_request()
                continue

            if response.status_code != 200:
                self.logger(f"Failed to fetch emails, status code={response.status_code}")
                return []

            emails = response.json().get("value", [])
            break
        else:
            self.logger.error("Unable to fetch emails after multiple attempts.")
            return []

        result = []
        now_utc = datetime.now(pytz.utc)
        cutoff = now_utc - timedelta(days=max_days)

        for email in emails:
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
