"""矩阵计算工具 —— Kivy 版，适配触屏与安卓打包。"""

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from mathtools.core import (
    determinant,
    equivalent_standard_form,
    fmt_value,
    inverse,
    multiply,
    transpose,
)

OPS = ["转置矩阵", "逆矩阵", "行列式", "矩阵乘法", "等价标准形"]

DIM_SPECS = {
    "转置矩阵": [("n", "阶数 n")],
    "逆矩阵": [("n", "阶数 n")],
    "行列式": [("n", "阶数 n")],
    "矩阵乘法": [("m1", "矩阵A 行数"), ("n1", "矩阵A 列数"),
                 ("n2", "矩阵B 行数"), ("p2", "矩阵B 列数")],
    "等价标准形": [("m", "行数 m"), ("n", "列数 n")],
}

ACCENT = (0.16, 0.45, 0.75, 1)
DARK = (0.10, 0.10, 0.10, 1)
GREY = (0.40, 0.40, 0.40, 1)


def show_popup(title, message):
    box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(16))
    msg = Label(text=message, color=DARK, font_size=dp(15),
                halign="center", valign="middle")
    msg.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    box.add_widget(msg)
    btn = Button(text="确定", size_hint_y=None, height=dp(46),
                 background_color=ACCENT, font_size=dp(15))
    box.add_widget(btn)
    popup = Popup(title=title, content=box, size_hint=(0.85, None),
                  height=dp(230), title_size=dp(16))
    btn.bind(on_release=popup.dismiss)
    popup.open()


class MatrixApp(App):
    def build(self):
        self.title = "矩阵计算工具"
        self.dim_entries = {}
        self.grids = []

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        header = Label(text="矩阵计算工具", font_size=dp(20), bold=True,
                       color=ACCENT, size_hint_y=None, height=dp(34))
        root.add_widget(header)

        self.page = BoxLayout(orientation="vertical", size_hint_y=None,
                              spacing=dp(10), padding=(0, dp(4)))
        self.page.bind(minimum_height=self.page.setter("height"))
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        scroll.add_widget(self.page)
        root.add_widget(scroll)

        self.page.add_widget(self._section_label("运算类型"))
        self.spinner = Spinner(text=OPS[0], values=OPS, size_hint_y=None,
                               height=dp(46), font_size=dp(15))
        self.spinner.bind(text=self._on_op_change)
        self.page.add_widget(self.spinner)

        self.page.add_widget(self._section_label("维度"))
        self.dim_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                 spacing=dp(6))
        self.dim_box.bind(minimum_height=self.dim_box.setter("height"))
        self.page.add_widget(self.dim_box)

        gen_btn = Button(text="生成输入框", size_hint_y=None, height=dp(46),
                         background_color=ACCENT, font_size=dp(15))
        gen_btn.bind(on_release=self._build_grids)
        self.page.add_widget(gen_btn)

        self.input_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                   spacing=dp(6))
        self.input_box.bind(minimum_height=self.input_box.setter("height"))
        self.page.add_widget(self.input_box)

        calc_btn = Button(text="计算", size_hint_y=None, height=dp(50),
                          background_color=(0.13, 0.60, 0.33, 1),
                          font_size=dp(17), bold=True)
        calc_btn.bind(on_release=self._calculate)
        self.page.add_widget(calc_btn)

        self.page.add_widget(self._section_label("计算结果"))
        self.result_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                    spacing=dp(6))
        self.result_box.bind(minimum_height=self.result_box.setter("height"))
        self.page.add_widget(self.result_box)

        self._build_dim_inputs()
        return root

    # ── 布局辅助 ──────────────────────────────────────────────────────────────

    def _section_label(self, text):
        lbl = Label(text=text, color=GREY, font_size=dp(13), bold=True,
                    size_hint_y=None, height=dp(22), halign="left",
                    valign="bottom")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        return lbl

    def _cell_width(self, cols):
        avail = Window.width - dp(40)
        spacing = dp(3)
        width = (avail - (cols - 1) * spacing) / cols
        return max(dp(34), min(dp(72), width))

    def _make_matrix_grid(self, cols, rows, cell_w, cell_h, editable):
        spacing = dp(3)
        grid = GridLayout(cols=cols, spacing=spacing, size_hint=(None, None),
                          width=cols * cell_w + (cols - 1) * spacing)
        grid.bind(minimum_height=grid.setter("height"))
        cells = []
        for _ in range(rows):
            row = []
            for _ in range(cols):
                if editable:
                    cell = TextInput(text="", multiline=False,
                                     input_type="number",
                                     size_hint=(None, None), width=cell_w,
                                     height=cell_h, font_size=dp(14),
                                     halign="center")
                else:
                    cell = None
                row.append(cell)
            cells.append(row)
        grid.cells = cells
        return grid

    # ── 维度与输入框 ──────────────────────────────────────────────────────────

    def _build_dim_inputs(self):
        self.dim_box.clear_widgets()
        self.dim_entries.clear()
        for key, text in DIM_SPECS[self.spinner.text]:
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            lbl = Label(text=text, color=DARK, font_size=dp(14),
                        size_hint_x=None, width=dp(110), halign="left",
                        valign="middle")
            lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            entry = TextInput(text="", multiline=False, input_type="number",
                              font_size=dp(14), halign="center")
            row.add_widget(lbl)
            row.add_widget(entry)
            self.dim_box.add_widget(row)
            self.dim_entries[key] = entry

    def _on_op_change(self, spinner, text):
        self._build_dim_inputs()
        self.input_box.clear_widgets()
        self.grids.clear()
        self.result_box.clear_widgets()

    def _build_grids(self, *args):
        self.input_box.clear_widgets()
        self.result_box.clear_widgets()
        self.grids.clear()

        try:
            dims = {k: int(v.text.strip()) for k, v in self.dim_entries.items()}
            if any(v < 1 for v in dims.values()):
                raise ValueError
        except ValueError:
            show_popup("错误", "请输入有效的正整数维度。")
            return

        op = self.spinner.text
        if op == "矩阵乘法":
            if dims["n1"] != dims["n2"]:
                show_popup("错误", f"矩阵A 的列数({dims['n1']})必须等于"
                                   f"矩阵B 的行数({dims['n2']})。")
                return
            specs = [("矩阵 A", dims["m1"], dims["n1"]),
                     ("矩阵 B", dims["n2"], dims["p2"])]
        elif op == "等价标准形":
            specs = [("矩阵", dims["m"], dims["n"])]
        else:
            specs = [("矩阵", dims["n"], dims["n"])]

        for title, rows, cols in specs:
            self.input_box.add_widget(self._section_label(
                f"{title}（{rows} × {cols}）"))
            grid = self._make_matrix_grid(cols, rows, self._cell_width(cols),
                                          dp(44), editable=True)
            for i, row in enumerate(grid.cells):
                for j, cell in enumerate(row):
                    grid.add_widget(cell)
            self.input_box.add_widget(grid)
            self.grids.append(grid)

    # ── 计算与结果 ────────────────────────────────────────────────────────────

    def _read_grid(self, grid):
        matrix = []
        for row in grid.cells:
            values = []
            for cell in row:
                text = cell.text.strip()
                if not text:
                    raise ValueError("存在空单元格。")
                try:
                    values.append(float(text))
                except ValueError:
                    raise ValueError(f"「{text}」不是有效数字。")
            matrix.append(values)
        return matrix

    def _add_result_matrix(self, matrix):
        rows, cols = len(matrix), len(matrix[0])
        grid = self._make_matrix_grid(cols, rows, self._cell_width(cols),
                                      dp(30), editable=False)
        for i in range(rows):
            for j in range(cols):
                grid.add_widget(Label(text=fmt_value(matrix[i][j]), color=DARK,
                                      font_size=dp(14), size_hint=(None, None),
                                      width=self._cell_width(cols),
                                      height=dp(30)))
        self.result_box.add_widget(grid)

    def _add_result_note(self, text):
        lbl = Label(text=text, color=ACCENT, font_size=dp(16), bold=True,
                    size_hint_y=None, height=dp(30), halign="left",
                    valign="middle")
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.result_box.add_widget(lbl)

    def _show_matrices(self, sections, note=None):
        self.result_box.clear_widgets()
        for title, matrix in sections:
            self.result_box.add_widget(self._section_label(title))
            self._add_result_matrix(matrix)
        if note:
            self._add_result_note(note)

    def _calculate(self, *args):
        op = self.spinner.text
        if not self.grids:
            show_popup("提示", "请先设置维度并点击「生成输入框」。")
            return
        try:
            if op == "矩阵乘法":
                a = self._read_grid(self.grids[0])
                b = self._read_grid(self.grids[1])
                self._show_matrices([("矩阵 A", a), ("矩阵 B", b),
                                     ("乘积矩阵", multiply(a, b))])
            elif op == "等价标准形":
                m = self._read_grid(self.grids[0])
                std, rank = equivalent_standard_form(m)
                self._show_matrices([("原矩阵", m), ("等价标准形", std)],
                                    note=f"秩 r = {rank}")
            else:
                matrix = self._read_grid(self.grids[0])
                if op == "转置矩阵":
                    self._show_matrices([("原矩阵", matrix),
                                         ("转置矩阵", transpose(matrix))])
                elif op == "逆矩阵":
                    inv = inverse(matrix)
                    if inv is None:
                        self._show_matrices([("原矩阵", matrix)],
                                            note="该矩阵不可逆（行列式为 0）")
                    else:
                        self._show_matrices([("原矩阵", matrix), ("逆矩阵", inv)])
                else:
                    det = determinant(matrix)
                    self._show_matrices([("原矩阵", matrix)],
                                        note=f"行列式 = {det:.6g}")
        except ValueError as e:
            show_popup("输入错误", str(e))


if __name__ == "__main__":
    MatrixApp().run()
