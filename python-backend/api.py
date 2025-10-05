# Import config first to set up environment variables
import config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4
import time
import logging

from simple_agents import (
    simple_triage_agent,
    simple_faq_agent,
    simple_trip_agent,
)
from main import create_initial_context
from optimized_agents import context_manager

from agents import (
    Runner,
    ItemHelpers,
    MessageOutputItem,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
    Handoff,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration (adjust as needed for deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Models
# =========================

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

class MessageResponse(BaseModel):
    content: str
    agent: str

class AgentEvent(BaseModel):
    id: str
    type: str
    agent: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None

class ChatResponse(BaseModel):
    conversation_id: str
    current_agent: str
    messages: List[MessageResponse]
    events: List[AgentEvent]
    context: Dict[str, Any]
    agents: List[Dict[str, Any]]

# =========================
# In-memory store for conversation state
# =========================

class ConversationStore:
    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        pass

    def save(self, conversation_id: str, state: Dict[str, Any]):
        pass

class InMemoryConversationStore(ConversationStore):
    _conversations: Dict[str, Dict[str, Any]] = {}

    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self._conversations.get(conversation_id)

    def save(self, conversation_id: str, state: Dict[str, Any]):
        self._conversations[conversation_id] = state

# TODO: when deploying this app in scale, switch to your own production-ready implementation
conversation_store = InMemoryConversationStore()

# =========================
# Helpers
# =========================

def _get_agent_by_name(name: str):
    """Return the agent object by name."""
    agents = {
        simple_triage_agent.name: simple_triage_agent,
        simple_faq_agent.name: simple_faq_agent,
        simple_trip_agent.name: simple_trip_agent,
    }
    return agents.get(name, simple_triage_agent)


def _build_agents_list() -> List[Dict[str, Any]]:
    """Build a list of all available agents and their metadata."""
    def make_agent_dict(agent):
        return {
            "name": agent.name,
            "description": getattr(agent, "handoff_description", ""),
            "handoffs": [getattr(h, "agent_name", getattr(h, "name", "")) for h in getattr(agent, "handoffs", [])],
            "tools": [getattr(t, "name", getattr(t, "__name__", "")) for t in getattr(agent, "tools", [])],
        }
    return [
        make_agent_dict(simple_triage_agent),
        make_agent_dict(simple_faq_agent),
        make_agent_dict(simple_trip_agent),
    ]

# =========================
# Main Chat Endpoint
# =========================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Main chat endpoint for agent orchestration.
    Handles conversation state, agent routing, and guardrail checks.
    """
    # Initialize or retrieve conversation state
    is_new = not req.conversation_id or conversation_store.get(req.conversation_id) is None
    if is_new:
        conversation_id: str = uuid4().hex
        ctx = create_initial_context()
        current_agent_name = simple_triage_agent.name
        state: Dict[str, Any] = {
            "input_items": [],
            "context": ctx,
            "current_agent": current_agent_name,
        }
        if req.message.strip() == "":
            conversation_store.save(conversation_id, state)
            return ChatResponse(
                conversation_id=conversation_id,
                current_agent=current_agent_name,
                messages=[],
                events=[],
                context=ctx.model_dump(),
                agents=_build_agents_list(),
                guardrails=[],
            )
    else:
        conversation_id = req.conversation_id  # type: ignore
        state = conversation_store.get(conversation_id)

    current_agent = _get_agent_by_name(state["current_agent"])
    state["input_items"].append({"content": req.message, "role": "user"})
    old_context = state["context"].model_dump().copy()

    try:
        # Add message to context manager
        context_manager.add_message("user", req.message)
        
        # Optimize input for free tier - limit conversation history
        optimized_input = state["input_items"][-config.MAX_CONVERSATION_HISTORY:] if len(state["input_items"]) > config.MAX_CONVERSATION_HISTORY else state["input_items"]
        
        # Apply rate limiting
        await config.rate_limiter.wait()
        
        # Use the original Runner.run method with optimizations
        result = await Runner.run(current_agent, optimized_input, context=state["context"])
        
        # Add response to context manager
        if hasattr(result, 'final_output'):
            context_manager.add_message("assistant", str(result.final_output), current_agent.name)
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        # Return a fallback response
        fallback_message = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
        state["input_items"].append({"role": "assistant", "content": fallback_message})
        return ChatResponse(
            conversation_id=conversation_id,
            current_agent=current_agent.name,
            messages=[MessageResponse(content=fallback_message, agent=current_agent.name)],
            events=[],
            context=state["context"].model_dump(),
            agents=_build_agents_list(),
        )

    messages: List[MessageResponse] = []
    events: List[AgentEvent] = []

    handed_off = False
    for item in result.new_items:
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            messages.append(MessageResponse(content=text, agent=item.agent.name))
            events.append(AgentEvent(id=uuid4().hex, type="message", agent=item.agent.name, content=text))
        # Handle handoff output and agent switching
        elif isinstance(item, HandoffOutputItem):
            # Record the handoff event
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="handoff",
                    agent=item.source_agent.name,
                    content=f"{item.source_agent.name} -> {item.target_agent.name}",
                    metadata={"source_agent": item.source_agent.name, "target_agent": item.target_agent.name},
                )
            )
            # If there is an on_handoff callback defined for this handoff, show it as a tool call
            from_agent = item.source_agent
            to_agent = item.target_agent
            # Find the Handoff object on the source agent matching the target
            ho = next(
                (h for h in getattr(from_agent, "handoffs", [])
                 if isinstance(h, Handoff) and getattr(h, "agent_name", None) == to_agent.name),
                None,
            )
            if ho:
                fn = ho.on_invoke_handoff
                fv = fn.__code__.co_freevars
                cl = fn.__closure__ or []
                if "on_handoff" in fv:
                    idx = fv.index("on_handoff")
                    if idx < len(cl) and cl[idx].cell_contents:
                        cb = cl[idx].cell_contents
                        cb_name = getattr(cb, "__name__", repr(cb))
                        events.append(
                            AgentEvent(
                                id=uuid4().hex,
                                type="tool_call",
                                agent=to_agent.name,
                                content=cb_name,
                            )
                        )
            current_agent = item.target_agent
            handed_off = True
        elif isinstance(item, ToolCallItem):
            tool_name = getattr(item.raw_item, "name", None)
            raw_args = getattr(item.raw_item, "arguments", None)
            tool_args: Any = raw_args
            if isinstance(raw_args, str):
                try:
                    import json
                    tool_args = json.loads(raw_args)
                except Exception:
                    pass
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="tool_call",
                    agent=item.agent.name,
                    content=tool_name or "",
                    metadata={"tool_args": tool_args},
                )
            )
            # If the tool is display_seat_map, send a special message so the UI can render the seat selector.
            if tool_name == "display_seat_map":
                messages.append(
                    MessageResponse(
                        content="DISPLAY_SEAT_MAP",
                        agent=item.agent.name,
                    )
                )
        elif isinstance(item, ToolCallOutputItem):
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="tool_output",
                    agent=item.agent.name,
                    content=str(item.output),
                    metadata={"tool_result": item.output},
                )
            )

    # If a handoff occurred, immediately run the target agent once so it can respond/action
    if handed_off:
        try:
            # Apply rate limiting before the follow-up run
            await config.rate_limiter.wait()
            followup_result = await Runner.run(current_agent, state["input_items"], context=state["context"])
            for item in followup_result.new_items:
                if isinstance(item, MessageOutputItem):
                    text = ItemHelpers.text_message_output(item)
                    messages.append(MessageResponse(content=text, agent=item.agent.name))
                    events.append(AgentEvent(id=uuid4().hex, type="message", agent=item.agent.name, content=text))
                elif isinstance(item, ToolCallItem):
                    tool_name = getattr(item.raw_item, "name", None)
                    raw_args = getattr(item.raw_item, "arguments", None)
                    tool_args: Any = raw_args
                    if isinstance(raw_args, str):
                        try:
                            import json
                            tool_args = json.loads(raw_args)
                        except Exception:
                            pass
                    events.append(
                        AgentEvent(
                            id=uuid4().hex,
                            type="tool_call",
                            agent=item.agent.name,
                            content=tool_name or "",
                            metadata={"tool_args": tool_args},
                        )
                    )
                    if tool_name == "display_seat_map":
                        messages.append(
                            MessageResponse(
                                content="DISPLAY_SEAT_MAP",
                                agent=item.agent.name,
                            )
                        )
                elif isinstance(item, ToolCallOutputItem):
                    events.append(
                        AgentEvent(
                            id=uuid4().hex,
                            type="tool_output",
                            agent=item.agent.name,
                            content=str(item.output),
                            metadata={"tool_result": item.output},
                        )
                    )
        except Exception as e:
            logger.error(f"Error during follow-up run after handoff: {e}")

    new_context = state["context"].dict()
    changes = {k: new_context[k] for k in new_context if old_context.get(k) != new_context[k]}
    if changes:
        events.append(
            AgentEvent(
                id=uuid4().hex,
                type="context_update",
                agent=current_agent.name,
                content="",
                metadata={"changes": changes},
            )
        )

    state["input_items"] = result.to_input_list()
    state["current_agent"] = current_agent.name
    conversation_store.save(conversation_id, state)

    return ChatResponse(
        conversation_id=conversation_id,
        current_agent=current_agent.name,
        messages=messages,
        events=events,
        context=state["context"].model_dump(),
        agents=_build_agents_list(),
    )
