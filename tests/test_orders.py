import pytest
import requests

from config import BASE_URL
from data import generate_customer


class ContactFieldTypeBug(AssertionError):
    """Известная серверная ошибка BUG-004 при неверном типе контактного поля."""


@pytest.mark.xfail(
    reason="BUG-004: docs/bugs/BUG-004-order-field-types.md",
    strict=True,
    raises=ContactFieldTypeBug,
)
@pytest.mark.parametrize("field", ["customer_name", "phone", "address"])
@pytest.mark.parametrize(
    "value",
    [pytest.param(True, id="boolean"), pytest.param(123, id="number")],
)
def test_create_order_rejects_invalid_contact_types(session_headers, field, value):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    customer = generate_customer()
    customer[field] = value

    response = requests.post(
        f"{BASE_URL}/orders",
        headers=session_headers,
        json=customer,
        timeout=10,
        allow_redirects=False,
    )

    if response.status_code == 500:
        error = response.json().get("error")
        if error == f"t.{field}?.trim is not a function":
            raise ContactFieldTypeBug(error)

    assert response.status_code == 422, response.text
    assert field in response.json()["error"]


def test_discount_does_not_cancel_free_delivery(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 3},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    customer = generate_customer()
    customer["promo_code"] = "QA60"

    response = requests.post(
        f"{BASE_URL}/orders",
        headers=session_headers,
        json=customer,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    order = response.json()
    assert order["status"] == "created"

    cart = order["cart"]
    assert cart["subtotal"] == 1560
    assert cart["discount"] == 156
    assert cart["delivery"] == 0
    assert cart["total"] == 1404


@pytest.mark.parametrize(
    "promo_code, discount, total",
    [
        pytest.param("QA60", 52, 667, id="valid"),
        pytest.param("qa60", 52, 667, id="lowercase"),
        pytest.param("Qa60", 52, 667, id="mixed-case"),
        pytest.param("  QA60  ", 52, 667, id="trimmed"),
        pytest.param("TEST", 0, 719, id="invalid"),
        pytest.param("", 0, 719, id="empty"),
        pytest.param("   ", 0, 719, id="spaces"),
    ],
)
def test_create_order_with_promo_code(session_headers, promo_code, discount, total):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    customer = generate_customer()
    customer["promo_code"] = promo_code

    response = requests.post(
        f"{BASE_URL}/orders",
        headers=session_headers,
        json=customer,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    order = response.json()
    assert order["status"] == "created"

    cart = order["cart"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == "pizza-margherita"
    assert cart["items"][0]["quantity"] == 1
    assert cart["subtotal"] == 520
    assert cart["discount"] == discount
    assert cart["delivery"] == 199
    assert cart["total"] == total


@pytest.mark.parametrize("field", ["customer_name", "phone", "address"])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="missing"),
        pytest.param("", id="empty"),
        pytest.param("   ", id="spaces"),
    ],
)
def test_create_order_rejects_missing_customer_data(session_headers, field, value):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    customer = generate_customer()
    if value is None:
        del customer[field]
    else:
        customer[field] = value

    response = requests.post(
        f"{BASE_URL}/orders",
        headers=session_headers,
        json=customer,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 422, response.text
    assert field in response.json()["error"]

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    cart = response.json()["cart"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == "pizza-margherita"
    assert cart["items"][0]["quantity"] == 1
    assert cart["subtotal"] == 520
    assert cart["total"] == 719

    response = requests.get(
        f"{BASE_URL}/orders",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text
    history = response.json()
    assert history["items"] == []
    assert history["total"] == 0


def test_create_order_rejects_empty_cart(session_headers):
    response = requests.post(
        f"{BASE_URL}/orders",
        headers=session_headers,
        json=generate_customer(),
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 422, response.text
    assert response.json()["error"] == "Корзина пуста"

    response = requests.get(
        f"{BASE_URL}/orders",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text
    history = response.json()
    assert history["items"] == []
    assert history["total"] == 0


def test_create_order_clears_cart(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 201, response.text

    customer = generate_customer()
    response = requests.post(
        f"{BASE_URL}/orders",
        headers=session_headers,
        json=customer,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 201, response.text

    order = response.json()

    assert order["id"]
    assert order["number"]
    assert order["status"] == "created"
    for field, value in customer.items():
        assert order[field] == value

    cart = order["cart"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == "pizza-margherita"
    assert cart["items"][0]["quantity"] == 1
    assert cart["subtotal"] == 520
    assert cart["discount"] == 0
    assert cart["delivery"] == 199
    assert cart["total"] == 719

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    cart = response.json()["cart"]
    assert cart["items"] == []
    assert cart["total"] == 0
