class EllipticCurve:
    def __init__(self, a: int, b: int, p: int):
        """
        Создает эллиптическую кривую в формк y^2 = x^3 + ax + b (mod p)
        :param a: Коэффицент a
        :param b: Коэффицент b
        :param p: Простой модуль конечного поля
        """
        if (4 * a**3 + 27 * b**2) % p == 0:
            raise ValueError("The curve is singular, choose different a and b.")
        self.a = a
        self.b = b
        self.p = p
        self.j_invariant = self.calculate_j_invariant()

    def calculate_j_invariant(self) -> int:
        """
        Вычисляет инвариант кривой
        :return: J-Инвариант
        """
        numerator = 1728 * 4 * self.a**3
        denominator = (4 * self.a**3 + 27 * self.b**2) % self.p
        if denominator == 0:
            raise ValueError("Cannot compute j-invariant, denominator is zero.")
        return (numerator * pow(denominator, -1, self.p)) % self.p

    def is_point_on_curve(self, x, y) -> bool:
        """
        Проверяет, что точка (x, y) lлежит на кривой.
        :param x: x-координата
        :param y: y-координата
        :return: True если точка лежит на кривой, False если нет
        """
        return (y**2 - (x**3 + self.a * x + self.b)) % self.p == 0


    def _count_quadratic_residues(self, n: int) -> int:
        """
        Считает количество решений y^2 ≡ n (mod p).
        :param n: Правая часть уравнения кривой
        :return: Количество решений (0, 1, или 2)
        """
        if pow(n, (self.p - 1) // 2, self.p) != 1:
            return 0  # n не квадратичный вычет
        if n == 0:
            return 1  # n = 0, тогда y = 0 единственное решение
        return 2  # TДва различных решения для y

    def __str__(self) -> str:
        return f"EllipticCurve(a={self.a}, b={self.b}, p={self.p})"


class Point:
    def __init__(self, curve: EllipticCurve, x: int, y: int):
        """
        Новая точка на эллиптической кривой
        :param curve: Эллиптическая кривая
        :param x: x-координата точки
        :param y: y-координата точки
        """
        self.curve = curve
        self.x = x
        self.y = y

        # Проверка находится ли точка на кривой
        if not (self.x is None and self.y is None):
            if not curve.is_point_on_curve(x, y):
                raise ValueError("The point is not on the given curve.")

    def order(self) -> int:
        """
        Вычисляет порядок точки (минимальное n такое, что n * P = O).
        :return: Порядок точки
        """
        current = Point(self.curve, None, None)
        n = 1

        while True:
            current = n * self
            if current.x is None and current.y is None:
                return n
            n += 1

    def __neg__(self):
        """
        Возращает обратную точку
        :return: Новая точка -P
        """
        if self.x is None or self.y is None:  # точка на бесконечности
            return self
        return Point(self.curve, self.x, (-self.y) % self.curve.p)

    def __add__(self, other):
        """
        Сложение двух точек на кривой
        :param other: Другая точка
        :return: Новая точка P + Q
        """
        if not isinstance(other, Point):
            raise TypeError("The operand must be a Point.")

        if self.curve != other.curve:
            raise ValueError("Points must be on the same curve.")

        # Обработка точки на бесконечности
        if self.x is None and self.y is None:
            return other
        if other.x is None and other.y is None:
            return self

        if self.x == other.x and self.y != other.y:
            # P + (-P) = O (точка на бесконечности)
            return Point(self.curve, None, None)

        if self.x == other.x:
            slope = (3 * self.x**2 + self.curve.a) * pow(2 * self.y, -1, self.curve.p)
        else:
            slope = (other.y - self.y) * pow(other.x - self.x, -1, self.curve.p)

        slope %= self.curve.p

        x_r = (slope**2 - self.x - other.x) % self.curve.p
        y_r = (slope * (self.x - x_r) - self.y) % self.curve.p

        return Point(self.curve, x_r, y_r)

    def __rmul__(self, n: int):
        """
        Скалярное произведение числа на точку
        :param n: Скаляр
        :return: Новая точка n * P
        """
        result = Point(self.curve, None, None)
        temp = self

        while n > 0:
            if n % 2 == 1:
                result += temp
            temp += temp
            n //= 2

        return result

    def __repr__(self) -> str:
        if self.x is None or self.y is None:
            return "Point() on infinity"
        return f"Point({self.x}, {self.y}) on {self.curve.__str__()}"

    @staticmethod
    def land(curve: EllipticCurve, x: int) -> "Point":
        """
        Возращает точку по x координате на кривой
        :param x: x-координата
        :return: Точка на кривой
        """
        rhs = (x**3 + curve.a * x + curve.b) % curve.p

        if pow(rhs, (curve.p - 1) // 2, curve.p) != 1:
            raise ValueError("The point is not on the given curve.")

        y = Point.mod_sqrt(rhs, curve.p)

        return Point(curve, x, y)

    @staticmethod
    def mod_sqrt(a: int, p: int):
        """
        Вычисляет квадратный корень по модулю p, используя алгоритм Тонелли-Шанкса.
        :param a: Число для извлечения корня
        :param p: Простой модуль
        :return: Квадратный корень по модлю p
        """
        if pow(a, (p - 1) // 2, p) != 1:
            raise ValueError(f"No square root exists for {a} modulo {p}")

        if p % 4 == 3:
            return pow(a, (p + 1) // 4, p)

        s, q = 0, p - 1
        while q % 2 == 0:
            s += 1
            q //= 2

        z = 2
        while pow(z, (p - 1) // 2, p) != p - 1:
            z += 1

        m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)

        while t != 0 and t != 1:
            t2 = t
            for i in range(1, m):

                t2 = pow(t2, 2, p)
                if t2 == 1:
                    break
            b = pow(c, 2 ** (m - i - 1), p)
            m, c, t, r = i, pow(b, 2, p), (t * b * b) % p, (r * b) % p

        return r
