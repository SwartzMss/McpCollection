# mcp_client_chatbot 项目说明

本项目基于 [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) 构建，主要用于与大语言模型 (LLM) 进行交互，并通过调用各种工具 (Tool) 完成任务。本文档详细介绍了项目的整体架构、主要组件、工作流程以及安装和使用方法。

## 目录

- [简介](#简介)
- [系统架构和工作流程](#系统架构和工作流程)
- [主要组件说明](#主要组件说明)
  - [main.py](#mainpy)
  - [config.py](#configpy)
  - [server.py](#serverpy)
  - [chat_session.py](#chat_sessionpy)
  - [llm_client.py](#llm_clientpy)
  - [tool.py](#toolpy)
- [安装与使用](#安装与使用)
- [服务组件安装指南](#服务组件安装指南)
- [开发与贡献](#开发与贡献)
- [许可证](#许可证)

## 简介

MCP Client 是一个智能对话客户端，支持与 LLM 的深度交互。系统能够根据用户输入自动选择和调用合适的工具，通过 MCP 服务器完成工具执行，并将执行结果反馈给用户，实现全自动化的交互体验。

## 系统架构和工作流程
![系统 UML](diagrams/output/mcp_client_chatbot.svg)

## 工作流程说明

1. **用户输入**  
   用户通过命令行输入问题或指令。

2. **ChatSession**  
   会话管理模块接收用户输入，并构造消息传递给 LLM。

3. **LLM 请求**  
   LLMClient 将用户消息以及当前可用工具列表提交给 LLM。

4. **响应解析**  
   LLM 返回的响应中可能包含工具调用指令，ChatSession 解析出相应的调用参数。

5. **工具执行**  
   ChatSession 根据指令查找合适的 MCP 服务器，通过 `server.py` 调用相应工具执行任务。

6. **结果反馈**  
   工具执行结果返回后，ChatSession 再次将结果传递给 LLM，生成最终答案。

7. **输出结果**  
   最终答案通过命令行展示给用户。

## 主要组件说明

### main.py
**main.py** 是项目的入口文件，负责加载配置、初始化 MCP 服务器和 LLM 客户端，并启动整个会话流程。

### config.py
**config.py** 用于加载环境变量和服务器配置（存储于 `servers_config.json`），确保项目所需的 API Key、Base URL 以及其他环境变量正确设置。

### server.py
**server.py** 定义了 Server 类，主要功能包括：
- 初始化 MCP 服务器连接；
- 列出服务器中可用的工具；
- 根据请求调用工具，并通过重试机制确保工具调用成功；
- 清理资源，保证程序退出时服务器连接正确关闭。

### chat_session.py
**chat_session.py** 是整个系统的核心，会话管理模块。它负责：
- 处理用户输入；
- 与 LLM 进行消息交互；
- 分析 LLM 响应中的工具调用；
- 调用相应服务器执行工具，并整合返回结果。

### llm_client.py
**llm_client.py** 封装了与大语言模型的通信逻辑，通过 OpenAI 接口向 LLM 发送请求并获取响应，同时支持将当前可用的工具列表传递给 LLM。

### tool.py
**tool.py** 定义了工具 (Tool) 类，描述了工具的名称、功能描述以及输入参数格式。该类还提供了一个格式化方法，使工具信息能够被 LLM 识别和使用。


## 安装与使用

### 环境配置

1. **安装 Python 3.8 及以上版本**。

2. **安装依赖库**  
  在项目根目录下执行：
  ```bash
  pip install -r requirements.txt
  ```
3. **配置环境变量**  
  在项目根目录下创建 .env 文件，并添加以下内容：
  ```ini
  API_KEY=your_api_key
  BASE_URL=your_base_url
  ```

### 服务器配置
编辑 servers_config.json 文件，根据需求配置 MCP 服务器，例如：
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "E:/"]
    }
  }
}
```

### 运行项目
```python
python main.py
```
启动后，系统将等待用户输入问题，自动与 LLM 交互，并根据需要调用工具执行任务，最终在命令行中输出答案。


## 服务组件安装指南

在 [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) 仓库中，MCP官方已经提供了许多服务（server）组件，这些组件通常以 npm 包的形式发布。这意味着：

- **在线安装**  
  如果你需要使用某个服务，例如 `server-filesystem`，只需通过 npm 在线安装即可，无需手动管理代码。

- **本地开发**  
  如果你开发了一个自定义服务，但还未发布到 npm，则需要在 MCP 的配置中指定该服务的本地路径，以便在本地进行调试和使用。

此外，你可以访问 [npmjs.com](https://www.npmjs.com/) 网站，搜索相应的包名来确认该服务是否已经发布。例如，搜索 “server-filesystem” 就可以查看它是否已经上线。