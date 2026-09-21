import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ── 数学函数（与 Kivy 版共用 mathtools.core）───────────────────────────────────

from mathtools.core import (
    determinant,
    equivalent_standard_form,
    format_matrix,
    inverse,
    multiply,
    transpose,
)


# ── GUI ───────────────────────────────────────────────────────────────────────

OPS = ["转置矩阵", "逆矩阵", "行列式", "矩阵乘法", "等价标准形"]


class MatrixApp:
    def __init__(self, root):
        self.root = root
        root.title("矩阵计算工具")
        root.resizable(False, False)

        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        # 操作选择
        ttk.Label(main, text="运算类型：").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.op_var = tk.StringVar(value=OPS[0])
        self.op_combo = ttk.Combobox(main, textvariable=self.op_var, values=OPS,
                                      state="readonly", width=16)
        self.op_combo.grid(row=0, column=1, sticky="w", pady=(0, 6))
        self.op_combo.bind("<<ComboboxSelected>>", self._on_op_change)

        # 维度输入区
        self.dim_entries = {}
        self.grids = []
        self.dim_frame = ttk.Frame(main)
        self.dim_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._build_dim_inputs()

        # 矩阵输入区
        self.input_frame = ttk.Frame(main)
        self.input_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # 计算按钮
        self.calc_btn = ttk.Button(main, text="计算", command=self._calculate)
        self.calc_btn.grid(row=3, column=0, columnspan=2, pady=(0, 8))

        # 结果显示区
        ttk.Label(main, text="计算结果：").grid(row=4, column=0, sticky="w")
        self.result_text = scrolledtext.ScrolledText(main, width=60, height=14,
                                                      font=("Courier New", 10))
        self.result_text.grid(row=5, column=0, columnspan=2, sticky="nsew")
        self.result_text.configure(state="disabled")

        self._on_op_change()

    def _build_dim_inputs(self):
        for w in self.dim_frame.winfo_children():
            w.destroy()
        self.dim_entries.clear()
        op = self.op_var.get()
        if op == "矩阵乘法":
            labels = [("m1", "矩阵A行数:"), ("n1", "矩阵A列数:"),
                      ("n2", "矩阵B行数:"), ("p2", "矩阵B列数:")]
        elif op == "等价标准形":
            labels = [("m", "行数 m:"), ("n", "列数 n:")]
        else:
            labels = [("n", "阶数 n:")]
        for i, (key, text) in enumerate(labels):
            ttk.Label(self.dim_frame, text=text).grid(row=i, column=0, sticky="w", padx=(0, 4), pady=2)
            entry = ttk.Entry(self.dim_frame, width=6)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.dim_entries[key] = entry
        ttk.Button(self.dim_frame, text="生成输入框", command=self._build_grids).grid(
            row=len(labels), column=0, columnspan=2, pady=(4, 0))

    def _on_op_change(self, event=None):
        self._build_dim_inputs()
        self._clear_grids()

    def _clear_grids(self):
        for w in self.input_frame.winfo_children():
            w.destroy()
        self.grids.clear()

    def _build_grids(self):
        self._clear_grids()
        op = self.op_var.get()
        try:
            dims = {k: int(v.get()) for k, v in self.dim_entries.items()}
            for k, v in dims.items():
                if v < 1:
                    raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的正整数维度。")
            return

        if op == "矩阵乘法":
            if dims["n1"] != dims["n2"]:
                messagebox.showerror("错误",
                    f"矩阵A的列数({dims['n1']})必须等于矩阵B的行数({dims['n2']})。")
                return
            specs = [("矩阵A", dims["m1"], dims["n1"]), ("矩阵B", dims["n2"], dims["p2"])]
        elif op == "等价标准形":
            specs = [("矩阵", dims["m"], dims["n"])]
        else:
            specs = [("矩阵", dims["n"], dims["n"])]

        for label, rows, cols in specs:
            ttk.Label(self.input_frame, text=f"{label} ({rows}x{cols})：",
                      font=("", 9, "bold")).pack(anchor="w", pady=(4, 2))
            frame = ttk.Frame(self.input_frame)
            frame.pack(anchor="w")
            entries = [[ttk.Entry(frame, width=8, justify="center") for _ in range(cols)]
                       for _ in range(rows)]
            for i, row_entries in enumerate(entries):
                for j, entry in enumerate(row_entries):
                    entry.grid(row=i, column=j, padx=2, pady=2)
            self.grids.append(entries)

    def _read_grid(self, entries):
        matrix = []
        for row_entries in entries:
            row = []
            for entry in row_entries:
                val = entry.get().strip()
                if not val:
                    raise ValueError("存在空单元格。")
                row.append(float(val))
            matrix.append(row)
        return matrix

    def _show_result(self, text):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

    def _calculate(self):
        op = self.op_var.get()
        if not self.grids:
            messagebox.showwarning("提示", "请先设置维度并点击「生成输入框」。")
            return
        try:
            if op == "矩阵乘法":
                a = self._read_grid(self.grids[0])
                b = self._read_grid(self.grids[1])
                result = multiply(a, b)
                out = f"矩阵A:\n{format_matrix(a)}\n\n矩阵B:\n{format_matrix(b)}\n\n乘积矩阵:\n{format_matrix(result)}"
            elif op == "等价标准形":
                m = self._read_grid(self.grids[0])
                std, rank = equivalent_standard_form(m)
                out = f"原矩阵:\n{format_matrix(m)}\n\n秩 r = {rank}\n\n等价标准形:\n{format_matrix(std)}"
            else:
                matrix = self._read_grid(self.grids[0])
                if op == "转置矩阵":
                    out = f"原矩阵:\n{format_matrix(matrix)}\n\n转置矩阵:\n{format_matrix(transpose(matrix))}"
                elif op == "逆矩阵":
                    inv = inverse(matrix)
                    inv_str = "该矩阵不可逆（行列式为0）" if inv is None else format_matrix(inv)
                    out = f"原矩阵:\n{format_matrix(matrix)}\n\n逆矩阵:\n{inv_str}"
                else:
                    det = determinant(matrix)
                    out = f"原矩阵:\n{format_matrix(matrix)}\n\n行列式 = {det:.6g}"
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return
        self._show_result(out)


if __name__ == "__main__":
    root = tk.Tk()
    MatrixApp(root)
    root.mainloop()
