"""Exercise the wrapper in a temporary installation without real containers."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DorkspaceExecTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        scripts = self.root / "scripts"
        scripts.mkdir()
        for name in ["dorkspace-exec", "require-container-host.sh"]:
            shutil.copy2(ROOT / "scripts" / name, scripts / name)
        self.wrapper = scripts / "dorkspace-exec"
        self.container_root = self.root / "container workspace"
        self.container_root.mkdir()
        for name in ["gai-dorkspace", "rad-p2-dorkspace", "umi-dorkspace"]:
            folder = self.root / "skills" / name
            folder.mkdir(parents=True)
            # The production schema uses unquoted scalars without spaces.
            config = (ROOT / "skills" / name / "environment.yaml").read_text()
            config = "\n".join(
                "starters_root: " + str(self.root) if line.startswith("starters_root:") else line
                for line in config.splitlines()
            )
            (folder / "environment.yaml").write_text(config + "\n")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.make_executable("hostname", "#!/bin/sh\nprintf '%s\\n' \"${FAKE_HOST:-dylan-lambda}\"\n")
        self.make_executable("ds", """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
Path(os.environ['RECEIPT']).write_text(json.dumps({'argv':sys.argv[1:],'cwd':os.getcwd()}))
if len(sys.argv) > 3:
    os.execvp('/bin/bash', ['bash', '-c', ' '.join(sys.argv[3:])])
""")
        self.make_executable("docker", """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
Path(os.environ['RECEIPT']).write_text(json.dumps({'argv':sys.argv[1:],'cwd':os.getcwd()}))
print('fake running containers')
""")
        self.receipt = self.root / "receipt.json"
        self.env = dict(os.environ, PATH=str(self.bin) + ":" + os.environ["PATH"],
                        RECEIPT=str(self.receipt), BG_ROOT=str(self.container_root))
        # Use real bash to evaluate ds's joined payload, but isolate startup files
        # and profile behavior from the real machine.
        self.make_executable("bash", """#!/bin/sh
if [ "$1" = -lic ]; then
    shift
    exec /bin/bash --noprofile --norc -c "$@"
fi
exec /bin/bash "$@"
""")

    def make_executable(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)

    def run_wrapper(self, *args):
        return subprocess.run([str(self.wrapper), *args], env=self.env,
                              text=True, capture_output=True)

    def test_default_targets_and_host_cwd(self):
        for environment, target in [("gai", "rad_abb_fa-bg-processes"),
                                    ("umi", "bg_sumi_6-bg-processes"),
                                    ("rad-p2", "workspace")]:
            with self.subTest(environment=environment):
                result = self.run_wrapper(environment, "--interactive")
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads(self.receipt.read_text())
                self.assertEqual(receipt, {"argv": ["exec", target], "cwd": str(self.root)})

    def test_container_expansion_quotes_and_exit_status(self):
        # Container variables and substitutions must survive all quoting layers;
        # dollar signs and apostrophes in data must remain literal.
        command = '''printf '%s\\n' "$PWD" "$BG_ROOT" "$(printf inside)" 'it'"'"'s $literal'; exit 23'''
        result = self.run_wrapper("gai", "--command", command)
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [str(self.container_root),
                         str(self.container_root), "inside", "it's $literal"])

    def test_script_with_spaces_and_apostrophe(self):
        script = self.container_root / "it's a script.sh"
        script.write_text('printf "%s\\n" "$PWD"; exit 17\n')
        result = self.run_wrapper("gai", "--script", script.name)
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.container_root))

    def test_target_overrides(self):
        for option, value, expected in [("--system", "bg_arc_2", "bg_arc_2-bg-processes"),
                                        ("--target", "workspace", "workspace")]:
            result = self.run_wrapper("gai", option, value, "--interactive")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(self.receipt.read_text())["argv"], ["exec", expected])

    def test_no_init_runs_without_login_flags(self):
        result = self.run_wrapper("gai", "--no-init", "--command", "printf done")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "done")
        payload = json.loads(self.receipt.read_text())["argv"][2]
        self.assertTrue(payload.startswith("bash -c "))

    def test_guard_stops_before_config_or_tools(self):
        self.env["FAKE_HOST"] = "wrong-host"
        shutil.rmtree(self.root / "skills")
        result = self.run_wrapper("gai", "--command", "exit 0")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Container skill host check failed.", result.stderr)
        self.assertFalse(self.receipt.exists())

    def test_status_does_not_execute_ds(self):
        result = self.run_wrapper("umi", "--status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "fake running containers")
        self.assertEqual(json.loads(self.receipt.read_text())["argv"][0], "ps")

    def test_invalid_target_does_not_execute_tools(self):
        result = self.run_wrapper("gai", "--target", "workspace; touch bad", "--interactive")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.receipt.exists())


if __name__ == "__main__":
    unittest.main()
