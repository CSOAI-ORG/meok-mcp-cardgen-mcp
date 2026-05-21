"""Smoke tests for meok-mcp-cardgen-mcp."""
import sys, os, inspect, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    emit_sep_1649_card,
    emit_sep_1960_card,
    emit_sep_2127_card,
    emit_all_cards,
    validate_card,
    sign_card,
    list_shapes,
)


SAMPLE_SERVER_JSON = {
    "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
    "name": "io.github.example/example-mcp",
    "version": "1.2.3",
    "description": "An example MCP that demonstrates a valid server.json shape.",
    "repository": {"url": "https://github.com/example/example-mcp", "source": "github"},
    "packages": [
        {"registryType": "pypi", "identifier": "example-mcp", "version": "1.2.3",
         "runtimeHint": "python", "transport": {"type": "stdio"}}
    ],
    "remotes": [{"type": "streamable-http", "url": "https://example.com/mcp"}],
}


def test_emit_sep_1649_card():
    r = emit_sep_1649_card(SAMPLE_SERVER_JSON)
    assert r["card"]["spec"] == "sep-1649"
    assert r["card"]["name"] == "io.github.example/example-mcp"
    assert r["card"]["version"] == "1.2.3"
    assert "signature" in r["card"]
    assert r["path"] == "/.well-known/mcp/server-card.json"


def test_emit_sep_1960_card_uses_remote_endpoint():
    r = emit_sep_1960_card(SAMPLE_SERVER_JSON)
    assert r["card"]["endpoint"] == "https://example.com/mcp"
    assert r["card"]["spec"] == "sep-1960"


def test_emit_sep_2127_card():
    r = emit_sep_2127_card(SAMPLE_SERVER_JSON)
    assert r["card"]["spec"] == "sep-2127"
    assert "$schema" in r["card"]
    assert r["card"]["packages"][0]["identifier"] == "example-mcp"


def test_emit_all_cards_returns_three_shapes():
    r = emit_all_cards(SAMPLE_SERVER_JSON)
    assert "sep-1649" in r["cards"]
    assert "sep-1960" in r["cards"]
    assert "sep-2127" in r["cards"]
    assert len(r["paths_to_host"]) == 3


def test_validate_card_passes_complete_1649():
    r = emit_sep_1649_card(SAMPLE_SERVER_JSON)
    v = validate_card(r["card"], "sep-1649")
    assert v["valid"] is True


def test_validate_card_catches_missing():
    v = validate_card({"name": "x"}, "sep-1649")
    assert v["valid"] is False
    assert len(v["issues"]) >= 3


def test_validate_card_unsupported_shape():
    v = validate_card({}, "fake-shape")
    assert "error" in v


def test_sign_card_strips_existing_signature():
    card = {"name": "x", "version": "1.0.0", "signature": "OLD"}
    r = sign_card(card)
    assert r["signed_card"]["signature"] != "OLD"
    assert "name" in r["signed_card"]


def test_list_shapes_returns_three():
    r = list_shapes()
    assert r["count"] == 3
    assert "sep-1649" in r["shapes"]
    assert "sep-1960" in r["shapes"]
    assert "sep-2127" in r["shapes"]


if __name__ == "__main__":
    g = dict(globals())
    fns = [v for k, v in g.items() if k.startswith("test_") and inspect.isfunction(v)]
    p = f = 0
    for fn in fns:
        try:
            fn(); print(f"OK {fn.__name__}"); p += 1
        except Exception as e:
            print(f"X  {fn.__name__}: {type(e).__name__}: {e}"); traceback.print_exc(); f += 1
    print(f"\n{p} passed, {f} failed")
