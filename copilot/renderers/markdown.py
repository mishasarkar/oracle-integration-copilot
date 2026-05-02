import json

from copilot.schemas import IntegrationSpec


def _json_block(payload) -> str:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            pass
    return json.dumps(payload, indent=2) if not isinstance(payload, str) else payload


def _normalise_pattern(raw: str) -> str:
    p = raw.lower().replace("-", "_").replace(" ", "_")
    if "schedule" in p:
        return "scheduled"
    if "event" in p:
        return "event_driven"
    if "request" in p or "response" in p or "synchronous" in p:
        return "request_response"
    if "file" in p or "ftp" in p or "sftp" in p or "batch" in p:
        return "file_based"
    return "scheduled"  # safe default for REST-based integrations


def _mermaid_diagram(spec: IntegrationSpec) -> str:
    src = spec.source.get("system", "Source")
    tgt = spec.target.get("system", "Target")
    pattern = _normalise_pattern(spec.pattern)

    lines = ["```mermaid", "sequenceDiagram"]

    if pattern == "scheduled":
        lines += [
            f"    participant Scheduler",
            f"    participant OIC as Oracle Integration Cloud",
            f"    participant Src as {src}",
            f"    participant Tgt as {tgt}",
            "",
            "    Scheduler->>OIC: Trigger (cron)",
            "    OIC->>Src: GET records",
            "    Src-->>OIC: Paginated response",
            "    loop For each record",
            "        OIC->>OIC: Transform & map fields",
            "        OIC->>Tgt: POST/PATCH record",
            "        Tgt-->>OIC: 201 Created / 200 OK",
            "    end",
            "    alt Record error",
            "        OIC->>OIC: Scope fault handler",
            "        OIC->>Notify: Alert (Slack / email)",
            "    end",
        ]
    elif pattern == "event_driven":
        lines += [
            f"    participant Src as {src}",
            f"    participant OIC as Oracle Integration Cloud",
            f"    participant Tgt as {tgt}",
            "",
            f"    Src->>OIC: Event / webhook payload",
            "    OIC->>OIC: Validate & transform",
            f"    OIC->>Tgt: POST record",
            f"    Tgt-->>OIC: Response",
            "    OIC-->>Src: Acknowledgement",
        ]
    elif pattern == "request_response":
        lines += [
            "    participant Caller",
            f"    participant OIC as Oracle Integration Cloud",
            f"    participant Tgt as {tgt}",
            "",
            "    Caller->>OIC: HTTP request",
            f"    OIC->>Tgt: Query / lookup",
            f"    Tgt-->>OIC: Result",
            "    OIC->>OIC: Transform response",
            "    OIC-->>Caller: HTTP response",
        ]
    else:  # file_based
        lines += [
            f"    participant Src as {src} (FTP/SFTP)",
            f"    participant OIC as Oracle Integration Cloud",
            f"    participant Tgt as {tgt}",
            "",
            "    OIC->>Src: Poll for new file",
            "    Src-->>OIC: File download",
            "    OIC->>OIC: Parse & transform records",
            f"    OIC->>Tgt: Batch upsert",
            f"    Tgt-->>OIC: Confirmation",
        ]

    lines.append("```")
    return "\n".join(lines)


def render(spec: IntegrationSpec) -> str:
    lines: list[str] = []

    lines.append(f"# {spec.title}")
    lines.append(f"\n**Pattern:** `{_normalise_pattern(spec.pattern)}`  ")
    lines.append(
        f"**Flow:** {spec.source.get('system', 'Source')} "
        f"→ Oracle Integration Cloud "
        f"→ {spec.target.get('system', 'Target')}"
    )

    lines.append("\n## Integration Flow\n")
    lines.append(_mermaid_diagram(spec))

    # Source
    lines.append("\n## Source System\n")
    lines.append(f"| Property | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| System | {spec.source.get('system', '—')} |")
    lines.append(f"| Endpoint | `{spec.source.get('endpoint', '—')}` |")
    lines.append(f"| Auth | {spec.source.get('auth', '—')} |")
    if spec.source.get("sample_payload"):
        lines.append("\n**Sample Source Payload:**\n")
        lines.append("```json")
        lines.append(_json_block(spec.source["sample_payload"]))
        lines.append("```")

    # Target
    lines.append("\n## Target System\n")
    lines.append(f"| Property | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| System | {spec.target.get('system', '—')} |")
    lines.append(f"| Endpoint | `{spec.target.get('endpoint', '—')}` |")
    lines.append(f"| Auth | {spec.target.get('auth', '—')} |")
    if spec.target.get("sample_payload"):
        lines.append("\n**Sample Target Payload:**\n")
        lines.append("```json")
        lines.append(_json_block(spec.target["sample_payload"]))
        lines.append("```")

    # Field mappings
    lines.append("\n## Field Mappings\n")
    lines.append("| Source Field | Target Field | Transformation | Required | Notes |")
    lines.append("|---|---|---|---|---|")
    for m in spec.mappings:
        transform = m.transformation or "—"
        notes = m.notes or "—"
        req = "Yes" if m.required else "No"
        lines.append(f"| `{m.source_field}` | `{m.target_field}` | {transform} | {req} | {notes} |")

    # Filters
    if spec.filters:
        lines.append("\n## Filters\n")
        for f in spec.filters:
            lines.append(f"- {f}")

    # Error handling
    lines.append("\n## Error Handling\n")
    if spec.error_handling:
        for e in spec.error_handling:
            lines.append(f"- {e}")
    else:
        lines.append("- *No error handling specified.*")

    # Monitoring
    if spec.monitoring:
        lines.append("\n## Monitoring\n")
        for m in spec.monitoring:
            lines.append(f"- {m}")

    # Assumptions and open questions
    lines.append("\n## Assumptions\n")
    lines.append(
        "> The following were inferred by the AI. **A human engineer must verify each one before building.**\n"
    )
    if spec.assumptions:
        for a in spec.assumptions:
            lines.append(f"- {a}")
    else:
        lines.append("- *None recorded.*")

    lines.append("\n## Open Questions\n")
    if spec.open_questions:
        for q in spec.open_questions:
            lines.append(f"- {q}")
    else:
        lines.append("- *None recorded.*")

    # References
    if spec.references:
        lines.append("\n## References\n")
        for r in spec.references:
            lines.append(f"- {r}")

    return "\n".join(lines)
