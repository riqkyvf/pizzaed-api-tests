import pytest
import requests

from config import BASE_URL


def test_get_products_returns_catalog():
    response = requests.get(
        f"{BASE_URL}/products",
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data["items"], list)
    assert data["items"]
    assert data["total"] == len(data["items"])


def test_get_product_by_id():
    response = requests.get(
        f"{BASE_URL}/products/pizza-margherita",
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    product = response.json()

    assert product["id"] == "pizza-margherita"


def test_get_nonexistent_product_returns_404():
    response = requests.get(
        f"{BASE_URL}/products/nonexistent-product",
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 404, response.text

    data = response.json()

    assert isinstance(data["error"], str)
    assert data["error"].strip()


@pytest.mark.parametrize("category", ["pizza", "drink", "dessert", "sauce"])
def test_get_products_filters_by_category(category):
    response = requests.get(
        f"{BASE_URL}/products",
        params={"category": category},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    products = response.json()["items"]

    assert products
    for product in products:
        assert product["category"] == category, product["id"]


@pytest.mark.parametrize("in_stock", [True, False])
def test_get_products_filters_by_stock(in_stock):
    response = requests.get(
        f"{BASE_URL}/products",
        params={"in_stock": str(in_stock).lower()},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    products = response.json()["items"]

    assert products
    for product in products:
        assert product["in_stock"] is in_stock, product["id"]


@pytest.mark.parametrize(
    "query",
    ["Маргарита", "Марг", "моцарелла", "вегетарианская", "соус", "несуществующийтовар"],
)
def test_get_products_search(query):
    catalog_response = requests.get(
        f"{BASE_URL}/products",
        timeout=10,
        allow_redirects=False,
    )

    assert catalog_response.status_code == 200, catalog_response.text

    catalog = catalog_response.json()["items"]
    assert catalog

    expected_ids = set()
    search_text = query.casefold()

    for product in catalog:
        searchable_values = [product["title"], product["description"]]
        searchable_values.extend(product["badges"])

        for value in searchable_values:
            if search_text in value.casefold():
                expected_ids.add(product["id"])
                break

    response = requests.get(
        f"{BASE_URL}/products",
        params={"q": query},
        timeout=10,
        allow_redirects=False,
    )

    assert response.status_code == 200, response.text

    products = response.json()["items"]
    actual_ids = {product["id"] for product in products}

    assert actual_ids == expected_ids
