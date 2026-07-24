def factorial(n):
    \"\"\"Вычисляет факториал числа n.\"\"\"
    if n < 0:
        raise ValueError(\"Факториал определен только для неотрицательных чисел.\")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


# Пример использования
if __name__ == \"__main__\":
    number = 5
    print(f\"Факториал {number} равен {factorial(number)}\")