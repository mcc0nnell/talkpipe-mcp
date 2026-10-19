# WindAnvil Commander — ChatGPT web/mobile cutover

Status: **migration instructions prepared; live mobile operation NOT yet verified** (2026-10-19).

## Why the current listing says “Desktop only”

The current privately installed WindAnvil Commander package declares the private MCP tunnel under both `mcp.json` and `.mcp.json`, with `mcpServers` in the compatibility manifest. OpenAI's imported-plugin behavior labels a plugin **Desktop only** when it contains these bundled MCP configurations, even if the transport is Streamable HTTP. This is a packaging/runtime classification, not a property of Blade capabilities.

Relevant OpenAI guidance:
- https://help.openai.com/en/articles/20001504-importing-and-syncing-plugin-marketplaces-from-github
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://developers.openai.com/plugins/deploy/connect-chatgpt

**Do not just delete the MCP files from the installed plugin to hide the badge.** That would remove the current MCP binding and strand its tools.

## Supported private connection (no public Blade ingress)

Continue using the existing `windanvil-commander` OpenAI Secure MCP Tunnel and the already-running, signed, fail-closed Blade facade. Create a **custom MCP server connection via ChatGPT's authenticated web UI**, rather than uploading a bundled MCP manifest as a private plugin:

1. On Butcher, perform the safe, read-only preflight:
   ```bash
   cd ~/lab/talkpipe-mcp
   python3 scripts/audit-tunnel-deployment.py
   ./scripts/private-tunnel.sh preflight
   ./scripts/private-tunnel.sh doctor
   ./scripts/manage-tunnel-cron.py check
   ```
   Confirm the managed tunnel is alive, polling, and launches `windanvil_commander_mcp.py`. Do not start duplicate clients.
2. In ChatGPT **web** with the account/workspace associated with the tunnel, open **Plugins → + → Add custom MCP server**.
3. Enter a user-facing name such as **WindAnvil Commander (Web)**. Under **Connection**, choose **Tunnel**, select the existing authorized tunnel, configure the prompted authentication, review the risk warning, then **Create as a plugin**. Confirm tool discovery lists the expected eight `commander_*` tools. Do not put API keys, signing keys, private runtime profiles, or complete tunnel credentials in chat or GitHub.
4. In a fresh ChatGPT web chat, invoke `commander_health` and `commander_status` from the newly created connection. Check that each response is a live Blade-sourced **PASS**, not a canned listing or a local preflight result.
5. From the ChatGPT iOS app, locate the **newly created** connection and invoke the same two diagnostic tools. Confirm there is **no Desktop only badge** on the new connection, and record actual results. Platform and workspace availability may vary.
6. Before allowing any writes or pipeline execution, test only the read-only `commander_host_inspect`, `commander_git_inspect`, `commander_process_list`, and `commander_process_probe` within their operator-pinned policies. Verify proof of grant admission and expected BLOCKED responses for unsupported operations. **Never perform arbitrary test writes or executions to demonstrate connectivity.**
7. Only after verified web + iOS calls, evaluate converting the original personal plugin into a skills-plus-registered-app package *if an eligible app ID exists and the editing workflow supports it*. That package must not retain directly declared `mcp.json` / `.mcp.json` servers or `mcpServers` binding. Keep the old package available until the replacement reaches parity.

## Acceptance criteria

- [ ] Existing desktop/private tunnel remains functional; no runtime key or signing material moved.
- [ ] Custom MCP tunnel connection is created and eight tools are discovered.
- [ ] ChatGPT web tool calls `commander_health` and `commander_status` return live Blade evidence.
- [ ] ChatGPT iOS can select the new connection, without “Desktop only”, and make a live diagnostic call.
- [ ] Denied signed capability remains denied; no direct shell, unauthenticated public MCP proxy, or bypass added.
- [ ] Original package remains installed until the web/mobile replacement is confirmed.

## If custom MCP creation is unavailable

Check ChatGPT plan/workspace custom MCP policy and whether the associated OpenAI Platform organization grants the operator **Tunnels Read + Use**. A working local tunnel alone does not grant mobile or web availability. If private tunnel-backed custom MCP is not available for this workspace, the alternative is a **separately deployed, authenticated** Streamable HTTP MCP app with proper identity, authorization, transport, and audit controls; the existing `commander.windanvil.com/mcp` Worker is currently documented as unconfigured and must not be represented as a live replacement.

This file is an operational migration contract, **not** a declaration that the user completed account-side connection or that mobile integration passed.
