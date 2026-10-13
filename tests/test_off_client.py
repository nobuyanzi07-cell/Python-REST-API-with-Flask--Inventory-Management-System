from unittest.mock import Mock, patch

import pytest
import requests

import off_client


def mock_response(json_data):
    res = Mock()
    res.json.return_value = json_data
    res.raise_for_status.return_value = None
    return res


@patch("off_client.requests.get")
def test_fetch_by_barcode_success(mock_get):
    mock_get.return_value = mock_response(
        {"status": 1, "product": {"code": "123", "product_name": "Cola", "brands": "Acme"}}
    )
    product = off_client.fetch_by_barcode("123")
    assert product["name"] == "Cola"
    assert product["brand"] == "Acme"
    assert product["barcode"] == "123"


@patch("off_client.requests.get")
def test_fetch_by_barcode_not_found(mock_get):
    mock_get.return_value = mock_response({"status": 0})
    assert off_client.fetch_by_barcode("000") is None


@patch("off_client.requests.get", side_effect=requests.ConnectionError("boom"))
def test_fetch_by_barcode_network_error(mock_get):
    with pytest.raises(off_client.ExternalAPIError):
        off_client.fetch_by_barcode("123")


@patch("off_client.requests.get")
def test_search_by_name(mock_get):
    mock_get.return_value = mock_response(
        {"products": [{"code": "1", "product_name": "Cola"}, {"code": "2", "product_name": "Cola Zero"}]}
    )
    results = off_client.search_by_name("cola")
    assert [p["name"] for p in results] == ["Cola", "Cola Zero"]


@patch("off_client.requests.get")
def test_search_by_name_empty(mock_get):
    mock_get.return_value = mock_response({"products": []})
    assert off_client.search_by_name("zzzz") == []


@patch("off_client.requests.get")
def test_missing_name_defaults_to_unknown(mock_get):
    mock_get.return_value = mock_response({"status": 1, "product": {"code": "9"}})
    assert off_client.fetch_by_barcode("9")["name"] == "Unknown"