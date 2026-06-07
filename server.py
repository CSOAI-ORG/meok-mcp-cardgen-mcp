#!/usr/bin/env python3
"""
Buy Pro: https://www.csoai.org/checkout

MEOK MCP Cardgen — generate signed .well-known MCP server cards
================================================================

By MEOK AI Labs · https://meok.ai · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-mcp-cardgen-mcp -->

WHAT THIS DOES
--------------
Claude Desktop 2.1 + Cursor 2026.4 ship MCP server-card *discovery* — they
look for these well-known paths:

  /.well-known/mcp/server-card.json   (SEP-1649 shape)
  /.well-known/mcp                     (SEP-1960 shape)
  /.well-known/mcp/sep-2127.json       (SEP-2127 GO reference impl shape)

There are ~2,000 MCPs on the official Registry. ALMOST NONE have a server
card today. This MCP generates all three shapes from one server.json — and
optionally HMAC-signs them so downstream clients can verify provenance.

TOOLS
-----
- emit_sep_1649_card(server_json): SEP-1649 server card
- emit_sep_1960_card(server_json): SEP-1960 lightweight discovery
- emit_sep_2127_card(server_json): SEP-2127 (Go reference impl) shape
- emit_all_cards(server_json): all three shapes in one bundle
- validate_card(card, shape): validate an existing card
- sign_card(card): HMAC-sign for verifiability

PRICING
-------
Free MIT self-host · £29/mo Pro hosted-badge service.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Optional
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("meok-mcp-cardgen")
_HMAC_SECRET = os.environ.get("MEOK_HMAC_SECRET", "")


SUPPORTED_SHAPES = ["sep-1649", "sep-1960", "sep-2127"]


def _sign(payload: dict) -> str:
    if not _HMAC_SECRET:
        return "unsigned-no-key-configured"
    return hmac.new(_HMAC_SECRET.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def emit_sep_1649_card(server_json: dict, well_known_url: Optional[str] = None) -> dict:
    """
    Generate SEP-1649 server card from server.json.

    Args:
        server_json: Contents of MCP server.json.
        well_known_url: Optional override for `self_url`.

    Returns:
        {card, path}
    """
    name = server_json.get("name", "unknown")
    card = {
        "spec": "sep-1649",
        "spec_version": "0.4",
        "name": name,
        "version": server_json.get("version", "1.0.0"),
        "description": server_json.get("description", ""),
        "self_url": well_known_url or f"https://{name.replace('io.github.', '').replace('/', '.example/')}/.well-known/mcp/server-card.json",
        "transport": [t.get("type", "stdio") for t in (server_json.get("packages", [{}])[0].get("transport", {}),) if t],
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False,
        },
        "provenance": {
            "publisher": "MEOK AI Labs (CSOAI LTD, UK Companies House 16939677)",
            "publisher_did": "did:web:meok.ai",
            "signed_by": "card_signature_below",
        },
        "issued_at": _ts(),
    }
    card["signature"] = _sign(card)
    return {"card": card, "path": "/.well-known/mcp/server-card.json"}


@mcp.tool()
def emit_sep_1960_card(server_json: dict, hosted_url: Optional[str] = None) -> dict:
    """
    Generate SEP-1960 (lightweight) discovery card.

    Args:
        server_json: server.json contents.
        hosted_url: Optional override for `endpoint`.

    Returns:
        {card, path}
    """
    name = server_json.get("name", "unknown")
    remotes = server_json.get("remotes", [])
    endpoint = hosted_url or (remotes[0]["url"] if remotes else f"https://{name.replace('io.github.', '').split('/')[0]}.example/mcp")
    card = {
        "spec": "sep-1960",
        "name": name,
        "endpoint": endpoint,
        "transport": (remotes[0].get("type") if remotes else "stdio"),
        "version": server_json.get("version", "1.0.0"),
        "description": (server_json.get("description") or "")[:200],
        "issued_at": _ts(),
    }
    card["signature"] = _sign(card)
    return {"card": card, "path": "/.well-known/mcp"}


@mcp.tool()
def emit_sep_2127_card(server_json: dict) -> dict:
    """
    Generate SEP-2127 (Go reference impl) shape.

    Args:
        server_json: server.json contents.

    Returns:
        {card, path}
    """
    name = server_json.get("name", "unknown")
    card = {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "spec": "sep-2127",
        "name": name,
        "version": server_json.get("version", "1.0.0"),
        "description": server_json.get("description", ""),
        "repository": server_json.get("repository", {}),
        "packages": server_json.get("packages", []),
        "remotes": server_json.get("remotes", []),
        "provenance": {
            "publisher_did": "did:web:meok.ai",
            "issued_at": _ts(),
        },
    }
    card["signature"] = _sign(card)
    return {"card": card, "path": "/.well-known/mcp/sep-2127.json"}


@mcp.tool()
def emit_all_cards(server_json: dict) -> dict:
    """
    Emit cards in all three discovery shapes — drop into your static-file host.

    Args:
        server_json: server.json contents.

    Returns:
        {cards: {sep-1649, sep-1960, sep-2127}, paths_to_host}
    """
    s49 = emit_sep_1649_card(server_json)
    s60 = emit_sep_1960_card(server_json)
    s27 = emit_sep_2127_card(server_json)
    return {
        "cards": {
            "sep-1649": s49["card"],
            "sep-1960": s60["card"],
            "sep-2127": s27["card"],
        },
        "paths_to_host": [s49["path"], s60["path"], s27["path"]],
        "hint": "Drop each card at its path under your domain. Claude Desktop 2.1 + Cursor 2026.4 will auto-discover.",
    }


@mcp.tool()
def validate_card(card: dict, shape: str = "sep-1649") -> dict:
    """
    Validate a server card against the chosen SEP shape.

    Args:
        card: The card dict.
        shape: One of sep-1649 / sep-1960 / sep-2127.

    Returns:
        {valid, issues}
    """
    issues = []
    if shape not in SUPPORTED_SHAPES:
        return {"error": f"Unsupported shape. Use one of {SUPPORTED_SHAPES}"}

    if shape == "sep-1649":
        for k in ["spec", "name", "version", "self_url", "capabilities"]:
            if k not in card:
                issues.append(f"missing: {k}")
        if card.get("spec") != "sep-1649":
            issues.append(f"spec field must be 'sep-1649', got {card.get('spec')!r}")
    elif shape == "sep-1960":
        for k in ["spec", "name", "endpoint"]:
            if k not in card:
                issues.append(f"missing: {k}")
        if card.get("spec") != "sep-1960":
            issues.append(f"spec field must be 'sep-1960', got {card.get('spec')!r}")
    elif shape == "sep-2127":
        for k in ["$schema", "name", "version", "packages"]:
            if k not in card:
                issues.append(f"missing: {k}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "shape": shape,
        "verified_at": _ts(),
    }


@mcp.tool()
def sign_card(card: dict) -> dict:
    """
    HMAC-sign a card so downstream clients can verify provenance.

    Args:
        card: The card dict (will be deep-copied; original not mutated).

    Returns:
        {signed_card, signature_only}
    """
    # Strip any existing signature first so the signing is deterministic
    payload = {k: v for k, v in card.items() if k != "signature"}
    sig = _sign(payload)
    return {
        "signed_card": {**payload, "signature": sig},
        "signature_only": sig,
        "hint": "Auditor recomputes HMAC over the card minus signature field with the same secret.",
    }


@mcp.tool()
def list_shapes() -> dict:
    """List the supported MCP server-card shapes and which clients consume them."""
    return {
        "shapes": {
            "sep-1649": {
                "spec_url": "https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649",
                "consumers": ["Claude Desktop 2.1+", "Cursor 2026.4+"],
                "well_known_path": "/.well-known/mcp/server-card.json",
            },
            "sep-1960": {
                "spec_url": "https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1960",
                "consumers": ["lightweight discovery clients"],
                "well_known_path": "/.well-known/mcp",
            },
            "sep-2127": {
                "spec_url": "https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2127",
                "consumers": ["Go reference impl + MCP gateways"],
                "well_known_path": "/.well-known/mcp/sep-2127.json",
            },
        },
        "count": len(SUPPORTED_SHAPES),
    }


if __name__ == "__main__":
    mcp.run()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/5kQ6oJ0xS3ce8sl7ew8k91j"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
