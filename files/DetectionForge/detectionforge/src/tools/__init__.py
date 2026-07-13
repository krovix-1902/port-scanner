"""
tools.py — DetectionForge's toolbelt.

Each function here is a *tool* the agent can call (the function-calling /
tool-use capability). They are plain Python functions on purpose: that keeps
them portable — the same functions can be registered with the Gemini SDK's
automatic function calling OR wrapped in Google ADK's FunctionTool. See the
README "Porting to ADK" note.

NOTE: the heavier tools (map_attack, validate_sigma, convert_rule) ship with a
working baseline plus a clearly-marked TODO where you slot in the full corpus /
backend during the build week.
"""
from __future__ import annotations

import re
import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Tool 1: fetch_cti — pull and clean a threat-intel article
# ---------------------------------------------------------------------------
def fetch_cti(url: str) -> str:
    """Fetch a cyber threat intelligence article and return its cleaned text.

    Args:
        url: A public URL to a threat-intel blog post or report.
    Returns:
        The article's main text, stripped of nav/scripts, truncated to a safe
        length for the model context.
    """
    resp = requests.get(url, timeout=20, headers={"User-Agent": "DetectionForge/0.1"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text[:20000]  # keep context tight; CTI articles are rarely longer than this matters


# ---------------------------------------------------------------------------
# Tool 2: validate_sigma — syntactic validation via pySigma
# ---------------------------------------------------------------------------
def validate_sigma(sigma_yaml: str) -> dict:
    """Validate a Sigma rule's YAML structure with pySigma.

    This is the agent's *self-correction* signal: on failure the agent reads the
    error and regenerates the rule (the agentic loop). Returns a dict the model
    can reason over.

    Args:
        sigma_yaml: The candidate Sigma rule as a YAML string.
    Returns:
        {"valid": bool, "errors": list[str]}
    """
    try:
        from sigma.collection import SigmaCollection
        SigmaCollection.from_yaml(sigma_yaml)
        return {"valid": True, "errors": []}
    except Exception as e:  # pySigma raises typed errors; surface them to the model
        return {"valid": False, "errors": [f"{type(e).__name__}: {e}"]}


# ---------------------------------------------------------------------------
# Tool 3: convert_rule — Sigma -> SPL / Elastic via pySigma backends
# ---------------------------------------------------------------------------
def convert_rule(sigma_yaml: str) -> dict:
    """Convert a validated Sigma rule into Splunk SPL and an Elastic query.

    Args:
        sigma_yaml: A *validated* Sigma rule.
    Returns:
        {"splunk_spl": str|None, "elastic_query": str|None, "errors": list[str]}
    """
    out = {"splunk_spl": None, "elastic_query": None, "errors": []}
    try:
        from sigma.collection import SigmaCollection
        from sigma.backends.splunk import SplunkBackend
        rules = SigmaCollection.from_yaml(sigma_yaml)
        out["splunk_spl"] = SplunkBackend().convert(rules)[0]
    except Exception as e:
        out["errors"].append(f"splunk: {type(e).__name__}: {e}")
    try:
        from sigma.collection import SigmaCollection
        from sigma.backends.elasticsearch import LuceneBackend
        rules = SigmaCollection.from_yaml(sigma_yaml)
        out["elastic_query"] = LuceneBackend().convert(rules)[0]
    except Exception as e:
        out["errors"].append(f"elastic: {type(e).__name__}: {e}")
    return out


# ---------------------------------------------------------------------------
# Tool 4: map_attack — RAG over a local MITRE ATT&CK corpus
# ---------------------------------------------------------------------------
# Loaded once at import; populated by build_attack_index() during setup.
_ATTACK_INDEX = None


def map_attack(behaviour: str) -> list[dict]:
    """Map an observed behaviour to the most likely MITRE ATT&CK technique(s)
    using semantic search over a local ATT&CK corpus (embeddings, no API cost).

    Args:
        behaviour: Plain-language description of an adversary behaviour.
    Returns:
        Up to 3 candidate techniques: [{"technique_id","technique_name","tactic","score"}]
    """
    global _ATTACK_INDEX
    if _ATTACK_INDEX is None:
        # TODO (setup): call build_attack_index() once to load the STIX bundle.
        # Fallback: a tiny hardcoded map so the agent still runs before the
        # full index is built. Replace with the real index for the submission.
        _MINI = [
            {"technique_id": "T1059.001", "technique_name": "PowerShell", "tactic": "Execution",
             "text": "powershell encoded command script execution"},
            {"technique_id": "T1566.001", "technique_name": "Spearphishing Attachment",
             "tactic": "Initial Access", "text": "phishing email malicious attachment macro"},
            {"technique_id": "T1547.001", "technique_name": "Registry Run Keys / Startup Folder",
             "tactic": "Persistence", "text": "registry run key persistence autostart"},
        ]
        b = behaviour.lower()
        scored = sorted(_MINI, key=lambda t: -sum(w in b for w in t["text"].split()))
        return [{k: t[k] for k in ("technique_id", "technique_name", "tactic")} | {"score": 0.5}
                for t in scored[:3]]

    # Real path: semantic search over the embedded ATT&CK corpus.
    return _ATTACK_INDEX.search(behaviour, top_k=3)


def build_attack_index(stix_path: str):
    """Build the semantic ATT&CK index from a MITRE STIX bundle (run once at setup).

    Download enterprise-attack.json from:
    https://github.com/mitre-attack/attack-stix-data
    """
    import json
    from sentence_transformers import SentenceTransformer
    import numpy as np

    with open(stix_path) as f:
        bundle = json.load(f)

    techniques = []
    for obj in bundle.get("objects", []):
        if obj.get("type") == "attack-pattern" and not obj.get("revoked"):
            ext = next((r for r in obj.get("external_references", [])
                        if r.get("source_name") == "mitre-attack"), None)
            if not ext:
                continue
            techniques.append({
                "technique_id": ext["external_id"],
                "technique_name": obj.get("name", ""),
                "tactic": ", ".join(p["phase_name"] for p in obj.get("kill_chain_phases", [])),
                "text": f"{obj.get('name','')}. {obj.get('description','')}",
            })

    model = SentenceTransformer("all-MiniLM-L6-v2")
    vecs = model.encode([t["text"] for t in techniques], normalize_embeddings=True)

    class _Index:
        def search(self, q, top_k=3):
            qv = model.encode([q], normalize_embeddings=True)[0]
            sims = vecs @ qv
            idx = np.argsort(-sims)[:top_k]
            return [{k: techniques[i][k] for k in ("technique_id", "technique_name", "tactic")}
                    | {"score": float(sims[i])} for i in idx]

    global _ATTACK_INDEX
    _ATTACK_INDEX = _Index()
    return _ATTACK_INDEX


# The set of tools exposed to the agent's function-calling loop.
AGENT_TOOLS = [fetch_cti, map_attack, validate_sigma, convert_rule]
