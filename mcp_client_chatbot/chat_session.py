import asyncio
import json
import logging
from typing import Any
from llm_client import LLMClient
from server import Server

class ChatSession:
    """Orchestrates the interaction between user, LLM, and tools."""
    def __init__(self, servers: list[Server], llm_client: LLMClient) -> None:
        self.servers = servers
        self.llm_client = llm_client

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        cleanup_tasks = []
        for server in self.servers:
            cleanup_tasks.append(asyncio.create_task(server.cleanup()))
        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")

    async def process_llm_response(self, llm_response: str) -> str:
        if not isinstance(llm_response, str):
            try:
                llm_response = llm_response.content
            except AttributeError:
                llm_response = str(llm_response)
        try:
            tool_call = json.loads(llm_response)
            if "tool" in tool_call and "arguments" in tool_call:
                logging.info(f"Executing tool: {tool_call['tool']}")
                logging.info(f"With arguments: {tool_call['arguments']}")
                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_call["tool"] for tool in tools):
                        try:
                            result = await server.execute_tool(
                                tool_call["tool"], tool_call["arguments"]
                            )
                            if isinstance(result, dict) and "progress" in result:
                                progress = result["progress"]
                                total = result["total"]
                                percentage = (progress / total) * 100
                                logging.info(
                                    f"Progress: {progress}/{total} ({percentage:.1f}%)"
                                )
                            return f"Tool execution result: {result}"
                        except Exception as e:
                            error_msg = f"Error executing tool: {str(e)}"
                            logging.error(error_msg)
                            return error_msg
                return f"No server found with tool: {tool_call['tool']}"
            return llm_response
        except json.JSONDecodeError:
            return llm_response

    async def start(self) -> None:
        """Main chat session handler."""
        try:
            for server in self.servers:
                try:
                    await server.initialize()
                except Exception as e:
                    logging.error(f"Failed to initialize server {server.name}: {e}")
                    await self.cleanup_servers()
                    return

            all_tools = []
            for server in self.servers:
                tools = await server.list_tools()
                print(f"Server: {server.name}")
                for tool in tools:
                    print(f"  Tool: {tool.name} - {tool.description}")              
                all_tools.extend(tools)

            available_tools = [tool.format_for_llm() for tool in all_tools]
            tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
            system_message = (
                "你是一名智能助手,请根据用户的问题选择合适的工具。若不需要使用工具，请直接回复"
            )
            messages = [{"role": "system", "content": system_message}]

            while True:
                try:
                    user_input = input("You: ").strip().lower()
                    if user_input in ["quit", "exit"]:
                        logging.info("\nExiting...")
                        break
                    messages.append({"role": "user", "content": user_input})
                    llm_response = self.llm_client.get_response(messages,available_tools)
                    logging.info("API Direct Response: %s", llm_response.choices[0].message)
                    result = await self.process_llm_response(llm_response)

                    if result != llm_response:
                        messages.append({"role": "assistant", "content": llm_response})
                        messages.append({"role": "system", "content": str(result)})
                        final_response = self.llm_client.get_response(messages)
                        logging.info("\nFinal response: %s", final_response)
                        messages.append({"role": "assistant", "content": final_response})
                    else:
                        messages.append({"role": "assistant", "content": llm_response})
                except KeyboardInterrupt:
                    logging.info("\nExiting...")
                    break
        finally:
            await self.cleanup_servers()
