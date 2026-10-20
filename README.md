# Xmake Addon 分发索引

本仓库管理 xdtc、xspm、cautest、x-pyocd、x-console 和 x-firmware 的分发配方。工具源码、命令入口和安装准备逻辑留在各自 Git 仓库；索引只记录来源、分发版本和固定源码提交。源码包 cmlib、gd32f4xx 继续由 xspm 管理，不属于本索引。

| Addon | 安装后命令 | 默认配置 |
| --- | --- | --- |
| xdtc | `xmake xdtc` | `xdtc.lua` |
| xspm | `xmake xspm` | `xspm.json` |
| cautest | `xmake ctest` | `ctest.lua` |
| x-pyocd | `xmake x-pyocd` | 无，显式传入 `--config=<JSON>` |
| x-console | `xmake x-console` | 无，显式传入 `--config=<JSON>` |
| x-firmware | `xmake x-firmware` | 无，显式传入 `--config=<JSON>` |

六个命令均支持 `--config=<路径>`。xdtc 默认从启动目录查找配置，显式 `-P` 时使用所选工程；xspm、ctest 按消费工程根目录定位。x-pyocd/x-console 不解析板描述，执行系统、速率、芯片、端口及运行命令等所需参数由 config 提供。x-firmware 的文件路径相对 JSON 所在目录，提供 app/upgrade/diff/inspect/product 操作。安装目录不参与应用路径解析。cautest 的配置仍使用 `ctest.*` API。

当前 xdtc 为 **0.11.0**、x-pyocd 为 **0.2.0**、x-console 为 **0.1.1**、x-firmware 为 **0.2.0**。xdtc 数据接口统一使用 `xdtc_` 前缀，不再提供裸名或 `updateRoot` 别名。Addon 与工具源码发布版本相同，历史配方和验证记录保留在下文。

## 安装与开发

x-firmware **0.1.0** 的文件 API、共享固件/产品头和纯 Lua LZ4/bsdiff 不依赖算法二进制。源码验证包括 C/Lua 格式互通、26 组独立 C 算法双向互通，以及真实隔离安装、API/规则/命令和增量处理；本索引配方的固定源码安装也已通过同一消费工程。详细接口和测试入口见 [x-firmware README](https://github.com/wmem/x-firmware)，固定源提交由 [配方](addons/x/x-firmware/xmake.lua)维护。

需要支持 Addon 的 Xmake；当前验证环境为 Linux x86_64、Xmake `3.1.1+HEAD.3ba37a0`。不能仅凭 `3.1.1` 版本号判断其他构建是否支持 Addon，应检查 `xmake addon --help`。cautest 安装还需要已有 Node >=20.6 和 npm，以及 npm lock 对应依赖的缓存或网络；配方不会安装系统 Node、npm 或全局 TypeScript。

消费工程可直接声明插件，配置与构建时由 Xmake 安装，无需项目初始化任务：

```lua
add_repositories("kunyi git@github.com:wmem/xmake-addons.git")
add_addons("xdtc 0.11.0", "x-pyocd 0.2.0", "x-console 0.1.0",
    "xspm 0.3.0", "cautest 0.6.1")
add_addons("x-firmware 0.2.0")
```

插件声明使用明确的完整版本，工程提交 `xmake-addons.lock` 同时固定版本和索引提交。升级 xdtc 0.11.0 时，须同步更新数据脚本和所引用组件中的 DSL 调用；旧裸名不再有效。旧配方保留供历史锁文件复现。

x-pyocd 与 x-console 分别提供可导入的 `@addon.x-pyocd.api` 与 `@addon.x-console.api`。xdtc 0.11.0 的 action 可声明 `{entry, select}`，直接调用这两个模块，无需工程转发脚本；已有 `{script, select}` 继续支持，两种入口互斥。配置读取接口只读取输入，不调用 entry。完整参数与平台依赖见 [x-pyocd README](https://github.com/wmem/x-pyocd)、[x-console README](https://github.com/wmem/x-console)；action 接口见 [xdtc 使用文档](https://github.com/wmem/xdtc/blob/master/docs/USAGE.md#action-输入)。

首次远程分发需要先推送工具实现提交及索引。对已经固定有效源码提交的配方，可注册本地索引，并用 `XMAKE_ADDON_SOURCE_ROOT` 指定包含工具 Git 仓库的目录：

```sh
xmake repo --add --global kunyi /path/to/xmake-addons-repo
XMAKE_ADDON_SOURCE_ROOT=/path/to/code/xmake \
  xmake addon --install kunyi@xdtc kunyi@x-pyocd kunyi@x-console kunyi@xspm kunyi@cautest
```

本地来源同样按配方固定提交检出，未提交修改不会参与安装；可以直接从工作副本运行准备脚本来验证未提交修改。远程索引发布后，省略 `XMAKE_ADDON_SOURCE_ROOT`，并将本地索引路径替换为 `https://github.com/wmem/xmake-addons.git`。安装通过 Xmake 索引完成；cautest 的配方执行 `npm ci --ignore-scripts`、`npm run build`，只安装生成的 JS 和必要资源，日常测试不重新编译 TS。开发阶段直接从工具原始目录或 Git URL 安装不会执行配方，应先运行各工具的 `scripts/prepare-addon.lua` 准备完整目录。

上面的索引安装命令需要所选版本已经有有效提交号。验证工作副本时，可在各自仓库根目录准备为完整 Addon，再安装到开发专用环境，例如：

```sh
# 在 x-pyocd 仓库根目录执行；输出目录须尚不存在。
xmake lua scripts/prepare-addon.lua /tmp/x-pyocd-addon-stage
xmake addon --install /tmp/x-pyocd-addon-stage
```

x-console 与 xdtc 使用相同准备流程。隔离验证应使用临时 `XMAKE_GLOBALDIR`，避免覆盖工程当前已安装的插件。插件安装不会自动安装 Python、pyOCD、Node.js 或 PowerShell。

Addon 版本与工具源码发布版本统一：当前 xdtc 为 `0.11.0`、xspm 为 `0.3.0`、cautest 为 `0.6.1`、x-pyocd 为 `0.2.0`、x-console 为 `0.1.1`。每个配方的 `add_versions()` 固定对应源码发布提交，不跟随浮动分支；Cautest 的 C API 版本仍独立维护。发布新版时先完成工具验证、提交和标签，再发布同号配方。仅文档修改不改变运行时版本。

此前采用独立的 Addon 版本号，旧配方保留供历史锁文件复现。迁移时修改 `add_addons()` 为上面的明确版本，再在消费工程执行 `xmake addon --upgrade -y`，提交更新后的 `xmake-addons.lock`。`xmake addon --list` 可查看全局活动版本；安装新版本后应确认 `xmake ctest --help` 默认配置为 `ctest.lua`，避免继续使用此前撤回的 `0.1.5` 入口。

## 验证

2026-10-18 的 xdtc 0.11.0 前缀接口迁移已通过工具十个套件、74项检查，索引19项隔离安装回归，以及4项固定源码设备插件接入检查。覆盖所有七个前缀接口、普通函数重名、旧别名移除和跨插件entry；[验证摘要](tests/validation-xdtc-prefix.json)明确区分本地验证与远程发布，未访问硬件。

```sh
ADDON_TEST_EVIDENCE=/tmp/addon-test-evidence \
  uv run --no-project python tests/test_addons.py
```

测试把当前三个工具的源码快照保存为本地 Git 提交，通过本地来源选项选择测试源码，仅替换配方中的提交号，实际执行索引安装流程。所有插件安装、仓库登记和包缓存使用临时 `XMAKE_GLOBALDIR`；不会改动用户的全局插件目录。npm 使用离线模式，缓存缺失会报错，不跳过或自动安装系统工具。

覆盖默认与指定配置、空格和中文路径、外部目录的 `-P`、真实文件生成、命名空间生成规则与模块、输出增量和缺失恢复、Git 源码包同步、Native C 测试成功和失败退出码、错误配置、原有 RC 保留、TS 准备失败后重试、拒绝覆盖及卸载。测试不是远程发布验证，也不访问 MCU 板卡。

新设备插件的隔离验证由 [test_device_addons.py](tests/test_device_addons.py) 独立执行：

```sh
DEVICE_ADDON_TEST_EVIDENCE=/tmp/device-addon-test-evidence \
  uv run --no-project python tests/test_device_addons.py
```

该测试把 xdtc、x-pyocd、x-console 当前工作副本保存为临时 Git 快照，仅在临时索引中把配方提交替换为快照提交；用户全局插件和原始配方不被覆盖。当前包含四项检查：

| 检查 | 实际范围 |
| --- | --- |
| 安装载荷和公开导入 | 真实索引安装后的命令入口、模块导入、xdtc 版本与 execute_entry |
| entry 组合调用及只读 | entry 导入两插件、中文和空格路径、模板资源基准、位置参数与 read_action_config 不执行入口 |
| CLI 配置检查与失败传播 | x-console dry-run、错误配置及 entry 异常导致非零退出 |
| 后端资源完整性 | 安装制品包含 Python、Node.js 和 PowerShell 所需运行资源 |

2026-10-13 的本地快照验证中，上述四项全部通过，0 failure、0 error；版本、范围与结果见 [设备插件接入验证](tests/validation-device-addons.json)。重新运行可用上面的 evidence 参数保留结果和命令日志；本地验证记录不代表远程版本已经发布。

设置 `DEVICE_ADDON_FIXED_SOURCES=1` 可改为验证原始配方中的固定提交，测试只克隆本地工具仓库，不替换提交号。2026-10-13 的固定提交安装同样通过上述四项检查。

插件自身另有 Lua 配置合同、模拟 pyOCD 编程/读回/重试/锁、Linux 伪终端交互及 Windows JSON 传输模拟测试，运行方法见各插件 README。隔离安装和模拟测试不访问实际 MCU；离线检查不能替代 Windows 实板下载、真实串口交互或远程发布验证。

同日另在 KY3133-B00 完成 Windows via WSL 实板验证：通过新插件和 xdtc entry 下载、逐段实读校验、复位，检查 COM23 STATUS/PONG、关闭重开及按行 console 的 EOF 退出。最后一轮使用固定提交配方和当前 MCU 工作区固件；硬件范围、证据及未覆盖项同样记录在上述验证文件中。

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
只修改工具源码不会改变已经安装的命令，`cautest 0.6.1` 声明本身无需改变。

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

2026-10-10，将分发版本统一为 xdtc `0.9.0`、xspm `0.3.0`、cautest `0.6.1`，均固定已有源码发布提交，运行时行为不变。19 项隔离安装与消费测试通过，见 [版本统一验证](tests/validation-version-alignment.json)。旧配方与历史验证记录保留。

2026-10-13 按已有同号发布约定发布 xdtc `0.10.0` 和 x-pyocd/x-console `0.1.0`。此前设备插件记录中的 xdtc Addon `0.4.0` 仅用于本地开发，未发布该配方。源码与固定配方验证后已推送，实际 MCU 工程从远程安装并更新工具锁，完成构建、布局、实板下载读回、复位和串口验收，见 [发布与实际工程接入验证](tests/validation-device-addons-release.json)。
