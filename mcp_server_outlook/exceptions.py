class McpError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(f"[MCP Error {code}] {message}")
        self.code = code
        self.message = message

class ErrorCode:
    MethodNotFound = -32601
    ConfigurationError = -32000
    AuthError = -32001