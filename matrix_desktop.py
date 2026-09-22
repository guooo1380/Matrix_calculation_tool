"""矩阵计算工具 —— Windows 桌面版。

界面直接复用 webapp/ 下的网页版（与线上 PWA 同一套 HTML/CSS/JS），
用 pywebview 的 WebView2 窗口渲染，因此外观和网页版完全一致。
计算全部在网页版的 app.js 里完成，Python 这边只负责开窗和提交用户建议。
"""

import os
import sys
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import webview
from webview.errors import WebViewException

# 网页版的 Netlify 表单端点，和线上站点共用同一个「suggestions」收件列表
FEEDBACK_URL = "https://matrix-calc-bd11eb44.netlify.app/"

# 默认的 private_mode 会在 %TEMP% 建随机目录且退出时删不掉，改成固定目录
STORAGE_PATH = os.path.join(
    os.environ.get("APPDATA") or os.path.expanduser("~"), "MatrixCalculator"
)


def resource_path(relative):
    """开发时取脚本同级目录，PyInstaller onefile 运行时取解包目录。"""
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, relative)


class Api:
    """暴露给页面里 window.pywebview.api 的方法。

    建议由 Python 这边发 POST：页面跑在本地 http server 上，直接 fetch
    Netlify 会被跨域拦掉，而且本地 '/' 是 pywebview 自己的静态服务。
    """

    def submit_feedback(self, message, contact=""):
        body = urlencode({
            "form-name": "suggestions",
            "bot-field": "",
            "message": message,
            "contact": contact,
        }).encode("utf-8")
        request = Request(
            FEEDBACK_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                return {"ok": 200 <= response.status < 400}
        except (URLError, OSError, TimeoutError):
            return {"ok": False}


def main():
    webview.create_window(
        "矩阵计算工具",
        resource_path(os.path.join("webapp", "index.html")),
        js_api=Api(),
        width=520,
        height=820,
        min_size=(400, 600),
        background_color="#F0F2F5",
    )
    try:
        webview.start(
            icon=resource_path(os.path.join("webapp", "app.ico")),
            storage_path=STORAGE_PATH,
        )
    except WebViewException:
        _missing_webview2()


def _missing_webview2():
    """console=False 的 exe 报错时什么都不显示，这里补一个能看懂的提示。"""
    import ctypes

    ctypes.windll.user32.MessageBoxW(
        0,
        "本程序需要 Microsoft Edge WebView2 运行时。\n"
        "请到微软官网搜索「WebView2 Runtime」下载安装后重试。",
        "缺少 WebView2 运行时",
        0x10,
    )


if __name__ == "__main__":
    main()
