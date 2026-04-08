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
    SalesPhase.STRATEGY: "strategy",
    SalesPhase.DELIVERABLE: "pitch_deck",
}

# Handoff prompts — only used for automatic silent transitions
HANDOFF_PROMPTS: dict[SalesPhase, str] = {
    SalesPhase.RESEARCH: (
        "Customer data is complete. Research regional energy incentives, "
        "pricing, and market data for this customer's area. Present your "
        "findings to the installer and ask if they have any additional "
        "context or priorities before moving to strategy."
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
    """Phase-based orchestrator for the Cleo, Cloover's AI Sales Coach.

    Key behaviors:
    - If lead data is already complete, skip data gathering → research
    - Research auto-triggers after data gathering completes
    - Research → Strategy requires user acknowledgment (interactive)
    - Strategy → Deliverable requires user saying "ready"
    - Deliverable auto-triggers after strategy is marked complete
    """

    def _maybe_fast_forward(self, context: AgentContext) -> bool:
        """On first interaction, if data is already complete, advance past gathering."""
        sd = _get_sales_data(context)
        # Skip gathering if data is complete (phase may already be RESEARCH from load)
        if sd.is_gathering_complete() and sd.phase in (SalesPhase.DATA_GATHERING, SalesPhase.RESEARCH):
            if sd.phase == SalesPhase.DATA_GATHERING:
                sd.phase = SalesPhase.RESEARCH
                _save_sales_data(context, sd)
            # Only fast-forward if no research has been done yet
            if not sd.regional_incentives and not sd.market_trends:
                logger.info("Lead data complete, no research yet — fast-forwarding to research")
                return True
        return False

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
            return sales_data.phase

        # Only auto-advance from data_gathering → research
        if (
            sales_data.phase == SalesPhase.DATA_GATHERING
            and sales_data.is_gathering_complete()
        ):
            return SalesPhase.RESEARCH

        # Strategy → Deliverable auto-advance when strategy is marked complete
        if (
            sales_data.phase == SalesPhase.STRATEGY
            and sales_data.is_strategy_complete()
        ):
            return SalesPhase.DELIVERABLE

        # Research → Strategy and other transitions are MANUAL
        # (the agent will set the phase when the user says to proceed)
        return None

    async def _run_agent(
        self,
        context: AgentContext,
        message: AgentMessage,
    ) -> AgentMessage:
        agent = await self.route(context, message)
        context.current_step += 1
        response = await agent.execute(context, message)
        context.history.append(message)
        context.history.append(response)
        return response

    async def execute(
        self, context: AgentContext, message: AgentMessage
    ) -> AgentMessage:
        # Fast-forward on first message if data is complete
        fast_forwarded = self._maybe_fast_forward(context)

        if fast_forwarded:
            # Inject the research handoff as the message
            sd = _get_sales_data(context)
            intro = (
                f"I already have the details for {sd.customer_name or 'this customer'} "
                f"in {sd.city or 'their area'}. Let me research the market "
                f"and incentives for their situation.\n\n"
                f"*Please hold on while I look into this...*"
            )

            handoff_msg = AgentMessage(
                role=MessageRole.USER,
                content=HANDOFF_PROMPTS.get(SalesPhase.RESEARCH, "Research this customer."),
            )
            research_response = await self._run_agent(context, handoff_msg)

            combined = intro + "\n\n---\n\n" + research_response.content
            return AgentMessage(
                role=MessageRole.ASSISTANT,
                content=combined,
                agent_name=research_response.agent_name,
                metadata={
                    "phase": "research",
                    **(research_response.metadata or {}),
                },
            )

        phase_before = _get_sales_data(context).phase
        response = await self._run_agent(context, message)

        new_phase = self._detect_phase_change(context, phase_before)
        if not new_phase or new_phase == phase_before:
            return response

        # Phase changed — auto-trigger next agent only for
        # data_gathering→research and strategy→deliverable
        logger.info(f"Auto-handoff: {phase_before.value} -> {new_phase.value}")
        sd = _get_sales_data(context)
        sd.phase = new_phase
        _save_sales_data(context, sd)

        handoff_prompt = HANDOFF_PROMPTS.get(new_phase)
        if not handoff_prompt:
            # No auto-handoff for this transition (e.g. research→strategy)
            return response

        handoff_msg = AgentMessage(
            role=MessageRole.USER,
            content=handoff_prompt,
        )
        next_response = await self._run_agent(context, handoff_msg)

        combined_content = (
            response.content + "\n\n---\n\n" + next_response.content
        )
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=combined_content,
            agent_name=next_response.agent_name,
            metadata=next_response.metadata,
        )

    async def stream(
        self, context: AgentContext, message: AgentMessage
    ) -> AsyncIterator[dict]:
        fast_forwarded = self._maybe_fast_forward(context)

        if fast_forwarded:
            sd = _get_sales_data(context)
            intro = (
                f"I already have the details for {sd.customer_name or 'this customer'} "
                f"in {sd.city or 'their area'}. Let me research the market "
                f"and incentives for their situation.\n\n"
                f"*Please hold on while I look into this...*"
            )
            yield {"type": "phase_changed", "phase": "research"}

            agent = await self.route(context, AgentMessage(
                role=MessageRole.USER,
                content=HANDOFF_PROMPTS.get(SalesPhase.RESEARCH, "Research."),
            ))
            yield {"type": "agent_selected", "agent": agent.name}

            context.current_step += 1
            handoff_msg = AgentMessage(
                role=MessageRole.USER,
                content=HANDOFF_PROMPTS.get(SalesPhase.RESEARCH, "Research."),
            )
            response = await agent.execute(context, handoff_msg)
            context.history.append(handoff_msg)
            context.history.append(response)

            yield {"type": "message", "content": intro + "\n\n---\n\n" + response.content, "agent": agent.name}
            yield {"type": "done"}
            return

        phase_before = _get_sales_data(context).phase
        agent = await self.route(context, message)
        yield {"type": "agent_selected", "agent": agent.name}

        context.current_step += 1
        response = await agent.execute(context, message)
        context.history.append(message)
        context.history.append(response)

        yield {"type": "message", "content": response.content, "agent": agent.name}

        new_phase = self._detect_phase_change(context, phase_before)
        if new_phase and new_phase != phase_before:
            sd = _get_sales_data(context)
            sd.phase = new_phase
            _save_sales_data(context, sd)
            yield {"type": "phase_changed", "phase": new_phase.value}

            handoff_prompt = HANDOFF_PROMPTS.get(new_phase)
            if handoff_prompt:
                handoff_msg = AgentMessage(role=MessageRole.USER, content=handoff_prompt)
                next_agent = await self.route(context, handoff_msg)
                yield {"type": "agent_selected", "agent": next_agent.name}

                context.current_step += 1
                next_response = await next_agent.execute(context, handoff_msg)
                context.history.append(handoff_msg)
                context.history.append(next_response)

                yield {"type": "message", "content": next_response.content, "agent": next_agent.name}

        yield {"type": "done"}
