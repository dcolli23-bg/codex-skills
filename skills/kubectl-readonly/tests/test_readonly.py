"""Exercise the approval boundary offline; no cluster or real credentials."""

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


MODULE = runpy.run_path(str(Path(__file__).parents[1] / "scripts/kubectl-readonly"))
MAIN = MODULE["main"]
PARSE = MODULE["parse"]
CONTEXT = MODULE["CONTEXT"]
PRIVILEGED_CONTEXT = MODULE["PRIVILEGED_CONTEXT"]
CONTEXTS = MODULE["CONTEXTS"]
CLUSTER = MODULE["CLUSTER"]
USER = MODULE["USER"]
SERVER = MODULE["SERVER"]
CONFIG = {
    "apiVersion": "v1", "kind": "Config", "current-context": CONTEXT,
    "contexts": [{"name": CONTEXT, "context": {"cluster": CLUSTER, "user": USER}}],
    "clusters": [{"name": CLUSTER, "cluster": {
        "server": SERVER, "certificate-authority-data": "TEST-CA",
    }}],
    "users": [{"name": USER, "user": {
        "client-certificate-data": "TEST-CERT", "client-key-data": "TEST-PRIVATE-KEY",
    }}],
}


class ReadonlyTests(unittest.TestCase):
    def setUp(self):
        self.account_home = "/home/test-laptop.user@example.com"
        self.account_patch = patch("pwd.getpwuid", side_effect=lambda _: SimpleNamespace(pw_dir=self.account_home))
        self.mock_account = self.account_patch.start()
        self.addCleanup(self.account_patch.stop)
        self.config = copy.deepcopy(CONFIG)
        self.selected_context = CONTEXT
        self.operations = []
        self.snapshots = []
        self.operation_status = 0
        self.operation_hook = None
        self.run_patch = patch("subprocess.run", side_effect=self.fake_run)
        self.mock_run = self.run_patch.start()
        self.addCleanup(self.run_patch.stop)

    def select_context(self, selected_context):
        self.selected_context = selected_context
        self.config = copy.deepcopy(CONFIG)
        self.config["current-context"] = selected_context
        self.config["contexts"][0]["name"] = selected_context

    def fake_run(self, command, **kwargs):
        self.assertEqual(command[0], "/usr/local/bin/kubectl")
        self.assertEqual(kwargs["env"], {
            "HOME": self.account_home, "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8", "KUBECTL_KUBERC": "false",
        })
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertFalse(kwargs.get("shell", False))
        if "config" in command:
            self.assertEqual(command[1:], [
                "--kubeconfig=" + self.account_home + "/.kube/config-auto",
                "--context=" + self.selected_context, "config", "view", "--minify",
                "--flatten", "--raw", "--output=json",
            ])
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(self.config).encode())
        snapshot = Path(command[1].removeprefix("--kubeconfig="))
        self.assertEqual(snapshot.stat().st_mode & 0o777, 0o600)
        self.assertEqual(snapshot.parent.stat().st_mode & 0o777, 0o700)
        config = json.loads(snapshot.read_text())
        self.assertEqual(config["current-context"], self.selected_context)
        self.assertEqual(config["contexts"], [{"name": self.selected_context, "context": {
            "cluster": CLUSTER, "user": USER,
            "namespace": self.config["contexts"][0]["context"].get("namespace", "default"),
        }}])
        self.assertEqual(config["clusters"][0]["cluster"]["server"], SERVER)
        self.assertEqual(config["users"][0]["user"], CONFIG["users"][0]["user"])
        self.assertEqual(command[2:7], [
            "--context=" + self.selected_context, "--server=" + SERVER,
            "--tls-server-name=k8s.rad-bill1.bg.bgrey.io",
            "--insecure-skip-tls-verify=false", "--request-timeout=30s",
        ])
        self.snapshots.append(snapshot)
        self.operations.append(command[7:])
        if self.operation_hook is not None:
            self.operation_hook(snapshot, config)
        if "stdout" in kwargs:
            kwargs["stdout"].write(b'{"test":"result"}\n')
        return subprocess.CompletedProcess(command, self.operation_status)

    def reject(self, args):
        self.mock_run.reset_mock()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            MAIN(args)
        self.assertEqual(error.exception.code, 2)
        self.mock_run.assert_not_called()

    def test_all_supported_command_paths(self):
        cases = [
            (["get", "pods", "-A"], ["get", "--all-namespaces=true", "pods"]),
            (["describe", "pod", "sumi-2204-0", "-n", "cell9"],
             ["describe", "--namespace=cell9", "pod", "sumi-2204-0"]),
            (["logs", "sumi-2204-0", "-c", "procman", "--tail=-1", "-p"],
             ["logs", "--container=procman", "--previous=true", "--tail=-1", "sumi-2204-0"]),
            (["events", "-A", "-w"], ["get", "events", "--all-namespaces=true", "--watch=true"]),
            (["top", "pods", "-A", "--containers"],
             ["top", "pod", "--all-namespaces=true", "--containers=true"]),
            (["top", "no", "bil-cell-9", "--sort-by=memory"],
             ["top", "node", "--sort-by=memory", "bil-cell-9"]),
            (["api-resources", "--verbs=get,list,watch,create"],
             ["api-resources", "--verbs=get,list,watch,create"]),
            (["api-versions"], ["api-versions"]),
            (["explain", "pods.spec.containers", "--api-version=v1", "--recursive"],
             ["explain", "--api-version=v1", "--recursive=true", "pods.spec.containers"]),
            (["version", "--client", "-o", "json"],
             ["version", "--client=true", "--output=json"]),
            (["cluster-info"], ["cluster-info"]),
            (["cluster-info", "dump", "--namespaces=cell9,cell13"],
             ["cluster-info", "dump", "--namespaces=cell9,cell13"]),
            (["wait", "pod/sumi-2204-0", "--for=delete", "--timeout=30s"],
             ["wait", "--for=delete", "--timeout=30s", "pod/sumi-2204-0"]),
            (["rollout", "history", "statefulset/sumi-2204", "--revision=3"],
             ["rollout", "history", "--revision=3", "statefulset/sumi-2204"]),
            (["rollout", "status", "statefulset/sumi-2204", "--watch=false", "--timeout=1m"],
             ["rollout", "status", "--watch=false", "--timeout=1m", "statefulset/sumi-2204"]),
        ]
        for selected_context in CONTEXTS:
            self.select_context(selected_context)
            for args, expected in cases:
                with self.subTest(context=selected_context, args=args):
                    self.assertEqual(MAIN(args + ["--context", selected_context]), 0)
                    self.assertEqual(self.operations[-1], expected)
                    self.assertFalse(self.snapshots[-1].exists())

    def test_common_realistic_inspection(self):
        columns = "custom-columns=NS:.metadata.namespace,IMAGES:.status.containerStatuses[*].imageID"
        args = [
            "get", "-A", "pods", "--field-selector", "metadata.name=sumi-2204-0",
            "-o", columns, "--request-timeout=45s",
        ]
        self.assertEqual(MAIN(args), 0)
        self.assertIn("--output=" + columns, self.operations[-1])
        self.assertIn("--field-selector=metadata.name=sumi-2204-0", self.operations[-1])
        self.assertIn("--request-timeout=45s", self.operations[-1])

    def test_all_resource_types_including_sensitive_and_custom_resources(self):
        for args in (
            ["get", "secrets", "-A", "-o", "json"],
            ["get", "configmaps,deployments.v1.apps", "-A"],
            ["get", "widgets.example.io/example"],
            ["get", "clusterroles", "system:controller:job-controller"],
            ["get", "pod/one", "service/two"],
        ):
            with self.subTest(args=args):
                self.assertEqual(MAIN(args), 0)

    def test_streaming_flags_and_boolean_values(self):
        for args, flag in (
            (["get", "--watch", "pods"], "--watch=true"),
            (["get", "pods", "--watch-only=true"], "--watch-only=true"),
            (["get", "pods", "-A=false"], "--all-namespaces=false"),
            (["logs", "-f", "--selector=app=sumi"], "--follow=true"),
        ):
            with self.subTest(args=args):
                self.assertEqual(MAIN(args), 0)
                self.assertIn(flag, self.operations[-1])

    def test_inline_templates_and_selector_strings_are_only_data(self):
        selector = "app=$(touch /tmp/not-executed); --server=evil"
        for output in (
            "jsonpath={.items[*].metadata.name}",
            "jsonpath-as-json={.items[*]}",
            'go-template={{range .items}}{{.metadata.name}}{{"\\n"}}{{end}}',
        ):
            self.assertEqual(MAIN(["get", "pods", "-l", selector, "-o", output]), 0)
            self.assertIn("--selector=" + selector, self.operations[-1])
            self.assertIn("--output=" + output, self.operations[-1])

    def test_repeated_slice_flags_preserve_every_value(self):
        for args, expected in (
            (["cluster-info", "dump", "--namespaces=cell9", "--namespaces=cell13,cell14"],
             ["--namespaces=cell9", "--namespaces=cell13,cell14"]),
            (["get", "pods", "-L", "app", "-L", "component"],
             ["--label-columns=app", "--label-columns=component"]),
            (["api-resources", "--verbs=get", "--verbs=list,watch"],
             ["--verbs=get", "--verbs=list,watch"]),
        ):
            with self.subTest(args=args):
                self.assertEqual(MAIN(args), 0)
                self.assertEqual(
                    [arg for arg in self.operations[-1] if arg.startswith(expected[0].split("=")[0])],
                    expected,
                )

    def test_only_explicit_allowlisted_contexts_are_accepted(self):
        for selected_context in CONTEXTS:
            self.select_context(selected_context)
            for context_args in (["--context", selected_context], ["--context=" + selected_context]):
                with self.subTest(context_args=context_args):
                    self.assertEqual(MAIN(["get", "pods"] + context_args), 0)
                    self.assertEqual(self.operations[-1], ["get", "pods"])
        for value in (
            "k8s/bg-rad-itf-context", "", "https://evil",
            CONTEXT + "-privileged", PRIVILEGED_CONTEXT + "-other",
        ):
            self.reject(["get", "pods", "--context=" + value])
        self.reject(["--context=" + CONTEXT, "get", "pods"])

    def test_default_ignores_current_context_and_caller_context_environment(self):
        self.config["current-context"] = PRIVILEGED_CONTEXT
        with patch.dict(os.environ, {"KUBECTL_CONTEXT": PRIVILEGED_CONTEXT}):
            self.assertEqual(MAIN(["get", "pods"]), 0)
        self.assertEqual(self.selected_context, CONTEXT)

    def test_selected_context_mismatch_fails_without_fallback(self):
        for selected_context, returned_context in (
            (CONTEXT, PRIVILEGED_CONTEXT), (PRIVILEGED_CONTEXT, CONTEXT),
        ):
            self.select_context(selected_context)
            self.config["contexts"][0]["name"] = returned_context
            self.mock_run.reset_mock()
            with self.subTest(context=selected_context), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(MAIN(["get", "pods", "--context", selected_context]), 1)
            self.assertEqual(self.mock_run.call_count, 1)
        self.assertFalse(self.operations)

    def test_config_failure_does_not_retry_with_another_context(self):
        self.mock_run.side_effect = None
        self.mock_run.return_value = subprocess.CompletedProcess([], 1, stdout=b"", stderr=b"denied")
        for context_args in ([], ["--context", PRIVILEGED_CONTEXT]):
            self.mock_run.reset_mock()
            with self.subTest(context_args=context_args), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(MAIN(["get", "pods"] + context_args), 1)
            self.assertEqual(self.mock_run.call_count, 1)
            selected_context = context_args[-1] if context_args else CONTEXT
            self.assertIn("--context=" + selected_context, self.mock_run.call_args.args[0])

    def test_read_failure_does_not_retry_with_another_context(self):
        self.operation_status = 1
        for selected_context in CONTEXTS:
            self.select_context(selected_context)
            self.mock_run.reset_mock()
            with self.subTest(context=selected_context):
                self.assertEqual(MAIN(["get", "pods", "--context", selected_context]), 1)
            self.assertEqual(self.mock_run.call_count, 2)

    def test_rejects_all_mutations_and_execution_before_any_subprocess(self):
        for command in (
            "apply", "create", "delete", "edit", "patch", "replace", "scale",
            "autoscale", "cordon", "uncordon", "drain", "taint", "label",
            "annotate", "run", "set", "expose", "certificate", "exec", "attach",
            "cp", "debug", "port-forward", "proxy", "plugin", "kustomize",
            "diff", "config", "auth", "arbitrary-plugin",
        ):
            for selected_context in CONTEXTS:
                with self.subTest(command=command, context=selected_context):
                    self.reject([command, "pods", "--context", selected_context])
        for subcommand in ("pause", "resume", "restart", "undo", "anything"):
            self.reject(["rollout", subcommand, "deployment/sumi"])
        self.reject(["top", "anything"])
        self.reject(["cluster-info", "anything"])

    def test_rejects_dangerous_flags_on_every_supported_operation(self):
        bases = [
            ["get", "pods"], ["describe", "pods"], ["logs", "pod/name"],
            ["events"], ["top", "pod"], ["top", "node"], ["api-resources"],
            ["api-versions"], ["explain", "pods"], ["version"], ["cluster-info"],
            ["cluster-info", "dump"], ["wait", "pod/name", "--for=delete"],
            ["rollout", "history", "deployment/name"],
            ["rollout", "status", "deployment/name"],
        ]
        dangerous = [
            "--raw=/api/v1/nodes/name/proxy/run",
            "--server=https://evil", "-shttps://evil", "--kubeconfig=/tmp/evil",
            "--cluster=evil", "--user=evil", "--token=secret",
            "--client-certificate=/tmp/cert", "--client-key=/tmp/key",
            "--certificate-authority=/tmp/ca", "--insecure-skip-tls-verify",
            "--tls-server-name=evil", "--as=admin", "--as-group=system:masters",
            "--username=evil", "--password=secret", "--profile=cpu",
            "--profile-output=/tmp/existing", "--log-file=/tmp/existing",
            "--cache-dir=/tmp/evil", "--kuberc=/tmp/evil",
            "--subresource=proxy", "--dry-run=server", "--force",
            "--filename=/tmp/file.yaml", "--kustomize=/tmp/path",
            "--output-directory=/tmp/existing", "--template=/etc/passwd",
            "--req=1s", "--name=other", "--method=POST",
        ]
        for selected_context in CONTEXTS:
            for base in bases:
                context_args = ["--context", selected_context]
                for flag in dangerous:
                    with self.subTest(context=selected_context, base=base, flag=flag):
                        self.reject(base + context_args + [flag])
                self.reject(base + context_args + ["--", "exec", "pod/name", "sh"])

    def test_paths_and_shell_payloads_are_not_resource_names(self):
        for value in (
            "../pods", "pods/../nodes", "pods/foo/proxy", "nodes/name/proxy/run",
            "/api/v1/pods", "https://evil/pods", "//evil", "pods%2Ffoo",
            "pods/foo?subresource=exec", "pods/foo#bar", "pods/foo\\bar",
            "pods/foo;touch", "$(touch /tmp/not-executed)", ".",
            "pods/", "pods,,services", "pods/\nfoo", "pods/\0foo",
        ):
            with self.subTest(value=value):
                self.reject(["get", value])
        self.reject(["get", "pods", "-n", "../other"])
        self.reject(["get", "pods", "-n", "INVALID"])
        self.reject(["cluster-info", "dump", "--namespaces=cell9,../bad"])
        self.reject(["explain", "pods", "--api-version=../../proxy"])

    def test_rejects_file_output_formats(self):
        for value in (
            "jsonpath-file=/etc/passwd", "custom-columns-file=/etc/passwd",
            "go-template-file=/etc/passwd", "templatefile=/etc/passwd",
            "go-template", "jsonpath=", "json;touch",
        ):
            self.reject(["get", "pods", "-o", value])

    def test_rejects_formats_and_flags_not_supported_by_the_command(self):
        for base in (
            ["wait", "pod/name", "--for=condition=Ready"],
            ["cluster-info", "dump"],
            ["rollout", "history", "statefulset/sumi-2204"],
        ):
            self.reject(base + ["-o", "wide"])
            self.reject(base + ["-o", "custom-columns=REV:.revision"])
            self.assertEqual(MAIN(base + ["-o", "json"]), 0)
        self.reject(["describe", "pods", "--field-selector=metadata.name=sumi-2204-0"])

    def test_required_arguments_and_bad_flag_values(self):
        for args in (
            ["get"], ["describe"], ["logs"], ["logs", "one", "two"],
            ["wait", "pod/name"], ["get", "pods", "--watch=maybe"],
            ["get", "pods", "--request-timeout=oops"],
            ["logs", "pod/name", "--tail=-2"],
            ["top", "pod", "--sort-by=anything"],
            ["rollout", "history"], ["explain"],
        ):
            with self.subTest(args=args):
                self.reject(args)

    def test_safe_environment_ignores_caller_overrides(self):
        with patch.dict(os.environ, {
            "KUBECONFIG": "/tmp/evil", "HOME": "/tmp/evil",
            "PATH": "/tmp/evil", "HTTPS_PROXY": "http://evil",
            "KUBECTL_KUBERC": "/tmp/evil", "KUBECTL_EXTERNAL_DIFF": "touch /tmp/evil",
        }):
            self.assertEqual(MAIN(["get", "pods"]), 0)
        self.assertEqual(self.mock_run.call_count, 2)

    def test_managed_config_follows_os_account_on_both_hosts(self):
        for home in ("/home/desktop-user", "/home/laptop.user@example.com"):
            with self.subTest(home=home), patch.dict(os.environ, {
                "HOME": "/tmp/evil", "KUBECONFIG": "/tmp/evil",
            }):
                self.account_home = home
                self.assertEqual(MAIN(["get", "pods"]), 0)
                self.mock_account.assert_called_with(os.getuid())

    def test_unknown_os_account_fails_closed_without_subprocess(self):
        self.mock_account.side_effect = KeyError("unmapped uid")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(MAIN(["get", "pods"]), 1)
        self.mock_run.assert_not_called()
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_config_target_and_transport_fail_closed(self):
        mutations = [
            lambda d: d["contexts"][0].update(name="other"),
            lambda d: d["contexts"][0]["context"].update(cluster="other"),
            lambda d: d["contexts"][0]["context"].update(user="other"),
            lambda d: d["clusters"][0].update(name="other"),
            lambda d: d["users"][0].update(name="other"),
            lambda d: d["clusters"][0]["cluster"].update(server="https://evil"),
            lambda d: d["clusters"][0]["cluster"].update(**{"proxy-url": "http://evil"}),
            lambda d: d["clusters"][0]["cluster"].update(**{"insecure-skip-tls-verify": True}),
            lambda d: d["clusters"][0]["cluster"].update(**{"tls-server-name": "evil"}),
            lambda d: d["users"][0]["user"].update(exec={"command": "/tmp/evil"}),
            lambda d: d["users"][0]["user"].update(**{"auth-provider": {"name": "evil"}}),
            lambda d: d["users"][0]["user"].pop("client-key-data"),
            lambda d: d["clusters"].append(copy.deepcopy(d["clusters"][0])),
            lambda d: d.update(contexts=[]),
        ]
        for selected_context in CONTEXTS:
            for mutate in mutations:
                self.select_context(selected_context)
                mutate(self.config)
                self.mock_run.reset_mock()
                with self.subTest(config=self.config), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(MAIN(["get", "pods", "--context", selected_context]), 1)
                    self.assertEqual(self.mock_run.call_count, 1)
                    self.assertFalse(self.operations)

    def test_snapshot_keeps_only_known_fields_and_survives_source_change(self):
        self.config["clusters"][0]["cluster"]["extensions"] = [{"future": "bad"}]
        self.config["users"][0]["user"]["future-executable"] = "bad"
        self.config["contexts"][0]["context"]["namespace"] = "cell9"

        def hook(snapshot, config):
            self.assertNotIn("extensions", config["clusters"][0]["cluster"])
            self.assertNotIn("future-executable", config["users"][0]["user"])
            self.assertEqual(config["contexts"][0]["context"]["namespace"], "cell9")
            self.config["users"][0]["user"]["exec"] = {"command": "evil"}
            self.config["clusters"][0]["cluster"]["server"] = "https://evil"
            self.assertEqual(json.loads(snapshot.read_text()), config)

        self.operation_hook = hook
        self.assertEqual(MAIN(["get", "pods"]), 0)
        self.assertFalse(self.snapshots[0].parent.exists())

    def test_preflight_errors_do_not_leak_credentials(self):
        for response in (
            subprocess.CompletedProcess([], 1, stdout=b"TEST-PRIVATE-KEY", stderr=b"secret"),
            subprocess.CompletedProcess([], 0, stdout=b"invalid JSON containing a secret"),
            subprocess.CompletedProcess([], 0, stdout=b"null"),
            subprocess.CompletedProcess([], 0, stdout=b'{"contexts": null}'),
            subprocess.CompletedProcess([], 0, stdout=b'{"contexts":{"name":1},"clusters":[1],"users":[1]}'),
        ):
            self.mock_run.side_effect = None
            self.mock_run.return_value = response
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(MAIN(["get", "pods"]), 1)
            self.assertNotIn("PRIVATE", stderr.getvalue())
            self.assertNotIn("secret", stderr.getvalue())

    def test_invalid_default_namespace_is_rejected_without_traceback(self):
        self.config["contexts"][0]["context"]["namespace"] = "../../secret"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(MAIN(["get", "pods"]), 1)
        self.assertEqual(self.mock_run.call_count, 1)
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertNotIn("secret", stderr.getvalue())

    def test_save_output_is_private_and_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pods.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MAIN(["get", "pods", "--save-output", str(output)]), 0)
            self.assertEqual(output.read_bytes(), b'{"test":"result"}\n')
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.reject(["get", "pods", "--save-output", str(output)])
            link = Path(directory) / "link"
            link.symlink_to(Path(directory) / "nonexistent")
            self.reject(["get", "pods", "--save-output", str(link)])

    def test_failed_read_does_not_create_output(self):
        self.operation_status = 7
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pods.json"
            self.assertEqual(MAIN(["get", "pods", "--save-output", str(output)]), 7)
            self.assertFalse(output.exists())
            self.assertFalse(self.snapshots[-1].exists())

    def test_output_race_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pods.json"
            self.operation_hook = lambda *_: output.write_bytes(b"preserve")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(MAIN(["get", "pods", "--save-output", str(output)]), 1)
            self.assertEqual(output.read_bytes(), b"preserve")
            self.assertFalse(self.snapshots[-1].exists())

    def test_return_codes_and_snapshot_cleanup_on_interrupt(self):
        self.operation_status = -15
        self.assertEqual(MAIN(["get", "pods"]), 143)
        self.operation_hook = lambda *_: (_ for _ in ()).throw(KeyboardInterrupt())
        self.assertEqual(MAIN(["get", "pods"]), 130)
        self.assertFalse(self.snapshots[-1].exists())

    def test_help_does_not_launch_kubectl(self):
        for args in (["--help"], ["get", "--help"], ["rollout", "status", "--help"]):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as error:
                MAIN(args)
            self.assertEqual(error.exception.code, 0)
        self.mock_run.assert_not_called()

    def test_parser_returns_only_normalized_allowlisted_arguments(self):
        operation, output, selected_context = PARSE(["get", "-ncell9", "pods", "--ignore-not-found=false"])
        self.assertEqual(operation, ["get", "--namespace=cell9", "--ignore-not-found=false", "pods"])
        self.assertIsNone(output)
        self.assertEqual(selected_context, CONTEXT)


if __name__ == "__main__":
    unittest.main()
