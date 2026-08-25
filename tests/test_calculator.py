import pytest
from app.calculator import add, subtract, multiply, divide, is_prime, mean


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_subtract():
    assert subtract(5, 3) == 2


def test_multiply():
    assert multiply(4, 3) == 12


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero_raises():
    with pytest.raises(ValueError):
        divide(10, 0)


@pytest.mark.parametrize("n,expected", [
    (1, False),
    (2, True),
    (17, True),
    (18, False),
    (0, False),
    (-5, False),
])
def test_is_prime(n, expected):
    assert is_prime(n) == expected


def test_mean():
    assert mean([1, 2, 3, 4]) == 2.5


def test_mean_empty_list_raises():
    with pytest.raises(ValueError):
        mean([])
