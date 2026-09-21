#!/usr/bin/env bash
# 在 WSL Ubuntu 中执行：构建安卓 APK
#
#   bash build_apk.sh
#
# 首次构建需下载 Android SDK/NDK（约 10-15GB 磁盘，30-60 分钟）。
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$HOME/mathTools"
VENV_DIR="$HOME/buildozer-env"

if [[ "$PROJECT_DIR" == /mnt/* ]]; then
    # /mnt/* 是 9P 挂载，I/O 很慢且符号链接/权限行为异常，复制到 WSL 原生文件系统
    echo "==> 项目在 Windows 挂载路径下，复制到 $BUILD_DIR 构建"
    mkdir -p "$BUILD_DIR/src"
    cp "$PROJECT_DIR/buildozer.spec" "$BUILD_DIR/"
    cp "$PROJECT_DIR/src/main.py" "$BUILD_DIR/src/"
    cp -r "$PROJECT_DIR/src/mathtools" "$BUILD_DIR/src/"
    # 安卓版用不到 Tkinter 界面和命令行版，与 buildozer.spec 的排除项保持一致
    rm -f "$BUILD_DIR/src/mathtools/ui/tkinter_app.py" \
          "$BUILD_DIR/src/mathtools/cli.py"
    find "$BUILD_DIR" -name __pycache__ -type d -prune -exec rm -rf {} +
    cd "$BUILD_DIR"
else
    cd "$PROJECT_DIR"
fi

echo "==> 安装系统依赖（需要 sudo 密码）"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    git zip unzip curl \
    python3 python3-pip python3-venv python3-dev \
    build-essential \
    openjdk-17-jdk \
    autoconf automake libtool pkg-config \
    zlib1g-dev libncurses-dev libffi-dev libssl-dev \
    cmake

echo "==> 准备 buildozer 虚拟环境"
python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
pip install buildozer cython==0.29.36

echo "==> 开始构建 debug APK"
buildozer android debug

echo ""
echo "==> 构建完成，APK 路径："
ls -lh bin/*.apk
echo ""
echo "把 APK 拷回 Windows 可用："
echo "  cp bin/*.apk /mnt/d/pythonProject/mathTools/"
