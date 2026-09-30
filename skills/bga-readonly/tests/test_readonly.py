"""Check the wrapper's approval boundary without credentials or network calls."""

import contextlib
import io
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch


MAIN = runpy.run_path(str(Path(__file__).parents[1] / "scripts/bga-readonly"))["main"]
CONNECTION = "67fbd876-5c7c-49b4-8481-e6fc795aaee7"
GET = ["get", CONNECTION, "--path", "/repos/berkshiregrey/bg_rad_core/pulls/96"]


class ReadonlyTests(unittest.TestCase):
    def setUp(self):
        self.run_patch = patch("subprocess.run")
        self.run = self.run_patch.start()
        self.addCleanup(self.run_patch.stop)
        self.run.side_effect = self.success
        self.file_patch = patch.object(Path, "is_file", return_value=True)
        self.file_patch.start()
        self.addCleanup(self.file_patch.stop)

    @staticmethod
    def success(command, **kwargs):
        if command[1] == "download":
            Path(command[command.index("--output") + 1]).write_bytes(b'{"number":96}\n')
        return subprocess.CompletedProcess([], 0, stdout=b'{"number":96}\n')

    def reject(self, args):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            MAIN(args)
        self.assertEqual(error.exception.code, 2)
        self.run.assert_not_called()

    def test_get_fixes_method_and_preserves_query_as_one_argument(self):
        query = "text=$(touch /tmp/not-executed); --method POST"
        self.assertEqual(MAIN(GET + ["--query", query, "--query", "page=2"]), 0)
        args, kwargs = self.run.call_args
        self.assertEqual(args[0][1:], [
            "call", CONNECTION, "--method", "GET",
            "--path=/repos/berkshiregrey/bg_rad_core/pulls/96",
            "--query=" + query, "--query=page=2",
        ])
        self.assertFalse(kwargs.get("shell", False))

    def test_rejects_write_and_passthrough_options(self):
        for extra in (
            ["--method", "POST"], ["--method=DELETE"], ["--meth", "GET"],
            ["--header", "X-HTTP-Method-Override: DELETE"],
            ["--url", "https://example.com"], ["--body-text", "{}"],
            ["--", "--method", "POST"],
        ):
            with self.subTest(extra=extra):
                self.reject(GET + extra)
        for command in ("call", "download", "request-endpoint", "post"):
            with self.subTest(command=command):
                self.reject([command])

    def test_rejects_malformed_inputs(self):
        self.reject(["get", "--method=POST", "--path", "/user"])
        self.reject(["get", "not-a-uuid", "--path", "/user"])
        for path in ("https://example.com", "//example.com", "/user?x=1", "/user#x"):
            self.reject(["get", CONNECTION, "--path", path])
        self.reject(GET + ["--query", "missing_equals"])

    def test_discovery_commands(self):
        for command in (["list"], ["permissions", CONNECTION]):
            self.assertEqual(MAIN(command), 0)
            self.assertEqual(self.run.call_args.args[0][1:], command)

    def test_output_is_private_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "response.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MAIN(GET + ["--output", str(output)]), 0)
            self.assertEqual(output.read_bytes(), b'{"number":96}\n')
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            command = self.run.call_args.args[0]
            self.assertEqual(command[1], "download")
            self.assertEqual(command[command.index("--method") + 1], "GET")
            self.assertNotEqual(command[-1], str(output))
            self.run.reset_mock()
            self.reject(GET + ["--output", str(output)])
            link = Path(temp) / "link"
            link.symlink_to(Path(temp) / "missing")
            self.reject(GET + ["--output", str(link)])

    def test_failure_does_not_create_output(self):
        self.run.side_effect = None
        self.run.return_value = subprocess.CompletedProcess([], 7, stdout=b"")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "response.json"
            self.assertEqual(MAIN(GET + ["--output", str(output)]), 7)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
