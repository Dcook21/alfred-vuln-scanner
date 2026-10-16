import json
import anthropic


def classify_findings(api_key: str, changes: dict) -> list:
    """
    Turn raw diff findings into structured notes Alfred can log and display.
    Returns a list of dicts: port, severity, status, note, recommended_action.
    Falls back to a minimal structure if the model doesn't return valid JSON.
    """
    if not any(changes.values()):
        return []

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "You are Alfred, a security triage agent reviewing scan findings for "
        "a system the operator owns. You are read-only: you observe and "
        "advise, you do not take action on the target yourself.\n\n"
        "For every finding below, return one JSON object with these exact keys:\n"
        '  "port": the port number as a string\n'
        '  "severity": one of "low", "medium", "high"\n'
        '  "status": one of "informational", "potential_threat", "confirmed_threat"\n'
        '  "note": one sentence describing what you observed\n'
        '  "recommended_action": one sentence, plain language, on what the '
        "operator should do about it\n\n"
        "Respond with ONLY a JSON array of these objects, no prose, no markdown "
        "fences, nothing else.\n\n"
        f"Findings: {json.dumps(changes)}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text").strip()

    try:
        notes = json.loads(raw)
        if isinstance(notes, list):
            return notes
    except json.JSONDecodeError:
        pass

    # Fallback: model didn't return clean JSON. Don't lose the finding —
    # log it as an unclassified note rather than silently dropping it.
    return [{
        "port": "unknown",
        "severity": "medium",
        "status": "potential_threat",
        "note": "Classification response could not be parsed as structured data.",
        "recommended_action": f"Review raw findings manually: {changes}",
    }]


def ask_alfred(api_key: str, question: str, status: dict, recent_alerts: list) -> str:
    """Answer a free-text question about current scan status and recent alerts."""
    client = anthropic.Anthropic(api_key=api_key)
    context = {
        "current_status": status,
        "recent_alerts": recent_alerts[:10],
    }
    prompt = (
        "You are Alfred, a personal security agent with a distinct voice: "
        "formal, dry, understated, a little protective of the operator and "
        "their system. You are competent and proactive, but you are not, "
        "and never claim to be, any copyrighted character (fictional butler, "
        "fictional AI, or otherwise) — you're your own thing, inspired by "
        "the general idea of a loyal, capable aide, nothing more specific "
        "than that. You are read-only: you observe and advise on the target "
        "system, you do not take action on it yourself.\n\n"
        "Answer the operator's question using only the context provided "
        "below. If the context doesn't contain the answer, say so plainly "
        "rather than guessing — do not invent findings or status that "
        "aren't in the context. Stay in voice, but keep it brief: a few "
        "sentences, not a report.\n\n"
        f"Context: {json.dumps(context)}\n\n"
        f"Question: {question}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
