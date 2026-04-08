from typing import AsyncIterator

from app.agents.base.agent import BaseAgent
from app.agents.base.types import AgentContext, AgentMessage
from app.agents.orchestrator.orchestrator import AgentOrchestrator
from app.agents.registry import registry
from app.agents.sales.schemas import SalesData, SalesPhase
from app.core.logging import logger

# Maps each phase to the agent name that handles it
PHASE_AGENT_MAP: dict[SalesPhase, str] = {
    SalesPhase.DATA_GATHERING: "data_gathering",
    SalesPhase.RESEARCH: "research",
    SalesPhase.STRATEGY: "strategy",
    SalesPhase.DELIVERABLE: "pitch_deck",
}


def _get_sales_data(context: AgentContext) -> SalesData:
    raw = context.shared_state.get("sales_data")
    if isinstance(raw, SalesData):
        return raw
    if isinstance(raw, dict):
        return SalesData(**raw)
    return SalesData()


class SalesSupervisor(AgentOrchestrator):
    """Phase-based orchestrator for the sales pipeline.

    Routes messages to the appropriate specialist agent based on the
    current phase in shared_state["sales_data"].phase. Checks transition
    conditions after each agent execution.
    """

    async def route(self, context: AgentContext, message: AgentMessage) -> BaseAgent:
        sales_data = _get_sales_data(context)
        phase = sales_data.phase

        # Look up the agent for the current phase
        agent_name = PHASE_AGENT_MAP.get(phase)
        if agent_name:
            agent = registry.get(agent_name)
            if agent:
                logger.info(f"Supervisor routing to '{agent_name}' (phase={phase.value})")
                return agent

        # Fallback to default confidence-based routing
        logger.warning(f"No agent for phase '{phase.value}', falling back to score-based routing")
        return await super().route(context, message)

    def _check_phase_transition(self, context: AgentContext) -> SalesPhase | None:
        """Check if conditions are met to advance to the next phase.
        Returns the new phase if a transition should happen, None otherwise.
        """
        sales_data = _get_sales_data(context)

        if sales_data.phase == SalesPhase.DATA_GATHERING and sales_data.is_gathering_complete():
            return SalesPhase.RESEARCH

        if sales_data.phase == SalesPhase.RESEARCH and sales_data.is_research_complete():
            return SalesPhase.STRATEGY

        if sales_data.phase == SalesPhase.STRATEGY and sales_data.is_strategy_complete():
            return SalesPhase.DELIVERABLE

        return None

    async def execute(self, context: AgentContext, message: AgentMessage) -> AgentMessage:
        """Execute a turn and check for phase transitions."""
        response = await super().execute(context, message)

        # Check if agent already advanced the phase (e.g., data_gathering agent)
        # If not, check transition conditions
        new_phase = self._check_phase_transition(context)
        if new_phase:
            sales_data = _get_sales_data(context)
            if sales_data.phase != new_phase:
                logger.info(f"Phase transition: {sales_data.phase.value} -> {new_phase.value}")
                sales_data.phase = new_phase
                context.shared_state["sales_data"] = sales_data.model_dump()

        return response

    async def stream(
        self, context: AgentContext, message: AgentMessage
    ) -> AsyncIterator[dict]:
        """Stream with phase change events."""
        sales_data_before = _get_sales_data(context)
        phase_before = sales_data_before.phase

        agent = await self.route(context, message)
        yield {"type": "agent_selected", "agent": agent.name}

        context.current_step += 1
        response = await agent.execute(context, message)
        context.history.append(message)
        context.history.append(response)

        # Check phase transition
        new_phase = self._check_phase_transition(context)
        sales_data_after = _get_sales_data(context)
        current_phase = sales_data_after.phase

        # The agent may have already transitioned (like data_gathering setting RESEARCH)
        if current_phase != phase_before:
            yield {"type": "phase_changed", "phase": current_phase.value}
        elif new_phase and new_phase != current_phase:
            sales_data_after.phase = new_phase
            context.shared_state["sales_data"] = sales_data_after.model_dump()
            yield {"type": "phase_changed", "phase": new_phase.value}

        yield {"type": "message", "content": response.content, "agent": agent.name}
        yield {"type": "done"}
