-- 分发版本对应工具源码提交；安装逻辑由工具仓库维护。
package("xdtc")
set_kind("addon")
set_homepage("https://github.com/wmem/xdtc")
set_description("xdtc 的 Xmake 命令插件")
add_urls("https://github.com/wmem/xdtc.git")
add_versions("0.1.0", "b24b54f4b708ee61b85634df1215909a15d43d5e")
add_versions("0.1.1", "e8b6c1b605054246e173a2b67b511fdd301efb06")
add_versions("0.1.2", "af7a5b1c350879e35fe2c9155c638c8ee9d67af7")
add_versions("0.2.0", "00f1f8c2d1f1a5e9c17b26d8ccc0f08b5575ece6")
on_load(function(package)
	-- 本地开发仍按配方的提交号检出，不消费未提交修改。
	local root = os.getenv("XMAKE_ADDON_SOURCE_ROOT")
	if root then
		local gitdir = path.join(path.absolute(root), "xdtc", ".git")
		assert(os.isdir(gitdir), "本地工具 Git 仓库不存在：" .. gitdir)
		package:set("urls", "file://" .. path.unix(gitdir))
	end
end)
on_install(function(package)
	import("prepare-addon", { rootdir = path.join(os.curdir(), "scripts"), anonymous = true }).install(package)
end)
on_test(function(package)
	assert(os.isfile(package:installdir("plugins/xdtc/main.lua")), "缺少插件命令入口")
	if package:version_str() ~= "0.1.0" then
		assert(os.isfile(package:installdir("rules/codegen/xmake.lua")), "缺少代码生成规则")
		assert(os.isfile(package:installdir("modules/generator.lua")), "缺少生成 API")
	end
end)
package_end()
