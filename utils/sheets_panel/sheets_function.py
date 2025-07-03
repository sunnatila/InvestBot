from oauth2client.service_account import ServiceAccountCredentials

from gspread_formatting import (
    CellFormat, Color, format_cell_range, Borders, Border
)
from core.settings import BASE_DIR
import gspread
import time

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        f"{BASE_DIR}\\invest3010-c6894eb19e75.json", scope
    )
    client = gspread.authorize(creds)
    return client.open("invest_table").sheet1


def format_row(row_num, num_cols, is_even):
    sheet = get_sheet()
    time.sleep(0.5)
    range_str = f"A{row_num}:{chr(64+num_cols)}{row_num}"
    cell_format = CellFormat(
        backgroundColor=Color(0.8, 0.9, 1) if is_even else Color(1,1,1),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE',
        borders=Borders(
            top=Border('SOLID', Color(0,0,0)),
            bottom=Border('SOLID', Color(0,0,0)),
            left=Border('SOLID', Color(0,0,0)),
            right=Border('SOLID', Color(0,0,0)),
        )
    )
    format_cell_range(sheet, range_str, cell_format)

async def add_info_function(*args):
    sheet = get_sheet()
    time.sleep(0.5)

    given_time = str(args[0])
    order_id = str(args[1])
    product_name = args[2]
    payment_date = str(args[3])
    user_name = args[4]
    phone_number = args[5]
    product_year = args[6]
    product_price = f"{args[7]} $"
    product_percentage = f"{args[8]}%"
    product_type = args[9]
    first_payment = f"{args[10]} $"
    per_month = f"{args[11]} $"
    debt_term = f"{args[12]} oy"
    benefit = f"{args[13]} $"
    all_debt = f"{args[14]} $"

    row_values = [
        given_time,
        order_id,
        product_name,
        payment_date,
        user_name,
        phone_number,
        product_year,
        product_price,
        product_percentage,
        product_type,
        first_payment,
        per_month,
        debt_term,
        benefit,
        all_debt,
    ]

    row_index = get_row_index_by_order_id(order_id)
    num_cols = len(row_values)

    if row_index:
        cell_range = f"A{row_index}:{chr(64+num_cols)}{row_index}"
        sheet.update(cell_range, [row_values])
    else:
        sheet.append_row(row_values)
        time.sleep(0.5)
        row_index = get_row_index_by_order_id(order_id)
    try:
        is_even = int(order_id) % 2 == 0
    except:
        is_even = False

    format_row(row_index, num_cols, is_even)



def get_row_index_by_order_id(order_id):
    sheet = get_sheet()
    time.sleep(0.5)

    all_data = sheet.get_all_values()
    for index, row in enumerate(all_data, start=1):
        if len(row) > 1 and row[1] == str(order_id):
            return index
    return None
