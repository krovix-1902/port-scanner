# DetectionForge 🛡️⚙️
### An autonomous detection-engineering agent — turns threat intel into validated, ATT&CK-mapped detection rules.

> **Kaggle 5-Day AI Agents Intensive — Capstone | Track: Agents for Business**
> A single Gemini-powered agent that reads a cyber threat intelligence report and produces a reviewer-ready **Sigma** detection rule — validated, mapped to **MITRE ATT&CK**, and converted to **Splunk SPL** and **Elastic** — with a built-in evaluation harness that proves rule quality.

---

## The problem

SOC detection engineers hand-write detection rules from threat intel — a slow, manual, error-prone process measured in days per rule. Meanwhile threat intel arrives faster than teams can operationalise it, so detections lag behind active threats. This is a real, costed enterprise problem: slow detection engineering = longer attacker dwell time = higher breach cost.

Recent research confirms it's hard *and* unsolved: Microsoft Research's **CTI-REALM** benchmark (2026) found even the best frontier model scores only **0.637** on end-to-end detection-rule generation — "the benchmark is not saturated." This is a frontier worth building on, not a solved toy problem.

## The solution

DetectionForge is **one agent** with a toolbelt that runs the detection-engineering loop autonomously:

```
CTI report ──▶ [extract IOCs + TTPs] ──▶ [map to MITRE ATT&CK] ──▶ [author Sigma]
                                                                        │
                          ┌─────────────────────────────────────────────┘
                          ▼
              [validate w/ pySigma] ──invalid──▶ self-correct & retry (×3)
                          │ valid
                          ▼
              [convert ▶ SPL + Elastic] ──▶ reviewer-ready detection "PR" + quality score
```

The output is a structured, validated artifact a senior analyst can review and ship — not free-form text.

## Why an agent?

This isn't a one-shot prompt. The task needs **planning** (decompose intel → behaviours → rule), **tool use** (validation, conversion, ATT&CK lookup), and crucially a **feedback loop** — the agent reads `pySigma` validation errors and *fixes its own rule* before continuing. That self-correction is the difference between an agent and a chatbot.

## Course capabilities demonstrated

The capstone requires ≥3 course concepts. DetectionForge shows **six**:

| Capability | Where | How |
|---|---|---|
| **Agent / tool use (ADK-portable)** | `src/agent.py`, `src/tools/` | Single agent + 4-tool belt via function calling |
| **Agentic loop** | `src/agent.py` | validate → read error → regenerate → re-validate |
| **Structured output** | `src/schemas.py` | Strict Pydantic `RuleVerdict` schema |
| **RAG / embeddings** | `src/tools/` `map_attack` | Semantic search over the MITRE ATT&CK corpus |
| **Memory / context** | `src/memory.py` | Dedup + house-style grounding from prior rules |
| **Security feature** | `src/agent.py` `sanitise_cti` | Prompt-injection guard on untrusted intel |
| **Spec-Driven Development** | `specs/*.feature` | Gherkin behaviour specs as source of truth |
| **Evaluation** | `eval/eval_harness.py` | 4-axis scoring vs labelled ground truth |

## Architecture

- **Model:** Gemini Flash via Google AI Studio (free tier; cheap + fast for the loop).
- **Agent:** one reasoning loop with automatic function calling (`google-genai`).
- **Tools:** `fetch_cti`, `map_attack` (ATT&CK RAG), `validate_sigma` (pySigma), `convert_rule` (Sigma→SPL/Elastic).
- **Zero-trust backstop:** the agent's claims are re-verified deterministically in code (validation re-run, conversion re-run) before anything is trusted — a Spec-Driven, policy-gated design.
- **Eval:** scores syntax validity, ATT&CK recall, convertibility, and LLM-judged specificity (false-positive control) against a hand-labelled set.

## Quickstart

```bash
git clone <your-repo-url> && cd detectionforge
pip install -r requirements.txt
cp .env.example .env            # add your free Google AI Studio key

# (once) build the ATT&CK index — download enterprise-attack.json first:
#   https://github.com/mitre-attack/attack-stix-data
python -c "from src.tools import build_attack_index; build_attack_index('enterprise-attack.json')"

# run the agent on a sample
python -m src.agent

# run the evaluation harness (produces eval_results.png)
python -m eval.eval_harness
```

> 🚨 **Never commit your API key.** `.env` is git-ignored; `.env.example` ships placeholders only.

## Evaluation results

`python -m eval.eval_harness` scores each rule on syntax, ATT&CK recall, convertibility, and specificity, prints a per-case table + aggregate, and saves `eval_results.png`. *(Run it and drop the chart + your aggregate number here — this is the proof judges look for.)*

## Honest limitations

- Rules are **analyst-assist**, reviewed by a human before deployment (human-in-the-loop).
- Detection **specificity** depends on the target log schema; the agent states its log-source assumptions explicitly rather than overclaiming coverage.
- Built on **public/synthetic** intel and samples only — no client or PII data.

## Porting to Google ADK

The tools in `src/tools/` are plain functions, so they drop straight into ADK:
```python
from google.adk.agents import Agent
from src.tools import AGENT_TOOLS
agent = Agent(model="gemini-2.5-flash", tools=AGENT_TOOLS, instruction=SYSTEM_INSTRUCTION)
```
*(Confirm the current ADK API against the course codelabs before submitting — ADK's surface changes between versions.)*

## License
Code under CC-BY 4.0 (capstone requirement). Built on open-source: pySigma, SigmaHQ, MITRE ATT&CK, sentence-transformers.

---
*Built by Rohan Khatri — BSc Computer Science for Cyber Security. A detection-engineering agent demonstrating SOC tooling, MITRE ATT&CK, and modern agent architecture.*
