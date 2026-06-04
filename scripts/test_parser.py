"""Direct test of research parser with actual user data."""
import asyncio, sys, os

# Add both src and project root to path
sys.path.insert(0, os.path.abspath("src"))
sys.path.insert(0, os.path.abspath("."))

from api.dependencies import init_system, get_node_context
from contentforge.nodes.research.research_parser import ResearchParser

async def test():
    await init_system()
    ctx = get_node_context(week_id="test-parse")
    parser = ResearchParser()
    with open("data/weeks/2026-W41/01_research/submitted_raw_research.md", "r", encoding="utf-8") as f:
        raw = f.read()
    print(f"Input length: {len(raw)} chars")
    result = await parser.process({"raw_research": [raw]}, ctx)
    topics = result.get("topic_bank", [])
    print(f"\nParser returned {len(topics)} topics")
    for t in topics:
        print(f"  [{t.suggested_format.value}] {t.title} - {t.summary[:60]}...")
    if not topics:
        print("\nFAILED - 0 topics extracted")
    else:
        print("\nSUCCESS!")

asyncio.run(test())
