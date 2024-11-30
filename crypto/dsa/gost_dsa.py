from lib.curve import EllipticCurve, Point
from random import randint
from hashlib import sha256


class GostDSA:
    def __init__(self):
        """
        Создает имплементацию цифровой подписи по ГОСТ 34.10-2018
        """

        p = 0x8000000000000000000000000000000000000000000000000000000000000431
        a = 0x07
        b = 0x5FBFF498AA938CE739B8E022FBAFEF40563F6E6A3472FC2A514C0CE9DAE23B7E
        self.curve = EllipticCurve(a=a, b=b, p=p)
        self.P = Point(
            self.curve,
            x=2,
            y=0x8E2A8A0E65147D4BD6316030E16D19C85C97F0A9CA267122B96ABBCEA7E8FC8,
        )
        self.q = 0x8000000000000000000000000000000150FE8A1892976154C59CFC193ACCF5B3
        self.m = 0x8000000000000000000000000000000150FE8A1892976154C59CFC193ACCF5B3

    def generate_key_pair(self) -> tuple[int, Point]:
        """
        Генерирует ключевую пару: закрытый и открытый ключи
        
        :return: Кортеж, содержащий закрытый и открытый ключи
        """
        d = randint(0, self.q)
        Q = d * self.P
        return d, Q

    def sign(self, message: bytes, d: int) -> str:
        """
        Возвращает цифровую подпись в виде шестнадцетиричной строки по переданному сообщению и закрытому ключу
        
        :param message: Подписываемое сообщение в байтах
        :param d: Закрытый ключ в виде числа
        :return: Шестнадцетиричная строка из конкатенированных двух векторов (r|s)
        """

        z = int(sha256(message).hexdigest(), 16)
        e = z % self.q
        if e == 0:
            e = 1
        s = 0
        r, k = self._find_r()
        while s == 0:
            r, k = self._find_r()
            s = (r * d + k * e) % self.q

        sig = bytes.fromhex(hex(r)[2:].zfill(64)) + bytes.fromhex(hex(s)[2:].zfill(64))
        return sig.hex()

    def check(self, signature: str, message: bytes, Q: Point) -> bool:
        """
        Проверяет валидность цифровой подписи

        :param signature: Цифровая подпись в виде шестнадцетиричной строки
        :param message: Изначальное сообщение в байтах
        :param Q: Открытый ключ для проверки подписи

        :return: True, если подпись валидная, False если нет
        """
        r_b, s_b = bytes.fromhex(signature[: len(signature) // 2]), bytes.fromhex(
            signature[len(signature) // 2 :]
        )
        r = int.from_bytes(r_b)
        s = int.from_bytes(s_b)

        z = int(sha256(message).hexdigest(), 16)
        e = z % self.q
        if e == 0:
            e = 1
        V = pow(e, -1, self.q)
        z1 = s * V % self.q
        z2 = -r * V % self.q

        C = z1 * self.P + z2 * Q
        R = C.x % self.q

        return R == r

    def _find_r(self) -> tuple[int, int]:
        r = 0
        k = 0
        while r == 0:
            k = randint(0, self.q)
            C = k * self.P
            r = C.x % self.q

        return r, k
