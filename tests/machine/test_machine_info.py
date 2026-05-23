import unittest
from unittest.mock import patch, MagicMock

from ww.machine.machine_info import (
    run,
    run_script,
    get_machine_info,
    print_info,
    MACHINES,
)


def batch_output(
    *,
    hostname="myserver",
    cpu_model="AMD Ryzen 7",
    cpu_cores="8",
    load="0.50 0.40 0.30",
    memory="4.0Gi/16Gi used",
    disk="50G/100G used (50%)",
    uptime="up 3 days",
    gpu="",
    services=None,
):
    """Build the multi-line batch output string that get_machine_info parses."""
    parts = [
        "---HOSTNAME---",
        hostname,
        "---CPU_MODEL---",
        cpu_model,
        "---CPU_CORES---",
        cpu_cores,
        "---LOAD---",
        load,
        "---MEMORY---",
        memory,
        "---DISK---",
        disk,
        "---UPTIME---",
        uptime,
        "---GPU---",
        gpu,
        "---SERVICES---",
    ]
    if services:
        parts.extend(services)
    parts.append("---END---")
    return "\n".join(parts)


class TestRun(unittest.TestCase):
    @patch("ww.machine.machine_info.subprocess.run")
    def test_local_returns_stdout(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="hello\n")
        result = run("echo hello")
        self.assertEqual(result, "hello")

    @patch("ww.machine.machine_info.subprocess.run")
    def test_local_returns_none_on_failure(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=1, stdout="")
        result = run("bad_cmd")
        self.assertIsNone(result)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_returns_none_on_timeout(self, mock_subprocess):
        import subprocess as sp

        mock_subprocess.side_effect = sp.TimeoutExpired("cmd", 10)
        result = run("slow_cmd")
        self.assertIsNone(result)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_uses_ssh(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="ok\n")
        result = run("hostname", remote="user@host")
        self.assertEqual(result, "ok")
        called_cmd = mock_subprocess.call_args[0][0]
        self.assertIn("ssh", called_cmd)
        self.assertIn("user@host", called_cmd)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_with_ssh_args(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="ok\n")
        run("hostname", remote="root@1.2.3.4", ssh_args="-i /path/key.pem")
        called_cmd = mock_subprocess.call_args[0][0]
        self.assertIn("-i /path/key.pem", called_cmd)
        self.assertIn("root@1.2.3.4", called_cmd)

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_includes_connect_timeout(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="ok\n")
        run("hostname", remote="user@host")
        called_cmd = mock_subprocess.call_args[0][0]
        self.assertIn("ConnectTimeout=5", called_cmd)
        self.assertIn("ProxyCommand=none", called_cmd)


class TestRunScript(unittest.TestCase):
    @patch("ww.machine.machine_info.subprocess.run")
    def test_local_returns_stdout(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="line1\nline2\n")
        result = run_script("echo line1\necho line2")
        self.assertEqual(result, "line1\nline2")

    @patch("ww.machine.machine_info.subprocess.run")
    def test_remote_pipes_via_ssh(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="ok\n")
        run_script("echo ok", remote="user@host")
        called_cmd = mock_subprocess.call_args[0][0]
        self.assertIn("ssh", called_cmd)
        self.assertIn("bash", called_cmd)


class TestGetMachineInfo(unittest.TestCase):
    @patch("ww.machine.machine_info.run_script")
    def test_parses_linux_output(self, mock_script):
        mock_script.return_value = batch_output()
        info = get_machine_info()
        assert info is not None
        self.assertEqual(info["hostname"], "myserver")
        self.assertEqual(info["cpu_cores"], "8")
        self.assertEqual(info["cpu_model"], "AMD Ryzen 7")
        self.assertEqual(info["load"], "0.50 0.40 0.30")
        self.assertEqual(info["memory"], "4.0Gi/16Gi used")
        self.assertEqual(info["disk"], "50G/100G used (50%)")
        self.assertEqual(info["uptime"], "up 3 days")
        self.assertIsNone(info["gpu"])

    @patch("ww.machine.machine_info.run")
    @patch("ww.machine.machine_info.run_script")
    def test_macos_memory_fallback(self, mock_script, mock_run):
        """When batch returns macos_mem, individual run() calls fill in memory."""
        mock_script.return_value = batch_output(memory="macos_mem")
        mock_run.side_effect = ["16384", str(16 * 1024**3), "3.2"]
        info = get_machine_info()
        assert info is not None
        self.assertIn("/16G used", info["memory"])

    @patch("ww.machine.machine_info.run_script")
    def test_gpu_detected(self, mock_script):
        mock_script.return_value = batch_output(gpu="RTX 4070, 168, 12282")
        info = get_machine_info()
        assert info is not None
        assert info["gpu"] is not None
        self.assertIn("RTX 4070", info["gpu"])
        self.assertIn("168MB", info["gpu"])

    @patch("ww.machine.machine_info.run_script")
    def test_gpu_not_detected(self, mock_script):
        mock_script.return_value = batch_output(gpu="")
        info = get_machine_info()
        assert info is not None
        self.assertIsNone(info["gpu"])

    @patch("ww.machine.machine_info.run_script")
    def test_services_detected(self, mock_script):
        mock_script.return_value = batch_output(services=["hysteria=UP", "nginx=DOWN"])
        info = get_machine_info(services=["hysteria", "nginx"])
        assert info is not None
        self.assertEqual(info["services"], [("hysteria", True), ("nginx", False)])

    @patch("ww.machine.machine_info.run_script")
    def test_returns_none_on_failure(self, mock_script):
        mock_script.return_value = None
        info = get_machine_info()
        self.assertIsNone(info)

    @patch("ww.machine.machine_info.run_script")
    def test_ssh_args_passed_through(self, mock_script):
        mock_script.return_value = batch_output()
        get_machine_info(remote="root@1.2.3.4", ssh_args="-i /key.pem")
        args = mock_script.call_args
        self.assertEqual(args[0][1], "root@1.2.3.4")
        self.assertEqual(args[0][2], "-i /key.pem")


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
