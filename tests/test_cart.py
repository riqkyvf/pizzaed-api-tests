import pytest
import requests

from config import BASE_URL


def test_delivery_is_free_at_exact_threshold(session_headers):
    products = [
        ("pizza-four-cheese", 1),
        ("pizza-margherita", 1),
        ("sauce-garlic", 4),
    ]
    for product_id, quantity in products:
        response = requests.post(
            f"{BASE_URL}/cart",
            headers=session_headers,
            json={"product_id": product_id, "quantity": quantity},
            timeout=10,
            allow_redirects=False,
        )
        assert response.status_code == 201, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    cart = response.json()["cart"]
    actual_quantities = {item["product_id"]: item["quantity"] for item in cart["items"]}
    assert actual_quantities == dict(products)
    assert cart["subtotal"] == 1500
    assert cart["discount"] == 0
    assert cart["delivery"] == 0
    assert cart["total"] == 1500


def test_decreasing_quantity_restores_paid_delivery(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 3},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    cart = response.json()["cart"]
    assert cart["subtotal"] == 1560
    assert cart["delivery"] == 0
    assert cart["total"] == 1560

    response = requests.patch(
        f"{BASE_URL}/cart/pizza-margherita",
        headers=session_headers,
        json={"quantity": 2},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

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
    assert cart["items"][0]["quantity"] == 2
    assert cart["subtotal"] == 1040
    assert cart["discount"] == 0
    assert cart["delivery"] == 199
    assert cart["total"] == 1239


@pytest.mark.parametrize("quantity", [-1, 21, 1.5])
def test_add_product_rejects_invalid_quantity(session_headers, quantity):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text
    cart_before = response.json()["cart"]

    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": quantity},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text
    assert response.json()["cart"] == cart_before


def test_repeated_add_does_not_exceed_quantity_limit(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 20},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    cart_before = response.json()["cart"]
    assert len(cart_before["items"]) == 1
    assert cart_before["items"][0]["product_id"] == "pizza-margherita"
    assert cart_before["items"][0]["quantity"] == 20
    assert cart_before["subtotal"] == 10400
    assert cart_before["discount"] == 0
    assert cart_before["delivery"] == 0
    assert cart_before["total"] == 10400

    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text
    assert response.json()["cart"] == cart_before


def test_add_unavailable_product_is_rejected(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "dessert-cheesecake", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 422, response.text
    assert response.json()["error"]

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    cart = response.json()["cart"]

    assert cart["items"] == []
    assert cart["subtotal"] == 0
    assert cart["total"] == 0


def test_delete_product_keeps_other_items(session_headers):
    for product_id in ["pizza-margherita", "drink-cola"]:
        response = requests.post(
            f"{BASE_URL}/cart",
            headers=session_headers,
            json={"product_id": product_id, "quantity": 1},
            timeout=10,
            allow_redirects=False,
        )

        assert response.status_code == 201, response.text

    response = requests.delete(
        f"{BASE_URL}/cart/pizza-margherita",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    cart = response.json()["cart"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == "drink-cola"
    assert cart["items"][0]["quantity"] == 1
    assert cart["subtotal"] == 160
    assert cart["discount"] == 0
    assert cart["delivery"] == 199
    assert cart["total"] == 359


def test_delete_last_product_clears_cart(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 201, response.text

    response = requests.delete(
        f"{BASE_URL}/cart/pizza-margherita",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )
    assert response.status_code == 200, response.text

    cart = response.json()["cart"]
    assert cart["items"] == []
    assert cart["subtotal"] == 0
    assert cart["discount"] == 0
    assert cart["delivery"] == 0
    assert cart["total"] == 0


def test_new_session_has_empty_cart(session_headers):
    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    cart = response.json()["cart"]

    assert cart["items"] == []
    assert cart["subtotal"] == 0
    assert cart["discount"] == 0
    assert cart["total"] == 0


def test_add_product_to_cart(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 201, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    cart = response.json()["cart"]

    assert len(cart["items"]) == 1

    item = cart["items"][0]
    assert item["product_id"] == "pizza-margherita"
    assert item["quantity"] == 1
    assert cart["subtotal"] == 520
    assert cart["discount"] == 0
    assert cart["delivery"] == 199
    assert cart["total"] == 719


def test_zero_quantity_removes_product(session_headers):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 201, response.text

    response = requests.patch(
        f"{BASE_URL}/cart/pizza-margherita",
        headers=session_headers,
        json={"quantity": 0},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    cart = response.json()["cart"]

    assert cart["items"] == []
    assert cart["subtotal"] == 0
    assert cart["discount"] == 0
    assert cart["delivery"] == 0
    assert cart["total"] == 0


def test_add_same_product_increases_quantity(session_headers):
    for _ in range(2):
        response = requests.post(
            f"{BASE_URL}/cart",
            headers=session_headers,
            json={"product_id": "pizza-margherita", "quantity": 1},
            timeout=10,
            allow_redirects=False,
        )

        assert response.status_code == 201, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    cart = response.json()["cart"]

    assert len(cart["items"]) == 1

    item = cart["items"][0]
    assert item["product_id"] == "pizza-margherita"
    assert item["quantity"] == 2
    assert cart["subtotal"] == 1040
    assert cart["discount"] == 0
    assert cart["delivery"] == 199
    assert cart["total"] == 1239


@pytest.mark.parametrize(
    "quantity, subtotal, delivery, total",
    [
        (2, 1040, 199, 1239),
        (3, 1560, 0, 1560),
    ],
)
def test_update_cart_quantity(session_headers, quantity, subtotal, delivery, total):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 201, response.text

    response = requests.patch(
        f"{BASE_URL}/cart/pizza-margherita",
        headers=session_headers,
        json={"quantity": quantity},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    response = requests.get(
        f"{BASE_URL}/cart",
        headers=session_headers,
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    cart = response.json()["cart"]

    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == quantity
    assert cart["subtotal"] == subtotal
    assert cart["delivery"] == delivery
    assert cart["total"] == total


@pytest.mark.parametrize("quantity", [-1, 21, 1.5])
def test_update_cart_rejects_invalid_quantity(session_headers, quantity):
    response = requests.post(
        f"{BASE_URL}/cart",
        headers=session_headers,
        json={"product_id": "pizza-margherita", "quantity": 1},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 201, response.text

    response = requests.patch(
        f"{BASE_URL}/cart/pizza-margherita",
        headers=session_headers,
        json={"quantity": quantity},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 422, response.text
    assert response.json()["error"]

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
