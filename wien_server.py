"""
wien_server.py - a minimal MCP server.

It offers two things:
  1. a RESOURCE: a fixed table of star temperatures (data you can read)
  2. a TOOL:     wien_peak, which calculates a blackbody's peak wavelength

You don't run this file yourself: demo_client.py starts it for you.
No network access and no API keys are needed.
"""

import json
from typing import Annotated, Literal

from mcp.server import MCPServer  # the MCP library does all the message handling
from pydantic import Field  # used to write rules for the tool's arguments

# Create the server. The name and version are what it reports about itself
# during the handshake (Part 1 of the demo).
server = MCPServer(name="wien-demo", version="0.1.0")

# Wien's displacement constant (CODATA 2022), in metre-kelvin.
B_WIEN = 2.897771955e-3


# ---------------------------------------------------------------------------
# THE RESOURCE: fixed data, found by its address (URI). It takes no arguments
# and computes nothing; asking for it just returns the table. (Part 2)
# ---------------------------------------------------------------------------
@server.resource(
    "physics://blackbody/reference-temperatures",  # the address; "physics://" is made up
    description="Effective temperatures of some well-known blackbodies.",
    mime_type="application/json",  # tells the client the data is JSON
)
def reference_temperatures() -> str:
    return json.dumps({
        "CMB": 2.725,
        "Betelgeuse": 3600,
        "Sun": 5772,
        "Sirius A": 9940,
    })


# ---------------------------------------------------------------------------
# THE TOOL: a function the client can call with arguments. (Parts 3-6)
#
# The type hints below are the tool's rules. The MCP library turns them into
# the JSON Schema you see in Part 3, and uses the same rules to reject bad
# calls, like the one in Part 6.
# ---------------------------------------------------------------------------
@server.tool(description="Peak emission wavelength of a blackbody (Wien's law).")
def wien_peak(
    # Rule: must be a number, greater than 0, at most 1e9. No default = required.
    temperature_k: Annotated[
        float, Field(gt=0, le=1e9, description="Blackbody temperature in kelvin.")
    ],
    # Rule: must be exactly "nm" or "um". Optional; "nm" if not given.
    unit: Annotated[
        Literal["nm", "um"], Field(description="Unit for the returned wavelength.")
    ] = "nm",
) -> dict:
    """Return the wavelength at which a blackbody's emission peaks."""
    lam_m = B_WIEN / temperature_k                      # Wien's law, in metres
    lam = lam_m * 1e9 if unit == "nm" else lam_m * 1e6  # convert to nm or um
    # Return a plain dict; the MCP library turns it into the reply message.
    return {
        "temperature_k": temperature_k,
        "peak_wavelength": round(lam, 4),
        "unit": unit,
    }


# Start the server. It waits for messages on its input (stdin), answers each
# one on its output (stdout), and stops when the input is closed.
if __name__ == "__main__":
    server.run()
