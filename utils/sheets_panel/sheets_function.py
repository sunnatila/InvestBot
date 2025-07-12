import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import (
    CellFormat, Color, format_cell_range, Borders, Border, TextRotation
)
from core.settings import BASE_DIR

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = f"{BASE_DIR}/invest3010-c6894eb19e75.json"

def get_creds():
    return ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)


def get_sync_telegram_worksheet():
    creds = get_creds()
    client = gspread.authorize(creds)
    sheet = client.open('invest_table')
    worksheet = sheet.worksheet('Telegram')
    return worksheet


def get_sync_payment_worksheet():
    creds = get_creds()
    client = gspread.authorize(creds)
    sheet = client.open('invest_table')
    worksheet = sheet.worksheet('To\'lov')
    return worksheet


async def format_row(row_num, num_cols, is_even):
    loop = asyncio.get_running_loop()
    worksheet = await loop.run_in_executor(None, get_sync_telegram_worksheet)

    range_str = f"A{row_num}:{chr(64 + num_cols)}{row_num}"
    bg_color = Color(0.8, 0.9, 1) if is_even else Color(1, 1, 1)
    cell_format = CellFormat(
        backgroundColor=bg_color,
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE',
        borders=Borders(*[Border('SOLID', Color(0, 0, 0))] * 4)
    )
    await loop.run_in_executor(None, format_cell_range, worksheet, range_str, cell_format)

async def get_row_index_by_order_id(order_id):
    loop = asyncio.get_running_loop()
    worksheet = await loop.run_in_executor(None, get_sync_telegram_worksheet)
    all_values = await loop.run_in_executor(None, worksheet.get_all_values)

    for index, row in enumerate(all_values, start=1):
        if len(row) > 1 and row[1] == str(order_id):
            return index
    return None

async def add_info_to_sheet(*args):

    loop = asyncio.get_running_loop()
    order_id = str(args[1])

    row_values = [
        str(args[0]), str(args[1]), args[2], str(args[3]), args[4],
        args[5], args[6], f"{args[7]} $", f"{args[8]}%", args[9],
        f"{args[10]} $", f"{args[11]} $", f"{args[12]} oy", f"{args[13]} $", f"{args[14]} $"
    ]

    worksheet = await loop.run_in_executor(None, get_sync_telegram_worksheet)


    all_values = await loop.run_in_executor(None, worksheet.get_all_values)

    row_index = None
    for index, row in enumerate(all_values, start=1):
        if len(row) > 1 and row[1] == order_id:
            row_index = index
            break

    num_cols = len(row_values)

    if row_index:
        def update_range():
            worksheet.update(f"A{row_index}:{chr(64 + num_cols)}{row_index}", [row_values])
        await loop.run_in_executor(None, update_range)
    else:
        def append_row():
            worksheet.append_row(row_values)
        await loop.run_in_executor(None, append_row)
        await asyncio.sleep(0.5)
        all_values = await loop.run_in_executor(None, worksheet.get_all_values)
        for index, row in enumerate(all_values, start=1):
            if len(row) > 1 and row[1] == order_id:
                row_index = index
                break

    is_even = order_id.isdigit() and int(order_id) % 2 == 0

    await format_row(row_index, num_cols, is_even)


async def add_order_to_sheets_async(db, order_id):
    data = await db.get_order_by_id(order_id)
    if not data:
        return
    payment_data = await db.get_payment_dates(order_id)
    payment_dates = []
    for payment_date in payment_data:
        payment_dates.append(payment_date[4])

    await add_payment_dates_to_sheet(
        order_id=data[0],
        user_name=data[1],
        order_name=data[4],
        dates=payment_dates
    )


async def add_payment_dates_to_sheet(order_id: int, user_name: str, order_name: str, dates: list, start_col=None):
    loop = asyncio.get_running_loop()
    worksheet = await loop.run_in_executor(None, get_sync_payment_worksheet)

    def col_num_to_letter(n):
        result = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result

    if start_col is None:
        all_values = await loop.run_in_executor(None, worksheet.get_all_values)
        max_col = 0
        for row in all_values:
            if len(row) > max_col:
                max_col = len(row)
        start_col = max_col + 1 if max_col > 0 else 1

    col_letter = col_num_to_letter(start_col)


    await loop.run_in_executor(
        None,
        worksheet.update,
        f"{col_letter}1",
        [[str(order_id)]],
        {"valueInputOption": "USER_ENTERED"}
    )


    await loop.run_in_executor(
        None,
        worksheet.update,
        f"{col_letter}2",
        [[f"Klent: {user_name}\nKredit: {order_name}"]],
        {"valueInputOption": "USER_ENTERED"}
    )


    start_row = 3
    date_strs = [[d] for d in dates]

    end_row = start_row + len(date_strs) - 1
    range_str = f"{col_letter}{start_row}:{col_letter}{end_row}"

    await loop.run_in_executor(None, worksheet.update, range_str, date_strs)


    total_rows = 2 + len(date_strs)
    full_range = f"{col_letter}1:{col_letter}{total_rows}"

    cell_format = CellFormat(
        textRotation=TextRotation(vertical=False),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE',
        borders=Borders(
            top=Border('SOLID', Color(0, 0, 0)),
            bottom=Border('SOLID', Color(0, 0, 0)),
            left=Border('SOLID', Color(0, 0, 0)),
            right=Border('SOLID', Color(0, 0, 0))
        ),
        backgroundColor=Color(0.9, 0.95, 1)
    )
    await loop.run_in_executor(None, format_cell_range, worksheet, full_range, cell_format)



async def update_payment_dates(order_id: int, date: str = None):
    loop = asyncio.get_running_loop()
    worksheet = await loop.run_in_executor(None, get_sync_payment_worksheet)

    all_values = await loop.run_in_executor(None, worksheet.get_all_values)
    header_row = all_values[0] if all_values else []
    try:
        col_index = header_row.index(str(order_id)) + 1
    except ValueError:
        return

    rows = all_values[2:] if len(all_values) > 2 else []

    date_cells = [row[col_index - 1] if len(row) >= col_index else "" for row in rows]

    updated_dates = []

    check_mark = " ✅"

    if date is None:
        for d in date_cells:
            if not d.endswith(check_mark):
                updated_dates.append(d + check_mark)
            else:
                updated_dates.append(d)
    else:
        for d in date_cells:
            clean_d = d.lstrip(check_mark).strip()
            if clean_d == date and not d.endswith(check_mark):
                updated_dates.append(clean_d + check_mark)
            else:
                updated_dates.append(d)

    start_row = 3
    end_row = start_row + len(updated_dates) - 1

    def col_num_to_letter(n):
        result = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result

    col_letter = col_num_to_letter(col_index)

    range_str = f"{col_letter}{start_row}:{col_letter}{end_row}"

    date_values = [[d] for d in updated_dates]

    await loop.run_in_executor(None, worksheet.update, range_str, date_values)
