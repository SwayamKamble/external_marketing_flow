"""End-to-end pipeline test that simulates the full dashboard flow."""

import asyncio
import sys

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from contentforge.core.config_loader import ConfigLoader
from contentforge.core.file_memory import FileMemory
from contentforge.core.llm_gateway import LLMGateway
from contentforge.core.logger import PipelineLogger
from contentforge.core.prompt_loader import PromptLoader
from contentforge.core.graph import build_pipeline_graph, DEFAULT_INTERRUPTS
from contentforge.core.state import ContentForgeState
from contentforge.nodes._base import NodeContext


def make_ctx(week_id):
    config = ConfigLoader("config")
    memory = FileMemory(data_dir="data")
    llm = LLMGateway(config=config)
    logger = PipelineLogger(log_dir="data/logs", log_level="DEBUG")
    prompts = PromptLoader(prompts_dir="prompts")
    brand = memory.get_brand_context()
    return NodeContext(
        week_id=week_id,
        config=config,
        memory=memory,
        llm=llm,
        logger=logger,
        prompts=prompts,
        brand_context=brand,
    )


async def main():
    wid = "e2e-test-003"
    ctx = make_ctx(wid)
    cfg = {"configurable": {"thread_id": wid}}

    # ── STEP 1: Start pipeline ──
    print("=" * 60)
    print("STEP 1: Start pipeline")
    print("=" * 60)
    app = build_pipeline_graph(ctx)
    initial = ContentForgeState(
        pipeline_status="research",
        raw_research=[],
        topic_bank=[],
        content={},
        carousel_status="",
    )
    await app.ainvoke(initial.model_dump(), config=cfg)
    snap = app.get_state(cfg)
    print(f"  Status:  {snap.values.get('pipeline_status')}")
    print(f"  Next:    {snap.next}")
    print(f"  Prompts: {len(snap.values.get('research_prompts', []))}")
    assert snap.next == ("research_parser",), f"Expected interrupt at research_parser, got {snap.next}"
    print("  OK\n")

    # ── STEP 2: Supply raw research ──
    print("=" * 60)
    print("STEP 2: Supply raw research")
    print("=" * 60)
    resume_int = [i for i in DEFAULT_INTERRUPTS if i != "research_parser"]
    app2 = build_pipeline_graph(ctx, interrupt_before=resume_int)
    app2.update_state(cfg, {
        "human_action_required": False,
        "human_action_type": None,
        "raw_research": [
            "AI agents are transforming enterprise workflows. Key developments include "
            "autonomous coding assistants, multi-agent orchestration frameworks, and "
            "specialized vertical AI tools.\n\n"
            "Topics:\n"
            "1) Autonomous code generation tools like Cursor and GitHub Copilot are "
            "changing how developers work. They can now write entire features.\n"
            "2) Multi-agent frameworks such as CrewAI and AutoGen enable teams of AI "
            "agents to collaborate on complex tasks.\n"
            "3) AI in healthcare diagnostics - new FDA-approved AI tools for radiology.\n"
            "4) Edge AI deployment is growing with smaller, faster models.\n"
            "5) LLM fine-tuning best practices for domain-specific applications.\n"
            "6) AI regulation in EU - the AI Act enforcement begins.\n"
            "7) Open source vs closed source models - the Llama 4 effect.\n"
            "8) AI-powered customer service replacing traditional call centers.\n"
            "9) Retrieval Augmented Generation (RAG) pipelines for enterprise.\n"
            "10) AI video generation tools (Sora, Runway) hitting mainstream."
        ],
    })
    await app2.ainvoke(None, config=cfg)
    snap2 = app2.get_state(cfg)
    st2 = ContentForgeState(**snap2.values)
    print(f"  Status:  {snap2.values.get('pipeline_status')}")
    print(f"  Next:    {snap2.next}")
    print(f"  Topics:  {len(st2.topic_bank)}")
    print(f"  Plan:    {len(st2.weekly_plan)}")
    plan_ids = [p.topic_id for p in st2.weekly_plan if p.topic_id]
    print(f"  Plan IDs: {plan_ids}")
    assert snap2.next == ("deep_prompt",), f"Expected interrupt at deep_prompt, got {snap2.next}"
    print("  OK\n")

    # ── STEP 3: Select topics ──
    print("=" * 60)
    print("STEP 3: Select topics")
    print("=" * 60)
    sel = plan_ids[:1]  # Select just 1 topic for speed
    print(f"  Selecting: {sel}")

    resume_int3 = [i for i in DEFAULT_INTERRUPTS if i != "deep_prompt"]
    app3 = build_pipeline_graph(ctx, interrupt_before=resume_int3)
    app3.update_state(cfg, {
        "human_action_required": False,
        "human_action_type": None,
        "selected_topics": sel,
        "topic_queue": sel,
        "pending_topic_id": sel[0],
        "topic_index": 1,
        "topic_total": len(sel),
    })
    await app3.ainvoke(None, config=cfg)
    snap3 = app3.get_state(cfg)
    print(f"  Status:  {snap3.values.get('pipeline_status')}")
    print(f"  Next:    {snap3.next}")
    print(f"  Pending: {snap3.values.get('pending_topic_id')}")
    assert snap3.next == ("deep_parse",), f"Expected interrupt at deep_parse, got {snap3.next}"
    print("  OK\n")

    # ── STEP 4: Supply deep research ──
    print("=" * 60)
    print("STEP 4: Supply deep research")
    print("=" * 60)
    tid = snap3.values.get("pending_topic_id")
    print(f"  Topic: {tid}")

    resume_int4 = [i for i in DEFAULT_INTERRUPTS if i not in ("deep_parse", "deep_prompt")]
    app4 = build_pipeline_graph(ctx, interrupt_before=resume_int4)
    app4.update_state(cfg, {
        "human_action_required": False,
        "human_action_type": None,
        "raw_deep_research": {
            tid: (
                "Detailed research about this topic. Key statistics show 40% adoption "
                "rate in enterprise. Expert quotes from leading researchers. Recent "
                "developments include new open-source frameworks. Performance benchmarks "
                "show 3x improvement. Market size projected at $50B by 2027. Key players "
                "include major tech companies. User adoption growing 200% YoY."
            )
        },
    })
    try:
        await app4.ainvoke(None, config=cfg)
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Get state even after error
        snap4 = app4.get_state(cfg)
        print(f"  Status after error: {snap4.values.get('pipeline_status')}")
        print(f"  Next after error:   {snap4.next}")
        print(f"  Content keys:       {list(snap4.values.get('content', {}).keys())}")
        print(f"  Queue:              {snap4.values.get('topic_queue')}")
        return

    snap4 = app4.get_state(cfg)
    print(f"  Status:  {snap4.values.get('pipeline_status')}")
    print(f"  Next:    {snap4.next}")
    print(f"  Pending: {snap4.values.get('pending_topic_id')}")
    print(f"  Content: {list(snap4.values.get('content', {}).keys())}")
    print(f"  Queue:   {snap4.values.get('topic_queue')}")
    assert snap4.next == ("edit_router",), f"Expected interrupt at edit_router, got {snap4.next}"
    print("  OK\n")

    # ── STEP 5: Approve content ──
    print("=" * 60)
    print("STEP 5: Approve content")
    print("=" * 60)
    
    # Simulate human approval
    from contentforge.core.state import ContentStatus
    updated_content = dict(snap4.values.get("content", {}))
    if tid in updated_content:
        tc = updated_content[tid]
        tc.status = ContentStatus.APPROVED
        updated_content[tid] = tc

    # Re-run graph bypassing edit_router
    resume_int5 = [i for i in DEFAULT_INTERRUPTS if i != "edit_router"]
    app5 = build_pipeline_graph(ctx, interrupt_before=resume_int5)
    app5.update_state(cfg, {
        "human_action_required": False,
        "human_action_type": None,
        "content": updated_content,
        "pipeline_status": "export",
    }, as_node="edit_router")
    
    await app5.ainvoke(None, config=cfg)
    snap5 = app5.get_state(cfg)
    print(f"  Status:  {snap5.values.get('pipeline_status')}")
    print(f"  Next:    {snap5.next}")
    print(f"  OK\n")

    print("=" * 60)
    print("E2E TEST COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
