"""Offline contract tests: no gateway or Jira requests are made."""

import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bg-jira-comments"
MODULE = runpy.run_path(str(SCRIPT))
MAIN = MODULE["main"]
CONNECTION = "9b8e56c5-0aee-4d28-a8a8-e3703dd9d2ef"
ENDPOINT = {
    "enabled": True, "method": "POST",
    "path": "/rest/api/3/issue/{issueIdOrKey}/comment",
}
PERMISSIONS = {
    "platform": "jira", "callable": True,
    "products": [{"enabled": True, "categories": [{
        "enabled": True, "endpoints": [ENDPOINT],
    }]}],
}
DOCUMENT = {
    "type": "doc", "version": 1, "content": [{
        "type": "paragraph", "content": [
            {"type": "text", "text": "[codex] Checked the historical evidence. "},
            {"type": "text", "text": "Related ticket", "marks": [
                {"type": "link", "attrs": {"href": "https://example.atlassian.net/browse/SKU100-123"}},
            ]},
        ],
    }],
}
CREATED = {"status": 201, "bodyText": '{"id":"12345"}', "bodyTruncated": False}


class CommentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.body = Path(temp.name) / "body.json"
        self.write_body(DOCUMENT)
        self.args = ["post", CONNECTION, "--issue", "SKU100-123", "--body-file", str(self.body)]
        self.permissions = copy.deepcopy(PERMISSIONS)
        self.created = copy.deepcopy(CREATED)
        self.run = patch("subprocess.run").start()
        self.addCleanup(patch.stopall)
        self.run.side_effect = self.respond
        patch.object(Path, "is_file", return_value=True).start()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def write_body(self, value):
        self.body.write_text(json.dumps(value), encoding="utf-8")

    def respond(self, command, **kwargs):
        value = self.permissions if command[-2] == "permissions" else self.created
        return subprocess.CompletedProcess(command, 0, json.dumps(value), "")

    def call(self, args=None):
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stderr):
            return MAIN(self.args if args is None else args)

    def reject(self, args):
        with self.assertRaises(SystemExit) as error:
            self.call(args)
        self.assertEqual(error.exception.code, 2)
        self.run.assert_not_called()

    def test_post_has_one_fixed_write_and_body_only(self):
        self.assertEqual(self.call(), 0)
        self.assertEqual(self.run.call_count, 2)
        permission, post = [call.args[0] for call in self.run.call_args_list]
        self.assertEqual(permission[1:], ["permissions", CONNECTION])
        self.assertEqual(post[1:9], [
            "call", CONNECTION, "--method", "POST", "--path",
            "/rest/api/3/issue/SKU100-123/comment", "--header", "Content-Type: application/json",
        ])
        self.assertEqual(post[9], "--body-text")
        self.assertEqual(json.loads(post[10]), {"body": DOCUMENT})
        self.assertEqual(len(post), 11)
        for call in self.run.call_args_list:
            self.assertNotIn("shell", call.kwargs)
            self.assertEqual(call.kwargs["timeout"], 150)
        self.assertEqual(json.loads(self.stdout.getvalue()), {"issue": "SKU100-123", "commentId": "12345"})

    def test_check_never_posts(self):
        self.assertEqual(self.call(["check", CONNECTION]), 0)
        self.run.assert_called_once()
        self.assertEqual(self.run.call_args.args[0][1], "permissions")

    def test_unknown_write_controls_rejected_before_network(self):
        for flag in ("--method", "--path", "--url", "--header", "--query",
                     "--client", "--body-text", "--visibility", "--iss"):
            with self.subTest(flag=flag):
                self.reject(self.args + [flag, "anything"])
        for command in ("edit", "delete", "transition", "attach", "call", "get"):
            with self.subTest(command=command):
                self.reject([command, CONNECTION])
        self.reject(["check", CONNECTION, "--issue", "SKU100-123"])

    def test_invalid_connection_and_target_never_reach_network(self):
        for connection in ("jira:default", "x/../../", ""):
            args = self.args.copy()
            args[1] = connection
            self.reject(args)
        for key in ("123", "sku100-123", "SKU100-0", "SKU100-123/comment/4",
                    "SKU100-123?x=1", "SKU100-123#x", "../SKU100-123",
                    "SKU100-123\n", "SKU100-123; touch /tmp/unwanted"):
            args = self.args.copy()
            args[3] = key
            self.reject(args)

    def test_body_payloads_rejected_before_network(self):
        for value in ([], None, {}, {"body": DOCUMENT},
                      {**DOCUMENT, "properties": []},
                      {**DOCUMENT, "type": "anything"},
                      {**DOCUMENT, "version": True},
                      {**DOCUMENT, "version": 2},
                      {**DOCUMENT, "content": []},
                      {**DOCUMENT, "content": [None]},
                      {**DOCUMENT, "content": [{"type": "paragraph", "content": {}}]},
                      {**DOCUMENT, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "No attribution"}]}]}):
            with self.subTest(value=value):
                self.write_body(value)
                self.assertEqual(self.call(), 1)
                self.run.assert_not_called()
        self.body.write_text("{bad json", encoding="utf-8")
        self.assertEqual(self.call(), 1)
        self.run.assert_not_called()

    def test_missing_body_never_reaches_network(self):
        self.body.unlink()
        self.assertEqual(self.call(), 1)
        self.run.assert_not_called()

    def test_denied_permissions_never_post(self):
        denied = [
            {**PERMISSIONS, "platform": "github"},
            {**PERMISSIONS, "callable": False},
            {**PERMISSIONS, "callable": "true"},
            {**PERMISSIONS, "products": []},
            {**PERMISSIONS, "products": None},
            [], None,
        ]
        for level in ("product", "category", "endpoint"):
            for flag in ("enabled", "platformEnabled"):
                value = copy.deepcopy(PERMISSIONS)
                product = value["products"][0]
                category = product["categories"][0]
                target = {"product": product, "category": category,
                          "endpoint": category["endpoints"][0]}[level]
                target[flag] = False
                denied.append(value)
        for overrides in ({"enabled": "true"}, {"method": "PUT"},
                          {"path": "/rest/api/3/issue/{issueIdOrKey}"},
                          {"path": "/rest/api/3/issue/{issueIdOrKey}/comment/{id}"}):
            value = copy.deepcopy(PERMISSIONS)
            value["products"][0]["categories"][0]["endpoints"][0].update(overrides)
            denied.append(value)
        for value in denied:
            with self.subTest(value=value):
                self.run.reset_mock()
                self.permissions = value
                self.assertEqual(self.call(), 1)
                self.run.assert_called_once()

    def test_legacy_permission_and_current_denial_precedence(self):
        legacy = {
            "platform": "jira", "callable": True,
            "permissions": [{"enabled": True, "children": [ENDPOINT]}],
        }
        self.permissions = legacy
        self.assertEqual(self.call(), 0)
        self.run.reset_mock()
        self.permissions = {**legacy, "products": []}
        self.assertEqual(self.call(), 1)
        self.run.assert_called_once()

    def test_permission_failures_never_post(self):
        for error in (subprocess.TimeoutExpired("permissions", 150), OSError("no client")):
            with self.subTest(error=error):
                self.run.reset_mock()
                self.run.side_effect = error
                self.assertEqual(self.call(), 1)
                self.run.assert_called_once()
        for result in (subprocess.CompletedProcess([], 1, "", "denied"),
                       subprocess.CompletedProcess([], 0, "{", "")):
            self.run.reset_mock()
            self.run.side_effect = None
            self.run.return_value = result
            self.assertEqual(self.call(), 1)
            self.run.assert_called_once()

    def test_unconfirmed_creation_never_retries(self):
        for value in ([], {}, {**CREATED, "status": 200},
                      {**CREATED, "status": 403},
                      {**CREATED, "bodyTruncated": True},
                      {**CREATED, "bodyText": "{"},
                      {**CREATED, "bodyText": "null"},
                      {**CREATED, "bodyText": '{"id":""}'},
                      {**CREATED, "bodyText": '{"id":true}'}):
            with self.subTest(value=value):
                self.run.reset_mock()
                self.created = value
                self.assertEqual(self.call(), 1)
                self.assertEqual(self.run.call_count, 2)
                self.assertIn("Do not retry blindly", self.stderr.getvalue())

    def test_post_network_failure_does_not_retry(self):
        for failure in (
            subprocess.TimeoutExpired("call", 150),
            OSError("interrupted"),
            subprocess.CompletedProcess([], 1, "", "network failed"),
            subprocess.CompletedProcess([], 0, "{", ""),
        ):
            with self.subTest(failure=failure):
                self.run.reset_mock()
                permission_result = subprocess.CompletedProcess([], 0, json.dumps(PERMISSIONS), "")
                self.run.side_effect = [permission_result, failure]
                self.assertEqual(self.call(), 1)
                self.assertEqual(self.run.call_count, 2)
                self.assertIn("Do not retry blindly", self.stderr.getvalue())

    def test_python_client_fallback(self):
        # Managed installations currently provide only the .py client.
        with patch.object(Path, "is_file", side_effect=[False, True]):
            self.assertEqual(self.call(["check", CONNECTION]), 0)
        command = self.run.call_args.args[0]
        self.assertEqual(command[0], sys.executable)
        self.assertTrue(command[1].endswith("bga-connections.py"))
        self.assertEqual(command[2:], ["permissions", CONNECTION])

    def test_missing_client_does_not_contact_gateway(self):
        with patch.object(Path, "is_file", return_value=False):
            self.assertEqual(self.call(), 1)
        self.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
