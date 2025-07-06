from oauth2client.service_account import ServiceAccountCredentials

from gspread_formatting import (
    CellFormat, Color, format_cell_range, Borders, Border
)
from core.settings import BASE_DIR
import gspread
import time

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = f"{BASE_DIR}/invest3010-c6894eb19e75.json"

async def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client.open("invest_table").sheet1

async def format_row(row_num, num_cols, is_even):
    sheet = await get_sheet()
    range_str = f"A{row_num}:{chr(64+num_cols)}{row_num}"
    bg_color = Color(0.8, 0.9, 1) if is_even else Color(1, 1, 1)
    cell_format = CellFormat(
        backgroundColor=bg_color,
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE',
        borders=Borders(*[Border('SOLID', Color(0,0,0))]*4)
    )
    format_cell_range(sheet, range_str, cell_format)

async def get_row_index_by_order_id(order_id):
    sheet = await get_sheet()
    for index, row in enumerate(sheet.get_all_values(), start=1):
        if len(row) > 1 and row[1] == str(order_id):
            return index
    return None

async def add_info_to_sheet(*args):
    sheet = await get_sheet()
    order_id = str(args[1])

    row_values = [
        str(args[0]), str(args[1]), args[2], str(args[3]), args[4],
        args[5], args[6], f"{args[7]} $", f"{args[8]}%", args[9],
        f"{args[10]} $", f"{args[11]} $", f"{args[12]} oy", f"{args[13]} $", f"{args[14]} $"
    ]

    row_index = await get_row_index_by_order_id(order_id)
    num_cols = len(row_values)

    if row_index:
        sheet.update(f"A{row_index}:{chr(64+num_cols)}{row_index}", [row_values])
    else:
        sheet.append_row(row_values)
        time.sleep(0.5)
        row_index = await get_row_index_by_order_id(order_id)

    is_even = str(order_id).isdigit() and int(order_id) % 2 == 0
    await format_row(row_index, num_cols, is_even)