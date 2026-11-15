# 打包 Windows 桌面 exe

当前 Windows exe 打的是 **pywebview 桌面版**（`matrix_desktop.py` + `webapp/`），配置在根目录的 `矩阵计算工具.spec`。

## 前置条件

```bash
pip install -e ".[desktop,package]"   # pywebview>=6.0 + pyinstaller==6.22.3
```

运行时还需要系统已安装 **Microsoft Edge WebView2 运行时**（Win11 一般自带，Win10 可能要单独装）。缺失时 exe 会弹出提示框引导下载，不会静默失败。

## 打包

在仓库根目录执行（spec 里的 `matrix_desktop.py`、`webapp`、`webapp/app.ico` 都是相对仓库根的路径）：

```bash
pyinstaller 矩阵计算工具.spec --noconfirm
```

产物：`dist/矩阵计算工具.exe`，约 11.8 MB，单文件免安装，双击运行。中间文件在 `build/`，两者都已被 `.gitignore` 排除。

不用 spec、纯命令行打一遍等价于：

```bash
pyinstaller --onefile --windowed --name "矩阵计算工具" --clean --noconfirm \
    --add-data "webapp;webapp" --icon webapp/app.ico \
    --runtime-tmpdir "%LOCALAPPDATA%\MatrixCalculator" \
    --exclude-module tkinter --exclude-module _tkinter \
    matrix_desktop.py
```

## 解包目录（`runtime_tmpdir`）

onefile 版启动时要把 exe 里打包的内容解压到一个临时目录，默认落在 `%TEMP%`。实测有机器会在这里失败，双击弹出 `Error / Could not create temporary directory!`（PyInstaller 内部错误码 PYI-2724），因此 spec 里显式指定了：

```python
runtime_tmpdir='%LOCALAPPDATA%\\MatrixCalculator'
```

三条经验，改这个值之前先看清楚：

1. **bootloader 只创建最后一级目录**，父目录必须已经存在。写成 `%LOCALAPPDATA%\MatrixCalculator\runtime` 会报 `LOADER: failed to create runtime-tmpdir path ... CreateDirectory: 系统找不到指定的路径`。
2. **不要指回 `%TEMP%`**。除了上面的拦截问题，还有第二层坑：如果解包目录在 `D:` 盘（例如用 `--runtime-tmpdir` 指到项目目录里调试），`.NET` 从该盘加载托管程序集会失败，表现为 `RuntimeError: Failed to resolve Python.Runtime.Loader.Initialize from ...\pythonnet\runtime\Python.Runtime.dll`（pywebview 依赖 pythonnet 调 WinForms），exe 无窗口直接退出。
3. 改完 `runtime_tmpdir` 要重新打包，可用 `build/矩阵计算工具/EXE-00.toc` 确认新值确实写进了 exe。

如果需要不依赖解包的一版（启动更快、也不用折腾临时目录），可以打成文件夹版：

```bash
pyinstaller --onedir --windowed --name "矩阵计算工具" --clean --noconfirm \
    --add-data "webapp;webapp" --icon webapp/app.ico \
    --exclude-module tkinter --exclude-module _tkinter \
    --distpath dist-onedir matrix_desktop.py
```

> `--add-data` 的分隔符在 Windows 上是 `;`，Linux/macOS 上是 `:`。

## 打包 Tkinter 版

Tkinter 版目前没有自己的 spec（原来的那份在阶段五被替换成了桌面版配置），从源码直接运行即可：

```bash
python -m mathtools.ui.tkinter_app
```

需要单独打成 exe 的话：

```bash
pyinstaller --onefile --windowed --name "矩阵计算工具-Tkinter" --clean --noconfirm \
    --paths src src/mathtools/ui/tkinter_app.py
```

`--paths src` 是必需的，否则 PyInstaller 找不到 `mathtools` 包。注意别用 `矩阵计算工具` 这个名字，会和桌面版的 exe 撞名互相覆盖。

## 闪退排查经验

`--windowed`（即 `console=False`）打出来的 exe **崩溃时不显示任何信息**，双击后窗口一闪就没了。踩过一次的完整排查路径：

1. 先临时改成 `console=True` 重新打包，让 traceback 打到控制台，拿到真实异常。
2. 本次的真实原因是 `matrix_gui.py` 里 `_on_op_change()` 的调用位置早于 `self.dim_entries = {}` 的初始化，访问了还不存在的属性。从 IDE 里跑不触发，是因为那条路径的调用顺序不同——**打包后行为不一致时优先怀疑初始化顺序**。
3. 修完改回 `console=False` 重新打包。

排查过程中另外两个坑：

- exe 是中文名，`tasklist | grep 矩阵` 因为编码问题匹配不上，判断进程是否存活要改用 PID 或 `tasklist /FI "PID eq ..."`。
- 在 Git Bash 里 `tasklist /FI ...` 的 `/FI` 会被当成路径做转换，必须写成 `//FI`，或者干脆切到 cmd 执行。

程序自己抛的错要给用户看，就别依赖控制台：桌面版里 `_missing_webview2()` 用 `ctypes.windll.user32.MessageBoxW` 弹窗，是 `console=False` 下唯一可靠的提示方式。
