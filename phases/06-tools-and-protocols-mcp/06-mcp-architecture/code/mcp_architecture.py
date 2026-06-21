"""Архитектура MCP: host ↔ client ↔ server — Build It для урока 6.2.

Без зависимостей. Игрушечная in-process модель MCP: сервер публикует три
примитива — tools (действия), resources (данные), prompts (заготовки); клиент их
перечисляет (discovery) и вызывает (invoke). Так видна роль каждого участника:
host оркестрирует, client говорит с server, server отдаёт примитивы.
"""


class MCPServer:
    """Сервер публикует tools / resources / prompts."""

    def __init__(self, name):
        self.name = name
        self._tools = {}
        self._resources = {}
        self._prompts = {}

    def add_tool(self, name, fn, description=""):
        self._tools[name] = {"fn": fn, "description": description}

    def add_resource(self, uri, content):
        self._resources[uri] = content

    def add_prompt(self, name, template):
        self._prompts[name] = template

    # --- discovery (что умеет сервер) ---
    def list_tools(self):
        return [{"name": n, "description": t["description"]} for n, t in self._tools.items()]

    def list_resources(self):
        return list(self._resources)

    def list_prompts(self):
        return list(self._prompts)

    # --- invoke (вызов примитива) ---
    def call_tool(self, name, **args):
        if name not in self._tools:
            raise KeyError(f"нет инструмента: {name}")
        return self._tools[name]["fn"](**args)

    def read_resource(self, uri):
        if uri not in self._resources:
            raise KeyError(f"нет ресурса: {uri}")
        return self._resources[uri]

    def get_prompt(self, prompt_name, **variables):
        if prompt_name not in self._prompts:
            raise KeyError(f"нет промпта: {prompt_name}")
        return self._prompts[prompt_name].format(**variables)


class MCPClient:
    """Клиент подключается к серверу; host через него оркеструет вызовы."""

    def __init__(self, server):
        self.server = server

    def discover(self):
        return {"tools": self.server.list_tools(),
                "resources": self.server.list_resources(),
                "prompts": self.server.list_prompts()}

    def call(self, tool, **args):
        return self.server.call_tool(tool, **args)


if __name__ == "__main__":
    srv = MCPServer("demo")
    srv.add_tool("sum", lambda a, b: a + b, "сложить")
    srv.add_resource("doc://policy", "Возврат в течение 14 дней.")
    srv.add_prompt("greet", "Здравствуйте, {name}!")
    client = MCPClient(srv)
    print("Discovery:", client.discover())
    print("call sum:", client.call("sum", a=2, b=3))
    print("resource:", srv.read_resource("doc://policy"))
    print("prompt:", srv.get_prompt("greet", name="Иван"))
