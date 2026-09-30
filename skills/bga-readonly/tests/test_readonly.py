"""Check the wrapper's approval boundary without credentials or network calls."""

import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch


MAIN = runpy.run_path(str(Path(__file__).parents[1] / "scripts/bga-readonly"))["main"]
CONNECTION = "67fbd876-5c7c-49b4-8481-e6fc795aaee7"
GET = ["get", CONNECTION, "--path", "/repos/berkshiregrey/bg_rad_core/pulls/96"]
ELASTIC = ["elastic", CONNECTION, "--index", "rad-bill1-log.records-alias"]
ELASTIC_PERMISSIONS = {
    "platform": "elastic", "callable": True,
    "permissions": [{"enabled": True, "children": [
        {"enabled": True, "platformEnabled": True, "method": "POST",
         "path": "/{index}/" + endpoint}
        for endpoint in ("_search", "_count", "_field_caps")
    ]}],
}


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
        if command[1] == "permissions":
            return subprocess.CompletedProcess([], 0, stdout=json.dumps(ELASTIC_PERMISSIONS).encode())
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

    def test_elastic_queries_fix_endpoint_and_preserve_body_as_data(self):
        query = {"query": {"match": {"message": "$(touch /tmp/not-executed); --method DELETE"}}}
        for operation, endpoint in (("search", "_search"), ("count", "_count"),
                                    ("field-caps", "_field_caps")):
            with self.subTest(operation=operation):
                self.run.reset_mock()
                self.assertEqual(MAIN(ELASTIC + ["--operation", operation,
                                               "--body-text", json.dumps(query)]), 0)
                self.assertEqual(self.run.call_args_list[0].args[0][1:], ["permissions", CONNECTION])
                args, kwargs = self.run.call_args
                self.assertEqual(args[0][1:6], [
                    "call", CONNECTION, "--method", "POST",
                    "--path=/rad-bill1-log.records-alias/" + endpoint,
                ])
                self.assertEqual(json.loads(args[0][6].removeprefix("--body-text=")), query)
                self.assertFalse(kwargs.get("shell", False))

    def test_elastic_body_file_and_complete_private_output(self):
        with tempfile.TemporaryDirectory() as temp:
            body = Path(temp) / "query.json"
            body.write_text('{"size": 0, "query": {"match_all": {}}}')
            output = Path(temp) / "response.json"
            args = ELASTIC + ["--body-file", str(body), "--query", "timeout=10s",
                              "--output", str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MAIN(args), 0)
            self.assertEqual(output.read_bytes(), b'{"number":96}\n')
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            command = self.run.call_args.args[0]
            self.assertEqual(command[1], "download")
            self.assertIn("--query=timeout=10s", command)
            self.assertIn('--body-text={"size": 0, "query": {"match_all": {}}}', command)
            self.run.reset_mock()
            self.reject(args)

    def test_elastic_rejects_paths_writes_and_malformed_bodies_before_network(self):
        for index in ("../logs", "logs/../_bulk", "logs/_delete_by_query", "%2e%2e", "..",
                      "_scripts", "https://example.com", "logs?x=1", "logs#x", "logs\\x"):
            with self.subTest(index=index):
                self.reject(["elastic", CONNECTION, "--index", index, "--body-text", "{}"])
        for extra in (["--path", "/_bulk"], ["--method", "DELETE"],
                      ["--operation", "delete_by_query"], ["--operation", "msearch"],
                      ["--header", "X-HTTP-Method-Override: DELETE"],
                      ["--url", "https://example.com"], ["--body-base64", "e30="],
                      ["--body-file", "/tmp/another-query.json"]):
            self.reject(ELASTIC + ["--body-text", "{}"] + extra)
        for body in ("{", "[]", "null", '{"size":NaN}'):
            self.reject(ELASTIC + ["--body-text", body])
        self.reject(ELASTIC)
        self.reject(ELASTIC + ["--body-file", "/nonexistent/bga-readonly-query.json"])

    def test_elastic_fails_closed_for_wrong_provider_or_disabled_permissions(self):
        denied = [
            {**ELASTIC_PERMISSIONS, "platform": "github"},
            {**ELASTIC_PERMISSIONS, "callable": False},
            {**ELASTIC_PERMISSIONS, "permissions": []},
            {**ELASTIC_PERMISSIONS, "permissions": [
                {**ELASTIC_PERMISSIONS["permissions"][0], "enabled": False}]},
        ]
        for override in ({"enabled": False}, {"platformEnabled": False},
                         {"method": "GET"}, {"path": "/{index}/_delete_by_query"}):
            endpoint = {**ELASTIC_PERMISSIONS["permissions"][0]["children"][0], **override}
            denied.append({**ELASTIC_PERMISSIONS, "permissions": [endpoint]})
        self.run.side_effect = None
        for permissions in denied:
            with self.subTest(permissions=permissions), tempfile.TemporaryDirectory() as temp:
                self.run.reset_mock()
                self.run.return_value = subprocess.CompletedProcess(
                    [], 0, stdout=json.dumps(permissions).encode())
                output = Path(temp) / "response.json"
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(MAIN(ELASTIC + ["--body-text", "{}", "--output", str(output)]), 1)
                self.run.assert_called_once()
                self.assertEqual(self.run.call_args.args[0][1], "permissions")
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
