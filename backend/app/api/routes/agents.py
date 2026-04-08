from fastapi import APIRouter

from app.schemas.agent import AgentInfo

router = APIRouter()


@router.get("/", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    """List all available agents and their capabilities."""
    # TODO: return from agent registry
    return []


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str) -> AgentInfo:
    """Get details about a specific agent."""
    # TODO: lookup from agent registry
    raise NotImplementedError
