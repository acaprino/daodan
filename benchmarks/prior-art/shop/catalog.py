"""Catalogo: gli SKU sono salvati in forma canonica."""

PRODUCTS = {
    "AB12": {"price": 19.90, "stock": 5},
    "ZX9": {"price": 4.50, "stock": 40},
}


def normalize_sku(raw):
    """Forma canonica: senza spazi ai lati, maiuscola, senza trattini."""
    return raw.strip().upper().replace("-", "")


def find(raw):
    return PRODUCTS.get(normalize_sku(raw))
