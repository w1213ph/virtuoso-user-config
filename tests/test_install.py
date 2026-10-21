import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", str(ROOT / "install.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.target = self.directory / "profile with spaces"
        self.entry = self.directory / ".cdsinit"
        self.original = b'; existing PDK and key bindings\r\n; non-UTF8 byte: \xff\r\n'
        self.entry.write_bytes(self.original)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, command, *options, expected=0):
        result = subprocess.run([sys.executable, str(ROOT / "install.py"), command,
                                 "--root", str(self.target), "--cdsinit", str(self.entry)] + list(options),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_plan_has_no_writes(self):
        self.run_cli("plan", "--op")
        self.assertFalse(self.target.exists())
        self.assertEqual(self.entry.read_bytes(), self.original)

    def test_install_multiple_entries_and_exact_rollback(self):
        other = self.directory / "project.cdsinit"
        self.run_cli("install", "--op", "--cdsinit", str(other))
        self.assertTrue(self.entry.read_bytes().startswith(self.original))
        self.assertEqual(self.entry.read_bytes().count(installer.BEGIN.rstrip()), 1)
        self.assertTrue(other.exists())
        self.run_cli("status")
        self.run_cli("install", expected=1)
        self.run_cli("rollback")
        self.assertEqual(self.entry.read_bytes(), self.original)
        self.assertFalse(other.exists())
        self.assertFalse((self.target / "ui.il").exists())

    def test_conflict_refuses_all_rollback_writes(self):
        self.run_cli("install", "--op")
        env = self.target / "ui.cdsenv"
        env.write_bytes(env.read_bytes() + b"; later local edit\n")
        current = self.entry.read_bytes()
        self.run_cli("rollback", expected=1)
        self.assertEqual(self.entry.read_bytes(), current)
        self.assertTrue((self.target / "ui.il").exists())

    def test_unrelated_startup_change_preserved_on_rollback(self):
        self.run_cli("install")
        self.entry.write_bytes(self.entry.read_bytes() + b"; later user setting\n")
        self.run_cli("rollback")
        self.assertTrue(self.entry.read_bytes().endswith(b"; later user setting\n"))
        self.assertNotIn(installer.BEGIN.rstrip(), self.entry.read_bytes())

    def test_modules_install_and_rollback_independently(self):
        self.run_cli("install", "--features", "q-scope")
        first = self.target
        self.target = self.directory / "second module"
        self.run_cli("install", "--features", "viva")
        second = self.target
        self.assertNotIn("hiSetFont", (first / "ui.il").read_text())
        self.assertNotIn("objectScope", (second / "ui.cdsenv").read_text())
        self.target = self.directory / "overlap"
        self.run_cli("install", "--features", "q-scope", expected=1)
        self.target = first
        self.run_cli("rollback")
        self.assertIn(str(second.as_posix()).encode(), self.entry.read_bytes())
        self.target = second
        self.run_cli("status")
        self.run_cli("rollback")
        self.assertEqual(self.entry.read_bytes(), self.original)

    def test_edit_inside_startup_block_blocks_rollback(self):
        self.run_cli("install", "--features", "q-scope")
        self.entry.write_bytes(self.entry.read_bytes().replace(b"Load failed", b"Changed"))
        self.run_cli("rollback", expected=1)
        self.assertTrue((self.target / "ui.il").exists())

    def test_missing_models_refused_before_writes(self):
        config = self.directory / "models.json"
        config.write_text(json.dumps({"profiles": [{"technology_read_path": str(self.directory),
                           "models": [{"file": str(self.directory / "missing.scs"), "section": "tt"}]}]}))
        self.run_cli("install", "--models", str(config), expected=1)
        self.assertFalse(self.target.exists())
        self.assertEqual(self.entry.read_bytes(), self.original)

    def test_models_and_annotations_generated_without_copying_models(self):
        model = self.directory / "model.scs"
        model.write_text("LOCAL MODEL CONTENT MUST NOT BE COPIED")
        config = self.directory / "models.json"
        config.write_text(json.dumps({"profiles": [{"technology_read_path": str(self.directory),
                           "models": [{"file": str(model), "section": "tt"}]}]}))
        self.run_cli("install", "--models", str(config), "--op")
        profile = (self.target / "ade-models/profiles.il").read_text()
        self.assertNotIn("LOCAL MODEL CONTENT", profile)
        self.assertIn('"tt"', profile)
        self.assertIn('vucAmModelProfiles=list(', profile)
        baseline = (self.target / "op-annotation/dc-op-annotations.as").read_text()
        active = (self.target / "op-annotation/dc-op-active.as").read_text()
        self.assertEqual(baseline.count("display mode:parameter"), 100)
        self.assertEqual(active.count("display mode:opPoint"), 100)
        self.assertEqual(baseline.count("opPoint annotate?:true"), 30)
        self.assertEqual(baseline.count("opPoint balloon?:true"), 100)
        self.run_cli("rollback")
        self.assertEqual(model.read_text(), "LOCAL MODEL CONTENT MUST NOT BE COPIED")

    def test_workspace_uses_local_template_and_restores_default(self):
        template = self.directory / "Basic.workspace"
        template.write_bytes(b"WCfg-test-only-fixture")
        workspace = self.directory / ".cadence/dfII/workspaces/Schematics"
        workspace.mkdir(parents=True)
        default = workspace / "workspace.default"
        default.write_bytes(b"Previous\n")
        args = argparse.Namespace(root=str(self.target), cdsinit=[str(self.entry)],
                                  op=False, devices=None, models=None, workspace_template=str(template))
        with mock.patch.object(installer.Path, "home", return_value=self.directory):
            installer.install(args)
        self.assertEqual((workspace / "Design_Default.workspace").read_bytes(), template.read_bytes())
        self.assertEqual(default.read_bytes(), b"Design_Default\n")
        args.command = "rollback"
        installer.state_action(args)
        self.assertEqual(default.read_bytes(), b"Previous\n")
        self.assertFalse((workspace / "Design_Default.workspace").exists())

    def test_failed_install_restores_already_written_files(self):
        args = argparse.Namespace(root=str(self.target), cdsinit=[str(self.entry)],
                                  op=False, devices=None, models=None, workspace_template=None)
        original_write = installer.write_atomic

        def fail_entry(path, data, mode=0o600):
            if path == self.entry:
                raise OSError("simulated write failure")
            original_write(path, data, mode)

        with mock.patch.object(installer, "write_atomic", side_effect=fail_entry):
            with self.assertRaises(OSError):
                installer.install(args)
        self.assertEqual(self.entry.read_bytes(), self.original)
        self.assertFalse((self.target / "ui.il").exists())
        self.assertEqual(json.loads((self.target / ".install.json").read_text())["status"], "install_failed_reverted")

    def test_device_validation(self):
        for data in ([{"library": "bad name", "cell": "nmos"}],
                     [{"library": "test", "cell": "nmos", "inline_slots": 7}],
                     [{"library": "test", "cell": "nmos"}] * 2):
            with self.assertRaises(ValueError):
                installer.annotations(data)

    @unittest.skipIf(os.name == "nt", "Windows symlink privileges vary")
    def test_symlink_entry_refused(self):
        actual = self.directory / "actual"
        self.entry.rename(actual)
        self.entry.symlink_to(actual)
        self.run_cli("install", expected=1)
        self.assertEqual(actual.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
