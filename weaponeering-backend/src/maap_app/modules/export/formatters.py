from __future__ import annotations

import csv
import io
import json
from typing import Any

from maap_app.modules.export.models import SIMULATION_LABEL


def to_markdown(title: str, sections: dict[str, Any]) -> str:
    lines = [f"# {title}", "", f"**{SIMULATION_LABEL}**", ""]
    for heading, content in sections.items():
        lines.append(f"## {heading}")
        lines.append("")
        if isinstance(content, list):
            for row in content:
                if isinstance(row, dict):
                    lines.append("- " + "; ".join(f"{k}: {v}" for k, v in row.items()))
                else:
                    lines.append(f"- {row}")
        elif isinstance(content, dict):
            for key, value in content.items():
                lines.append(f"- **{key}**: {value}")
        else:
            lines.append(str(content))
        lines.append("")
    return "\n".join(lines)


def to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"# {SIMULATION_LABEL}\n"
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def to_json_package(manifest: dict[str, Any], sections: dict[str, Any]) -> str:
    payload = {
        "simulation_label": SIMULATION_LABEL,
        "manifest": manifest,
        "sections": sections,
    }
    return json.dumps(payload, indent=2, ensure_ascii=True)
