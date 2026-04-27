"""Creates and seeds the pizza_sales SQLite database with realistic sample data."""
import random
from datetime import date, timedelta
from sqlalchemy import create_engine, text

ENGINE = create_engine("sqlite:///./pizza_sales.db")

CITIES = ["Chicago", "New York", "Houston", "Phoenix", "Dallas", "Seattle", "Miami", "Denver"]

CITY_REGION = {
    "Chicago": ("Midwest", "James Patel"),
    "New York": ("Northeast", "Sarah Chen"),
    "Houston": ("South", "Marcus Williams"),
    "Phoenix": ("West", "Linda Torres"),
    "Dallas": ("South", "Kevin Brown"),
    "Seattle": ("West", "Amy Nakamura"),
    "Miami": ("Southeast", "Carlos Rivera"),
    "Denver": ("West", "Rachel Scott"),
}

PRODUCTS = {
    "pepperoni":   ("Classic",    12.99),
    "margherita":  ("Classic",    10.99),
    "bbq_chicken": ("Specialty",  13.99),
    "veggie":      ("Specialty",  11.99),
    "hawaiian":    ("Classic",    11.49),
}


def create_tables(conn):
    # Drop and recreate all tables for a clean seed
    conn.execute(text("DROP TABLE IF EXISTS orders"))
    conn.execute(text("DROP TABLE IF EXISTS locations"))
    conn.execute(text("DROP TABLE IF EXISTS products"))

    conn.execute(text("""
        CREATE TABLE locations (
            city         TEXT PRIMARY KEY,
            region       TEXT NOT NULL,
            manager_name TEXT NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE products (
            pizza_type TEXT PRIMARY KEY,
            category   TEXT NOT NULL,
            base_price REAL NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE orders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            city       TEXT NOT NULL,
            pizza_type TEXT NOT NULL,
            quantity   INTEGER NOT NULL,
            sale_date  DATE NOT NULL,
            revenue    REAL NOT NULL
        )
    """))
    conn.commit()


def seed_locations(conn):
    for city, (region, manager) in CITY_REGION.items():
        conn.execute(
            text("INSERT INTO locations VALUES (:city, :region, :manager)"),
            {"city": city, "region": region, "manager": manager},
        )
    conn.commit()


def seed_products(conn):
    for pizza, (category, price) in PRODUCTS.items():
        conn.execute(
            text("INSERT INTO products VALUES (:pizza, :category, :price)"),
            {"pizza": pizza, "category": category, "price": price},
        )
    conn.commit()


def seed_orders(conn, n=500):
    today = date.today()
    start = today - timedelta(days=180)
    pizza_types = list(PRODUCTS.keys())

    for _ in range(n):
        city = random.choice(CITIES)
        pizza = random.choice(pizza_types)
        qty = random.randint(1, 4)
        base_price = PRODUCTS[pizza][1]
        # Add ±15 % price variation
        revenue = round(qty * base_price * random.uniform(0.85, 1.15), 2)
        delta = random.randint(0, (today - start).days)
        sale_date = start + timedelta(days=delta)

        conn.execute(
            text(
                "INSERT INTO orders (city, pizza_type, quantity, sale_date, revenue) "
                "VALUES (:city, :pizza, :qty, :date, :rev)"
            ),
            {"city": city, "pizza": pizza, "qty": qty, "date": sale_date.isoformat(), "rev": revenue},
        )
    conn.commit()


def main():
    with ENGINE.connect() as conn:
        create_tables(conn)
        seed_locations(conn)
        seed_products(conn)
        seed_orders(conn, 500)
    print("Database seeded: 500 orders across 8 cities")


if __name__ == "__main__":
    main()
