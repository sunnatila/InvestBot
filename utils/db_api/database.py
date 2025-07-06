import sqlite3
from datetime import datetime
from utils.sheets_panel import add_info_to_sheet


class Database:
    def __init__(self, db_path='db.sqlite3'):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    # ------------- ORDER METHODS -------------

    async def add_order(self, user_name, phone, pr_name, pr_year, pr_type, pr_price,
                        pr_percent, debt_term, pay_day, first_pay=0):

        user = await self.get_user(user_name, phone)
        if not user:
            self.cursor.execute("INSERT INTO order_users (name, phone_number) VALUES (?, ?)", (user_name, phone))
            self.connection.commit()
            user = await self.get_user(user_name, phone)

        user_id = user[0]
        benefit = round((pr_price - first_pay) * pr_percent / 100) if first_pay else round(pr_price * pr_percent / 100)
        total_debt = (pr_price - first_pay + benefit) if first_pay else (pr_price + benefit)
        per_month = round(total_debt / debt_term)

        today = datetime.today().date()
        order_id = self.cursor.execute("SELECT COUNT(id) FROM orders").fetchone()[0] + 1
        pr_type_name = (await self.get_product_type(pr_type))[1]

        self.cursor.execute("""
            INSERT INTO orders (id, user_id, product_name, product_year, product_type_id, product_price,
                                product_percentage, all_debt, debt_term, payment_date, first_payment, 
                                per_month_debt, benefit, given_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, user_id, pr_name, pr_year, pr_type, pr_price, pr_percent,
              total_debt, debt_term, pay_day, first_pay, per_month, benefit, today, today))

        self.connection.commit()

        await add_info_to_sheet(today, order_id, pr_name, pay_day, user_name, phone, pr_year,
                                pr_price, pr_percent, pr_type_name, first_pay, per_month,
                                debt_term, benefit, total_debt)

    async def update_order_by_id(self, order_id, pay_amount):
        current_debt = self.cursor.execute("SELECT all_debt FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not current_debt:
            return False

        new_debt = max(float(current_debt[0]) - float(pay_amount), 0)
        today = datetime.today().date()

        self.cursor.execute("UPDATE orders SET all_debt = ?, updated_at = ? WHERE id = ?",
                            (new_debt, today, order_id))
        self.connection.commit()

        data = await self.get_order_by_id(order_id)

        await add_info_to_sheet(
            data[14], data[0], data[4], data[10], data[1], data[2],
            data[5], data[6], data[7], data[3], data[11], data[12],
            data[9], data[13], new_debt
        )
        return True

    async def get_orders_by_phone(self, phone):
        query = """
            SELECT orders.id, order_users.name, order_users.phone_number, product_types.name,
                   orders.product_name, orders.product_year, orders.product_price,
                   orders.product_percentage, orders.all_debt, orders.debt_term,
                   orders.payment_date, orders.first_payment, orders.per_month_debt,
                   orders.benefit, orders.given_time, orders.updated_at
            FROM orders
            LEFT JOIN order_users ON orders.user_id = order_users.id
            LEFT JOIN product_types ON orders.product_type_id = product_types.id
            WHERE order_users.phone_number = ?
        """
        return self.cursor.execute(query, (phone,)).fetchall() or None

    async def get_order_by_id(self, order_id):
        query = """
            SELECT orders.id, order_users.name, order_users.phone_number, product_types.name,
                   orders.product_name, orders.product_year, orders.product_price,
                   orders.product_percentage, orders.all_debt, orders.debt_term,
                   orders.payment_date, orders.first_payment, orders.per_month_debt,
                   orders.benefit, orders.given_time, orders.updated_at
            FROM orders
            LEFT JOIN order_users ON orders.user_id = order_users.id
            LEFT JOIN product_types ON orders.product_type_id = product_types.id
            WHERE orders.id = ?
        """
        return self.cursor.execute(query, (order_id,)).fetchone()

    # ------------- USER METHODS -------------

    async def get_user(self, name, phone):
        return self.cursor.execute("SELECT * FROM order_users WHERE name = ? AND phone_number = ?",
                                   (name, phone)).fetchone()

    async def get_user_by_number(self, number):
        return self.cursor.execute("SELECT * FROM order_users WHERE phone_number = ?", (number,)).fetchone()

    # ------------- PRODUCT TYPE METHODS -------------

    async def add_product_type(self, type_name):
        type_id = self.cursor.execute("SELECT COUNT(id) FROM product_types").fetchone()[0] + 1
        self.cursor.execute("INSERT INTO product_types (id, name) VALUES (?, ?)", (type_id, type_name))
        self.connection.commit()

    async def get_product_types(self):
        return self.cursor.execute("SELECT * FROM product_types").fetchall()

    async def get_product_type(self, type_id):
        return self.cursor.execute("SELECT * FROM product_types WHERE id = ?", (type_id,)).fetchone()

    async def del_product_type(self, type_id):
        self.cursor.execute("DELETE FROM product_types WHERE id = ?", (type_id,))
        self.connection.commit()
