"""Protocol tests use a fake local Blade socket, not fabricated signing claims."""
import os
import pathlib
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

from blade_local_client import BladeBlocked, health, status, talkpipe_run
import windanvil_commander_mcp


class BladeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.socket_path = pathlib.Path(self.tmp.name) / "blade.sock"
        self.env = patch.dict(os.environ, {"WINDANVIL_LOCAL_SOCKET": str(self.socket_path)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def once(self, reply):
        listening = socket.socket(socket.AF_UNIX)
        listening.bind(str(self.socket_path))
        os.chmod(self.socket_path, 0o600)
        listening.listen(1)
        messages = []

        def serve():
            try:
                conn, _ = listening.accept()
                with conn:
                    chunks = []
                    while chunk := conn.recv(4096):
                        chunks.append(chunk)
                    messages.append(b"".join(chunks).decode())
                    conn.sendall(reply)
            finally:
                listening.close()

        task = threading.Thread(target=serve, daemon=True)
        task.start()
        return task, messages

    def test_absent_socket_blocks(self):
        with self.assertRaisesRegex(BladeBlocked, "socket_unavailable"):
            health()
        self.assertEqual(windanvil_commander_mcp.commander_health()["outcome"], "BLOCKED")

    def test_status_exchange(self):
        task, messages = self.once(b"OK\tgrant=active\n")
        self.assertEqual(status(), "grant=active\n")
        task.join(timeout=2)
        self.assertEqual(messages, ["STATUS\n"])

    def test_execute_only_fixed_capability(self):
        task, messages = self.once(b"OK\texecuted\n")
        digest = "a" * 64
        self.assertEqual(talkpipe_run("normalize", digest), "executed\n")
        task.join(timeout=2)
        self.assertEqual(messages, ["EXEC\ttalkpipe.run\tschema=windanvil.blade.talkpipe-exec/v1;pipeline=normalize;pipeline_sha256=" + digest + "\n"])

    def test_reject_invalid_pipeline_and_hash_without_socket(self):
        for name in ("../etc", "some;command", "white space", ""):
            with self.assertRaisesRegex(BladeBlocked, "pipeline_name_invalid"):
                talkpipe_run(name, "a"*64)
        with self.assertRaisesRegex(BladeBlocked, "pipeline_digest_invalid"):
            talkpipe_run("normalize", "b"*63)

    def test_reject_blade_denial(self):
        task, _ = self.once(b"ERR\tbad grant\n")
        with self.assertRaisesRegex(BladeBlocked, "blade_rejected_operation"):
            health()
        task.join(timeout=2)

    def test_reject_bad_socket_permissions(self):
        task, _ = self.once(b"OK\n")
        os.chmod(self.socket_path, 0o666)
        with self.assertRaisesRegex(BladeBlocked, "identity_or_permissions"):
            status()
        # Close listener without waiting for a nonexistent client.
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(self.socket_path))
            client.shutdown(socket.SHUT_WR)
            client.recv(4096)
        task.join(timeout=2)

    def test_reject_invalid_wire_response(self):
        task, _ = self.once(b"garbage")
        with self.assertRaisesRegex(BladeBlocked, "protocol_invalid"):
            health()
        task.join(timeout=2)

    def test_no_direct_talkpipe_fallback(self):
        result = windanvil_commander_mcp.commander_talkpipe_run("normalize", "a"*64)
        self.assertEqual(result["outcome"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
