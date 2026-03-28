import os
from dotenv import load_dotenv

from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import (
    SaveQuestionToolArgsTool,
    SearchSavedCorrectToolUsesTool,
    SaveTextMemoryTool,
)
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService

load_dotenv()


class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(
            id="default_user",
            email="guest@example.com",
            group_memberships=["admin", "user"]   # give all permissions
        )


def setup_vanna_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")

    llm = GeminiLlmService(api_key=api_key, model="gemini-1.5-flash")

    db_tool = RunSqlTool(
        sql_runner=SqliteRunner(database_path="clinic.db")
    )

    agent_memory = DemoAgentMemory(max_items=1000)
    user_resolver = SimpleUserResolver()

    tools = ToolRegistry()
    # use .register() — confirmed correct in the official README source
    tools.register_local_tool(db_tool, access_groups=["admin", "user"])
    tools.register_local_tool(VisualizeDataTool(), access_groups=["admin", "user"])
    tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=["admin"])
    tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=["admin", "user"])
    tools.register_local_tool(SaveTextMemoryTool(), access_groups=["admin", "user"])

    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
    )

    print("✓ Vanna 2.0 Agent initialized")
    return agent