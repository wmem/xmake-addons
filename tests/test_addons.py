"""使用真实 Xmake 和本地 Git 源码提交验证索引安装，不访问板卡或全局插件目录。"""
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import tempfile
import unittest

INDEX = Path(__file__).resolve().parents[1]
TOOLS = INDEX.parent
COMMANDS = {"xdtc": "xdtc", "xspm": "xspm", "cautest": "ctest"}


class AddonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="xmake-addons-中文 ")
        cls.base = Path(cls.tmp.name)
        cls.addClassCleanup(cls.finish)
        cls.env = dict(os.environ, XMAKE_GLOBALDIR=str(cls.base / "global"),
                       XMAKE_COLORTERM="n", npm_config_offline="true",
                       npm_config_audit="false", npm_config_fund="false")
        # 外部会话的 RC 和工程选择不能污染隔离测试。
        for key in ("XMAKE_RCFILES", "XMAKE_PROJECT_DIR", "CAUTEST_XMAKE_CONFIG",
                    "CAUTEST_ADDON_ENTRY", "XMAKE_PKG_INSTALLDIR"):
            cls.env.pop(key, None)
        cls.logs = cls.base / "logs"
        cls.logs.mkdir()
        repo = cls.base / "repo"
        for tool in COMMANDS:
            root = TOOLS / tool
            files = subprocess.check_output(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
            ).decode().split("\0")
            source = cls.base / "sources" / tool
            source.mkdir(parents=True)
            for name in sorted(set(files)):
                if name and (root / name).is_file() and not any(
                    part in {".git", ".xmake", "build", "dist", "node_modules"}
                    for part in Path(name).parts
                ):
                    target = source / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(root / name, target)
            cls.exec(["git", "init", "-q", "-b", "main"], cwd=source)
            cls.exec(["git", "add", "."], cwd=source)
            cls.exec(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                      "commit", "-qm", "plugin snapshot"], cwd=source)
            commit = cls.exec(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
            recipe = INDEX / "addons" / tool[0] / tool / "xmake.lua"
            text = recipe.read_text()
            text = re.sub(r'add_versions\("0.1.0", "[^"\n]+"\)',
                          f'add_versions("0.1.0", "{commit}")', text)
            dest = repo / "addons" / tool[0] / tool / "xmake.lua"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
        cls.env["XMAKE_ADDON_SOURCE_ROOT"] = str(cls.base / "sources")
        # Xmake 的默认公共索引也必须禁用网络，避免安装时顺带拉取它。
        cls.exec(["xmake", "g", "--network=private"])
        cls.exec(["xmake", "repo", "--add", "--global", "fixture", str(repo)])
        # 跑完整配方，包括 Cautest 的 npm/TS 构建。缺少缓存时报错，不偷偷跳过。
        cls.exec(["xmake", "addon", "--install", "-y",
                  "fixture@xdtc", "fixture@xspm", "fixture@cautest"], timeout=120)
        for tool, command in COMMANDS.items():
            runtime = cls.base / "global/.xmake/addons" / tool / "0.1.0/plugins" / command / "runtime"
            assert runtime.is_dir(), runtime
            assert not (runtime / "node_modules").exists()
        cls.project = cls.base / "consumer with spaces"
        cls.project.mkdir()
        (cls.project / "xmake.lua").write_text('target("product")\n    set_kind("phony")\n')
        cls.exec(["git", "init", "-q"], cwd=cls.base / "repo")
        cls.remote = cls.base / "library"
        cls.remote.mkdir()
        cls.exec(["git", "init", "-q", "-b", "main"], cwd=cls.remote)
        (cls.remote / "value.txt").write_text("library\n")
        cls.exec(["git", "add", "."], cwd=cls.remote)
        cls.exec(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                  "commit", "-qm", "fixture"], cwd=cls.remote)

    @classmethod
    def finish(cls):
        evidence = os.environ.get("ADDON_TEST_EVIDENCE")
        if evidence:
            output = Path(evidence)
            output.mkdir(parents=True, exist_ok=True)
            if hasattr(cls, "logs"):
                shutil.copytree(cls.logs, output / "logs", dirs_exist_ok=True)
        cls.tmp.cleanup()

    @classmethod
    def exec(cls, args, cwd=None, expected=0, timeout=60):
        process = subprocess.Popen(args, cwd=cwd or cls.base, env=cls.env,
                                   text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            raise AssertionError("命令超时：" + repr(args) + "\n" + stdout + stderr)
        result = subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
        number = len(list(cls.logs.iterdir()))
        (cls.logs / f"{number:03d}-{Path(args[0]).name}.log").write_text(
            repr(args) + "\n" + result.stdout + result.stderr)
        if expected is None:
            assert result.returncode != 0, result.stdout + result.stderr
        else:
            assert result.returncode == expected, result.stdout + result.stderr
        return result

    def run_tool(self, tool, *args, **kw):
        return self.exec(["xmake", tool, *args], cwd=self.project, **kw)

    def test_01_help_without_project_include(self):
        for command in COMMANDS.values():
            with self.subTest(command=command):
                text = self.run_tool(command, "--help").stdout
                self.assertIn("--config", text)
                self.assertIn(f"xmake {command}", text)
        self.assertIn("xspm.json", self.run_tool("xspm", "--help").stdout)

    def test_02_xdtc_default_selected_and_missing(self):
        (self.project / "data.lua").write_text('return {sample={enable=true,match="value.tpl",value=42}}\n')
        (self.project / "value.tpl").write_text('int value = {{ value }};\n')
        config = 'return {data="data.lua",tpl={{files={"value.tpl"},out="%s"}}}\n'
        (self.project / "xdtc.lua").write_text(config % "default.c")
        self.run_tool("xdtc")
        self.assertEqual((self.project / "default.c").read_text(), "int value = 42;")
        selected = self.project / "selected 中文.lua"
        selected.write_text(config % "selected.c")
        self.exec(["xmake", "xdtc", "-P", str(self.project), "--config=selected 中文.lua"])
        self.assertTrue((self.project / "selected.c").is_file())
        self.run_tool("xdtc", f"--config={selected}")
        self.run_tool("xdtc", "--config=missing.lua", expected=None)

    def test_03_xspm_default_and_selected_root(self):
        manifest = {"version": 1, "dependencies": {"library": str(self.remote) + "#main"}}
        (self.project / "xspm.json").write_text(json.dumps(manifest))
        self.run_tool("xspm", "--lock")
        self.run_tool("xspm", "--status")
        self.assertTrue((self.project / "deps/library/value.txt").is_file())
        sub = self.project / "config with spaces"
        sub.mkdir()
        selected = sub / "packages.json"
        selected.write_text(json.dumps(manifest))
        self.exec(["xmake", "xspm", "-P", str(self.project), "--config=config with spaces/packages.json", "--lock"])
        self.run_tool("xspm", f"--config={selected}", "--status")
        self.assertTrue((sub / "deps/library/value.txt").is_file())
        self.assertTrue((sub / "xspm-lock.json").is_file())
        self.run_tool("xspm", "--config=missing.json", "--list", expected=None)

    def write_ctest(self, file, case="answer", value=42):
        (file.parent / "test.c").write_text(f'''#include <cautest/cautest.h>
CAUTEST_CASE({case}) {{ CAUTEST_EXPECT_EQ_INT({value}, 42); }}
CAUTEST_SUITE(addon_suite, CAUTEST_CASE_ENTRY({case}));
''')
        file.write_text('''target("test.addon")
    set_kind("binary")
    set_default(false)
    add_rules("cautest.native")
    add_files("test.c")
    add_values("cautest.registry.suites", "addon_suite")
target_end()
ctest.native {id="unit.addon",target="test.addon"}
''')

    def test_04_ctest_default_native(self):
        self.write_ctest(self.project / "ctest.lua")
        jobs = json.loads(self.run_tool("ctest", "--list", "--json").stdout)
        self.assertEqual([job["id"] for job in jobs], ["unit.addon"])
        self.run_tool("ctest", "--plan", "--json")
        summary = json.loads(self.run_tool("ctest", "--json", "--reporter=json").stdout)
        report = json.loads(Path(summary["resultPath"]).read_text())
        self.assertEqual(report["status"], "SUCCESS")
        self.assertEqual(report["jobs"][0]["groups"][0]["cases"][0]["status"], "PASS")

    def test_05_ctest_selected_and_failure_exit(self):
        sub = self.project / "tests with spaces"
        sub.mkdir()
        selected = sub / "selected.lua"
        self.write_ctest(selected, case="expected_failure", value=0)
        jobs = json.loads(self.exec(["xmake", "ctest", "-P", str(self.project),
                                   "--config=tests with spaces/selected.lua", "--list", "--json"]).stdout)
        self.assertEqual(len(jobs), 1)
        summary = json.loads(self.exec(["xmake", "ctest", "-P", str(self.project), f"--config={selected}", "--json"], expected=1).stdout)
        self.assertEqual(summary["status"], "FAIL")
        self.run_tool("ctest", "--config=missing.lua", "--list", expected=3)
        selected.write_text("this is invalid Lua !!!\n")
        broken = self.run_tool("ctest", f"--config={selected}", "--list", expected=3)
        self.assertNotIn("invalid task", broken.stdout + broken.stderr)

    def test_06_ctest_invalid_default_does_not_break_other_commands(self):
        (self.project / "ctest.lua").write_text("this is invalid Lua !!!\n")
        self.run_tool("ctest", "--help")
        self.run_tool("xdtc", "--help")
        targets = self.run_tool("show", "-l", "targets").stdout
        self.assertIn("product", targets)
        self.assertNotIn("test.addon", targets)
        self.run_tool("ctest", "--list", expected=3)

    def test_07_existing_rcfile_is_preserved(self):
        self.write_ctest(self.project / "ctest.lua")
        marker = self.base / "existing rc.lua"
        marker.write_text('rc_available = true\n')
        config = self.project / "ctest.lua"
        config.write_text('if not rc_available then ctest._fail("原有 RC 必须保留") end\n' + config.read_text())
        previous = self.env.get("XMAKE_RCFILES")
        self.env["XMAKE_RCFILES"] = str(marker)
        try:
            self.run_tool("ctest", "--list", "--json")
        finally:
            if previous is None:
                self.env.pop("XMAKE_RCFILES")
            else:
                self.env["XMAKE_RCFILES"] = previous

    def test_075_cautest_build_failure_and_retry(self):
        source = self.base / "broken-source"
        shutil.copytree(TOOLS / "cautest", source, ignore=shutil.ignore_patterns(
            ".git", "node_modules", "dist", ".cautest", ".xmake", "release"))
        lock = source / "package-lock.json"
        original = lock.read_text()
        lock.write_text("{invalid lock")
        output = self.base / "retry-stage"
        result = self.exec(["xmake", "lua", str(source / "scripts/prepare-addon.lua"), str(output)], expected=None)
        self.assertIn("npm", result.stdout + result.stderr)
        self.assertFalse(output.exists())
        lock.write_text(original)
        self.exec(["xmake", "lua", str(source / "scripts/prepare-addon.lua"), str(output)])
        self.assertTrue((output / "addon/plugins/ctest/runtime/dist/adapters/xmake/entry.js").is_file())
        # 准备脚本不会覆盖已有目录，也不会把 node_modules 带进运行包。
        self.assertFalse((output / "addon/plugins/ctest/runtime/node_modules").exists())
        self.exec(["xmake", "lua", str(source / "scripts/prepare-addon.lua"), str(output)], expected=None)

    def test_08_uninstall_and_commands_disappear(self):
        for tool in COMMANDS:
            self.exec(["xmake", "addon", "--remove", tool])
        for command in COMMANDS.values():
            self.run_tool(command, "--help", expected=None)


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    result = program.result
    evidence = os.environ.get("ADDON_TEST_EVIDENCE")
    if evidence:
        output = Path(evidence)
        output.mkdir(parents=True, exist_ok=True)
        (output / "result.json").write_text(json.dumps({
            "status": "PASS" if result.wasSuccessful() else "FAIL",
            "tests": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors), "skipped": len(result.skipped),
        }, indent=2) + "\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)
