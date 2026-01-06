# Константы для настройки бизнес-логики
DEFAULT_CURRENCY = "USD"
TAX_RATE = 0.21
MIN_PRICE = 0
MIN_QTY = 0

# Конфигурация скидочных купонов
COUPON_RATES = {
    "SAVE10": 0.10,
    "SAVE20": {"base": 0.05, "threshold": 200, "bonus": 0.20},
    "VIP": {"base": 10, "threshold": 100, "bonus": 50}
}


def parse_request(request: dict):
    """Извлекает данные из запроса."""
    user_id = request.get("user_id")
    items = request.get("items")
    coupon = request.get("coupon")
    currency = request.get("currency")
    return user_id, items, coupon, currency


def validate_request(user_id, items, currency):
    """Проверяет корректность входных данных."""
    if user_id is None:
        raise ValueError("user_id is required")

    if items is None:
        raise ValueError("items is required")

    if not isinstance(items, list):
        raise ValueError("items must be a list")

    if len(items) == 0:
        raise ValueError("items must not be empty")

    for item in items:
        if "price" not in item or "qty" not in item:
            raise ValueError("item must have price and qty")
        if item["price"] <= MIN_PRICE:
            raise ValueError("price must be positive")
        if item["qty"] <= MIN_QTY:
            raise ValueError("qty must be positive")


def calculate_subtotal(items):
    """Вычисляет общую сумму без скидок."""
    subtotal = 0
    for item in items:
        subtotal += item["price"] * item["qty"]
    return subtotal


def _apply_coupon_logic(subtotal, coupon):
    """Применяет логику расчета скидки для конкретного купона."""
    if coupon is None or coupon == "":
        return 0

    if coupon not in COUPON_RATES:
        raise ValueError("unknown coupon")

    coupon_config = COUPON_RATES[coupon]

    if isinstance(coupon_config, (int, float)):
        # Простой процентный купон (SAVE10)
        return int(subtotal * coupon_config)

    elif isinstance(coupon_config, dict):
        # Сложные купоны с условиями
        if coupon == "SAVE20":
            if subtotal >= coupon_config["threshold"]:
                return int(subtotal * coupon_config["bonus"])
            else:
                return int(subtotal * coupon_config["base"])

        elif coupon == "VIP":
            if subtotal >= coupon_config["threshold"]:
                return coupon_config["bonus"]
            else:
                return coupon_config["base"]

    return 0


def calculate_discount(subtotal, coupon):
    """Вычисляет размер скидки на основе купона."""
    return _apply_coupon_logic(subtotal, coupon)


def calculate_tax(amount):
    """Вычисляет налог для указанной суммы."""
    return int(amount * TAX_RATE)


def generate_order_id(user_id, items):
    """Генерирует идентификатор заказа."""
    return f"{user_id}-{len(items)}-X"


def process_checkout(request: dict) -> dict:
    """
    Обрабатывает заказ: парсит, валидирует, рассчитывает и возвращает результат.

    Args:
        request: Словарь с данными заказа

    Returns:
        Словарь с результатами обработки заказа
    """
    # 1. Парсинг запроса
    user_id, items, coupon, currency = parse_request(request)

    # 2. Валидация данных
    validate_request(user_id, items, currency)

    # 3. Расчеты
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(subtotal, coupon)
    total_after_discount = max(0, subtotal - discount)
    tax = calculate_tax(total_after_discount)
    total = total_after_discount + tax

    # 4. Подготовка результата
    order_id = generate_order_id(user_id, items)

    return {
        "order_id": order_id,
        "user_id": user_id,
        "currency": currency or DEFAULT_CURRENCY,
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total,
        "items_count": len(items),
    }