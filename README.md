# MEOK MCP Cardgen

> ## 🧱 Free MIT · paid hosted card-validation badge from £29/mo
> See [meok.ai/docs](https://meok.ai/docs).

# Generate signed .well-known MCP server cards (SEP-1649 + 1960 + 2127)

<!-- mcp-name: io.github.CSOAI-ORG/meok-mcp-cardgen-mcp -->

[![PyPI](https://img.shields.io/pypi/v/meok-mcp-cardgen-mcp)](https://pypi.org/project/meok-mcp-cardgen-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What this does

Claude Desktop 2.1 (April 2026) and Cursor 2026.4 ship MCP server-card *discovery* — they look for these well-known paths:

- `/.well-known/mcp/server-card.json` — **SEP-1649** shape
- `/.well-known/mcp` — **SEP-1960** lightweight shape
- `/.well-known/mcp/sep-2127.json` — **SEP-2127** (Go reference impl) shape

There are ~2,000 MCPs on the official registry. Almost none have a server card today. This MCP turns one `server.json` into all three card shapes, then HMAC-signs each so downstream clients can verify provenance.

## Tools

| Tool | Purpose |
|---|---|
| `emit_sep_1649_card(server_json)` | Generate SEP-1649 card |
| `emit_sep_1960_card(server_json)` | Generate SEP-1960 card |
| `emit_sep_2127_card(server_json)` | Generate SEP-2127 card |
| `emit_all_cards(server_json)` | All three in one bundle |
| `validate_card(card, shape)` | Lint an existing card |
| `sign_card(card)` | HMAC-sign a card |
| `list_shapes()` | Supported shapes + consuming clients |

## Why this matters NOW

The MCP spec is converging on `.well-known` discovery. The first MCPs to ship server cards will be auto-discovered by Claude Desktop / Cursor / Cline / Windsurf without users editing config files.

If you're publishing to the official registry, run this once and host the three card files alongside your repo. Done.

## Sister MCPs

- `mcp-spec-compliance-mcp` — audit your server.json against the spec before generating cards
- `agent-mcp-router-mcp` — route to multiple MCPs from one endpoint
- `agent-replay-debugger-mcp` — debug card-discovery flows

Full catalogue: [meok.ai/anthropic-registry](https://meok.ai/anthropic-registry)

## Pricing

| Option | Price |
|---|---|
| Self-host MIT | £0 |
| Pro hosted-badge | £29/mo (custom verify URL + uptime) |
| Substrate add-on | £499/mo |

Buy: https://meok.ai/docs

## Licence

MIT. By [MEOK AI Labs](https://meok.ai) (CSOAI LTD, UK Companies House 16939677).
