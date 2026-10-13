from flask import Flask, jsonify, request

import off_client

app = Flask(__name__)

inventory = {}
_counter = {"next_id": 1}


def reset_inventory():
    inventory.clear()
    _counter["next_id"] = 1


def _validate(data, partial=False):
    """Return (clean_dict, error_message)."""
    clean = {}
    if not partial or "name" in data:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            return None, "'name' is required and must be a non-empty string"
        clean["name"] = name.strip()
    if "price" in data:
        price = data["price"]
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            return None, "'price' must be a non-negative number"
        clean["price"] = price
    if "quantity" in data:
        qty = data["quantity"]
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 0:
            return None, "'quantity' must be a non-negative integer"
        clean["quantity"] = qty
    for field in ("brand", "barcode", "category", "ingredients"):
        if field in data:
            clean[field] = data[field]
    return clean, None


def _create_item(data):
    item = {
        "name": "",
        "brand": "",
        "barcode": "",
        "category": "",
        "ingredients": "",
        "price": 0.0,
        "quantity": 0,
    }
    item.update(data)
    item["id"] = _counter["next_id"]
    inventory[item["id"]] = item
    _counter["next_id"] += 1
    return item


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


# ---------- CRUD ----------

@app.get("/inventory")
def list_items():
    items = list(inventory.values())
    name = request.args.get("name")
    if name:
        items = [i for i in items if name.lower() in i["name"].lower()]
    return jsonify(items), 200


@app.get("/inventory/<int:item_id>")
def get_item(item_id):
    item = inventory.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item), 200


@app.post("/inventory")
def add_item():
    data = request.get_json(silent=True) or {}
    clean, error = _validate(data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(_create_item(clean)), 201


@app.patch("/inventory/<int:item_id>")
def update_item(item_id):
    item = inventory.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "No update data provided"}), 400
    clean, error = _validate(data, partial=True)
    if error:
        return jsonify({"error": error}), 400
    item.update(clean)
    return jsonify(item), 200


@app.delete("/inventory/<int:item_id>")
def delete_item(item_id):
    if item_id not in inventory:
        return jsonify({"error": "Item not found"}), 404
    del inventory[item_id]
    return jsonify({"message": f"Item {item_id} deleted"}), 200


# ---------- External API helpers ----------

@app.get("/external/barcode/<barcode>")
def external_barcode(barcode):
    try:
        product = off_client.fetch_by_barcode(barcode)
    except off_client.ExternalAPIError as exc:
        return jsonify({"error": f"External API error: {exc}"}), 502
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@app.get("/external/search")
def external_search():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "'name' query parameter is required"}), 400
    try:
        products = off_client.search_by_name(name)
    except off_client.ExternalAPIError as exc:
        return jsonify({"error": f"External API error: {exc}"}), 502
    return jsonify(products), 200


@app.post("/inventory/import")
def import_item():
    """Fetch a product from OpenFoodFacts and add it to inventory."""
    data = request.get_json(silent=True) or {}
    barcode, name = data.get("barcode"), data.get("name")
    if not barcode and not name:
        return jsonify({"error": "Provide 'barcode' or 'name'"}), 400

    extra, error = _validate({k: data[k] for k in ("price", "quantity") if k in data}, partial=True)
    if error:
        return jsonify({"error": error}), 400

    try:
        if barcode:
            product = off_client.fetch_by_barcode(barcode)
        else:
            results = off_client.search_by_name(name, limit=1)
            product = results[0] if results else None
    except off_client.ExternalAPIError as exc:
        return jsonify({"error": f"External API error: {exc}"}), 502

    if not product:
        return jsonify({"error": "Product not found"}), 404

    product.update(extra)
    return jsonify(_create_item(product)), 201


if __name__ == "__main__":
    app.run(debug=True)