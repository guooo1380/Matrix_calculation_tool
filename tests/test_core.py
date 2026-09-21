"""mathtools.core 的单元测试。

运行： pip install -e . 后执行 python -m unittest discover -s tests -p "test_*.py" -v
      未安装时可用 PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"
"""

import unittest

from mathtools.core import (
    determinant,
    equivalent_standard_form,
    fmt_value,
    format_matrix,
    inverse,
    multiply,
    transpose,
)


def assert_matrix_equal(test, got, want, tol=1e-9):
    test.assertEqual(len(got), len(want), f"行数不符：{got} / {want}")
    for i, (got_row, want_row) in enumerate(zip(got, want)):
        test.assertEqual(len(got_row), len(want_row), f"第 {i} 行列数不符")
        for j, (g, w) in enumerate(zip(got_row, want_row)):
            test.assertAlmostEqual(g, w, delta=tol, msg=f"第 {i} 行第 {j} 列不符")


class TestTranspose(unittest.TestCase):
    def test_square(self):
        self.assertEqual(transpose([[1, 2], [3, 4]]), [[1, 3], [2, 4]])

    def test_non_square(self):
        got = transpose([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(got, [[1, 4], [2, 5], [3, 6]])

    def test_single_row(self):
        self.assertEqual(transpose([[7, 8, 9]]), [[7], [8], [9]])


class TestInverse(unittest.TestCase):
    def test_2x2(self):
        got = inverse([[4, 7], [2, 6]])
        assert_matrix_equal(self, got, [[0.6, -0.7], [-0.2, 0.4]])

    def test_3x3(self):
        got = inverse([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
        assert_matrix_equal(self, got, [[-24, 18, 5], [20, -15, -4], [-5, 4, 1]])

    def test_singular_returns_none(self):
        self.assertIsNone(inverse([[1, 2], [2, 4]]))

    def test_zero_matrix_returns_none(self):
        self.assertIsNone(inverse([[0, 0], [0, 0]]))

    def test_product_is_identity(self):
        a = [[2, 1, 0], [1, 3, 1], [0, 1, 2]]
        product = multiply(a, inverse(a))
        assert_matrix_equal(self, product, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], tol=1e-9)


class TestDeterminant(unittest.TestCase):
    def test_1x1(self):
        self.assertEqual(determinant([[5]]), 5)

    def test_2x2(self):
        self.assertEqual(determinant([[1, 2], [3, 4]]), -2)

    def test_3x3(self):
        self.assertEqual(determinant([[6, 1, 1], [4, -2, 5], [2, 8, 7]]), -306)

    def test_singular_is_zero(self):
        self.assertAlmostEqual(determinant([[1, 2], [2, 4]]), 0, delta=1e-9)

    def test_identity_is_one(self):
        identity = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
        self.assertEqual(determinant(identity), 1)


class TestMultiply(unittest.TestCase):
    def test_2x2(self):
        got = multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
        self.assertEqual(got, [[19, 22], [43, 50]])

    def test_non_square_shape(self):
        got = multiply([[1, 2, 3], [4, 5, 6]], [[1, 0], [0, 1], [1, 1]])
        self.assertEqual(len(got), 2)
        self.assertEqual(len(got[0]), 2)
        self.assertEqual(got, [[4, 5], [10, 11]])

    def test_identity(self):
        a = [[3, 1], [2, 4]]
        self.assertEqual(multiply(a, [[1, 0], [0, 1]]), a)


class TestEquivalentStandardForm(unittest.TestCase):
    def test_rank_deficient(self):
        std, rank = equivalent_standard_form([[1, 2], [2, 4]])
        self.assertEqual(rank, 1)
        assert_matrix_equal(self, std, [[1, 0], [0, 0]])

    def test_full_rank(self):
        std, rank = equivalent_standard_form([[1, 2], [3, 4]])
        self.assertEqual(rank, 2)
        assert_matrix_equal(self, std, [[1, 0], [0, 1]])

    def test_wide_matrix(self):
        std, rank = equivalent_standard_form([[1, 2, 3], [2, 4, 6]])
        self.assertEqual(rank, 1)
        assert_matrix_equal(self, std, [[1, 0, 0], [0, 0, 0]])

    def test_tall_matrix(self):
        std, rank = equivalent_standard_form([[1, 2], [2, 4], [1, 1]])
        self.assertEqual(rank, 2)
        assert_matrix_equal(self, std, [[1, 0], [0, 1], [0, 0]])

    def test_zero_matrix(self):
        std, rank = equivalent_standard_form([[0, 0], [0, 0]])
        self.assertEqual(rank, 0)
        assert_matrix_equal(self, std, [[0, 0], [0, 0]])


class TestFormatting(unittest.TestCase):
    def test_fmt_value_integer(self):
        self.assertEqual(fmt_value(3), "3")
        self.assertEqual(fmt_value(2.0), "2")
        self.assertEqual(fmt_value(-5.0), "-5")

    def test_fmt_value_decimal(self):
        self.assertEqual(fmt_value(0.6), "0.6")
        self.assertEqual(fmt_value(-0.7), "-0.7")
        self.assertEqual(fmt_value(1 / 3), "0.3333")

    def test_format_matrix_shape(self):
        rows = format_matrix([[1, 2.5], [3, 4]]).splitlines()
        self.assertEqual([line.split() for line in rows],
                         [["1", "2.5000"], ["3", "4"]])


if __name__ == "__main__":
    unittest.main()
