"""
demo_client.py - a client that talks to wien_server.py by hand.

It uses NO MCP library. It just writes JSON-RPC 2.0 messages to the server
and reads the replies, printing everything so you can see exactly what
travels between client and server.

There is no LLM in this demo: the client sends the messages an LLM
application would send.

Run it from the folder containing both files:
    python demo_client.py          # pauses before each part (press Enter)
    python demo_client.py --fast   # runs straight through
"""

import json
import subprocess
import sys

# Pause between parts unless "--fast" was given on the command line.
PAUSE = "--fast" not in sys.argv

# ---------------------------------------------------------------------------
# START THE SERVER
# Launch wien_server.py as a separate program and connect two pipes to it:
#   stdin  = a pipe INTO the server  (we write messages here)
#   stdout = a pipe OUT of the server (we read replies here)
# ---------------------------------------------------------------------------
proc = subprocess.Popen(
    [sys.executable, "wien_server.py"],  # same as "python wien_server.py", same Python
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,  # hide the server's log messages
    text=True,                  # send and receive text, not bytes
    bufsize=1,                  # line by line
)


def part(title):
    """Print a banner for the next part, then wait for Enter."""
    print("\n" + "=" * 68)
    print(f"  {title}")
    print("=" * 68)
    if PAUSE:
        input("  [Enter]")


def send(message, expect_reply=True):
    """Send one message to the server and, usually, read one reply back."""
    # 1. Show what we're sending.
    print("\n--> SENT")
    print(json.dumps(message, indent=2))

    # 2. Send it: one message = one line of JSON. flush() pushes it out now.
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()

    # A notification (no "id") gets no reply, so don't wait for one.
    if not expect_reply:
        print("\n    (a notification has no 'id', so no reply is expected)")
        return None

    # 3. Wait for one line back and turn it into a Python dict.
    reply = json.loads(proc.stdout.readline())

    # 4. Show what we received.
    print("\n<-- RECEIVED")
    print(json.dumps(reply, indent=2))
    return reply


# Every message has the same shape:
#   "jsonrpc": "2.0"   -> this is JSON-RPC 2.0
#   "id":      a number -> the reply carries the same id, so they can be matched
#   "method":  what we're asking for
#   "params":  the details (optional)

# ---------------------------------------------------------------------------
part("PART 1 - Handshake: agree on a protocol version")
# The client introduces itself and says which protocol version it speaks.
# The server replies with its own name, version, and what it offers.
send({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "raw-client", "version": "0.1.0"},
    },
})
# "I'm ready." No "id", so this is a notification: no reply comes back.
send({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect_reply=False)

# ---------------------------------------------------------------------------
part("PART 2 - RESOURCES: static data, addressed by URI")
# First ask what data exists, then read it by its address. No arguments.
send({"jsonrpc": "2.0", "id": 2, "method": "resources/list"})
send({
    "jsonrpc": "2.0", "id": 3, "method": "resources/read",
    "params": {"uri": "physics://blackbody/reference-temperatures"},
})

# ---------------------------------------------------------------------------
part("PART 3 - DISCOVERY: tools/list returns the JSON Schema")
# Ask what tools exist. The reply includes each tool's rules (inputSchema),
# generated from the type hints in wien_server.py.
send({"jsonrpc": "2.0", "id": 4, "method": "tools/list"})

# ---------------------------------------------------------------------------
part("PART 4 - A valid call: the Sun, 5772 K")
# Use the tool: give it a temperature, get back the peak wavelength.
send({
    "jsonrpc": "2.0", "id": 5, "method": "tools/call",
    "params": {"name": "wien_peak", "arguments": {"temperature_k": 5772, "unit": "nm"}},
})

# ---------------------------------------------------------------------------
part("PART 5 - Chaining: take Betelgeuse's 3600 K from the resource")
# Same tool, using a temperature from the Part 2 table. (Typed in by hand
# here; with an LLM, the model would read it from the table itself.)
send({
    "jsonrpc": "2.0", "id": 6, "method": "tools/call",
    "params": {"name": "wien_peak", "arguments": {"temperature_k": 3600, "unit": "nm"}},
})

# ---------------------------------------------------------------------------
part("PART 6 - TOOL error: schema violated. Note 'isError' INSIDE a result")
# Break a rule on purpose: "angstrom" is not allowed (only "nm" or "um").
# The reply is still a "result", but with isError: true and an explanation,
# so an LLM could read it and try again.
send({
    "jsonrpc": "2.0", "id": 7, "method": "tools/call",
    "params": {"name": "wien_peak",
               "arguments": {"temperature_k": 5772, "unit": "angstrom"}},
})

# ---------------------------------------------------------------------------
part("PART 7 - PROTOCOL error: no such method. Note the 'error' member")
# Call a method that doesn't exist. Now the reply has an "error" with a
# standard JSON-RPC code (-32601 = method not found) instead of a "result".
send({"jsonrpc": "2.0", "id": 8, "method": "tools/summon", "params": {}})

# ---------------------------------------------------------------------------
print("\n" + "=" * 68)
print("  Two failure channels:")
print("    result + isError:true  -> the MODEL sees it and can retry")
print("    error + code           -> the PROGRAMMER sees it; model never does")
print("=" * 68)

# Close the pipe into the server: "nothing more is coming". The server stops.
proc.stdin.close()
proc.wait(timeout=5)
