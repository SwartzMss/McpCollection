from mcp.server.fastmcp import FastMCP
import os
import logging
from dotenv import load_dotenv
from mail_fetcher import OutlookMailFetcher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outlook_mailer")

# Initialize FastMCP service
mcp = FastMCP(
    name="Outlook Mail MCP Server",
    description="Tool for fetching Outlook emails",
    dependencies=["httpx", "pytz", "python-dotenv"]
)

@mcp.tool()
def list_recent_emails(max_count: int = 5, max_days: int = 2) -> str:
    """
    Get a list of recent email subjects.
    
    Parameters:
      - max_count: Maximum number of emails to return (1~50)
      - max_days: Maximum number of days to search (1~30)
    """
    # Restrict parameter range
    max_count = min(max(1, max_count), 50)
    max_days = min(max(1, max_days), 30)

    fetcher = OutlookMailFetcher(
        logger=logger,
        access_token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN")
    )
    try:
        subjects = fetcher.list_recent_emails(max_count=max_count, max_days=max_days)
        if not subjects:
            return "No matching emails found"
        result = "Recent Email Subjects:\n" + "\n".join(f"{i+1}. {subject}" for i, subject in enumerate(subjects))
        return result
    except Exception as e:
        logger.exception("Tool execution failed")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
