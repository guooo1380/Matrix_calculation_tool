def transpose(matrix):
    n = len(matrix)
    return [[matrix[j][i] for j in range(n)] for i in range(n)]


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
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    result = [[sum(a[i][k] * b[k][j] for k in range(cols_a)) for j in range(cols_b)] for i in range(rows_a)]
    return result


def equivalent_standard_form(matrix):
    m, n = len(matrix), len(matrix[0])
    a = [[float(v) for v in row] for row in matrix]
    rank = 0
    for k in range(min(m, n)):
        # 在剩余子矩阵中找最大主元
        best_r, best_c, best_val = k, k, abs(a[k][k])
        for i in range(k, m):
            for j in range(k, n):
                if abs(a[i][j]) > best_val:
                    best_r, best_c, best_val = i, j, abs(a[i][j])
        if best_val < 1e-12:
            break
        # 交换行和列，将主元移到 (k, k)
        a[k], a[best_r] = a[best_r], a[k]
        for row in a:
            row[k], row[best_c] = row[best_c], row[k]
        # 归一化主元行
        pivot = a[k][k]
        a[k] = [v / pivot for v in a[k]]
        # 消去主元列其余元素
        for i in range(m):
            if i != k and abs(a[i][k]) > 1e-12:
                factor = a[i][k]
                a[i] = [x - factor * y for x, y in zip(a[i], a[k])]
        # 消去主元行其余元素
        for j in range(n):
            if j != k and abs(a[k][j]) > 1e-12:
                factor = a[k][j]
                for i in range(m):
                    a[i][j] -= factor * a[i][k]
        rank += 1
    # 构造等价标准形 [I_r 0; 0 0]
    return [[1.0 if (i == j and i < rank) else 0.0 for j in range(n)] for i in range(m)], rank


def print_matrix(matrix):
    for row in matrix:
        print("  ".join(f"{v:>8.4f}" if isinstance(v, float) else f"{v:>8}" for v in row))


def read_matrix(rows, cols, label="矩阵"):
    print(f"\n请按行输入 {rows}x{cols} {label} 的元素（用空格分隔）:")
    matrix = []
    for i in range(rows):
        while True:
            row = input(f"  第 {i + 1} 行: ").split()
            if len(row) != cols:
                print(f"  需要 {cols} 个元素，请重新输入。")
                continue
            try:
                matrix.append([float(x) if "." in x else int(x) for x in row])
            except ValueError:
                print("  包含非法字符，请重新输入。")
                continue
            break
    return matrix


def read_int(prompt, valid=None):
    while True:
        try:
            val = int(input(prompt))
            if valid is not None and val not in valid:
                print(f"  请输入 {sorted(valid)} 中的一个值。\n")
                continue
            if val < 1:
                print("  必须为正整数。\n")
                continue
            return val
        except ValueError:
            print("  请输入有效整数。\n")


def main():
    print("请选择运算类型：")
    print("  1 - 转置矩阵")
    print("  2 - 逆矩阵")
    print("  3 - 行列式")
    print("  4 - 矩阵乘法")
    print("  5 - 等价标准形")
    while True:
        choice = input("请输入选项(1/2/3/4/5): ").strip()
        if choice in ("1", "2", "3", "4", "5"):
            break
        print("无效选项，请输入 1、2、3、4 或 5。\n")

    if choice == "4":
        print("\n请输入第一个矩阵的行列数：")
        m = read_int("  行数 m: ")
        n = read_int("  列数 n: ")
        print("\n请输入第二个矩阵的行列数：")
        n2 = read_int("  行数 n: ")
        p = read_int("  列数 p: ")
        if n != n2:
            print(f"\n错误：第一个矩阵的列数({n})必须等于第二个矩阵的行数({n2})，无法相乘。")
            return
        a = read_matrix(m, n, "第一个矩阵")
        b = read_matrix(n2, p, "第二个矩阵")
        print(f"\n第一个矩阵({m}x{n}):")
        print_matrix(a)
        print(f"\n第二个矩阵({n2}x{p}):")
        print_matrix(b)
        print(f"\n乘积矩阵({m}x{p}):")
        print_matrix(multiply(a, b))
        return

    if choice == "5":
        print("\n请输入矩阵的行列数：")
        m = read_int("  行数 m: ")
        n = read_int("  列数 n: ")
        matrix = read_matrix(m, n)
        print(f"\n原矩阵:")
        print_matrix(matrix)
        std, rank = equivalent_standard_form(matrix)
        print(f"\n矩阵的秩 r = {rank}")
        print(f"\n等价标准形:")
        print_matrix(std)
        return

    if choice == "2":
        n = read_int("\n请输入方阵的阶数(任意正整数): ")
    else:
        n = read_int("\n请输入方阵的阶数(2/3/4/5): ", valid={2, 3, 4, 5})
    matrix = read_matrix(n, n)

    print(f"\n原矩阵:")
    print_matrix(matrix)

    if choice == "1":
        print(f"\n转置矩阵:")
        print_matrix(transpose(matrix))
    elif choice == "2":
        inv = inverse(matrix)
        print(f"\n逆矩阵:")
        if inv is None:
            print("  该矩阵不可逆（行列式为0）")
        else:
            print_matrix(inv)
    else:
        print(f"\n行列式 = {determinant(matrix)}")


if __name__ == "__main__":
    main()
