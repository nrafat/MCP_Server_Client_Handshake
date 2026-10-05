# MCP from the inside: a minimal server and a hand-written client

PHYS 7440, Week 5 Meeting 1 — live demo by Nafis Rafat Niloy.

This demo shows exactly what travels between an MCP client and an MCP server. The server offers one **resource** (a table of star temperatures) and one **tool** (Wien's law). The client uses no MCP library: it writes JSON-RPC 2.0 messages by hand and prints every message in both directions.

No network access and no API keys are needed.

## Setup and run

Requires Python 3.10 or newer (tested with 3.12.3). Open a terminal and run:

```bash
git clone https://github.com/nrafat/MCP_Server_Client_Handshake.git
cd MCP_Server_Client_Handshake
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python demo_client.py
```

Press Enter to step through the seven parts. To run straight through instead:

```bash
python demo_client.py --fast
```

Compare your output with `transcript.txt`. The two numbers to check are `502.0395` (Part 4) and `804.9367` (Part 5).

## What each part shows

| Part | Message sent | What it shows |
| --- | --- | --- |
| 1 | `initialize`, then `notifications/initialized` | The handshake: agree on a protocol version. The second message has no `id`, so it is a notification and gets no reply. |
| 2 | `resources/list`, then `resources/read` | A resource: fixed data found by its address (URI). No arguments. |
| 3 | `tools/list` | Discovery: the tool's name, description, and rules for its arguments (JSON Schema). |
| 4 | `tools/call` with 5772 K | A valid call: the Sun peaks at 502 nm. |
| 5 | `tools/call` with 3600 K | Chaining: Betelgeuse's temperature from the Part 2 table gives 805 nm, near-infrared. |
| 6 | `tools/call` with `unit: "angstrom"` | A **tool error**: the rules reject the argument. The reply is a `result` with `isError: true`, so an LLM would see it and could retry. |
| 7 | `tools/summon` | A **protocol error**: no such method. The reply is an `error` with code `-32601`, meant for the programmer, not the model. |

There is no LLM in this demo. The client sends the messages an LLM application would send; in Part 5, the 3600 K is typed in by hand, where a model would read it from the table itself.

## The files

| File | What it does |
| --- | --- |
| `wien_server.py` | The MCP server. Defines the resource and the tool as ordinary Python functions; the `mcp` library handles all the messages. The tool's type hints become its JSON Schema. |
| `demo_client.py` | The client. Starts the server, sends each message, and prints everything. You only run this file; it starts the server for you. |
| `requirements.txt` | The library versions to install. |
| `transcript.txt` | Expected output, for comparison. |

Both Python files are commented section by section.

## Troubleshooting

| What you see | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mcp'` | The venv is not active, or the install was skipped | `source .venv/bin/activate`, then `pip install -r requirements.txt` |
| `JSONDecodeError` in the client | The server crashed on startup | Run `python wien_server.py` on its own to see the real error; Ctrl+C to stop it |
| `can't open file 'wien_server.py'` | Running from the wrong folder | `cd MCP_Server_Client_Handshake` first |
| The script sits silent | It is waiting for Enter | Press Enter, or rerun with `--fast` |

## Try it yourself

- Change the temperature in Part 4 to another star and check the answer by hand: λ_peak = b / T, with b = 2.897771955 × 10⁻³ m·K.
- Add a second tool to `wien_server.py` (for example, Stefan–Boltzmann flux, σT⁴), then add a `tools/call` for it in `demo_client.py`. Run Part 3 and check that the new tool appears in `tools/list`.
- Break a rule a different way: send `temperature_k: -5`, or leave it out. What does the error message say?

## Further reading

- Model Context Protocol specification: https://modelcontextprotocol.io
- Anthropic, "Introducing the Model Context Protocol" (November 2024): https://www.anthropic.com/news/model-context-protocol

## Acknowledgement

Code and documentation written with assistance from Claude (Anthropic).
