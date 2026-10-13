import argparse
import os
import sys

import requests

API_URL = os.environ.get("INVENTORY_API_URL", "http://127.0.0.1:5000")


def api(method, path, **kwargs):
    try:
        response = requests.request(method, API_URL + path, timeout=20, **kwargs)
    except requests.RequestException as exc:
        print(f"Error: cannot reach API ({exc})")
        sys.exit(1)
    try:
        data = response.json()
    except ValueError:
        data = {}
    return response.status_code, data


def fmt(item):
    return (
        f"[{item.get('id', '-')}] {item.get('name')} | brand: {item.get('brand') or '-'} "
        f"| barcode: {item.get('barcode') or '-'} | price: {item.get('price', 0)} "
        f"| qty: {item.get('quantity', 0)}"
    )


def show(status, data, ok=(200, 201)):
    if status not in ok:
        print(f"Error ({status}): {data.get('error', 'Unknown error')}")
        return 1
    if "message" in data:
        print(data["message"])
    elif isinstance(data, list):
        if not data:
            print("No items found.")
        for item in data:
            print(fmt(item))
    else:
        print(fmt(data))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Inventory management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all items")

    p = sub.add_parser("view", help="View one item")
    p.add_argument("id", type=int)

    p = sub.add_parser("add", help="Add an item")
    p.add_argument("--name", required=True)
    p.add_argument("--price", type=float, default=0)
    p.add_argument("--quantity", type=int, default=0)
    p.add_argument("--brand")
    p.add_argument("--barcode")

    p = sub.add_parser("update", help="Update an item")
    p.add_argument("id", type=int)
    p.add_argument("--name")
    p.add_argument("--price", type=float)
    p.add_argument("--quantity", type=int)

    p = sub.add_parser("delete", help="Delete an item")
    p.add_argument("id", type=int)

    p = sub.add_parser("lookup", help="Look up a product on OpenFoodFacts")
    p.add_argument("--barcode")
    p.add_argument("--name")

    p = sub.add_parser("import", help="Fetch from OpenFoodFacts and add to inventory")
    p.add_argument("--barcode")
    p.add_argument("--name")
    p.add_argument("--price", type=float, default=0)
    p.add_argument("--quantity", type=int, default=0)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.command

    if cmd == "list":
        return show(*api("GET", "/inventory"))
    if cmd == "view":
        return show(*api("GET", f"/inventory/{args.id}"))
    if cmd == "add":
        body = {k: v for k, v in vars(args).items() if k != "command" and v is not None}
        return show(*api("POST", "/inventory", json=body))
    if cmd == "update":
        body = {k: v for k, v in vars(args).items() if k not in ("command", "id") and v is not None}
        if not body:
            print("Error: provide at least one field to update")
            return 1
        return show(*api("PATCH", f"/inventory/{args.id}", json=body))
    if cmd == "delete":
        return show(*api("DELETE", f"/inventory/{args.id}"))
    if cmd == "lookup":
        if args.barcode:
            return show(*api("GET", f"/external/barcode/{args.barcode}"))
        if args.name:
            return show(*api("GET", "/external/search", params={"name": args.name}))
        print("Error: provide --barcode or --name")
        return 1
    if cmd == "import":
        if not (args.barcode or args.name):
            print("Error: provide --barcode or --name")
            return 1
        body = {k: v for k, v in vars(args).items() if k != "command" and v is not None}
        return show(*api("POST", "/inventory/import", json=body))
    return 1


if __name__ == "__main__":
    sys.exit(main())