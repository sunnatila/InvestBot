import sqlite3
from datetime import datetime
from utils.sheets_panel import add_info_function


class Database:
    def __init__(self, db_path: str='db.sqlite3'):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()


    # order methods --------------------------------------------------------------

    async def add_order(self, user_name, phone_number, product_name, product_year, product_type,
                  product_price, product_percentage, debt_term, payment_date,
                  first_payment: float = 0):
        user = await self.get_user(user_name, phone_number)
        if not user:
            insert_user_query = """
                    INSERT INTO order_users (name, phone_number) VALUES (?, ?)
                """
            self.cursor.execute(insert_user_query, (user_name, phone_number))
            self.connection.commit()
            user = await self.get_user(user_name, phone_number)
            user_id = user[0]
        else:
            user_id = user[0]


        if first_payment:
            benefit = round((product_price - first_payment) * product_percentage / 100)
            total_debt = (product_price - first_payment) + benefit
        else:
            benefit = round(product_price * product_percentage / 100)
            total_debt = product_price + benefit

        per_month = round(total_debt / debt_term)
        date = datetime.today().date()
        last_id_tuple = self.cursor.execute("SELECT COUNT(id) FROM orders").fetchone()
        last_id = last_id_tuple[0] + 1
        pr_type = await self.get_product_type(product_type)
        pr_type_name = pr_type[1]

        insert_order_query = """
                INSERT INTO orders (id, user_id, product_name, product_year, product_type_id, product_price, 
                                    product_percentage, all_debt, debt_term, payment_date, first_payment, per_month_debt, benefit, given_time, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        self.cursor.execute(insert_order_query, (
            last_id, user_id, product_name, product_year, product_type, product_price,
            product_percentage, total_debt, debt_term, payment_date, first_payment,
            per_month, benefit, date, date
        ))
        self.connection.commit()
        await add_info_function(date, last_id, product_name, payment_date,
                                user_name, phone_number, product_year, product_price,
                                product_percentage, pr_type_name, first_payment,
                                per_month, debt_term, benefit, total_debt
                                )

    async def get_orders_by_phone(self, phone_number):
        query = """
            SELECT 
                orders.id,
                order_users.name AS user_name,
                order_users.phone_number,
                product_types.name AS product_type_name,
                orders.product_name,
                orders.product_year,
                orders.product_price,
                orders.product_percentage,
                orders.all_debt,
                orders.debt_term,
                orders.payment_date,
                orders.first_payment,
                orders.per_month_debt,
                orders.benefit,
                orders.given_time,
                orders.updated_at
            FROM orders
            LEFT JOIN order_users ON orders.user_id = order_users.id
            LEFT JOIN product_types ON orders.product_type_id = product_types.id
            WHERE order_users.phone_number = ?
        """
        res = self.cursor.execute(query, (phone_number,)).fetchall()
        if res:
            return res
        return None


    async def get_order_by_id(self, product_id):
        query = """
            SELECT 
                orders.id,
                order_users.name AS user_name,
                order_users.phone_number,
                product_types.name AS product_type_name,
                orders.product_name,
                orders.product_year,
                orders.product_price,
                orders.product_percentage,
                orders.all_debt,
                orders.debt_term,
                orders.payment_date,
                orders.first_payment,
                orders.per_month_debt,
                orders.benefit,
                orders.given_time,
                orders.updated_at
            FROM orders
            LEFT JOIN order_users ON orders.user_id = order_users.id
            LEFT JOIN product_types ON orders.product_type_id = product_types.id
            WHERE orders.id = ?
        """
        return self.cursor.execute(query, (product_id,)).fetchone()

    async def update_order_by_id(self, product_id, debt_price):
        query_select = """
            SELECT all_debt FROM orders WHERE id = ?
        """
        result = self.cursor.execute(query_select, (product_id,)).fetchone()

        if not result:
            return False

        current_debt = result[0]

        updated_debt = float(current_debt) - float(debt_price)
        if updated_debt < 0:
            updated_debt = 0

        query_update = """
            UPDATE orders SET all_debt = ?, updated_at = ? WHERE id = ?
        """
        self.cursor.execute(query_update, (updated_debt, datetime.today().date(), product_id))
        self.connection.commit()
        data = await self.get_order_by_id(product_id)

        await add_info_function(
            data[14],  # given_time
            data[0],  # id
            data[4],  # product_name
            data[10],  # payment_date
            data[1],  # user_name
            data[2],  # phone_number
            data[5],  # product_year
            data[6],  # product_price
            data[7],  # product_percentage
            data[3],  # product_type_name
            data[11],  # first_payment
            data[12],  # per_month_debt
            data[9],  # debt_term
            data[13],  # benefit
            updated_debt  # new all_debt
        )

        return True

    # user methods -------------------------------------------------------------------------------

    async def get_user(self, user_name, phone_number):
        query = """
            SELECT * FROM order_users WHERE name = ? AND phone_number = ?
        """
        res = self.cursor.execute(query, (user_name, phone_number)).fetchone()
        if res:
            return res
        return None

    async def get_user_by_number(self, number):
        query = """
            SELECT * FROM order_users WHERE phone_number = ?
        """
        res = self.cursor.execute(query, (number,)).fetchone()
        if res:
            return res
        return None

    # product type methods -------------------------------------------------------------------------------

    async def add_product_type(self, type_name):
        last_id_tuple  = self.cursor.execute("SELECT COUNT(id) FROM product_types").fetchone()
        last_id = last_id_tuple[0] + 1
        query = """
            INSERT INTO product_types (id, name) VALUES (?, ?)
        """
        self.cursor.execute(query, (last_id, type_name,))
        self.connection.commit()

    async def get_product_types(self):
        query = """
            SELECT * FROM product_types
        """
        return self.cursor.execute(query).fetchall()

    async def get_product_type(self, type_id):
        query = """
            SELECT * FROM product_types WHERE id=?
        """
        return self.cursor.execute(query, (type_id, )).fetchone()

    async def del_product_type(self, type_id):
        query = """
            DELETE FROM product_types WHERE id = ?
        """
        self.cursor.execute(query, (type_id,))
        self.connection.commit()
