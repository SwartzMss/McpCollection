import json
import os
from dotenv import load_dotenv
from typing import Any

class Configuration:
    """Manages configuration and environment variables for the MCP client."""
    def __init__(self) -> None:
        self.load_env()
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL")

    @staticmethod
    def load_env() -> None:
        """Load environment variables from .env file."""
        load_dotenv()

    @staticmethod
    def load_config(file_path: str) -> dict[str, Any]:
        """Load server configuration from JSON file."""
        with open(file_path, "r") as f:
            return json.load(f)

    def api_key(self) -> str:
        """Get the API key."""
        if not self.api_key:
            raise ValueError("API_KEY not found in environment variables")
        return self.api_key

    def base_url(self) -> str:
        """Get the BASE URL."""
        if not self.base_url:
            raise ValueError("BASE_URL not found in environment variables")
        return self.base_url   
