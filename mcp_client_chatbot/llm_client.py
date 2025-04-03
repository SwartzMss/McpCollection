import logging
from openai import OpenAI

class LLMClient:
    """Manages communication with the LLM provider."""
    def __init__(self, api_key: str, base_url: str) -> None:
        self.llm_client = OpenAI(api_key=api_key, base_url=base_url)

    def get_response(self, messages: list[dict[str, str]], available_tools: list[dict[str, any]] = None) -> str:
        try:
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",       
                messages=messages,
                tools=available_tools if available_tools else None, # 可用的工具列表
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message
        except Exception as e:
            error_message = f"Error getting LLM response: {str(e)}"
            logging.error(error_message)
            return (
                f"I encountered an error: {error_message}. "
                "Please try again or rephrase your request."
            )
