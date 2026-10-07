# Xmake Addon 分发索引

本仓库管理 xdtc、xspm 和 cautest 的分发配方。工具源码、命令入口和安装准备逻辑留在各自 Git 仓库；索引只记录来源、分发版本和固定源码提交。源码包 cmlib、gd32f4xx 继续由 xspm 管理，不属于本索引。

| Addon | 安装后命令 | 默认配置 |
| --- | --- | --- |
| xdtc | `xmake xdtc` | `xdtc.lua` |
| xspm | `xmake xspm` | `xspm.json` |
| cautest | `xmake ctest` | `ctest.lua` |

三个命令均支持 `--config=<路径>`。xdtc 默认从启动目录查找配置，显式 `-P` 时使用所选工程；xspm、ctest 按消费工程根目录定位。安装目录不参与应用路径解析。cautest 的配置仍使用 `ctest.*` API。

## 安装与开发

需要支持 Addon 的 Xmake；当前验证环境为 Linux x86_64、Xmake `3.1.1+HEAD.3ba37a0`。不能仅凭 `3.1.1` 版本号判断其他构建是否支持 Addon，应检查 `xmake addon --help`。cautest 安装还需要已有 Node >=20.6 和 npm，以及 npm lock 对应依赖的缓存或网络；配方不会安装系统 Node、npm 或全局 TypeScript。

消费工程直接声明插件，配置与构建时由 Xmake 安装，无需项目初始化任务：

```lua
add_repositories("kunyi git@github.com:wmem/xmake-addons.git")
add_addons("xdtc 0.3.x", "xspm 0.1.x", "cautest 0.1.x")
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

Cautest `0.1.1` 修复符号链接工程路径与实际编译目录混用的问题。11 项插件回归通过，
包含先通过符号链接保存配置，再从实际目录执行 Native 测试且保持 debug 模式的场景。
版本和范围见 [ctest 路径修复验证](tests/validation-ctest-path.json)。

Cautest `0.1.2` 配方固定源码 `9678893`（工具内部版本 0.4.0）。
它移除配置文件原文摘要，按实际工程、模式、平台、架构和构建目录校验上下文，
解决配置值未变化、仅配置文本重写时误报 `Xmake configuration changed during this run` 的问题。
12 项插件回归通过，包含该场景；真实固定提交的配方安装及 Native Case 在隔离目录通过。
版本和范围见 [ctest 增量接入验证](tests/validation-ctest-incremental.json)。

Cautest `0.1.3` 配方固定源码 `6f2fdaa`（工具内部版本 0.5.0），增加 Run Collector，
支持在所有选中 Job 结束后统一收集产物；用例失败时仍执行，收集失败进入报告并返回错误码。
13 项插件回归通过，包含真实配方安装后的 FAIL 运行收集，以及 list / plan 不执行收集。
版本和范围见 [ctest 收集器接入验证](tests/validation-ctest-collectors.json)。

Cautest `0.1.4` 配方固定源码 `c2e5782`（工具内部版本 0.6.1，C API 2.2），提供可移植 MCU
运行时和 `includes("@addon/cautest/mcu")` 普通固件构建入口。19 项隔离插件回归通过，
包含只使用公开规则、不调用 ctest 即可编译及执行公共 MCU 运行时；此前 Native 用法继续通过。
真实 GD32/RT-Thread 测试由消费工程和 MSP 提供，详见
[MCU 接入验证](tests/validation-ctest-mcu.json)及工具仓库的实板记录。

工具源码和新索引推送后，消费工程执行 `xmake addon --upgrade`，由 Xmake 更新已安装插件及
`xmake-addons.lock`。有独立 Addon lock 的消费工程需要分别升级；
只修改工具源码不会改变已经安装的命令，`cautest 0.1.x` 声明本身无需改变。

xspm `0.1.1` 配方固定源码 `f4a6133`（工具版本 v0.3.0），支持顶层 `xspm.json`
的 `package` 指定所有依赖的本地开发分支；同步保护额外本地提交，源码 ref 与 lock 继续固定版本。
2026-10-06 的 13 项插件回归通过，包含实际安装后的工程分支、重复同步和指定配置。
工具完整测试同时通过，其中新增 16 项分支回归。版本与范围见
[工程分支验证](tests/validation-xspm-package.json)。

xdtc `0.1.2` 固定源码 `af7a5b1`（工具 v0.6.0），使用 `gen/data/run` 和工程注册的动作。
选项位于子命令之前；配置内部路径默认相对配置文件，绝对路径直接使用。
2026-10-06 的 14 项插件回归通过，包括数据文本重新加载、脚本及动作执行、配置转发、
当前目录与 -P、空格／中文路径和错误退出；工具 44 项回归通过。
详见 [动作与路径验证](tests/validation-xdtc-actions.json)。

xdtc `0.2.0` 固定源码 `00f1f8c`（工具 v0.7.0）。action 改为 `{script, select}`，
select 支持 `"."`、点分对象路径和 Lua 函数；旧字符串声明需要迁移。
gen/data/run 的数据语义保持不变，公开 select_action 供应用读取器复用筛选。
源码 51 项与隔离真实配方安装 15 项回归通过，见
[输入筛选验证](tests/validation-xdtc-select.json)。

xdtc `0.2.1` 固定源码 `afaf17d`（工具 v0.8.0），新增 `includes("@addon/xdtc/config")` 与 `xdtc_config(file):select(selector)`。select 返回读取函数，由使用方在脚本环境中显式调用后取得 table；支持对象路径和函数组装，不改变现有 action 或生成入口。源码 58 项、隔离真实配方安装 16 项回归通过，见 [配置引用验证](tests/validation-xdtc-config.json)。


xdtc `0.2.2` 固定源码 `c365c23`（工具 v0.8.1），新增 `xdtc_config(file):select_action(name)`。返回读取函数，复用任务配置中 action 的选择器并返回数据目录，不执行 action 脚本或代码生成；项目不再需要包装读取模块。源码 62 项与隔离真实配方安装 17 项回归通过，见 [action 配置引用验证](tests/validation-xdtc-action-config.json)。


xdtc `0.3.0` 固定源码 `1953d42`（工具 v0.9.0），run 和 action 入口统一改为 `main(data, api, ...)`。脚本能力作为第二个参数传入，命令位置参数从第三个参数开始；旧脚本接收位置参数时需要调整签名。api.template.render/render_file 复用既有模板引擎，返回字符串，是否渲染与写文件由脚本决定；文件模板相对当前脚本目录。源码 69 项与隔离真实配方安装 18 项回归通过，见 [脚本 API 验证](tests/validation-xdtc-script-api.json)。
