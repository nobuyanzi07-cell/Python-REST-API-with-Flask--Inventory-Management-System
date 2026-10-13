from unittest.mock import patch

import cli

ITEM = {"id": 1, "name": "Milk", "brand": "", "barcode": "", "price": 1.5, "quantity": 10}


def run(argv, status=200, data=None):
    with patch("cli.api", return_value=(status, data if data is not None else {})) as mock_api:
        code = cli.main(argv)
    return code, mock_api


def test_list_prints_items(capsys):
    code, _ = run(["list"], data=[ITEM])
    assert code == 0
    assert "Milk" in capsys.readouterr().out


def test_list_empty(capsys):
    run(["list"], data=[])
    assert "No items found" in capsys.readouterr().out


def test_view_calls_correct_endpoint():
    _, mock_api = run(["view", "1"], data=ITEM)
    mock_api.assert_called_once_with("GET", "/inventory/1")


def test_view_not_found(capsys):
    code, _ = run(["view", "9"], status=404, data={"error": "Item not found"})
    assert code == 1
    assert "Item not found" in capsys.readouterr().out


def test_add_sends_body():
    _, mock_api = run(["add", "--name", "Milk", "--price", "1.5", "--quantity", "10"], 201, ITEM)
    method, path = mock_api.call_args[0]
    assert (method, path) == ("POST", "/inventory")
    assert mock_api.call_args[1]["json"] == {"name": "Milk", "price": 1.5, "quantity": 10}


def test_update_sends_only_given_fields():
    _, mock_api = run(["update", "1", "--quantity", "5"], data=ITEM)
    assert mock_api.call_args[0] == ("PATCH", "/inventory/1")
    assert mock_api.call_args[1]["json"] == {"quantity": 5}


def test_update_requires_field(capsys):
    code = cli.main(["update", "1"])
    assert code == 1
    assert "at least one field" in capsys.readouterr().out


def test_delete(capsys):
    code, mock_api = run(["delete", "1"], data={"message": "Item 1 deleted"})
    assert code == 0
    mock_api.assert_called_once_with("DELETE", "/inventory/1")
    assert "deleted" in capsys.readouterr().out


def test_lookup_barcode():
    _, mock_api = run(["lookup", "--barcode", "123"], data=ITEM)
    mock_api.assert_called_once_with("GET", "/external/barcode/123")


def test_lookup_name():
    _, mock_api = run(["lookup", "--name", "cola"], data=[ITEM])
    mock_api.assert_called_once_with("GET", "/external/search", params={"name": "cola"})


def test_lookup_requires_argument(capsys):
    assert cli.main(["lookup"]) == 1


def test_import_barcode():
    _, mock_api = run(["import", "--barcode", "123", "--price", "2", "--quantity", "4"], 201, ITEM)
    assert mock_api.call_args[0] == ("POST", "/inventory/import")
    assert mock_api.call_args[1]["json"] == {"barcode": "123", "price": 2.0, "quantity": 4}


def test_import_requires_argument():
    assert cli.main(["import"]) == 1


def test_api_unreachable_exits():
    import requests
    import pytest

    with patch("cli.requests.request", side_effect=requests.ConnectionError("down")):
        with pytest.raises(SystemExit):
            cli.api("GET", "/inventory")