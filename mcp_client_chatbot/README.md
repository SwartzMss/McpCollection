## 服务组件安装指南

在 [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) 仓库中，MCP官方已经提供了许多服务（server）组件，这些组件通常以 npm 包的形式发布。这意味着：

- **在线安装**  
  如果你需要使用某个服务，例如 `server-filesystem`，只需通过 npm 在线安装即可，无需手动管理代码。

- **本地开发**  
  如果你开发了一个自定义服务，但还未发布到 npm，则需要在 MCP 的配置中指定该服务的本地路径，以便在本地进行调试和使用。

此外，你可以访问 [npmjs.com](https://www.npmjs.com/) 网站，搜索相应的包名来确认该服务是否已经发布。例如，搜索 “server-filesystem” 就可以查看它是否已经上线。
