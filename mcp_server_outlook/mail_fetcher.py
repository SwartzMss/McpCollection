import os
import httpx
import pytz
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from dotenv import load_dotenv

# Directly import classes from exceptions.py
from exceptions import McpError, ErrorCode

# Load environment variables to retrieve necessary credentials
load_dotenv()

class OutlookMailFetcher:
    """
    Microsoft Graph API Email Fetching Service
    """

    def __init__(
        self, 
        logger: logging.Logger,
        access_token: str,
        refresh_token: str,
        api_version: str = "v1.0"
    ):
        self.logger = logger
        self.api_version = api_version
        self._validate_tokens(access_token, refresh_token)
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._load_client_credentials()

    def _validate_tokens(self, access_token: str, refresh_token: str):
        if not all([access_token, refresh_token]):
            raise McpError(
                ErrorCode.AuthError,
                "Access token and refresh token must be provided"
            )

    def _load_client_credentials(self):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        if not all([self.client_id, self.client_secret]):
            raise McpError(
                ErrorCode.ConfigurationError,
                "Missing client credentials in environment variables"
            )

    def refresh_token_request(self) -> bool:
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        try:
            response = httpx.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": "https://login.microsoftonline.com/common/oauth2/nativeclient",
                    "scope": "Mail.ReadBasic Mail.Read Mail.ReadWrite offline_access"
                },
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["access_token"]
            self.logger.info("Access token refreshed successfully")
            return True
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Token refresh failed: HTTP {e.response.status_code}")
            raise McpError(
                ErrorCode.AuthError,
                f"Token refresh failed: {e.response.text}"
            ) from e
        except Exception as e:
            self.logger.error(f"Token refresh error: {str(e)}")
            raise McpError(
                ErrorCode.AuthError,
                f"Token refresh error: {str(e)}"
            ) from e

    def list_recent_emails(
        self, 
