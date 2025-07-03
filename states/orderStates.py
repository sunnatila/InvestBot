

from aiogram.fsm.state import StatesGroup, State




class OrderStates(StatesGroup):
    user_name = State()
    phone_number = State()
    product_name = State()
    product_type = State()
    product_year = State()
    product_price = State()
    product_percentage = State()
    debt_term = State()
    payment_date = State()
    access_first_payment = State()
    first_payment = State()
    order_access = State()


class OrderEditState(StatesGroup):
    phone_number = State()
    product_id = State()
    access_payment = State()
    debt_price = State()
    access_edit = State()
