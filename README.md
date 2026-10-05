# Xmake Addon 分发索引

本仓库管理 xdtc、xspm 和 cautest 的分发配方。工具源码、命令入口和安装准备逻辑留在各自 Git 仓库；索引只记录来源、分发版本和固定源码提交。源码包 cmlib、gd32f4xx 继续由 xspm 管理，不属于本索引。

| Addon | 安装后命令 | 默认配置 |
| --- | --- | --- |
| xdtc | `xmake xdtc` | `xdtc.lua` |
| xspm | `xmake xspm` | `xspm.json` |
| cautest | `xmake ctest` | `ctest.lua` |

三个命令均支持 `--config=<路径>`。默认和相对配置路径以消费工程根目录为基准，其他目录运行时使用 `-P <工程目录>`。安装目录不参与应用配置的相对路径解析。cautest 的配置仍使用 `ctest.*` API。

## 安装与开发

需要支持 Addon 的 Xmake；当前验证环境为 Linux x86_64、Xmake `3.1.1+HEAD.3ba37a0`。不能仅凭 `3.1.1` 版本号判断其他构建是否支持 Addon，应检查 `xmake addon --help`。cautest 安装还需要已有 Node >=20.6 和 npm，以及 npm lock 对应依赖的缓存或网络；配方不会安装系统 Node、npm 或全局 TypeScript。

消费工程直接声明插件，配置与构建时由 Xmake 安装，无需项目初始化任务：

```lua
add_repositories("kunyi git@github.com:wmem/xmake-addons.git")
add_addons("xdtc 0.1.x", "xspm 0.1.x", "cautest 0.1.x")
```

提交工程生成的 `xmake-addons.lock` 固定分发版本。

首次远程分发需要先推送工具实现提交及索引。发布前可以注册本地索引，并用 `XMAKE_ADDON_SOURCE_ROOT` 指定包含三个工具 Git 仓库的目录：

```sh
xmake repo --add --global kunyi /path/to/xmake-addons-repo
XMAKE_ADDON_SOURCE_ROOT=/path/to/code/xmake \
  xmake addon --install kunyi@xdtc kunyi@xspm kunyi@cautest
```

本地来源同样按配方固定提交检出，未提交修改不会参与安装；可以直接从工作副本运行准备脚本来验证未提交修改。远程索引发布后，省略 `XMAKE_ADDON_SOURCE_ROOT`，并将本地索引路径替换为 `https://github.com/wmem/xmake-addons.git`。安装通过 Xmake 索引完成；cautest 的配方执行 `npm ci --ignore-scripts`、`npm run build`，只安装生成的 JS 和必要资源，日常测试不重新编译 TS。开发阶段直接从工具原始目录或 Git URL 安装不会执行配方，应先运行各工具的 `scripts/prepare-addon.lua` 准备完整目录。

Addon 分发版本单独维护，首版为 `0.1.0`，不改变各工具现有内部版本或 Cautest 协议版本。每个配方的 `add_versions()` 固定完整源码提交，不跟随浮动分支。发布新版时先完成工具验证与提交，再更新配方版本及提交。xdtc `0.1.1` 另提供 `@addon/xdtc/codegen` 规则及 `@addon.xdtc.generator` 模块，
复用核心生成 API。规则仅在内容变化时写入输出，具体接入见工具 README。

## 验证

```sh
ADDON_TEST_EVIDENCE=/tmp/addon-test-evidence \
  uv run --no-project python tests/test_addons.py
```

测试把当前三个工具的源码快照保存为本地 Git 提交，通过本地来源选项选择测试源码，仅替换配方中的提交号，实际执行索引安装流程。所有插件安装、仓库登记和包缓存使用临时 `XMAKE_GLOBALDIR`；不会改动用户的全局插件目录。npm 使用离线模式，缓存缺失会报错，不跳过或自动安装系统工具。

覆盖默认与指定配置、空格和中文路径、外部目录的 `-P`、真实文件生成、命名空间生成规则与模块、输出增量和缺失恢复、Git 源码包同步、Native C 测试成功和失败退出码、错误配置、原有 RC 保留、TS 准备失败后重试、拒绝覆盖及卸载。测试不是远程发布验证，也不访问 MCU 板卡。

2026-10-05 在上述本机环境执行验证：9 项插件集成测试通过；原有 xdtc 的 6 个套件、35 项检查，xspm 的完整测试及 Cautest 的 15 项相关测试通过。此外，当前配方已用真实工具仓库的固定提交完成隔离安装，并运行三个命令及 Native 测试。版本、范围和结果见 [验证记录](tests/validation.json)。远程发布和用户全局安装未执行。

2026-10-05 补充 xdtc `0.1.1` 的规则与模块后，10 项插件集成测试通过，无失败或跳过。
版本与范围见 [代码生成接入验证](tests/validation-codegen.json)。
