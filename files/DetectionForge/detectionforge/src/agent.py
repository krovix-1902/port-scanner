"""
agent.py — DetectionForge core single agent.

A SINGLE agent (one reasoning loop) with a toolbelt. It ingests cyber threat
intel and produces a validated, ATT&CK-mapped detection rule (Sigma + SPL +
Elastic), self-correcting when validation fails.

Capabilities demonstrated:
  - Function calling / tool use   (AGENT_TOOLS, automatic function calling)
  - Agentic loop                  (validate -> self-correct -> retry)
  - Structured output             (Pydantic RuleVerdict schema)
  - RAG / embeddings              (map_attack over the ATT&CK corpus)
  - Memory / context engineering  (RuleMemory: dedup + style grounding)
  - Security feature              (sanitise_cti guards against prompt injection
                                   hidden in fetched intel)

Porting to ADK: the same `AGENT_TOOLS` functions can be handed to
`google.adk.agents.Agent(tools=AGENT_TOOLS, ...)`. This module uses the
google-genai SDK directly so it runs out-of-the-box; see README.
"""
from __future__ import annotations

import os
import re

from google import genai
from google.genai import types

from .schemas import RuleVerdict
from .tools import AGENT_TOOLS, validate_sigma, convert_rule
from .memory import RuleMemory


SYSTEM_INSTRUCTION = """You are DetectionForge, an autonomous detection-engineering agent.
Given cyber threat intelligence, you:
  1. Extract a short threat summary, IOCs, and adversary behaviours (TTPs).
  2. Map each behaviour to MITRE ATT&CK using the map_attack tool.
  3. Author a Sigma detection rule in YAML.
  4. Validate it with validate_sigma. If invalid, READ the errors and fix the
     rule, then re-validate. Retry up to 3 times.
  5. Convert the validated rule with convert_rule.
  6. State your log-source assumptions honestly (what fields/log source the rule
     needs, and the false-positive risk). Do NOT overclaim detection coverage.

Be precise. A specific rule that matches the malicious behaviour but not benign
activity is worth more than a broad rule that fires on everything.
"""

# A conservative guard against prompt-injection smuggled inside fetched CTI text.
_INJECTION_PATTERNS = [
    r"ignore (all |previous |above )?instructions",
    r"disregard .{0,20}(system|prompt|rules)",
    r"you are now",
    r"new instructions:",
]


def sanitise_cti(text: str) -> str:
    """Security feature: neutralise obvious instruction-injection in untrusted
    intel before it reaches the model. Flags rather than silently dropping."""
    flagged = text
    for pat in _INJECTION_PATTERNS:
        flagged = re.sub(pat, "[REDACTED-POSSIBLE-INJECTION]", flagged, flags=re.IGNORECASE)
    return flagged


class DetectionForgeAgent:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.memory = RuleMemory()

    def run(self, cti_text: str) -> RuleVerdict:
        """Run the full triage->detection pipeline on a piece of threat intel."""
        cti_text = sanitise_cti(cti_text)
        style = self.memory.style_examples()
        style_block = ("\n\nHouse style — match the structure of these prior rules:\n"
                       + "\n---\n".join(style)) if style else ""

        # Phase 1: agentic generation with automatic function calling.
        # The SDK runs the tool-use loop for us (model calls map_attack /
        # validate_sigma / convert_rule until it stops).
        prompt = (
            "Threat intelligence to analyse:\n\n"
            f"{cti_text}\n{style_block}\n\n"
            "Produce a complete detection rule following your instructions. "
            "Use the tools. Return your final answer as the structured schema."
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=AGENT_TOOLS,                 # function calling
                response_mime_type="application/json",
                response_schema=RuleVerdict,        # structured output
                temperature=0.2,
            ),
        )

        verdict: RuleVerdict = response.parsed

        # Phase 2: deterministic backstop (zero-trust on LLM output / SDD policy).
        # We re-run validation in code rather than trusting the model's claim.
        v = validate_sigma(verdict.rule.sigma_yaml)
        verdict.rule.validation_passed = v["valid"]
        verdict.rule.validation_errors = v["errors"]
        if v["valid"]:
            conv = convert_rule(verdict.rule.sigma_yaml)
            verdict.rule.splunk_spl = conv["splunk_spl"]
            verdict.rule.elastic_query = conv["elastic_query"]
            if not self.memory.is_duplicate(verdict.rule.title):
                self.memory.add(verdict.rule.title, verdict.rule.sigma_yaml)

        return verdict


if __name__ == "__main__":
    sample = ("An adversary sent a phishing email with a malicious Office "
              "attachment. On open, a macro launched powershell.exe with a "
              "base64-encoded command that downloaded a second-stage payload "
              "and created a Registry Run key for persistence.")
    agent = DetectionForgeAgent()
    result = agent.run(sample)
    print(result.model_dump_json(indent=2))
