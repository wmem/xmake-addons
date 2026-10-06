-- 分发版本对应工具源码提交；安装逻辑由工具仓库维护。
package("xspm")
set_kind("addon")
set_homepage("https://github.com/wmem/xspm")
set_description("xspm 的 Xmake 命令插件")
add_urls("https://github.com/wmem/xspm.git")
add_versions("0.1.0", "020a9231c3eb6f5b5adec2895f0375ecc44eaaba")
add_versions("0.1.1", "f4a6133c177e9767379933bb63784854ab9e5ec9")
on_load(function(package)
    -- 本地开发仍按配方的提交号检出，不消费未提交修改。
    local root = os.getenv("XMAKE_ADDON_SOURCE_ROOT")
    if root then
        local gitdir = path.join(path.absolute(root), "xspm", ".git")
        assert(os.isdir(gitdir), "本地工具 Git 仓库不存在：" .. gitdir)
        package:set("urls", "file://" .. path.unix(gitdir))
    end
end)
on_install(function(package)
    import("prepare-addon", { rootdir = path.join(os.curdir(), "scripts"), anonymous = true }).install(
        package
    )
end)
on_test(function(package)
    assert(os.isfile(package:installdir("plugins/xspm/main.lua")), "缺少插件命令入口")
end)
package_end()
