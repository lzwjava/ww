import unittest
from unittest.mock import patch, MagicMock

from ww.machine.machine_info import run, get_machine_info, print_info, MACHINES


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

        mock_run.side_effect = sp.TimeoutExpired("cmd", 10)
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


class TestGetMachineInfo(unittest.TestCase):
    @patch("ww.machine.machine_info.run")
    def test_local_linux(self, mock_run):
        mock_run.side_effect = lambda cmd, *a, **kw: {
            "hostname": "myserver",
            "nproc": "8",
            "lscpu | grep '^Model name' | sed 's/Model name:\\s*//'": "AMD Ryzen 7",
            "cat /proc/loadavg | awk '{print $1, $2, $3}'": "0.50 0.40 0.30",
            'free -h | awk \'/^Mem:/{print $3"/"$2" used"}\'': "4.0Gi/16Gi used",
            'df -h / | awk \'NR==2{print $3"/"$2" used ("$5")"}\'': "50G/100G used (50%)",
            "uptime -p": "up 3 days",
        }.get(cmd)
        info = get_machine_info()
        self.assertEqual(info["hostname"], "myserver")
        self.assertEqual(info["cpu_cores"], "8")
        self.assertEqual(info["cpu_model"], "AMD Ryzen 7")
        self.assertEqual(info["load"], "0.50 0.40 0.30")
        self.assertEqual(info["memory"], "4.0Gi/16Gi used")
        self.assertEqual(info["disk"], "50G/100G used (50%)")
        self.assertEqual(info["uptime"], "up 3 days")
        self.assertIsNone(info["gpu"])

    @patch("ww.machine.machine_info.run")
    def test_local_macos_fallback(self, mock_run):
        """When Linux commands return None, macOS fallbacks are used."""
        call_count = {"n": 0}
        macos_responses = {
            "hostname": "lzw-mac",
            "sysctl -n hw.ncpu": "8",
            "sysctl -n machdep.cpu.brand_string": "Apple M2",
            "sysctl -n vm.loadavg | awk '{print $2, $3, $4}'": "2.50 2.40 2.30",
            "vm_stat | head -1 | grep -o '[0-9]*' | tail -1": "16384",
            "sysctl -n hw.memsize": str(16 * 1024**3),
            "uptime | sed 's/.*up /up /' | sed 's/,.*//'": "up 2 days",
        }

        def fake_run(cmd, *a, **kw):
            # Linux commands return None; macOS commands return values
            if cmd in (
                "nproc",
                "lscpu | grep '^Model name' | sed 's/Model name:\\s*//'",
                "cat /proc/loadavg | awk '{print $1, $2, $3}'",
                'free -h | awk \'/^Mem:/{print $3"/"$2" used"}\'',
                "uptime -p",
            ):
                return None
            return macos_responses.get(cmd)

        mock_run.side_effect = fake_run
        # Patch the vm_stat awk command separately since it's built with f-string
        original_run = mock_run

        def run_with_vm_stat(cmd, *a, **kw):
            if "vm_stat | awk" in cmd:
                return "3.2"
            return fake_run(cmd, *a, **kw)

        mock_run.side_effect = run_with_vm_stat
        info = get_machine_info()
        self.assertEqual(info["hostname"], "lzw-mac")
        self.assertEqual(info["cpu_cores"], "8")
        self.assertEqual(info["cpu_model"], "Apple M2")
        self.assertEqual(info["load"], "2.50 2.40 2.30")
        self.assertIn("/16G used", info["memory"])

    @patch("ww.machine.machine_info.run")
    def test_gpu_detected(self, mock_run):
        def fake_run(cmd, *a, **kw):
            if "nvidia-smi" in cmd:
                return "RTX 4070, 168, 12282"
            return "stub"

        mock_run.side_effect = fake_run
        info = get_machine_info()
        self.assertIsNotNone(info["gpu"])
        self.assertIn("RTX 4070", info["gpu"])
        self.assertIn("168MB", info["gpu"])

    @patch("ww.machine.machine_info.run")
    def test_gpu_not_detected(self, mock_run):
        mock_run.return_value = None
        info = get_machine_info()
        self.assertIsNone(info["gpu"])

    @patch("ww.machine.machine_info.run")
    def test_ssh_args_passed_through(self, mock_run):
        mock_run.return_value = "val"
        get_machine_info(remote="root@1.2.3.4", ssh_args="-i /key.pem")
        for call in mock_run.call_args_list:
            args = call[0]
            if len(args) >= 3:
                self.assertEqual(args[2], "-i /key.pem")


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


class TestPrintInfo(unittest.TestCase):
    def test_prints_all_fields(
        self,
    ):
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
        # Should not raise
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
        # Should not raise
        print_info(info, "Test")


if __name__ == "__main__":
    unittest.main()
