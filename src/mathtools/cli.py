"""矩阵运算命令行工具：交互式输入，结果打印到终端。"""

from mathtools.core import (
    determinant,
    equivalent_standard_form,
    format_matrix,
    inverse,
    multiply,
    transpose,
)


def print_matrix(matrix):
    print(format_matrix(matrix))


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
