from typing import AsyncIterator

from app.agents.base.agent import BaseAgent
from app.agents.base.types import AgentContext, AgentMessage, MessageRole
from app.agents.orchestrator.orchestrator import AgentOrchestrator
from app.agents.registry import registry
from app.agents.sales.schemas import SalesData, SalesPhase
from app.core.logging import logger

# Maps each phase to the agent name that handles it
PHASE_AGENT_MAP: dict[SalesPhase, str] = {
    SalesPhase.DATA_GATHERING: "data_gathering",
    SalesPhase.RESEARCH: "research",
    SalesPhase.ANALYSIS: "analysis",
    SalesPhase.STRATEGY: "strategy",
    SalesPhase.DELIVERABLE: "pitch_deck",
}

# Auto-handoff messages injected by the supervisor when
# transitioning to a new phase without user input.
HANDOFF_PROMPTS: dict[SalesPhase, str] = {
    SalesPhase.RESEARCH: (
        "Customer data gathering is complete. "
        "Research regional energy incentives, pricing, and "
        "market data for this customer's area."
    ),
    SalesPhase.ANALYSIS: (
        "Market research is complete. "
        "Run the data analysis: geocode the customer, pull PVGIS "
        "solar yield, fetch SMARD wholesale prices, and infer house "
        "type, heating costs, optimal product bundle, and financing."
    ),
    SalesPhase.STRATEGY: (
        "Analysis is complete with solar yield, retail price, and "
        "bundle inferred. Propose a personalized sales strategy for "
        "this customer grounded in those numbers."
    ),
    SalesPhase.DELIVERABLE: (
        "The sales strategy has been finalized. "
        "Generate the personalized pitch deck for the customer."
    ),
}


def _get_sales_data(context: AgentContext) -> SalesData:
    raw = context.shared_state.get("sales_data")
    if isinstance(raw, SalesData):
        return raw
    if isinstance(raw, dict):
        return SalesData(**raw)
    return SalesData()


def _save_sales_data(
    context: AgentContext, data: SalesData
) -> None:
    context.shared_state["sales_data"] = data.model_dump()


class SalesSupervisor(AgentOrchestrator):
    """Phase-based orchestrator for the sales pipeline.

    Routes messages to the correct specialist agent based on the
    current phase. When a phase transition occurs, automatically
    triggers the next agent with a handoff message — the user
    does not need to send a message between phases.
    """

    async def route(
        self, context: AgentContext, message: AgentMessage
    ) -> BaseAgent:
        sales_data = _get_sales_data(context)
        phase = sales_data.phase

        agent_name = PHASE_AGENT_MAP.get(phase)
        if agent_name:
            agent = registry.get(agent_name)
            if agent:
                logger.info(
                    f"Supervisor routing to '{agent_name}' "
                    f"(phase={phase.value})"
                )
                return agent

        logger.warning(
            f"No agent for phase '{phase.value}', "
            f"falling back to score-based routing"
        )
        return await super().route(context, message)

    def _detect_phase_change(
        self, context: AgentContext, phase_before: SalesPhase
    ) -> SalesPhase | None:
        """Return the new phase if it changed, else None."""
        sales_data = _get_sales_data(context)
        if sales_data.phase != phase_before:
            # Agent already advanced the phase
            return sales_data.phase

        # Safety-net check based on data conditions
        if (
            sales_data.phase == SalesPhase.DATA_GATHERING
            and sales_data.is_gathering_complete()
        ):
            return SalesPhase.RESEARCH
        if (
            sales_data.phase == SalesPhase.RESEARCH
            and sales_data.is_research_complete()
        ):
            return SalesPhase.ANALYSIS
        if (
            sales_data.phase == SalesPhase.ANALYSIS
            and sales_data.is_analysis_complete()
        ):
            return SalesPhase.STRATEGY
        if (
            sales_data.phase == SalesPhase.STRATEGY
            and sales_data.is_strategy_complete()
        ):
            return SalesPhase.DELIVERABLE

        return None

    async def _run_agent(
        self,
        context: AgentContext,
        message: AgentMessage,
    ) -> AgentMessage:
        """Route to the right agent and execute one turn."""
        agent = await self.route(context, message)
        context.current_step += 1
        response = await agent.execute(context, message)
        context.history.append(message)
        context.history.append(response)
        return response

    # ------------------------------------------------------------------
    # execute(): used by the REST (non-streaming) path
    # ------------------------------------------------------------------

    async def execute(
        self, context: AgentContext, message: AgentMessage
    ) -> AgentMessage:
        phase_before = _get_sales_data(context).phase

        response = await self._run_agent(context, message)

        new_phase = self._detect_phase_change(
            context, phase_before
        )
        if not new_phase or new_phase == phase_before:
            return response

        # Phase changed — auto-trigger the next agent
        logger.info(
            f"Auto-handoff: {phase_before.value} -> "
            f"{new_phase.value}"
        )
        sd = _get_sales_data(context)
        sd.phase = new_phase
        _save_sales_data(context, sd)

        handoff_prompt = HANDOFF_PROMPTS.get(new_phase, "Continue.")
        handoff_msg = AgentMessage(
            role=MessageRole.USER,
            content=handoff_prompt,
        )

        next_response = await self._run_agent(
            context, handoff_msg
        )

        # Combine both responses so the user sees the full picture
        combined_content = (
            response.content
            + "\n\n---\n\n"
            + next_response.content
        )
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=combined_content,
            agent_name=next_response.agent_name,
            metadata=next_response.metadata,
        )

    # ------------------------------------------------------------------
    # stream(): used by the WebSocket path
    # ------------------------------------------------------------------

    async def stream(
        self, context: AgentContext, message: AgentMessage
    ) -> AsyncIterator[dict]:
        phase_before = _get_sales_data(context).phase

        # Run the current-phase agent
        agent = await self.route(context, message)
        yield {"type": "agent_selected", "agent": agent.name}

        context.current_step += 1
        response = await agent.execute(context, message)
        context.history.append(message)
        context.history.append(response)

        yield {
            "type": "message",
            "content": response.content,
            "agent": agent.name,
        }

        # Check for phase transition
        new_phase = self._detect_phase_change(
            context, phase_before
        )
        if new_phase and new_phase != phase_before:
            sd = _get_sales_data(context)
            sd.phase = new_phase
            _save_sales_data(context, sd)

            yield {
                "type": "phase_changed",
                "phase": new_phase.value,
            }

            # Auto-trigger the next agent
            handoff_prompt = HANDOFF_PROMPTS.get(
                new_phase, "Continue."
            )
            handoff_msg = AgentMessage(
                role=MessageRole.USER,
                content=handoff_prompt,
            )

            next_agent = await self.route(
                context, handoff_msg
            )
            yield {
                "type": "agent_selected",
                "agent": next_agent.name,
            }

            context.current_step += 1
            next_response = await next_agent.execute(
                context, handoff_msg
            )
            context.history.append(handoff_msg)
            context.history.append(next_response)

            yield {
                "type": "message",
                "content": next_response.content,
                "agent": next_agent.name,
            }

        yield {"type": "done"}
