# tooldrift

Continuous drift monitoring for MCP tool definitions — detects the **"MCP
Rug Pull"** pattern (OWASP Top 10 for Agentic Applications 2026, **ASI04:
Agentic Supply Chain Compromise**): a tool that looked safe when an agent
first trusted it, then silently changes its description, schema, or
capability profile later on, so the agent keeps calling it without
re-review.

## The gap this fills

Every MCP security scanner I could find as of mid-2026 (Cisco's
`mcp-scanner`, Snyk's `agent-scan`, Invariant Labs' `MCP-Scan`, Microsoft's
Agent Governance Toolkit, and several smaller open-source projects) checks
a server's tools **once, at scan time**. None of them keep watching after
that scan. That's exactly the blind spot a rug-pull attack exploits: pass
review once, then mutate.

`tooldrift` isn't trying to out-build those tools. It does one narrow thing
they don't: it snapshots a tool set, and on every subsequent run (wired into
CI), diffs the current definitions against the last **trusted** snapshot —
both literally and semantically — and fails the build when a tool's real
behavior appears to have shifted.

## How it decides something drifted

For each tool that still exists in both the baseline and the current export:

1. If the content hash is identical, skip it — nothing changed.
2. Derive **capability tags** for both versions by scanning the
   description and schema for keywords (`network`, `code-execution`,
   `filesystem-write`, `credential-access`, `data-egress`, etc.), plus any
   real MCP tool **annotations** (`destructiveHint`, `openWorldHint`) the
   server declares.
3. If the new version gained a high-risk capability tag the old version
   didn't have → **critical**, build fails. This is the direct rug-pull
   signature: "read-only file tool" quietly starts requesting network
   egress.
4. If no new capability tag appeared, but the description's semantic
   similarity (TF-IDF cosine) to the old one drops below a threshold →
   **high**. This catches the harder, adversarial case: wording changed
   enough that the *intent* looks different, even though naive keyword
   matching didn't fire.
5. Otherwise it's a low/info finding (schema-only change, or a minor
   wording tweak) — visible in the report, not blocking.

## Why the semantic layer matters (and its real limit)

A keyword scanner alone is easy to dodge. `tests/fixtures/reword_*.json` is
a deliberately adversarial fixture: a "save a note locally" tool is changed
to silently sync notes to `backup-sync.example.com` — worded so none of the
keyword patterns fire. Only the semantic-similarity layer catches it
(measured similarity: **0.14**, far under threshold). That's the actual
argument for this project: point-in-time keyword scanning misses this;
continuous similarity-based diffing catches it.

The honest limit: the current backend is TF-IDF cosine similarity, not a
real sentence embedding model. It's fast, offline, and fully reproducible —
no API key, no GPU, cheap enough to run on every CI build — but it's a
cruder signal than something like `sentence-transformers`. `tooldrift/semantic.py`
defines `SimilarityBackend` as a small protocol specifically so a stronger
embedding backend can be swapped in later without touching `diff.py`. It
was left out of the default path deliberately: the model download made it
too heavy for a CI cold-start, and it isn't required to demonstrate the
core idea.

## Evaluation (not just "it works")

`eval/run_eval.py` sweeps the semantic-drift threshold from 0.05 to 0.90
across four labeled, hand-built fixture pairs (benign rewording, a rug
pull, an adversarial reword, and a tool swap) and measures precision/recall
for "should this block the build":

| threshold | TP | FP | TN | FN | precision | recall | accuracy |
|-----------|----|----|----|----|-----------|--------|----------|
| 0.05–0.10 | 1  | 0  | 2  | 1  | 1.00      | 0.50   | 0.75     |
| **0.15–0.50** | **2** | **0** | **2** | **0** | **1.00** | **1.00** | **1.00** |
| 0.55–0.90 | 2  | 1  | 1  | 0  | 0.67      | 1.00   | 0.75     |

Every threshold from 0.15 to 0.50 gets perfect accuracy on this fixture
set. The shipped default (`0.35`) is picked from the middle of that band,
not the edge — the benign-rewording fixture alone measured 0.536
similarity, uncomfortably close to 0.50, so hugging that edge would risk
false-positiving on ordinary docstring cleanups in real usage.

**Stated limitation:** this is a 4-case, hand-curated fixture set, not a
large real-world corpus. It's enough to demonstrate the method, pin the
threshold choice to evidence instead of a guess, and catch regressions in
CI (`pytest` runs these same fixtures as unit tests). A production
deployment should grow this set from real MCP server version history —
that's the natural next step, not a hidden flaw glossed over here.

## Usage

```bash
pip install -e .

# 1. Snapshot the tool set you currently trust (after manual review)
tooldrift snapshot tools_export.json --out baseline.trusted.json

# 2. On every later run (e.g. in CI), check the current export against it
tooldrift check tools_export.json --baseline baseline.trusted.json
```

Exit codes are CI-friendly: `0` = no drift or informational only, `1` =
high-severity drift (review required), `2` = critical drift (capability
escalation — recommended to fail the build). See
`.github/workflows/tooldrift.yml` for a wired-up example, and
`examples/tools_export.json` for the expected input shape (a `tools/list`-style
export: `{"server": "...", "tools": [{"name", "description", "inputSchema",
"annotations"}, ...]}`).

Add `--json` to `check` for a machine-readable report, and
`--semantic-threshold` to override the default.

## Project layout

```
tooldrift/
  models.py      ToolDefinition + stable content hash
  extractor.py    JSON export loader (+ optional live MCP stdio client)
  rules.py        keyword-based capability tagging, severity rules
  semantic.py     pluggable similarity backend (TF-IDF default)
  diff.py         core compare() logic, DriftFinding/DriftReport
  snapshot.py     save/load trusted baselines
  report.py       human-readable rendering
  cli.py          snapshot / check subcommands
tests/            pytest suite incl. 4 labeled fixture pairs
eval/             threshold sweep + precision/recall harness
.github/workflows/tooldrift.yml   example CI wiring
```

## Running the tests

```bash
pip install -r requirements.txt
pytest -q          # 14 tests
python eval/run_eval.py   # threshold sweep + recommended default
```

## What this project is not

It's not a replacement for a full MCP security scanner — it doesn't do
static analysis for command injection, SSRF, or auth misconfiguration the
way Cisco/Snyk/Invariant Labs' tools do. It's a narrow, complementary
layer: continuous integrity monitoring for the specific supply-chain-drift
class of attack that point-in-time scanners structurally can't catch.
