"""
tooldrift — continuous integrity monitoring for MCP tool definitions.

Detects "MCP Rug Pull" attacks (OWASP Agentic Applications Top 10, ASI04:
Agentic Supply Chain Compromise): a tool that looked safe when first
approved, then silently changes its description, schema, or requested
permissions later on, so an agent keeps trusting it without re-review.

Most existing MCP scanners check a server once, at scan time. tooldrift
is designed to run on every CI build (or on a schedule) and diff the
current tool set against the last *trusted* snapshot, flagging anything
that drifted -- textually or semantically.
"""

__version__ = "0.1.0"
