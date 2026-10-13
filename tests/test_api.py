from unittest.mock import patch

import pytest

import app as app_module
from off_client import ExternalAPIError

PRODUCT = {
    "name": "Nutella",
    "brand": "Ferrero",
    "barcode": "3017620422003",
    "category": "Spreads",
    "ingredients": "Sugar, palm oil",
}


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    app_module.reset_inventory()
    with app_module.app.test_client() as c:
        yield c


def make_item(client, **overrides):
    body = {"name": "Milk", "price": 1.5, "quantity": 10}
    body.update(overrides)
    return client.post("/inventory", json=body)


# ---- Create ----
def test_add_item(client):
    res = make_item(client)
    assert res.status_code == 201
    assert res.get_json()["id"] == 1
    assert res.get_json()["name"] == "Milk"


def test_add_item_missing_name(client):
    assert client.post("/inventory", json={"price": 1}).status_code == 400


def test_add_item_invalid_price(client):
    assert make_item(client, price=-5).status_code == 400


def test_add_item_invalid_quantity(client):
    assert make_item(client, quantity="ten").status_code == 400


# ---- Read ----
def test_list_items_empty(client):
    res = client.get("/inventory")
    assert res.status_code == 200
    assert res.get_json() == []


def test_list_items(client):
    make_item(client)
    make_item(client, name="Bread")
    assert len(client.get("/inventory").get_json()) == 2


def test_list_filter_by_name(client):
    make_item(client)
    make_item(client, name="Bread")
    res = client.get("/inventory?name=bre")
    assert [i["name"] for i in res.get_json()] == ["Bread"]


def test_get_item(client):
    make_item(client)
    res = client.get("/inventory/1")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Milk"


def test_get_item_not_found(client):
    assert client.get("/inventory/99").status_code == 404


# ---- Update ----
def test_update_item(client):
    make_item(client)
    res = client.patch("/inventory/1", json={"quantity": 3, "price": 2.0})
    assert res.status_code == 200
    assert res.get_json()["quantity"] == 3
    assert res.get_json()["name"] == "Milk"


def test_update_item_not_found(client):
    assert client.patch("/inventory/99", json={"quantity": 1}).status_code == 404


def test_update_item_empty_body(client):
    make_item(client)
    assert client.patch("/inventory/1", json={}).status_code == 400


def test_update_item_invalid(client):
    make_item(client)
    assert client.patch("/inventory/1", json={"price": "free"}).status_code == 400


# ---- Delete ----
def test_delete_item(client):
    make_item(client)
    assert client.delete("/inventory/1").status_code == 200
    assert client.get("/inventory/1").status_code == 404


def test_delete_item_not_found(client):
    assert client.delete("/inventory/99").status_code == 404


# ---- External API routes ----
@patch("app.off_client.fetch_by_barcode", return_value=PRODUCT)
def test_external_barcode(mock_fetch, client):
    res = client.get("/external/barcode/3017620422003")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Nutella"


@patch("app.off_client.fetch_by_barcode", return_value=None)
def test_external_barcode_not_found(mock_fetch, client):
    assert client.get("/external/barcode/000").status_code == 404


@patch("app.off_client.fetch_by_barcode", side_effect=ExternalAPIError("down"))
def test_external_barcode_api_error(mock_fetch, client):
    assert client.get("/external/barcode/000").status_code == 502


@patch("app.off_client.search_by_name", return_value=[PRODUCT])
def test_external_search(mock_search, client):
    res = client.get("/external/search?name=nutella")
    assert res.status_code == 200
    assert len(res.get_json()) == 1


def test_external_search_requires_name(client):
    assert client.get("/external/search").status_code == 400


@patch("app.off_client.search_by_name", side_effect=ExternalAPIError("down"))
def test_external_search_api_error(mock_search, client):
    assert client.get("/external/search?name=x").status_code == 502


# ---- Import ----
@patch("app.off_client.fetch_by_barcode", return_value=dict(PRODUCT))
def test_import_by_barcode(mock_fetch, client):
    res = client.post("/inventory/import", json={"barcode": "3017620422003", "price": 4.5, "quantity": 7})
    assert res.status_code == 201
    body = res.get_json()
    assert body["name"] == "Nutella"
    assert body["price"] == 4.5
    assert body["quantity"] == 7
    assert client.get("/inventory/1").status_code == 200


@patch("app.off_client.search_by_name", return_value=[dict(PRODUCT)])
def test_import_by_name(mock_search, client):
    res = client.post("/inventory/import", json={"name": "nutella"})
    assert res.status_code == 201
    assert res.get_json()["brand"] == "Ferrero"


@patch("app.off_client.fetch_by_barcode", return_value=None)
def test_import_not_found(mock_fetch, client):
    assert client.post("/inventory/import", json={"barcode": "000"}).status_code == 404
    assert client.get("/inventory").get_json() == []


def test_import_requires_identifier(client):
    assert client.post("/inventory/import", json={}).status_code == 400


@patch("app.off_client.fetch_by_barcode", side_effect=ExternalAPIError("down"))
def test_import_api_error(mock_fetch, client):
    assert client.post("/inventory/import", json={"barcode": "1"}).status_code == 502


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}