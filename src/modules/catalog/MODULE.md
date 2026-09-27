---
id: module-catalog
title: Catalog Module (example)
updated: 2026-07-03
---

# Catalog Module (example)

Purpose: a **worked example** of a bounded context following this foundation's rules —
Clean Architecture layers, DDD tactical patterns, and the testing conventions. It manages
a product catalog: creating products and listing them for sale. It does **not** own
pricing strategy, inventory, or orders. This module is reference code to imitate
(COD-050); it is not wired into the no-op template Taskfile. Delete it (and
`tests/modules/catalog/`) when starting a real project.

## Public API (the contract — everything else is private)

| Entry point | Layer | Description |
| -- | -- | -- |
| `AddProduct.handle(AddProductCommand) -> ProductId` | application | Create a product and list it for sale |
| `add_product_handler(use_case, payload) -> Response` | interface | Inbound edge: validate + translate errors |
| `ProductRepository` | application | Port other modules/adapters implement |

## Events

| Direction | Event | Schema | Notes |
| -- | -- | -- | -- |
| — | — | — | none yet; a real module would publish `ProductListed` |

## Owned data

Products (id, name, price, listed). No other module reads or writes catalog products
directly — they go through the public API above.

## Invariants (MUST always hold — each maps to a test)

1. A product always has a non-empty name.
2. Money is never negative and always carries a 3-letter ISO-4217 currency.
3. A *listed* product always has a non-zero price.
4. Product ids are unique within the catalog.

## Dependencies

| Uses module | Via | Why |
| -- | -- | -- |
| — | — | none; the domain imports only the standard library (ARC-002) |

## Layout

```
domain/product.py                          # Money, ProductId, Product, CatalogError
application/ports.py                        # ProductRepository (port)
application/add_product.py                  # AddProduct use case, AddProductCommand
infrastructure/in_memory_product_repository.py
interface/http_handler.py                  # framework-free inbound example
```

Tests mirror this at `tests/modules/catalog/unit/test_catalog.py`. Run them with the
python-uv profile (`task test`) or, ad hoc, `PYTHONPATH=. pytest tests/modules/catalog`.
