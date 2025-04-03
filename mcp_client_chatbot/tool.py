from typing import Any, Dict

class Tool:
    """Represents a tool with its properties and formatting."""
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM."""
        return {
            "type": "function",
            "function": {
                "name": self.name,              
                "description": self.description,  
                "parameters": self.input_schema
            }
        }
