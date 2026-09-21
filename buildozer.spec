[app]

# 应用显示名（手机桌面上看到的名字）
title = 矩阵计算工具

# 包名与域，最终 applicationId = package.domain + package.name
# 上架 Google Play 前需改成自己的唯一域名，且发布后不可更改
package.name = mathtools
package.domain = com.example

source.dir = src
source.include_exts = py,png,jpg,jpeg,kv,ttf

# 只打包 Kivy 版所需文件，排除 Tkinter 界面、命令行版和缓存
source.exclude_patterns =
    mathtools/ui/tkinter_app.py,
    mathtools/cli.py,
    __pycache__/*,
    */__pycache__/*,
    */*/__pycache__/*

version = 1.0.0

# Kivy 版本与本机一致，避免行为差异
requirements = python3,kivy==2.3.1

orientation = portrait
fullscreen = False

# 应用图标：把 512x512 的 PNG 放到 src/assets/icon.png 后取消注释
# （仓库里已有 webapp/icon-512.png，可直接复制到 src/assets/icon.png）
# logo = assets/icon.png
# android.icon = assets/icon.png

presplash.color = "#2973BF"

# 纯本地计算，无需任何权限
android.permissions =

android.api = 34
android.minapi = 21
android.ndk_api = 21

# 首次构建自动接受 SDK 许可，避免卡在交互提示
android.accept_sdk_license = True

# 构建 debug APK，可直接安装到手机测试
android.release_artifact = apk

android.archs = arm64-v8a
android.allow_backup = False

# 返回键退出应用（Kivy 默认行为）
android.wakelock = False

[buildozer]
log_level = 2
warn_on_root = 1
