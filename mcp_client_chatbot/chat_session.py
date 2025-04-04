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
        if hasattr(llm_response, "tool_calls") and llm_response.tool_calls:
            tool_messages = []
            for tool_call in llm_response.tool_calls:
                tool_name = tool_call.function.name
                #debug for print
                logging.info(f"start calling tools: {tool_name}...")
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}
                found = False
                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_name for tool in tools):
                        found = True
                        try:
                            result = await server.execute_tool(tool_name, tool_args)
                            #debug for print
                            logging.info(f"Tool {tool_name} executed successfully: {result}")
                            if isinstance(result.content, list):
                                content_str = "\n".join(
                                    item.get("text") if isinstance(item, dict) and "text" in item else str(item)
                                    for item in result.content
                                )
                            else:
                                content_str = str(result.content)
                            logging.info(f"Tool {content_str}")
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": content_str,      
                            }
                            tool_messages.append(tool_message)
                        except Exception as e:
                                error_msg = f"Error executing tool: {str(e)}"
                                logging.error(error_msg)
                                return error_msg
                        break
                if not found:
                    error_message = f"No server found with tool: {tool_name}"
                    logging.error(error_message)
                    tool_messages.append({
                        "role": "error",
                        "tool_call_id": tool_call.id,
                        "content": error_message
                    })
            return tool_messages
        #debug for print
        #logging.info(f"no need calling tools...")
        return llm_response.content                

    async def start(self) -> None:
        """Main chat session handler."""
        try:
            for server in self.servers:
                try:
                    logging.info(f"Initializing MCP server: {server.name}...")
                    await server.initialize()
                    logging.info(f"MCP server {server.name} initialized successfully.")
                except Exception as e:
                    logging.error(f"Failed to initialize MCP server {server.name}: {e}")
                    await self.cleanup_servers()
                    return

            all_tools = []
            for server in self.servers:
                tools = await server.list_tools()
                # debug for print
                # print(f"Server: {server.name}")
                # for tool in tools:
                #     print(f" * Tool: {tool.name} - {tool.description}")              
                all_tools.extend(tools)

            available_tools = [tool.format_for_llm() for tool in all_tools]
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
                    messages.append(llm_response)

                    # debug for print
                    logging.info("API Direct Response: %s", llm_response)
                    tool_message = await self.process_llm_response(llm_response)

                    if tool_message != llm_response.content and isinstance(tool_message, list) and tool_message:
                        messages.extend(tool_message)
                        llm_response = self.llm_client.get_response(messages)
                        # debug for print
                        logging.info("API Direct Response: %s", llm_response)
                        messages.append(llm_response)
                        logging.info("Answer: %s", llm_response.content)
                    else:
                        logging.info("Answer: %s", llm_response.content)
                except KeyboardInterrupt:
                    logging.info("\nExiting...")
                    break
        finally:
            await self.cleanup_servers()
