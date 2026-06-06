"""FastAPI dependencies and system initialization."""

import os
from typing import AsyncGenerator

from fastapi import Request

from contentforge.core.config_loader import ConfigLoader
from contentforge.core.db import DatabaseManager
from contentforge.core.file_memory import FileMemory
from contentforge.core.llm_gateway import LLMGateway
from contentforge.core.logger import PipelineLogger
from contentforge.core.prompt_loader import PromptLoader
from contentforge.nodes._base import NodeContext

# Global instances (initialized on startup)
_db: DatabaseManager | None = None
_logger: PipelineLogger | None = None
_config: ConfigLoader | None = None
_memory: FileMemory | None = None
_llm: LLMGateway | None = None
_prompts: PromptLoader | None = None


async def init_system():
    """Initializes all singleton core dependencies."""
    global _db, _logger, _config, _memory, _llm, _prompts
    
    is_vercel = os.getenv("VERCEL") == "1"
    if is_vercel:
        import shutil
        if os.path.exists("data"):
            shutil.copytree("data", "/tmp/data", dirs_exist_ok=True)
        data_dir = "/tmp/data"
        log_dir = "/tmp/logs"
        db_path = "/tmp/pipeline.db"
    else:
        data_dir = "data"
        log_dir = "data/logs"
        db_path = os.getenv("PIPELINE_DB_PATH", "data/pipeline.db")

    _logger = PipelineLogger(
        log_dir=log_dir,
        log_level=os.getenv("LOG_LEVEL", "DEBUG"),
    )
    
    _db = DatabaseManager(db_path=db_path)
    _db.initialize()
    
    _config = ConfigLoader("config")
    _memory = FileMemory(data_dir=data_dir)
    
    # We load brand context early so that LLM gateway can utilize configuration immediately
    # though Gateway itself just uses config map
    _llm = LLMGateway(config=_config)
    _prompts = PromptLoader(prompts_dir="prompts")

    _logger.event("system.startup", {"status": "initialized"})


async def close_system():
    """Cleans up resources."""
    global _db
    if _db:
        _db.close()


def get_logger() -> PipelineLogger:
    assert _logger is not None, "System not initialized"
    return _logger


def get_config() -> ConfigLoader:
    assert _config is not None, "System not initialized"
    return _config


def get_memory() -> FileMemory:
    assert _memory is not None, "System not initialized"
    return _memory


def get_db() -> DatabaseManager:
    assert _db is not None, "System not initialized"
    return _db


def get_llm() -> LLMGateway:
    assert _llm is not None, "System not initialized"
    return _llm


def get_prompts() -> PromptLoader:
    assert _prompts is not None, "System not initialized"
    return _prompts


def get_node_context(week_id: str = "default_week") -> NodeContext:
    """Builds a complete NodeContext object using current singletons."""
    brand_context = {}
    if _memory:
        brand_context = _memory.get_brand_context()
        
    return NodeContext(
        week_id=week_id,
        config=get_config(),
        memory=get_memory(),
        llm=get_llm(),
        logger=get_logger(),
        prompts=get_prompts(),
        brand_context=brand_context
    )
