"""隔离安装xdtc和两个设备Addon；fake后端与PTY验证不访问真实板卡。"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

INDEX = Path(__file__).resolve().parents[1]
TOOLS = INDEX.parent
VERSIONS = {"xdtc": "0.11.0", "x-pyocd": "0.2.0", "x-console": "0.1.0"}


class DeviceAddonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="device-addons-中文 ")
        cls.base = Path(cls.tmp.name)
        cls.addClassCleanup(cls.finish)
        cls.logs = cls.base / "logs"
        cls.logs.mkdir()
        cls.env = dict(os.environ, XMAKE_GLOBALDIR=str(cls.base / "global"), XMAKE_COLORTERM="n", XMAKE_STATS="false")
        for name in ("XMAKE_RCFILES", "XMAKE_PROJECT_DIR", "XMAKE_PKG_INSTALLDIR"):
            cls.env.pop(name, None)
        for name in VERSIONS:
            source = cls.base / "sources" / name
            recipe = (INDEX / "addons" / name[0] / name / "xmake.lua").read_text()
            if os.environ.get("DEVICE_ADDON_FIXED_SOURCES") == "1":
                # 固定提交验证保留原始配方，不能用工作副本快照代替待发布制品。
                cls.run_command(["git", "clone", "-q", str(TOOLS / name), str(source)])
            else:
                shutil.copytree(TOOLS / name, source, ignore=shutil.ignore_patterns(
                    ".git", ".xmake", "build", "__pycache__", ".agent"))
                cls.run_command(["git", "init", "-q", "-b", "main"], cwd=source)
                cls.run_command(["git", "add", "."], cwd=source)
                cls.run_command(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                                 "commit", "-qm", "插件测试快照"], cwd=source)
                commit = cls.run_command(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
                recipe = re.sub(r'add_versions\("[^"\n]+", "[^"\n]+"\)',
                                lambda match: re.sub(r', "[^"\n]+"\)', f', "{commit}")', match[0]), recipe)
            file = cls.base / "repo/addons" / name[0] / name / "xmake.lua"
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(recipe)
        cls.env["XMAKE_ADDON_SOURCE_ROOT"] = str(cls.base / "sources")
        cls.run_command(["xmake", "g", "--network=private"])
        cls.run_command(["xmake", "repo", "--add", "--global", "fixture", str(cls.base / "repo")])
        cls.run_command(["xmake", "addon", "--install", "-y", *[f"fixture@{name}" for name in VERSIONS]], timeout=60)
        cls.consumer = cls.base / "consumer 中文"
        cls.consumer.mkdir()
        (cls.consumer / "xmake.lua").write_text('target("fixture")\nset_kind("phony")\n')
        cls.runtime = cls.base / "global/.xmake/addons"

    @classmethod
    def finish(cls):
        evidence = os.environ.get("DEVICE_ADDON_TEST_EVIDENCE")
        if evidence:
            output = Path(evidence)
            output.mkdir(parents=True, exist_ok=True)
            shutil.copytree(cls.logs, output / "logs", dirs_exist_ok=True)
        cls.tmp.cleanup()

    @classmethod
    def run_command(cls, args, cwd=None, expected=0, timeout=30):
        result = subprocess.run(args, cwd=cwd or cls.base, env=cls.env, text=True,
                                capture_output=True, timeout=timeout)
        (cls.logs / f"{len(list(cls.logs.iterdir())):03d}.log").write_text(
            repr(args) + "\n" + result.stdout + result.stderr)
        if expected is None:
            assert result.returncode != 0, result.stdout + result.stderr
        else:
            assert result.returncode == expected, result.stdout + result.stderr
        return result

    def test_01_installed_payload_and_public_imports(self):
        for name, version in VERSIONS.items():
            self.assertTrue((self.runtime / name / version / "plugins" / name / "main.lua").is_file())
            self.run_command(["xmake", name, "--help"], cwd=self.consumer)
        script = '''local pyocd=import("@addon.x-pyocd.api",{anonymous=true})
local terminal=import("@addon.x-console.api",{anonymous=true})
local xdtc=import("@addon.xdtc.generator",{anonymous=true})
assert(type(pyocd.flash)=="function" and type(terminal.open)=="function")
assert(xdtc.version()=="0.11.0" and type(xdtc.execute_entry)=="function")'''
        self.run_command(["xmake", "lua", "-c", script], cwd=self.consumer)

    def test_02_entry_imports_addons_and_reads_without_execution(self):
        nested = self.consumer / "配置 空格"
        nested.mkdir(exist_ok=True)
        (nested / "data.lua").write_text('''return {
download={host="linux",project_root="/tmp",report_dir="/tmp",runtime={python="unused"}},
console={host="linux",mode="raw",runtime={python="unused"},serial={port="/dev/fixture",baud_rate=115200,
data_bits=8,parity="none",stop_bits=1,flow_control="none",board_control={}}}}''')
        (nested / "value.tpl").write_text("{{host}}")
        (nested / "xdtc.lua").write_text('''return {data="data.lua",actions={
flash={select="download",entry=function(config,api,marker)
local pyocd=import("@addon.x-pyocd.api",{anonymous=true})
assert(pyocd.plan(config,"probes").host=="linux")
io.writefile(path.join(os.scriptdir(),marker),api.template.render_file("value.tpl",config))
end},console={select="console",entry=function(config)
local terminal=import("@addon.x-console.api",{anonymous=true})
assert(terminal.plan(config).serial.port=="/dev/fixture")
end}}}''')
        self.run_command(["xmake", "xdtc", f"--config={nested / 'xdtc.lua'}", "flash", "marker.txt"], cwd=self.consumer)
        self.assertEqual((nested / "marker.txt").read_text(), "linux")
        self.run_command(["xmake", "xdtc", "-P", str(self.consumer), f"--config={nested / 'xdtc.lua'}", "console"])
        (nested / "marker.txt").unlink()
        self.run_command(["xmake", "lua", "-c", f'''local xdtc=import("@addon.xdtc.generator",{{anonymous=true}})
assert(xdtc.read_action_config({json.dumps(str(nested / 'xdtc.lua'), ensure_ascii=False)},"flash").host=="linux")'''], cwd=self.consumer)
        self.assertFalse((nested / "marker.txt").exists())

    def test_03_cli_dry_run_and_error_propagation(self):
        file = self.consumer / "console.json"
        file.write_text(json.dumps({"host": "linux", "mode": "raw", "runtime": {"python": "unused"},
            "serial": {"port": "/dev/fixture", "baud_rate": 9600, "data_bits": 8, "parity": "none",
                       "stop_bits": 1, "flow_control": "none", "board_control": {}}}))
        result = self.run_command(["xmake", "x-console", "--config=" + str(file), "--dry-run"], cwd=self.consumer)
        self.assertIn('"baud_rate":9600', result.stdout.replace(" ", ""))
        file.write_text('{"serial":{}}')
        result = self.run_command(["xmake", "x-console", "--config=" + str(file), "--dry-run"], cwd=self.consumer, expected=None)
        self.assertIn("host", result.stdout + result.stderr)
        (self.consumer / "data.lua").write_text("return {}")
        (self.consumer / "xdtc.lua").write_text('return {data="data.lua",actions={bad={select=".",entry=function() raise("entry failure") end}}}')
        result = self.run_command(["xmake", "xdtc", "bad"], cwd=self.consumer, expected=None)
        self.assertIn("entry failure", result.stdout + result.stderr)

    def test_04_installed_backend_resources(self):
        # 检查实际安装制品是否包含各后端所需资源。
        for name in ("x-pyocd", "x-console"):
            root = self.runtime / name / VERSIONS[name] / "modules/runtime"
            self.assertTrue(root.is_dir())
            expected = ("worker.py", "run.ps1") if name == "x-pyocd" else ("terminal.py", "terminal.mjs", "serial.ps1", "transport.mjs")
            for file in expected:
                self.assertTrue((root / file).is_file(), root / file)


if __name__ == "__main__":
    suite = unittest.main(verbosity=2, exit=False)
    evidence = os.environ.get("DEVICE_ADDON_TEST_EVIDENCE")
    if evidence:
        output = Path(evidence)
        output.mkdir(parents=True, exist_ok=True)
        (output / "result.json").write_text(json.dumps({"status": "PASS" if suite.result.wasSuccessful() else "FAIL",
            "tests": suite.result.testsRun, "failures": len(suite.result.failures), "errors": len(suite.result.errors),
            "sourceMode": "fixed" if os.environ.get("DEVICE_ADDON_FIXED_SOURCES") == "1" else "snapshot"}, indent=2) + "\n")
    raise SystemExit(0 if suite.result.wasSuccessful() else 1)
