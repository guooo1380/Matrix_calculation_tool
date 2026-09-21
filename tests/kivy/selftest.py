"""驱动 Kivy 界面做端到端功能验证（手机竖屏尺寸）。

用法： python tests/kivy/selftest.py
"""
import os
import sys
from pathlib import Path

os.environ["KIVY_NO_ARGS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from kivy.config import Config

Config.set("graphics", "width", "400")
Config.set("graphics", "height", "780")
Config.set("graphics", "resizable", "0")
Config.set("graphics", "window_state", "visible")

from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout

from mathtools.ui.kivy_app import MatrixApp

PASS, FAIL = [], []


def read_result_matrices(app):
    """从 result_box 里按添加顺序取出各矩阵的文本（Kivy children 是逆序）。"""
    grids = [c for c in reversed(app.result_box.children)
             if isinstance(c, GridLayout)]
    return [[lbl.text for lbl in reversed(g.children)] for g in grids]


def notes(app):
    return [c.text for c in reversed(app.result_box.children)
            if c.__class__.__name__ == "Label" and c.bold and c.font_size > 15]


def check(name, got, want):
    if got == want:
        PASS.append(name)
    else:
        FAIL.append(f"{name}: 期望 {want}，实际 {got}")


def fill(app, grids_data):
    for grid, data in zip(app.grids, grids_data):
        flat = [v for row in data for v in row]
        for cell, val in zip([c for r in grid.cells for c in r], flat):
            cell.text = str(val)


def run_case(app, op, dims, matrices):
    app.spinner.text = op
    for key, val in dims.items():
        app.dim_entries[key].text = str(val)
    app._build_grids()
    fill(app, matrices)
    app._calculate()


CASES = [
    ("转置矩阵", {"n": 2}, [[[1, 2], [3, 4]]],
     lambda m, n: check("转置矩阵", m[-1], ["1", "3", "2", "4"])),
    ("逆矩阵", {"n": 2}, [[[4, 7], [2, 6]]],
     lambda m, n: check("逆矩阵", m[-1], ["0.6", "-0.7", "-0.2", "0.4"])),
    ("行列式", {"n": 2}, [[[1, 2], [3, 4]]],
     lambda m, n: check("行列式", n, ["行列式 = -2"])),
    ("矩阵乘法", {"m1": 2, "n1": 2, "n2": 2, "p2": 2},
     [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
     lambda m, n: check("矩阵乘法", m[-1], ["19", "22", "43", "50"])),
    ("等价标准形", {"m": 2, "n": 2}, [[[1, 2], [2, 4]]],
     lambda m, n: (check("等价标准形", m[-1], ["1", "0", "0", "0"]),
                   check("等价标准形-秩", n, ["秩 r = 1"]))),
]

STATE = {"i": 0, "app": None}


def step(dt):
    i = STATE["i"]
    app = STATE["app"]
    if i >= len(CASES):
        # 额外验证：奇异矩阵不可逆 + 空单元格报错
        run_case(app, "逆矩阵", {"n": 2}, [[[1, 2], [2, 4]]])
        check("不可逆提示", notes(app), ["该矩阵不可逆（行列式为 0）"])

        app.spinner.text = "行列式"
        app.dim_entries["n"].text = "2"
        app._build_grids()
        app.grids[0].cells[0][0].text = "5"
        app._calculate()
        check("空单元格拦截", app.result_box.children == [], True)

        # 乘法维度不匹配
        app.spinner.text = "矩阵乘法"
        for k, v in {"m1": 2, "n1": 3, "n2": 2, "p2": 2}.items():
            app.dim_entries[k].text = str(v)
        app._build_grids()
        check("维度不匹配拦截", app.grids, [])

        print("\n===== 测试结果 =====")
        for p in PASS:
            print(f"  PASS  {p}")
        for f in FAIL:
            print(f"  FAIL  {f}")
        print(f"\n通过 {len(PASS)} / {len(PASS) + len(FAIL)}")
        app.stop()
        return

    op, dims, mats, verify = CASES[i]
    run_case(app, op, dims, mats)
    verify(read_result_matrices(app), notes(app))
    STATE["i"] = i + 1
    Clock.schedule_once(step, 0.35)


def start(app):
    STATE["app"] = app
    Clock.schedule_once(step, 0.8)


app = MatrixApp()
Clock.schedule_once(lambda dt: start(app), 0)
app.run()
