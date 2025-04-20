
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import requests

# 初始化 MCP 服务
mcp = FastMCP(
    name="Gomoku MCP Server",
    description="MCP bridge for communicating with local Gomoku environment",
)

BASE_URL = "http://localhost:8080"

class MoveInput(BaseModel):
    x: int = Field(..., description="落子的横坐标")
    y: int = Field(..., description="落子的纵坐标")
    color: int = Field(..., description="落子的颜色，1 表示黑子，2 表示白子")

@mcp.tool()
def get_board_state() -> dict:
    """获取当前棋盘状态"""
    response = requests.get(f"{BASE_URL}/get_board")
    return response.json()

@mcp.tool()
def get_move_status() -> dict:
    """查询是否可以继续对局，以及当前该谁落子"""
    response = requests.get(f"{BASE_URL}/can_move")
    return response.json()

@mcp.tool()
def move_piece(data: MoveInput) -> dict:
    """执行一次落子操作"""
    response = requests.post(f"{BASE_URL}/move", json=data.dict())
    return response.json()

@mcp.tool()
def reset_game() -> dict:
    """重置当前棋盘，开始新的一局"""
    response = requests.post(f"{BASE_URL}/reset")
    return {"status": response.status_code}

if __name__ == "__main__":
    mcp.run()
