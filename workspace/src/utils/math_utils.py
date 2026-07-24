"""Модуль с математическими утилитами."""

from typing import Union


async def sum_numbers(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Складывает два числа.

    Args:
        a: Первое слагаемое.
        b: Второе слагаемое.

    Returns:
        Сумма двух чисел.
    """
    return a + b
