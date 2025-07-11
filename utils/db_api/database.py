import aiosqlite
from datetime import date
import calendar
from utils.sheets_panel import add_info_to_sheet


class Database:
    def __init__(self, db_path='db.sqlite3'):
        self.db_path = db_path

    # ----------------- HELPERS -----------------

    async def _execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")  # Agar foreign key ishlatilsa
            cursor = await db.execute(query, params)
            data = None
            if fetchone:
                data = await cursor.fetchone()
            elif fetchall:
                data = await cursor.fetchall()
            if commit:
                await db.commit()
            await cursor.close()
            return data

    # ------------- ORDER METHODS -------------


    async def add_order(self, user_name, phone, pr_name, pr_year, pr_type, pr_price,
                        pr_percent, debt_term, pay_day, first_pay=0):

        user = await self.get_user(user_name, phone)
        if not user:
            await self._execute(
                "INSERT INTO order_users (name, phone_number) VALUES (?, ?)",
                (user_name, phone),
                commit=True
            )
            user = await self.get_user(user_name, phone)

        user_id = user[0]
        benefit = round((pr_price - first_pay) * pr_percent / 100) if first_pay else round(pr_price * pr_percent / 100)
        total_debt = (pr_price - first_pay + benefit) if first_pay else (pr_price + benefit)
        per_month = round(total_debt / debt_term)

        today = date.today()
        count = await self._execute("SELECT COUNT(id) FROM orders", fetchone=True)
        order_id = count[0] + 1 if count else 1

        pr_type_row = await self.get_product_type(pr_type)
        pr_type_name = pr_type_row[1] if pr_type_row else ""

        await self._execute("""
            INSERT INTO orders (id, user_id, product_name, product_year, product_type_id, product_price,
                                product_percentage, all_debt, debt_term, payment_date, first_payment, 
                                per_month_debt, benefit, given_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, user_id, pr_name, pr_year, pr_type, pr_price, pr_percent,
              total_debt, debt_term, pay_day, first_pay, per_month, benefit, today, today),
              commit=True)

        await self.create_payment_dates(order_id, pay_day, debt_term, per_month)

        await add_info_to_sheet(today, order_id, pr_name, pay_day, user_name, phone, pr_year,
                                pr_price, pr_percent, pr_type_name, first_pay, per_month,
                                debt_term, benefit, total_debt)

    async def update_order_by_id(self, order_id, pay_amount):
        current_debt_row = await self._execute("SELECT all_debt FROM orders WHERE id = ?", (order_id,), fetchone=True)
        if not current_debt_row:
            return False

        new_debt = max(float(current_debt_row[0]) - float(pay_amount), 0)
        today = date.today()

        await self._execute("UPDATE orders SET all_debt = ?, updated_at = ? WHERE id = ?",
                            (new_debt, today, order_id), commit=True)

        data = await self.get_order_by_id(order_id)

        if data:
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
            WHERE order_users.phone_number = ? AND orders.all_debt > 0
        """
        return await self._execute(query, (phone,), fetchall=True)

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
        return await self._execute(query, (order_id,), fetchone=True)


    # ------------- USER METHODS -------------

    async def get_user(self, name, phone):
        return await self._execute(
            "SELECT * FROM order_users WHERE name = ? AND phone_number = ?",
            (name, phone), fetchone=True
        )

    async def get_user_by_number(self, number):
        return await self._execute(
            "SELECT * FROM order_users WHERE phone_number = ?",
            (number,), fetchone=True
        )


    async def get_per_month_payment(self, order_id):
        return await self._execute("SELECT per_month_debt FROM orders WHERE id = ?", (order_id,), fetchone=True)


    # ------------- PRODUCT TYPE METHODS -------------

    async def add_product_type(self, type_name):
        count = await self._execute("SELECT COUNT(id) FROM product_types", fetchone=True)
        type_id = count[0] + 1 if count else 1
        await self._execute(
            "INSERT INTO product_types (id, name) VALUES (?, ?)",
            (type_id, type_name), commit=True
        )

    async def get_product_types(self):
        return await self._execute("SELECT * FROM product_types", fetchall=True)

    async def get_product_type(self, type_id):
        return await self._execute("SELECT * FROM product_types WHERE id = ?", (type_id,), fetchone=True)

    async def get_product_type_by_name(self, name):
        return await self._execute("SELECT * FROM product_types WHERE name = ?", (name,), fetchone=True)

    async def del_product_type(self, type_id):
        await self._execute("DELETE FROM product_types WHERE id = ?", (type_id,), commit=True)


    # ----------------- PAYMENT DATES METHODS -------------


    async def create_payment_dates(self, order_id: int, start_day: int, months: int, per_month_payment):
        today = date.today()
        year = today.year
        month = today.month

        month += 1
        if month > 12:
            month = 1
            year += 1

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            async with db.execute("BEGIN"):
                for i in range(months):
                    current_month = month + i
                    current_year = year + (current_month - 1) // 12
                    current_month = (current_month - 1) % 12 + 1

                    last_day = calendar.monthrange(current_year, current_month)[1]
                    payment_day = start_day if start_day <= last_day else last_day

                    payment_date = date(current_year, current_month, payment_day)
                    count = await self._execute("SELECT COUNT(id) FROM payment_dates", fetchone=True)
                    payment_id = count[0] + 1 if count else 1
                    query = """
                        INSERT INTO payment_dates (id, order_id, payment_date, payment_sum, is_payment)
                        VALUES (?, ?, ?, ?, False)
                    """
                    await db.execute(query, (payment_id, order_id, payment_date, per_month_payment))
                    await db.commit()


    async def update_payment_sum(self, order_id, payment_sum, month_payment: bool = False, full_payment: bool = False):
        if month_payment:
            payment_id = await self._execute("SELECT id FROM payment_dates WHERE order_id = ? AND is_payment = False", (order_id,), fetchone=True)
            await self._execute("UPDATE payment_dates SET payment_sum = 0, is_payment = ? WHERE id = ?", (True, payment_id[0]), commit=True)
        elif full_payment:
            await self._execute("UPDATE payment_dates SET payment_sum = 0, is_payment = ? WHERE order_id = ?", (True, order_id), commit=True)
        else:
            payment_id = await self._execute("SELECT id, payment_sum FROM payment_dates WHERE order_id = ? AND is_payment = False", (order_id,), fetchone=True)
            pay_sum = payment_id[1] - payment_sum
            if pay_sum == 0:
                await self._execute("UPDATE payment_dates SET payment_sum = 0, is_payment = ? WHERE id = ?", (True, payment_id[0]), commit=True)
                return
            await self._execute("UPDATE payment_dates SET payment_sum = ?, is_payment = ? WHERE id = ?", (pay_sum, False, payment_id[0]), commit=True)

    async def get_monthly_payment_sum(self):
        return await self._execute("SELECT payment_sum FROM payment_dates", fetchone=True)


    async def get_payment_dates(self, order_id):
        return await self._execute("SELECT * FROM payment_dates WHERE order_id = ?", (order_id,), fetchall=True)

    async def get_previous_payment(self, order_id):
        """
        Oldingi oy uchun to'lov holatini qaytaradi.
        Agar mavjud bo'lmasa None qaytaradi.
        """
        query = """
            SELECT id, payment_sum, is_payment FROM payment_dates
            WHERE order_id = ? AND is_payment = False
        """
        return await self._execute(query, (order_id,), fetchone=True)


