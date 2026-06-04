"""LangGraph state machine for ContentForge pipeline."""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from contentforge.core.state import ContentForgeState, enum_value, status_is
from contentforge.nodes._base import NodeContext

# Import all our nodes
from contentforge.nodes.research.brand_context_loader import BrandContextLoader
from contentforge.nodes.research.research_prompt_generator import ResearchPromptGenerator
from contentforge.nodes.research.research_parser import ResearchParser
from contentforge.nodes.scoring.topic_scorer import TopicScorer
from contentforge.nodes.scoring.calendar_planner import CalendarPlanner
from contentforge.nodes.deep_research.deep_research_prompt_generator import DeepResearchPromptGenerator
from contentforge.nodes.deep_research.deep_research_parser import DeepResearchParser
from contentforge.nodes.content.content_router import ContentRouter
from contentforge.nodes.content.theme_designer import ThemeDesigner
from contentforge.nodes.content.caption_writer import CaptionWriter
from contentforge.nodes.content.image_prompt_engineer import ImagePromptEngineer
from contentforge.nodes.content.carousel.carousel_creator import CarouselCreator
from contentforge.nodes.content.carousel.slide_content_writer import SlideContentWriter
from contentforge.nodes.content.carousel.react_code_generator import ReactCodeGenerator
from contentforge.nodes.content.reel.script_writer import ScriptWriter
from contentforge.nodes.editing.edit_router import EditRouter
from contentforge.nodes.editing.chat_edit_agent import ChatEditAgent
from contentforge.nodes.export.content_aggregator import ContentAggregator
from contentforge.nodes.export.file_packager import FilePackager


# Global checkpointer so API requests share the same state.
# Allowlist our state module types so strict msgpack mode remains compatible.
_checkpoint_serde = JsonPlusSerializer().with_msgpack_allowlist(
    [
        ("contentforge.core.state", "ContentFormat"),
        ("contentforge.core.state", "ContentStatus"),
        ("contentforge.core.state", "Topic"),
        ("contentforge.core.state", "PlanItem"),
        ("contentforge.core.state", "TopicContent"),
        ("contentforge.core.state", "DeepResearchItem"),
        ("contentforge.core.state", "Theme"),
        ("contentforge.core.state", "Caption"),
        ("contentforge.core.state", "CarouselSlide"),
        ("contentforge.core.state", "Platform"),
    ]
)
_shared_checkpointer = MemorySaver(serde=_checkpoint_serde)

DEFAULT_INTERRUPTS = ["research_parser", "deep_parse", "edit_router"]

def build_pipeline_graph(node_context: NodeContext, interrupt_before: list[str] | None = None) -> Any:
    """Builds and wires the full LangGraph state machine."""
    
    # Initialize the graph builder with our strictly typed Pydantic state
    workflow = StateGraph(ContentForgeState)

    def _state_input(state: ContentForgeState) -> dict[str, Any]:
        """Build a node input dict while preserving nested Pydantic objects.

        Using model_dump() here would recursively turn Topic/PlanItem models into
        plain dicts, but many nodes rely on attribute access (topic.id, etc.).
        """
        return {name: getattr(state, name) for name in state.__class__.model_fields}
    
    # ---------------------------------------------------------
    # 1. Instantiate Nodes (injecting context dependency)
    # ---------------------------------------------------------
    
    # Research Phase
    async def n_brand_loader(state: ContentForgeState):
        result = await BrandContextLoader().run(_state_input(state), node_context)
        return result

    async def n_prompt_gen(state: ContentForgeState):
        result = await ResearchPromptGenerator().run(_state_input(state), node_context)
        return result

    async def n_research_parser(state: ContentForgeState):
        result = await ResearchParser().run(_state_input(state), node_context)
        return result

    # Scoring & Planning
    async def n_scorer(state: ContentForgeState):
        result = await TopicScorer().run(_state_input(state), node_context)
        return result

    async def n_planner(state: ContentForgeState):
        result = await CalendarPlanner().run(_state_input(state), node_context)
        return result

    # Deep Research
    async def n_deep_prompt(state: ContentForgeState):
        result = await DeepResearchPromptGenerator().run(_state_input(state), node_context)
        return result

    async def n_deep_parse(state: ContentForgeState):
        result = await DeepResearchParser().run(_state_input(state), node_context)
        return result

    # Content Gen
    async def n_router(state: ContentForgeState):
        result = await ContentRouter().run(_state_input(state), node_context)
        return result

    async def n_theme(state: ContentForgeState):
        result = await ThemeDesigner().run(_state_input(state), node_context)
        return result

    async def n_captions(state: ContentForgeState):
        result = await CaptionWriter().run(_state_input(state), node_context)
        return result
        
    async def n_image_engineer(state: ContentForgeState):
        result = await ImagePromptEngineer().run(_state_input(state), node_context)
        return result

    async def n_carousel_create(state: ContentForgeState):
        result = await CarouselCreator().run(_state_input(state), node_context)
        return result

    async def n_slide_writer(state: ContentForgeState):
        result = await SlideContentWriter().run(_state_input(state), node_context)
        return result

    async def n_react_gen(state: ContentForgeState):
        result = await ReactCodeGenerator().run(_state_input(state), node_context)
        return result

    async def n_reel_script(state: ContentForgeState):
        result = await ScriptWriter().run(_state_input(state), node_context)
        return result

    # Editing & Export
    async def n_edit_router(state: ContentForgeState):
        result = await EditRouter().run(_state_input(state), node_context)
        return result

    async def n_chat_edit(state: ContentForgeState):
        result = await ChatEditAgent().run(_state_input(state), node_context)
        return result

    async def n_export_agg(state: ContentForgeState):
        result = await ContentAggregator().run(_state_input(state), node_context)
        return result

    async def n_packaging(state: ContentForgeState):
        result = await FilePackager().run(_state_input(state), node_context)
        return result

    # ---------------------------------------------------------
    # 2. Add Nodes to Graph
    # ---------------------------------------------------------
    workflow.add_node("brand_loader", n_brand_loader)
    workflow.add_node("prompt_gen", n_prompt_gen)
    workflow.add_node("research_parser", n_research_parser)
    workflow.add_node("scorer", n_scorer)
    workflow.add_node("planner", n_planner)
    
    workflow.add_node("deep_prompt", n_deep_prompt)
    workflow.add_node("deep_parse", n_deep_parse)
    
    workflow.add_node("content_router", n_router)
    workflow.add_node("theme_designer", n_theme)
    workflow.add_node("caption_writer", n_captions)
    workflow.add_node("image_prompt", n_image_engineer)
    
    workflow.add_node("carousel_supervisor", n_carousel_create)
    workflow.add_node("slide_writer", n_slide_writer)
    workflow.add_node("react_gen", n_react_gen)
    
    workflow.add_node("reel_script", n_reel_script)
    
    workflow.add_node("edit_router", n_edit_router)
    workflow.add_node("chat_edit", n_chat_edit)
    
    workflow.add_node("export_agg", n_export_agg)
    workflow.add_node("packaging", n_packaging)

    # ---------------------------------------------------------
    # 3. Define Conditional Edges (Routers)
    # ---------------------------------------------------------
    
    def format_router(state: ContentForgeState) -> str:
        """Determines which content format sub-graph to trigger.
        
        FIX: Previously only routed PENDING topics to format sub-graphs and
        sent everything else to edit_router, which meant DRAFT topics (already
        generated by carousel/reel/image) skipped theme_designer and caption_writer.
        Now DRAFT topics route to theme_designer to continue the normal flow.
        """
        tid = state.pending_topic_id
        if not tid or tid not in state.content:
            return "edit_router" # Fallback

        tc = state.content[tid]
        current_status = enum_value(tc.status)

        # APPROVED or EXPORTED topics go straight to edit_router → export
        if current_status in ("approved", "exported"):
            return "edit_router"

        # DRAFT topics already have content generated — skip format sub-graphs
        # and route to theme_designer to continue the normal flow
        # (theme → captions → edit → export)
        if current_status == "draft":
            return "theme_designer"

        # PENDING topics need content generation — route to format-specific nodes
        fmt = enum_value(tc.content_format)
        if fmt == "carousel":
            return "carousel_supervisor"
        elif fmt == "reel":
            return "reel_script"
        elif fmt == "single_image" or fmt == "news_post":
            return "image_prompt"
        return "edit_router"

    def carousel_router(state: ContentForgeState) -> str:
        """Determines carousel step based on internal status."""
        status = state.carousel_status
        if status == "generating_code":
            return "react_gen"
        elif status == "done":
            # Route to theme_designer so captions get generated too
            return "theme_designer"
        return "slide_writer"

    def edit_action_router(state: ContentForgeState) -> str:
        """Determines if we need human feedback or export."""
        # If human_action_required is True, LangGraph will interrupt.
        # Once resumed, we check if they gave feedback.
        if state.human_feedback:
            return "chat_edit"
        return "export_agg"

    def deep_research_router(state: ContentForgeState) -> str:
        """Loops deep research topic-by-topic until queue is exhausted."""
        if state.topic_queue:
            return "deep_prompt"
        return "content_router"

    def post_packaging_router(state: ContentForgeState) -> str:
        """After packaging one topic, continue with next topic if needed."""
        selected_topics = state.selected_topics or []
        if not selected_topics:
            return END

        for topic_id in selected_topics:
            tc = state.content.get(topic_id)
            if not tc:
                return "content_router"
            if not status_is(tc.status, "exported"):
                return "content_router"

        return END

    # ---------------------------------------------------------
    # 4. Wire the Edges
    # ---------------------------------------------------------
    
    workflow.set_entry_point("brand_loader")
    
    # Phase 1: Research
    workflow.add_edge("brand_loader", "prompt_gen")
    # Human interrupts here (paste raw research)
    workflow.add_edge("prompt_gen", "research_parser")
    workflow.add_edge("research_parser", "scorer")
    
    # Phase 2: Scoring & Planning
    workflow.add_edge("scorer", "planner")
    # Human interrupts here to approve/edit plan
    workflow.add_edge("planner", "deep_prompt")
    
    # Phase 3: Deep Research
    # Human interrupts to run deep prompts
    workflow.add_edge("deep_prompt", "deep_parse")
    workflow.add_conditional_edges("deep_parse", deep_research_router)

    # Phase 4: Content Generation
    # (Content Router branches out)
    workflow.add_conditional_edges("content_router", format_router)
    
    # - Carousel Sub-graph
    workflow.add_conditional_edges("carousel_supervisor", carousel_router)
    workflow.add_edge("slide_writer", "carousel_supervisor")
    workflow.add_edge("react_gen", "carousel_supervisor")
    
    # - Reel Sub-graph
    workflow.add_edge("reel_script", "theme_designer")
    
    # - Image Sub-graph
    workflow.add_edge("image_prompt", "theme_designer")
    
    # All branches eventually hit theme & captions
    workflow.add_edge("theme_designer", "caption_writer")
    workflow.add_edge("caption_writer", "edit_router")

    # Phase 5: Editing
    workflow.add_conditional_edges("edit_router", edit_action_router)
    workflow.add_edge("chat_edit", "edit_router") # Loop back

    # Phase 6: Export
    workflow.add_edge("export_agg", "packaging")
    workflow.add_conditional_edges("packaging", post_packaging_router)

    # ---------------------------------------------------------
    # 5. Compile!
    # ---------------------------------------------------------
    
    # Persist state so we can interrupt memory
    # interrupt_before: pause BEFORE these nodes run (user must provide input)
    # interrupt_after: pause AFTER planner runs (user must select topics)
    app = workflow.compile(
        checkpointer=_shared_checkpointer,
        interrupt_before=interrupt_before if interrupt_before is not None else DEFAULT_INTERRUPTS,
        interrupt_after=["planner"],
    )
    
    return app
