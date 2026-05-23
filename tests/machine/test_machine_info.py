import unittest
from unittest.mock import patch, MagicMock

from ww.machine.machine_info import (
    run,
    run_script,
    get_machine_info,
    print_info,
    build_batch_script,
    MACHINES,
)


class TestRun(unittest.TestCase):
    @patch("ww.machine.machine_info.subprocess.run")
    def test_local_returns_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="hello\n")
        result = run("echo hello")
        self.assertEqual(result, "hello")

    @patch("ww.machine.machine_info.subprocess.run")
    def test_local_returns_none_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = run("bad_cmd")
        self.assertIsNone(result)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_returns_none_on_timeout(self, mock_run):
        import subprocess as sp

        mock_run.side_effect = sp.TimeoutExpired("cmd", 15)
        result = run("slow_cmd")
        self.assertIsNone(result)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_uses_ssh(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n")
        result = run("hostname", remote="user@host")
        self.assertEqual(result, "ok")
        called_cmd = mock_run.call_args[0][0]
        self.assertIn("ssh", called_cmd)
        self.assertIn("user@host", called_cmd)
        self.assertIn("hostname", called_cmd)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_with_ssh_args(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n")
        run("hostname", remote="root@1.2.3.4", ssh_args="-i /path/key.pem")
        called_cmd = mock_run.call_args[0][0]
        self.assertIn("-i /path/key.pem", called_cmd)
        self.assertIn("root@1.2.3.4", called_cmd)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_includes_connect_timeout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n")
        run("hostname", remote="user@host")
        called_cmd = mock_run.call_args[0][0]
        self.assertIn("ConnectTimeout=5", called_cmd)
        self.assertIn("ProxyCommand=none", called_cmd)


class TestRunScript(unittest.TestCase):
    @patch("ww.machine.machine_info.subprocess.run")
    def test_local_runs_bash(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="out\n")
        result = run_script("echo out")
        self.assertEqual(result, "out")
        called_cmd = mock_run.call_args[0][0]
        self.assertEqual(called_cmd, "bash")

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_pipes_to_ssh_bash(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="out\n")
        result = run_script("echo out", remote="user@host")
        self.assertEqual(result, "out")
        called_cmd = mock_run.call_args[0][0]
        self.assertIn("ssh", called_cmd)
        self.assertIn("bash", called_cmd)
        # Script is passed via stdin
        self.assertEqual(mock_run.call_args[1]["input"], "echo out")

    @patch("ww.machine.machine_info.subprocess.run")
    def test_returns_none_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = run_script("bad")
        self.assertIsNone(result)


class TestBuildBatchScript(unittest.TestCase):
    def test_base_script_has_sections(self):
        script = build_batch_script()
        for section in [
            "HOSTNAME",
            "CPU_MODEL",
            "CPU_CORES",
            "LOAD",
            "MEMORY",
            "DISK",
            "UPTIME",
            "GPU",
            "SERVICES",
            "END",
        ]:
            self.assertIn(f"---{section}---", script)

    def test_services_appended(self):
        script = build_batch_script(["hysteria", "nginx"])
        self.assertIn("pgrep -x hysteria", script)
        self.assertIn("pgrep -x nginx", script)
        self.assertIn("hysteria=UP", script)
        self.assertIn("nginx=UP", script)

    def test_no_services(self):
        script = build_batch_script([])
        self.assertNotIn("pgrep", script)


SAMPLE_OUTPUT = """---HOSTNAME---
DMIT-KiXdN3dnsQ
---CPU_MODEL---
AMD EPYC 9655 96-Core Processor
---CPU_CORES---
1
---LOAD---
0.92 1.16 1.24
---MEMORY---
1.0Gi/1.9Gi used
---DISK---
8.6G/20G used (46%)
---UPTIME---
up 6 weeks, 1 day, 8 hours, 57 minutes
---GPU---
---SERVICES---
hysteria=UP
---END---"""


SAMPLE_OUTPUT_MACOS = """---HOSTNAME---
lzw-mac.local
---CPU_MODEL---
Apple M2
---CPU_CORES---
8
---LOAD---
2.89 2.63 2.94
---MEMORY---
macos_mem
---DISK---
12Gi/460Gi used (20%)
---UPTIME---
up 2 days
---GPU---
---SERVICES---
---END---"""


class TestGetMachineInfo(unittest.TestCase):
    @patch("ww.machine.machine_info.run_script")
    def test_parses_linux_output(self, mock_script):
        mock_script.return_value = SAMPLE_OUTPUT
        info = get_machine_info(remote="root@host", services=["hysteria"])
        assert info is not None
        self.assertEqual(info["hostname"], "DMIT-KiXdN3dnsQ")
        self.assertEqual(info["cpu_model"], "AMD EPYC 9655 96-Core Processor")
        self.assertEqual(info["cpu_cores"], "1")
        self.assertEqual(info["load"], "0.92 1.16 1.24")
        self.assertEqual(info["memory"], "1.0Gi/1.9Gi used")
        self.assertEqual(info["disk"], "8.6G/20G used (46%)")
        self.assertIsNone(info["gpu"])
        self.assertEqual(info["services"], [("hysteria", True)])

    @patch("ww.machine.machine_info.run_script")
    @patch("ww.machine.machine_info.run")
    def test_parses_macos_output(self, mock_run, mock_script):
        mock_script.return_value = SAMPLE_OUTPUT_MACOS
        # macOS memory fallback
        mock_run.side_effect = lambda cmd, *a, **kw: {
            "vm_stat | head -1 | grep -o '[0-9]*' | tail -1": "16384",
            "sysctl -n hw.memsize": str(16 * 1024**3),
        }.get(cmd.split("&&")[0].strip() if "&&" in cmd else cmd, None)
        info = get_machine_info()
        assert info is not None
        self.assertEqual(info["hostname"], "lzw-mac.local")
        self.assertEqual(info["cpu_model"], "Apple M2")
        self.assertEqual(info["cpu_cores"], "8")

    @patch("ww.machine.machine_info.run_script")
    def test_returns_none_on_failure(self, mock_script):
        mock_script.return_value = None
        info = get_machine_info(remote="bad@host")
        self.assertIsNone(info)

    @patch("ww.machine.machine_info.run_script")
    def test_services_false_when_down(self, mock_script):
        output = SAMPLE_OUTPUT.replace("hysteria=UP", "hysteria=DOWN")
        mock_script.return_value = output
        info = get_machine_info(services=["hysteria"])
        assert info is not None
        self.assertEqual(info["services"], [("hysteria", False)])

    @patch("ww.machine.machine_info.run_script")
    def test_no_services(self, mock_script):
        mock_script.return_value = SAMPLE_OUTPUT
        info = get_machine_info()
        assert info is not None
        self.assertEqual(info["services"], [])


class TestMachines(unittest.TestCase):
    def test_local_no_remote(self):
        cfg = MACHINES["local"]
        self.assertIsNone(cfg["remote"])
        self.assertNotIn("ssh_args", cfg)

    def test_workstation_config(self):
        cfg = MACHINES["workstation"]
        self.assertEqual(cfg["remote"], "lzw@192.168.1.36")

    def test_dmit_config(self):
        cfg = MACHINES["dmit"]
        self.assertEqual(cfg["remote"], "root@69.63.219.52")
        self.assertIn("id_rsa.pem", cfg["ssh_args"])
        self.assertIn("hysteria", cfg["services"])


class TestPrintInfo(unittest.TestCase):
    def test_prints_all_fields(self):
        info = {
            "hostname": "testhost",
            "cpu_model": "Test CPU",
            "cpu_cores": "4",
            "load": "1.0 0.5 0.25",
            "memory": "8G/16G used",
            "disk": "50G/100G used (50%)",
            "uptime": "up 1 day",
            "gpu": None,
        }
        print_info(info, "Test")

    def test_prints_gpu_when_present(self):
        info = {
            "hostname": "testhost",
            "cpu_model": "Test CPU",
            "cpu_cores": "4",
            "load": "1.0 0.5 0.25",
            "memory": "8G/16G used",
            "disk": "50G/100G used (50%)",
            "uptime": "up 1 day",
            "gpu": "RTX 4070 (500MB/12282MB)",
        }
        print_info(info, "Test")

    def test_prints_services(self):
        info = {
            "hostname": "testhost",
            "cpu_model": "Test CPU",
            "cpu_cores": "4",
            "load": "1.0 0.5 0.25",
            "memory": "8G/16G used",
            "disk": "50G/100G used (50%)",
            "uptime": "up 1 day",
            "gpu": None,
        }
        services = [("hysteria", True), ("nginx", False)]
        print_info(info, "Test", services=services)


if __name__ == "__main__":
    unittest.main()
