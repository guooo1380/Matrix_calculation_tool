"""pywebview 桌面版自检：真的开一个窗口，检查页面、JS API 和计算链路后自动关闭。

用法： python tests/desktop/selftest.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import webview

from matrix_desktop import Api, resource_path

RESULTS = []


def check(name, value, expect):
    ok = value == expect
    RESULTS.append((ok, name, value, expect))


def probe(window):
    if not window.events.loaded.wait(20):
        RESULTS.append((False, "页面加载", "timeout", "loaded"))
        window.destroy()
        return

    js = window.evaluate_js
    check("标题", js("document.title"), "矩阵计算工具")
    check("运算胶囊数", js("document.querySelectorAll('.op-pill').length"), 5)
    check("顶栏渐变", "linear-gradient" in str(js(
        "getComputedStyle(document.querySelector('.header')).backgroundImage")), True)
    check("JS API 注入", js(
        "typeof (window.pywebview && window.pywebview.api &&"
        " window.pywebview.api.submit_feedback)"), "function")
    check("无 service worker 注册", js(
        "navigator.serviceWorker.controller === null"), True)

    # 走一遍完整交互：切到转置 → 2x3 → 填数 → 计算
    js("""
        document.querySelector('.op-pill[data-op="transpose"]').click();
        document.getElementById('dim-m').value = '2';
        document.getElementById('dim-n').value = '3';
        document.getElementById('gen-btn').click();
        document.querySelectorAll('.cell-input').forEach((c, i) => { c.value = i + 1; });
        document.getElementById('calc-btn').click();
    """)
    check("结果卡片可见", js("document.getElementById('result-card').hidden"), False)
    check("结果矩阵块数", js(
        "document.querySelectorAll('#result-content .result-block').length"), 2)
    check("转置后行数", js(
        "document.querySelectorAll('#result-content .matrix-tbl')[1].rows.length"), 3)
    check("转置后每行列数", js(
        "document.querySelectorAll('#result-content .matrix-tbl')[1].rows[0].cells.length"), 2)
    check("转置首格值", js(
        "document.querySelectorAll('#result-content .matrix-tbl')[1].rows[0].cells[0].textContent"), "1")
    check("转置末格值", js(
        "document.querySelectorAll('#result-content .matrix-tbl')[1].rows[2].cells[1].textContent"), "6")

    # 行列式：2x2 单位阵 → det = 1
    js("""
        document.querySelector('.op-pill[data-op="determinant"]').click();
        document.getElementById('dim-n').value = '2';
        document.getElementById('gen-btn').click();
        var c = document.querySelectorAll('.cell-input');
        c[0].value = '1'; c[1].value = '0'; c[2].value = '0'; c[3].value = '1';
        document.getElementById('calc-btn').click();
    """)
    check("行列式结果", js(
        "document.querySelector('#result-content .result-scalar').textContent"), "det = 1")

    # 不可逆矩阵要走红字提示而不是崩溃
    js("""
        document.querySelector('.op-pill[data-op="inverse"]').click();
        document.getElementById('dim-n').value = '2';
        document.getElementById('gen-btn').click();
        var c = document.querySelectorAll('.cell-input');
        c[0].value = '1'; c[1].value = '2'; c[2].value = '2'; c[3].value = '4';
        document.getElementById('calc-btn').click();
    """)
    check("不可逆提示", js(
        "document.querySelector('#result-content .result-note').textContent"),
        "该矩阵不可逆（行列式为 0）")

    # 空单元格按 0 处理 + Toast 提示维度非法
    js("""
        document.querySelector('.op-pill[data-op="transpose"]').click();
        document.getElementById('dim-m').value = '99';
        document.getElementById('gen-btn').click();
    """)
    check("维度越界 Toast", js(
        "document.getElementById('toast').textContent"), "维度须为 1 ~ 20 的正整数")

    window.destroy()


def main():
    window = webview.create_window(
        "自检",
        resource_path("webapp/index.html"),
        js_api=Api(),
        width=520,
        height=820,
        background_color="#F0F2F5",
    )
    webview.start(probe, window)

    failed = [r for r in RESULTS if not r[0]]
    for ok, name, value, expect in RESULTS:
        print(("[PASS] " if ok else "[FAIL] ") + name + " -> " + repr(value)
              + ("" if ok else "  (期望 " + repr(expect) + ")"))
    print()
    print("通过 {}/{}".format(len(RESULTS) - len(failed), len(RESULTS)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
