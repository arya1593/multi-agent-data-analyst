"""Creates and seeds the sales SQLite database with global e-commerce demo data."""
import random
from datetime import date, timedelta
from sqlalchemy import create_engine, text

ENGINE = create_engine("sqlite:///./pizza_sales.db")

CITY_INFO = {
    "New York":    ("North America", "United States"),
    "Los Angeles": ("North America", "United States"),
    "Chicago":     ("North America", "United States"),
    "Toronto":     ("North America", "Canada"),
    "Houston":     ("North America", "United States"),
    "London":      ("Europe",        "United Kingdom"),
    "Paris":       ("Europe",        "France"),
    "Berlin":      ("Europe",        "Germany"),
    "Amsterdam":   ("Europe",        "Netherlands"),
    "Madrid":      ("Europe",        "Spain"),
    "Tokyo":       ("Asia Pacific",  "Japan"),
    "Singapore":   ("Asia Pacific",  "Singapore"),
    "Sydney":      ("Asia Pacific",  "Australia"),
    "Mumbai":      ("Asia Pacific",  "India"),
    "Seoul":       ("Asia Pacific",  "South Korea"),
}

PRODUCTS = {
    "Laptop":               ("Technology",     899.00),
    "Smartphone":           ("Technology",     599.00),
    "Tablet":               ("Technology",     349.00),
    "Wireless Headphones":  ("Technology",     199.00),
    "Monitor":              ("Technology",     349.00),
    "Office Chair":         ("Furniture",      299.00),
    "Standing Desk":        ("Furniture",      549.00),
    "Bookshelf":            ("Furniture",      149.00),
    "Filing Cabinet":       ("Furniture",      199.00),
    "Desk Lamp":            ("Furniture",       59.00),
    "Notebook Bundle":      ("Office Supplies",  12.00),
    "Premium Pen Set":      ("Office Supplies",   8.00),
    "Stapler Kit":          ("Office Supplies",  15.00),
    "Printer Paper":        ("Office Supplies",  25.00),
    "Whiteboard Markers":   ("Office Supplies",  18.00),
}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]


def create_tables(conn):
    conn.execute(text("DROP TABLE IF EXISTS orders"))
    conn.execute(text("DROP TABLE IF EXISTS products"))
    conn.execute(text("DROP TABLE IF EXISTS regions"))

    conn.execute(text("""
        CREATE TABLE regions (
            city    TEXT PRIMARY KEY,
            country TEXT NOT NULL,
            region  TEXT NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE products (
            product_name TEXT PRIMARY KEY,
            category     TEXT NOT NULL,
            base_price   REAL NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE orders (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            city             TEXT NOT NULL,
            product_name     TEXT NOT NULL,
            category         TEXT NOT NULL,
            customer_segment TEXT NOT NULL,
            quantity         INTEGER NOT NULL,
            order_date       DATE NOT NULL,
            revenue          REAL NOT NULL
        )
    """))
    conn.commit()


def seed_regions(conn):
    for city, (region, country) in CITY_INFO.items():
        conn.execute(
            text("INSERT INTO regions VALUES (:city, :country, :region)"),
            {"city": city, "country": country, "region": region},
        )
    conn.commit()


def seed_products(conn):
    for name, (category, price) in PRODUCTS.items():
        conn.execute(
            text("INSERT INTO products VALUES (:name, :category, :price)"),
            {"name": name, "category": category, "price": price},
        )
    conn.commit()


def seed_orders(conn, n=600):
    today = date.today()
    start = today - timedelta(days=180)
    cities = list(CITY_INFO.keys())
    product_list = list(PRODUCTS.keys())

    for _ in range(n):
        city = random.choice(cities)
        product = random.choice(product_list)
        category, base_price = PRODUCTS[product]
        segment = random.choice(SEGMENTS)
        qty = random.randint(1, 5)
        revenue = round(qty * base_price * random.uniform(0.88, 1.12), 2)
        delta = random.randint(0, (today - start).days)
        order_date = start + timedelta(days=delta)

        conn.execute(
            text(
                "INSERT INTO orders (city, product_name, category, customer_segment, "
                "quantity, order_date, revenue) "
                "VALUES (:city, :product, :category, :segment, :qty, :date, :rev)"
            ),
            {
                "city": city, "product": product, "category": category,
                "segment": segment, "qty": qty,
                "date": order_date.isoformat(), "rev": revenue,
            },
        )
    conn.commit()


def main():
    with ENGINE.connect() as conn:
        create_tables(conn)
        seed_regions(conn)
        seed_products(conn)
        seed_orders(conn, 600)
    print("Database seeded: 600 orders across 15 cities in 3 regions")


if __name__ == "__main__":
    main()
