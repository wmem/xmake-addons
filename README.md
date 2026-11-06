# xmake-addons

管理六个 Xmake Addon 的分发配方、完整版本及固定源码提交；各工具实现仍由自己的仓库维护。

正式文档从[文档首页](docs/index.mdoc)进入；[使用文档](docs/usage/index.mdoc)按任务组织，[查询参考](docs/usage/reference/index.mdoc)保存精确规则，[开发文档](docs/development/index.mdoc)说明实现与验证。

安装方法见[首次安装与版本锁定](docs/usage/quickstart.mdoc)，维护配方见[开发文档](docs/development/index.mdoc)。

## 本地文档

已全局安装 edoc 时，在本仓库根目录执行：

```sh
edoc validate
edoc
```

打开 output/index.html 阅读离线文档。正文与配置位于 docs/，各层 index 维护顺序；修改源文后重新生成。

## 开发与验证

```sh
uv run --no-project python tests/test_addons.py
```

上述命令在仓库根执行。完整依赖、测试入口及验证范围见[开发文档](docs/development/index.mdoc)。
