# Inventory Management System

Flask REST API + CLI for managing retail inventory, with product data pulled from the
[OpenFoodFacts API](https://world.openfoodfacts.org/data).

## Features
- CRUD for inventory items (in-memory store)
- Fetch product details from OpenFoodFacts by barcode or name
- Import external products directly into inventory
- argparse CLI that talks to the API
- pytest suite (external API calls are mocked)

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python app.py                   # terminal 1: API at http://127.0.0.1:5000
python cli.py list              # terminal 2
```
Set `INVENTORY_API_URL` to point the CLI at a different host.

## API Endpoints
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/inventory` | List items (`?name=` filter) |
| GET | `/inventory/<id>` | Get one item |
| POST | `/inventory` | Create item (`name` required; `price`, `quantity`, `brand`, `barcode`) |
| PATCH | `/inventory/<id>` | Update fields |
| DELETE | `/inventory/<id>` | Delete item |
| GET | `/external/barcode/<barcode>` | Look up product by barcode |
| GET | `/external/search?name=` | Search products by name |
| POST | `/inventory/import` | Fetch by `barcode` or `name` and add to inventory |
| GET | `/health` | Health check |

Status codes: 200/201 success, 400 invalid input, 404 not found, 502 external API failure.

## CLI Usage
```bash
python cli.py add --name "Milk" --price 1.5 --quantity 10
python cli.py list
python cli.py view 1
python cli.py update 1 --quantity 25
python cli.py delete 1
python cli.py lookup --barcode 3017620422003
python cli.py lookup --name nutella
python cli.py import --barcode 3017620422003 --price 4.99 --quantity 20
python cli.py import --name nutella --price 4.99 --quantity 20
```

## Tests
```bash
pytest -v
```

## Design Notes
- `off_client.py` isolates all external calls so they can be mocked.
- Data is stored in memory and resets when the server restarts.
- The CLI never touches data directly; it only calls the API.

## Git Workflow
Feature branches (`feature/crud`, `feature/external-api`, `feature/cli`, `feature/tests`), each merged via pull request into `main` and then deleted.