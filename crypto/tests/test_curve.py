import pytest
from hsecrypto.lib.curve import EllipticCurve, Point


@pytest.fixture
def curve():
    return EllipticCurve(a=1, b=1, p=23)


def test_elliptic_curve_initialization(curve: EllipticCurve):
    assert curve.a == 1
    assert curve.b == 1
    assert curve.p == 23
    assert curve.j_invariant is not None

    with pytest.raises(ValueError):
        EllipticCurve(a=0, b=0, p=23)


def test_is_point_on_curve(curve: EllipticCurve):

    assert curve.is_point_on_curve(3, 10)

    assert not curve.is_point_on_curve(1, 2)


def test_point_order(curve: EllipticCurve):
    point = Point(curve, 3, 10)

    assert point.order() == 28


def test_point_addition(curve: EllipticCurve):

    point1 = Point(curve, 3, -10)
    point2 = Point(curve, 3, 10)

    result_point = point1 + point2
    assert curve.is_point_on_curve(result_point.x, result_point.y)


def test_point_negation(curve: EllipticCurve):

    point = Point(curve, 3, 10)

    neg_point = -point
    assert curve.is_point_on_curve(neg_point.x, neg_point.y)
    assert neg_point.y == (-point.y) % curve.p


def test_point_multiplication(curve: EllipticCurve):
    point = Point(curve, 3, 10)

    result_point = 28 * point
    assert result_point.x is None and result_point.y is None


def test_point_compression(curve: EllipticCurve):
    point = Point(curve, 3, 10)

    compressed = point.compress()
    decompressed_point = Point.uncompress(curve, compressed)
    assert point.x == decompressed_point.x
    assert point.y == decompressed_point.y


def test_mod_sqrt(curve: EllipticCurve):
    a = 4
    sqrt = Point.mod_sqrt(a, curve.p)

    assert (sqrt**2) % curve.p == a


def test_point_on_infinity(curve: EllipticCurve):
    point_infinity = Point(curve, None, None)

    assert point_infinity + point_infinity == point_infinity
    assert point_infinity.__neg__() == point_infinity
