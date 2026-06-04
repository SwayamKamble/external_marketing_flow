"""Node to bundle content into a zip or final directory structure."""

from __future__ import annotations

import os
import shutil
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


class FilePackager(BaseNode):
    """Packages all artifacts for a specific week/topic into a zip/folder.

    Prepares the final handoff file structure (e.g. for a social media
    manager to download as a Zip from a frontend).
    """

    node_name = "file_packager"
    category = "export"
    description = "Packages the final content payload into delivery folders."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        
        if not context.week_id or not topic_id:
            return {"pipeline_status": "export"}

        # In a production system, this would gather all artifacts from `data/<week_id>`
        # and zip them up.
        
        out_path = os.path.join("data", context.week_id, "exports", topic_id)
        os.makedirs(out_path, exist_ok=True)
        
        # We simulate the packaging by just returning the path and a 'done' flag
        if context.logger:
             context.logger.event("files.packaged", {"path": out_path})

        return {"pipeline_status": "export", "delivery_path": out_path}
