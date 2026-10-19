#!/usr/bin/env bash
# Configure and run a private OpenAI Secure MCP Tunnel to TalkPipe's stdio MCP.
# Secrets are read from CONTROL_PLANE_API_KEY at runtime, not this repository.
set -euo pipefail
umask 077

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
client="${TUNNEL_CLIENT_BIN:-$HOME/.local/bin/tunnel-client}"
python="${TALKPIPE_PYTHON:-$HOME/lab/talkpipe-runtime/.venv/bin/python}"
profile_dir="${TUNNEL_CLIENT_PROFILE_DIR:-$HOME/.config/tunnel-client}"
profile="${TUNNEL_CLIENT_PROFILE:-windanvil-commander}"

usage() {
  printf 'Usage: %s preflight|configure|doctor|run\n' "${0##*/}" >&2
  printf 'Configuration requires CONTROL_PLANE_TUNNEL_ID.\n' >&2
  printf 'Doctor/run require CONTROL_PLANE_API_KEY with Tunnels Read + Use.\n' >&2
  exit 2
}
test -x "$client" || { echo "tunnel-client not executable: $client" >&2; exit 2; }
test -x "$python" || { echo "TalkPipe Python environment unavailable: $python" >&2; exit 2; }
test -f "$root/windanvil_commander_mcp.py" || { echo "TalkPipe MCP source unavailable" >&2; exit 2; }

mode="${1:-}"
case "$mode" in
  preflight)
    exec "$python" "$root/scripts/commander-preflight.py"
    ;;
  configure)
    id="${CONTROL_PLANE_TUNNEL_ID:-}"
    if [[ ! "$id" =~ ^tunnel_[A-Za-z0-9_-]{10,128}$ ]]; then
      echo "Set CONTROL_PLANE_TUNNEL_ID from OpenAI Platform tunnel settings." >&2
      exit 2
    fi
    mkdir -p "$profile_dir"
    chmod 0700 "$profile_dir"
    "$client" init --sample sample_mcp_stdio_local \
      --profile "$profile" --profile-dir "$profile_dir" \
      --tunnel-id "$id" \
      --control-plane-api-key-ref env:CONTROL_PLANE_API_KEY \
      --health-listen-addr 127.0.0.1:0 \
      --mcp-command "$python -u $root/windanvil_commander_mcp.py"
    echo "Local tunnel profile configured. No key was written."
    ;;
  doctor|run)
    if [[ -z "${CONTROL_PLANE_API_KEY:-}" ]]; then
      echo "CONTROL_PLANE_API_KEY is required; obtain a restricted runtime key in OpenAI Platform." >&2
      exit 2
    fi
    if [[ "$mode" == doctor ]]; then
      exec "$client" doctor --profile "$profile" --profile-dir "$profile_dir" --explain
    fi
    exec "$client" run --profile "$profile" --profile-dir "$profile_dir"
    ;;
  *) usage ;;
esac
