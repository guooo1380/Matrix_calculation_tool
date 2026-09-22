# 打包安卓 APK

> **当前状态：APK 至今没有构建成功过**，卡在环境准备阶段的网络问题上（`dl.google.com`、Gradle 分发、PyPI 均不可达）。
> 本文记录的是完整的准备清单和已确认的失败原因，等网络可达时可以照着一次跑通。
> 在此之前，安卓版的功能正确性靠 `tests/kivy/selftest.py`（400×780 窗口里跑完五种运算和三个异常分支）和 `tests/kivy/layoutcheck.py`（布局溢出检查）保证。

## 构建方式

Buildozer 只支持在 Linux 上跑，Windows 需要 WSL2 + Ubuntu。准备好环境后，在仓库根目录执行：

```bash
bash build_apk.sh
```

脚本会装系统依赖、建 buildozer 虚拟环境、执行 `buildozer android debug`，产物在 `bin/*.apk`。
如果项目位于 `/mnt/*`（Windows 挂载路径），脚本会先把需要的文件复制到 `~/mathTools` 再构建——9P 挂载的 I/O 很慢，而且符号链接和权限行为异常。

首次构建要下载 Android SDK/NDK，约 10–15 GB 磁盘、30–60 分钟。

## 目录结构约定

`buildozer.spec` 里 `source.dir = src`，即把 `src/` 下的内容作为 App 根目录：

```
src/
├── main.py            # Buildozer 固定找这个名字作为入口
└── mathtools/         # 必须与 main.py 同级，否则 import 不到
```

`main.py` 只做一件事：`from mathtools.ui.kivy_app import MatrixApp` 然后 `MatrixApp().run()`。

`source.exclude_patterns` 排除了安卓上用不到的 Tkinter 界面和命令行版；`build_apk.sh` 的复制逻辑与它保持一致。**改动 `src/` 下的文件布局时，这两处都要同步改。**

`buildozer.spec` 必须是 UTF-8 + LF，存成 CRLF 会解析异常。仓库的 `.gitattributes` 已经把 `*.spec` 和 `*.sh` 钉死为 LF。

## 环境准备清单（已验证的坑）

### 1. WSL2 + Ubuntu

`wsl --install -d Ubuntu --no-launch` 可能超时。绕过的办法：

```bash
# 用 DISM 启用功能后重启
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --update
```

Ubuntu 从 GitHub 下载也可能超时（`WININET_E_TIMEOUT`）。改从 `cloud-images.ubuntu.com` 取 24.04 的 rootfs tar，再导入：

```bash
wsl --import Ubuntu D:\WSL\Ubuntu <rootfs.tar.gz>
```

### 2. 不能用 root 跑 Buildozer

Buildozer 会拒绝以 root 身份运行。需要建一个普通用户并给它免密 sudo：

```bash
useradd -m -s /bin/bash builder
echo "builder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/builder
```

### 3. Ubuntu 24.04 的 PEP 668 限制

系统 Python 不允许直接 `pip install`。用 venv（`build_apk.sh` 已经这么做，虚拟环境在 `~/buildozer-env`），或者退而用 `--break-system-packages`。

### 4. cython 版本必须钉死

```bash
pip install buildozer cython==0.29.36
```

`requirements = python3,kivy==2.3.1` 配 cython 3 会破坏 python-for-android 的构建，必须用 0.29.36。

### 5. 系统依赖

`build_apk.sh` 里已经列全：git/zip/unzip/curl、python3 及 dev/venv/pip、build-essential、openjdk-17-jdk、autoconf/automake/libtool/pkg-config、zlib1g-dev/libncurses-dev/libffi-dev/libssl-dev、cmake。

## 应用图标

`buildozer.spec` 里的图标配置目前是注释状态。要启用：把一张 512×512 的 PNG 放到 `src/assets/icon.png`（仓库里已有 `webapp/icon-512.png` 可以直接复制过去），然后取消这两行注释：

```ini
logo = assets/icon.png
android.icon = assets/icon.png
```

## 上架前必须改的配置

```ini
package.domain = com.example   # 改成自己的唯一域名
```

最终 `applicationId = package.domain + package.name`（现在是 `com.example.mathtools`）。**发布后不可更改**，上架 Google Play 前一定要先改掉占位域名。

其余配置：`android.api = 34`、`android.minapi = 21`、`android.ndk_api = 21`、`android.archs = arm64-v8a`、`orientation = portrait`、`android.permissions =`（纯本地计算，不申请任何权限）。
