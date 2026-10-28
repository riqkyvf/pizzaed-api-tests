import requests

from config import BASE_URL
from data import generate_customer


def test_carts_are_isolated_between_sessions(session_headers_pair):
    products = ["pizza-margherita", "drink-cola"]

    for headers, product_id in zip(session_headers_pair, products, strict=True):
        response = requests.post(
            f"{BASE_URL}/cart",
            headers=headers,
            json={"product_id": product_id, "quantity": 1},
            timeout=10,
            allow_redirects=False,
        )
        assert response.status_code == 201, response.text

    for headers, product_id in zip(session_headers_pair, products, strict=True):
        response = requests.get(
            f"{BASE_URL}/cart",
            headers=headers,
            timeout=10,
            allow_redirects=False,
        )
        assert response.status_code == 200, response.text

        cart = response.json()["cart"]
        assert len(cart["items"]) == 1
        assert cart["items"][0]["product_id"] == product_id
        assert cart["items"][0]["quantity"] == 1


def test_orders_are_isolated_between_sessions(session_headers_pair):
    products = ["pizza-margherita", "drink-cola"]
    order_ids = []

    for headers, product_id in zip(session_headers_pair, products, strict=True):
        response = requests.post(
            f"{BASE_URL}/cart",
            headers=headers,
            json={"product_id": product_id, "quantity": 1},
            timeout=10,
            allow_redirects=False,
        )
        assert response.status_code == 201, response.text

        response = requests.post(
            f"{BASE_URL}/orders",
            headers=headers,
            json=generate_customer(),
            timeout=10,
            allow_redirects=False,
        )
        assert response.status_code == 201, response.text
        order = response.json()
        assert order["status"] == "created"
        order_ids.append(order["id"])

    assert order_ids[0] != order_ids[1]

    for headers, order_id in zip(session_headers_pair, order_ids, strict=True):
        response = requests.get(
            f"{BASE_URL}/orders",
            headers=headers,
            timeout=10,
            allow_redirects=False,
        )
        assert response.status_code == 200, response.text

        history = response.json()
        assert history["total"] == 1
        assert len(history["items"]) == 1
        assert history["items"][0]["id"] == order_id
