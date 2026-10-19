# TalkPipe MCP

An intentionally narrow **local MCP tool adapter** for [mcc0nnell/talkpipe](https://github.com/mcc0nnell/talkpipe). Built to make approved TalkPipe pipelines invocable by MCP clients, including future ChatGPT connections.

**Status (October 2026):** The stdio adapter has been exercised by the official MCP Python SDK client. This is **not yet connected to ChatGPT as a custom plugin**. It is not a network service.

## Setup

Python 3.11+:

```bash
git clone https://github.com/mcc0nnell/talkpipe-mcp.git
cd talkpipe-mcp
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -u talkpipe_mcp.py
```

Installation pins the user's TalkPipe fork to commit `1b40f4c73a27a6ffb72f4715f5768c7cb12f3ffd` and MCP SDK version `1.30.0`. No other model or network provider is required for the three included workflows.

## Tools

| Tool | Description |
| --- | --- |
| `talkpipe_capabilities` | List fixed workflows and per-call limits |
| `talkpipe_run` | Run a selected, bounded TalkPipe Pipe API pipeline |

Approved `talkpipe_run` workflows:

- `normalize`: collapse whitespace within each item.
- `keyword_filter`: normalize then filter items containing `needle` (literal, case-insensitive).
- `text_statistics`: normalize then yield character/word counts and a 160-character preview.

Example MCP tool arguments:

```json
{"workflow":"keyword_filter","items":["  SignPipe  ", "TalkPipe on Butcher", "Lightpanda MCP"],"needle":"pipe"}
```

MCP clients that support local `stdio` servers can configure the command as the **absolute path** to the venv's Python executable and the arguments as `-u` and the **absolute path** to `talkpipe_mcp.py`. See [examples/stdio-config.json](examples/stdio-config.json) and replace paths before use.

## Safety boundaries

Only approved deterministic workflows may run. No arbitrary ChatterLang, Python evaluation, shell subprocesses, web requests, data persistence, or model-provider calls are exposed. Input is bounded to 100 strings, 4096 characters each, 65536 total characters; result output is capped at 50 items. Results are returned to the MCP caller and never intentionally written to storage by this adapter.

**Do not expose this stdio server to the public Internet.** The absence of a network listener does not imply it is safe to wrap in an unauthenticated HTTP gateway. Deploying via Cloudflare requires identity-based access, an authenticated Streamable HTTP MCP endpoint, request authorization, destination/pipeline policy, resource isolation, and operational audit controls. The ChatGPT connection requires user-controlled installation/authorization.

## Scope and next steps

This is a real TalkPipe pipeline adapter, not an LLM or a generalized code runner. Future versions can add *reviewed* named workflows for accessibility testing, browser receipt normalization, or WindAnvil evidence. A ChatGPT-installable remote MCP connector is **not claimed or implemented**.

License: Apache-2.0. See [LICENSE](LICENSE).

## Connect privately to ChatGPT

The preferred deployment for this personal, read-only MCP bridge is OpenAI's
**Secure MCP Tunnel**: no public Cloudflare URL, firewall opening, or inbound
HTTP listener is required. The tunnel client calls this MCP server over local
stdio and polls the OpenAI control plane via outbound HTTPS.

### On Butcher

The supported `tunnel-client` release is installed at
`~/.local/bin/tunnel-client` and the TalkPipe runtime is at
`~/lab/talkpipe-runtime/.venv/bin/python`. Confirm the 9 tests first:

```bash
cd ~/lab/talkpipe-mcp
~/lab/talkpipe-runtime/.venv/bin/python -m unittest discover -s tests -v
```

In [OpenAI Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels),
create a tunnel and associate it with the ChatGPT workspace you will use.
It must be usable by a runtime API key with the **Tunnels Read + Use**
permission. Do not use an admin key as the long-lived runtime key.

In a shell on Butcher, obtain the exact tunnel identifier and configure:

```bash
export CONTROL_PLANE_TUNNEL_ID='tunnel_REPLACE_WITH_YOUR_ID'
./scripts/private-tunnel.sh configure
```

The private profile is saved in `~/.config/tunnel-client/`, mode `0600`,
and contains a key **reference**, not a credential. The script refuses
missing or invalid identifiers. For security, **do not put secrets in a command
line or in Git**. Supply a restricted runtime API key through the securely
configured `CONTROL_PLANE_API_KEY` environment variable on the host.

```bash
./scripts/private-tunnel.sh doctor
./scripts/private-tunnel.sh run
```

Keep the `run` process alive while using TalkPipe in ChatGPT. Its health
admin UI is loopback-only and the tunnel is outbound-only.

### In ChatGPT (web)

Open [Plugins](https://chatgpt.com/plugins), select **+ → Add custom MCP
server**, enter the name `TalkPipe`, select **Tunnel**, choose the
associated tunnel or enter its ID, and review authentication and the
risk warning. Select **Create as a plugin** only after inspecting the
discovered read-only `talkpipe_capabilities` and `talkpipe_run` tools.

This user-initiated connection requires the relevant ChatGPT workspace
permissions and Platform tunnel permissions. A functioning local adapter
or stored tunnel profile does not mean ChatGPT is connected. Test by invoking
`talkpipe_capabilities` and then a benign `talkpipe_run` invocation from
ChatGPT; only that confirms the end-to-end path.

**Current operational boundary:** Until those account-side tunnel and
ChatGPT steps are completed and a real tool call succeeds, this repository
is *ready for private connection*, not *connected*. The adapter does not
expose arbitrary ChatterLang or Python.

Cloudflare Workers/Tunnel can provide a public alternative, but that would
require a separate authenticated MCP transport and identity configuration.
Do not publish the existing unprotected stdio tool behind an anonymous HTTP
proxy.
