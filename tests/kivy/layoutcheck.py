"""验证手机竖屏尺寸下矩阵网格不会横向溢出。

用法： python tests/kivy/layoutcheck.py
"""
import os
import sys
from pathlib import Path

os.environ["KIVY_NO_ARGS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from kivy.config import Config

PHONE_W, PHONE_H = 400, 780
Config.set("graphics", "width", str(PHONE_W))
Config.set("graphics", "height", str(PHONE_H))
Config.set("graphics", "resizable", "0")

from kivy.clock import Clock

from mathtools.ui.kivy_app import MatrixApp

ok, bad = [], []


def check_widths(app, cols):
    app.spinner.text = "等价标准形"
    app.dim_entries["m"].text = "3"
    app.dim_entries["n"].text = str(cols)
    app._build_grids()
    grid = app.grids[0]
    fits = grid.width <= PHONE_W
    cells = [c for r in grid.cells for c in r]
    tappable = all(c.width >= 34 for c in cells)
    label = f"{cols} 列: 网格宽 {grid.width:.0f}px / 屏宽 {PHONE_W}px"
    (ok if (fits and tappable) else bad).append(
        label + ("  OK" if fits and tappable else
                 f"  {'溢出' if not fits else ''}{' 单元过小' if not tappable else ''}"))


def run(dt):
    app = dt_app["a"]
    for cols in (2, 3, 4, 5, 6, 8):
        check_widths(app, cols)

    app.spinner.text = "矩阵乘法"
    for k, v in {"m1": 3, "n1": 3, "n2": 3, "p2": 3}.items():
        app.dim_entries[k].text = str(v)
    app._build_grids()
    total_h = sum(g.height for g in app.grids)
    (ok if total_h > 0 else bad).append(f"乘法双网格总高 {total_h:.0f}px")

    page = app.page
    scrollable = page.height > PHONE_H - 100
    (ok if scrollable else bad).append(
        f"整页高 {page.height:.0f}px，可纵向滚动={scrollable}")

    print("\n===== 布局检查 =====")
    for o in ok:
        print("  OK   ", o)
    for b in bad:
        print("  WARN ", b)
    print(f"\n通过 {len(ok)} / {len(ok) + len(bad)}")
    app.stop()


dt_app = {}
app = MatrixApp()
Clock.schedule_once(lambda d: dt_app.setdefault("a", app), 0)
Clock.schedule_once(run, 1.2)
app.run()
