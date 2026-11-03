"""Protect user settings and port selection without starting Docker."""
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("setup", Path(__file__).resolve().parents[1] / "scripts/setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def test_port_update_preserves_other_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(f"# Keep comment\n{setup.PREFIX}_MEMORY_LIMIT=7g\n{setup.PREFIX}_PORT=41000\nOTHER=value\n")
            setup.set_port(path, 49000)
            self.assertEqual(path.read_text(), f"# Keep comment\n{setup.PREFIX}_MEMORY_LIMIT=7g\n{setup.PREFIX}_PORT=49000\nOTHER=value\n")

    def test_occupied_port_is_not_available(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            self.assertFalse(setup.available(listener.getsockname()[1]))

    def test_occupied_default_selects_free_port_and_reports_it(self):
        config = {"services": {setup.SERVICE: {"ports": [{"host_ip": "127.0.0.1", "published": str(setup.DEFAULT_PORT)}]}}}
        calls = []
        def run(*args, **kwargs):
            from types import SimpleNamespace
            calls.append((args, kwargs))
            return SimpleNamespace(stdout=json.dumps(config) if "config" in args else
                                   '{"OSType":"linux","NCPU":2}' if "info" in args else "")
        with tempfile.TemporaryDirectory() as directory, patch.object(setup, "ROOT", Path(directory)), \
                patch.object(setup, "run", side_effect=run), patch.object(setup.shutil, "which", return_value="docker"), \
                patch.object(setup.shutil, "disk_usage") as disk, \
                patch.object(setup, "available", side_effect=lambda port: port != setup.DEFAULT_PORT), \
                patch.dict(setup.os.environ, {}, clear=True), patch("sys.argv", ["setup.py"]):
            disk.return_value.free = 20 * 1024**3
            setup.main()
            self.assertIn(f"{setup.PREFIX}_PORT={setup.DEFAULT_PORT + 1}", (Path(directory) / ".env").read_text())
            startup = next(kwargs for args, kwargs in calls if "up" in args)
            self.assertEqual(startup["env"][setup.PREFIX + "_PORT"], str(setup.DEFAULT_PORT + 1))
            self.assertEqual(startup["env"][setup.PREFIX + "_CPUS"], "2")
            smoke = next(args for args, kwargs in calls if "tests/smoke.py" in args)
            self.assertEqual(smoke[-1], f"http://localhost:{setup.DEFAULT_PORT + 1}")

    def test_explicit_occupied_port_never_changes_settings(self):
        config = {"services": {setup.SERVICE: {"ports": [{"host_ip": "127.0.0.1", "published": str(setup.DEFAULT_PORT)}]}}}
        def run(*args, **kwargs):
            from types import SimpleNamespace
            return SimpleNamespace(stdout=json.dumps(config) if "config" in args else
                                   '{"OSType":"linux","NCPU":2}' if "info" in args else "")
        with tempfile.TemporaryDirectory() as directory, patch.object(setup, "ROOT", Path(directory)), \
                patch.object(setup, "run", side_effect=run), patch.object(setup.shutil, "which", return_value="docker"), \
                patch.object(setup.shutil, "disk_usage") as disk, \
                patch.object(setup, "available", return_value=False), \
                patch("sys.argv", ["setup.py", "--port", "49000"]):
            disk.return_value.free = 20 * 1024**3
            with self.assertRaisesRegex(RuntimeError, "occupied"):
                setup.main()
            self.assertFalse((Path(directory) / ".env").exists())


if __name__ == "__main__":
    unittest.main()
