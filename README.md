# 矩阵计算工具

纯 Python 手写的矩阵运算工具，**运行时零第三方依赖**（不用 numpy，算法全部自己实现），一套运算核心配四种界面：命令行、Tkinter 桌面、Kivy 安卓、pywebview 桌面。

![Python](https://img.shields.io/badge/python-%E2%89%A53.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Android-lightgrey)

[![tests](https://github.com/guooo1380/mathTools/actions/workflows/tests.yml/badge.svg)](https://github.com/guooo1380/mathTools/actions/workflows/tests.yml)

## 支持的运算

| 运算 | 说明 | 阶数限制 |
|---|---|---|
| 转置矩阵 | 支持任意 m×n | 无 |
| 逆矩阵 | Gauss-Jordan 消元 + 列主元选取，奇异矩阵返回「不可逆」 | 任意正整数阶 |
| 行列式 | 余子式展开递归求解 | 命令行界面限 2–5 阶 |
| 矩阵乘法 | 要求前一个矩阵的列数等于后一个的行数 | 无 |
| 等价标准形 | 求秩 r 并给出 `[I_r 0; 0 0]` 标准形 | 无 |

## 四种界面

| 界面 | 入口 | 依赖 | 说明 |
|---|---|---|---|
| 命令行 | `mathtools` 或 `python -m mathtools.cli` | 无 | 交互式输入，结果打印到终端 |
| Tkinter 桌面 | `python -m mathtools.ui.tkinter_app` | 无（标准库自带） | 下拉选运算 → 填维度 → 生成输入框 → 计算 |
| Kivy 触屏 | `python src/main.py` | `kivy==2.3.1` | 适配手机竖屏，可用 Buildozer 打成 APK |
| pywebview 桌面 | `python matrix_desktop.py` | `pywebview>=6.0` + WebView2 运行时 | 复用 `webapp/` 里的网页界面，外观与线上版一致 |
| 网页 / PWA | 浏览器直接打开 `webapp/index.html` | 无 | 与已部署的线上站点同一套 HTML/CSS/JS |

## 快速开始

```bash
# 克隆后安装为可编辑包（只装 mathtools 本身，无第三方依赖）
pip install -e .

# 命令行版
mathtools

# 桌面版（Tkinter，无需安装任何依赖）
python -m mathtools.ui.tkinter_app
```

不想装包也可以直接指定源码路径：

```bash
# Linux / macOS / Git Bash
PYTHONPATH=src python -m mathtools.cli

# Windows cmd
set PYTHONPATH=src && python -m mathtools.cli
```

可选依赖按需安装：

```bash
pip install -e ".[android]"   # Kivy 界面
pip install -e ".[desktop]"   # pywebview 桌面版
pip install -e ".[package]"   # PyInstaller，打 Windows exe
```

## 项目结构

```
├── src/
│   ├── main.py                  # Buildozer 安卓入口
│   └── mathtools/
│       ├── core.py              # 矩阵运算核心，四种界面共用
│       ├── cli.py               # 命令行交互
│       └── ui/
│           ├── tkinter_app.py   # Tkinter 桌面界面
│           └── kivy_app.py      # Kivy 触屏界面
├── tests/
│   ├── test_core.py             # 运算核心单元测试（CI 跑这个）
│   ├── kivy/
│   │   ├── selftest.py          # Kivy 端到端自测，会开真实窗口
│   │   └── layoutcheck.py       # 手机竖屏布局溢出检查
│   └── desktop/
│       └── selftest.py          # pywebview 桌面版自检，会开真实窗口
├── webapp/                      # 网页版界面，pywebview 桌面版与安卓壳都直接复用它
├── matrix_desktop.py            # pywebview 桌面版入口
├── android-build/               # 安卓 WebView 壳工程 + 手工打包脚本
│   ├── app-src/                 # Manifest、MainActivity.java、strings.xml
│   └── scripts/build_apk.py     # aapt2 → javac → d8 → zipalign → apksigner
├── buildozer.spec               # 安卓 APK 打包配置（Kivy 路线）
├── 矩阵计算工具.spec             # PyInstaller 桌面 exe 打包配置
├── build_apk.sh                 # 在 WSL Ubuntu 里构建 APK
└── docs/                        # 开发过程与两端打包指南
```

## 测试

```bash
# 运算核心单元测试，24 个用例，纯标准库
pip install -e .
python -m unittest discover -s tests -p "test_*.py" -v

# Kivy 端到端自测（需要显示器，会弹出 400x780 的窗口）
python tests/kivy/selftest.py
python tests/kivy/layoutcheck.py

# pywebview 桌面版自检（需要显示器，会真的开窗口）
python tests/desktop/selftest.py
```

`tests/kivy/` 下的脚本不匹配 `test_*.py`，因此不会被 unittest 自动发现，也不会在无显示器的 CI 里执行。

## 打包

- Windows 桌面 exe：[docs/打包-Windows.md](docs/打包-Windows.md)
- 安卓 APK（WebView 壳，**当前可用**）：[docs/打包-Android-WebView.md](docs/打包-Android-WebView.md)，产物 `dist/矩阵计算工具.apk`，一条命令 `python android-build/scripts/build_apk.py` 重建
- 安卓 APK（Kivy + Buildozer，本机未跑通）：[docs/打包-Android.md](docs/打包-Android.md)

## 已知限制

- 行列式用余子式递归展开，复杂度 O(n!)，阶数一大就会明显变慢，因此命令行界面把它限制在 2–5 阶；求逆用的是 Gauss-Jordan，不受此限制。
- 所有浮点判零统一用 `1e-12` 阈值，接近奇异的矩阵可能被判定为奇异。
- 等价标准形只返回按秩构造的 `[I_r 0; 0 0]`，不记录过程中的行列交换，因此不能用来反推变换矩阵。
- Tkinter 版在输入有误时只弹错误提示框，不会清空上一次的结果区，屏幕上有可能是旧结果。
- 安卓版目前有两个打包路线：实际可用的是 WebView 壳（`dist/矩阵计算工具.apk`，界面即 `webapp/`，完全离线、不申请权限）；Kivy + Buildozer 那条依赖 NDK 交叉编译，本机仍未跑通，详见各自文档。
- pywebview 桌面版需要系统已安装 Microsoft Edge WebView2 运行时，缺失时程序会弹窗提示。

## 开发过程

这个项目是分了几个阶段、跨多个会话逐步长出来的，完整时间线、每一步的取舍和踩过的坑记录在 [docs/开发过程.md](docs/开发过程.md)。

## License

[MIT](LICENSE) © 2026 guooo1380
