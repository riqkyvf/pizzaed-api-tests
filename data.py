from uuid import uuid4


def generate_customer():
    customer_id = uuid4()

    return {
        "customer_name": f"Тестовый покупатель {customer_id.hex}",
        "phone": f"+7900{customer_id.int % 10_000_000:07d}",
        "address": f"Тестовый город, улица {customer_id.hex}, дом 1",
    }
