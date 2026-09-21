"""矩阵运算核心，供命令行、Tkinter 与 Kivy 界面共用。"""


def transpose(matrix):
    rows, cols = len(matrix), len(matrix[0])
    return [[matrix[j][i] for j in range(rows)] for i in range(cols)]


def inverse(matrix):
    n = len(matrix)
    aug = [[float(matrix[i][j]) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)] for i in range(n)]
    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot_row][col]) < 1e-12:
            return None
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]
        pivot = aug[col][col]
        aug[col] = [v / pivot for v in aug[col]]
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                aug[row] = [a - factor * b for a, b in zip(aug[row], aug[col])]
    return [aug[i][n:] for i in range(n)]


def determinant(matrix):
    n = len(matrix)
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    det = 0
    for j in range(n):
        minor = [[matrix[i][k] for k in range(n) if k != j] for i in range(1, n)]
        det += ((-1) ** j) * matrix[0][j] * determinant(minor)
    return det


def multiply(a, b):
    cols_a = len(a[0])
    cols_b = len(b[0])
    return [[sum(a[i][k] * b[k][j] for k in range(cols_a)) for j in range(cols_b)] for i in range(len(a))]


def equivalent_standard_form(matrix):
    m, n = len(matrix), len(matrix[0])
    a = [[float(v) for v in row] for row in matrix]
    rank = 0
    for k in range(min(m, n)):
        best_r, best_c, best_val = k, k, abs(a[k][k])
        for i in range(k, m):
            for j in range(k, n):
                if abs(a[i][j]) > best_val:
                    best_r, best_c, best_val = i, j, abs(a[i][j])
        if best_val < 1e-12:
            break
        a[k], a[best_r] = a[best_r], a[k]
        for row in a:
            row[k], row[best_c] = row[best_c], row[k]
        pivot = a[k][k]
        a[k] = [v / pivot for v in a[k]]
        for i in range(m):
            if i != k and abs(a[i][k]) > 1e-12:
                factor = a[i][k]
                a[i] = [x - factor * y for x, y in zip(a[i], a[k])]
        for j in range(n):
            if j != k and abs(a[k][j]) > 1e-12:
                factor = a[k][j]
                for i in range(m):
                    a[i][j] -= factor * a[i][k]
        rank += 1
    return [[1.0 if (i == j and i < rank) else 0.0 for j in range(n)] for i in range(m)], rank


def format_matrix(matrix):
    lines = []
    for row in matrix:
        lines.append("  ".join(f"{v:>9.4f}" if isinstance(v, float) else f"{v:>9}" for v in row))
    return "\n".join(lines)


def fmt_value(v):
    """把数值渲染成紧凑字符串：整数不带小数点，浮点最多保留 4 位。"""
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return str(v)
