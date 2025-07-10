import asyncio
import gspread
import gspread_asyncio
from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import (
    CellFormat, Color, format_cell_range, Borders, Border, TextRotation
)
from core.settings import BASE_DIR
from calendar import monthrange

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

    payment_dates = []
    pay_day = data[10]
    debt_term = data[9]
    start_date = date.today()
    for i in range(debt_term):
        month = (start_date.month + i) % 12 + 1
        year = start_date.year + ((start_date.month - 1 + i) // 12)

        last_day = monthrange(year, month)[1]
        day = pay_day if pay_day <= last_day else last_day
        payment_dates.append(date(year, month, day).isoformat())


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
            n, remainder = divmod(n -1, 26)
            result = chr(65 + remainder) + result
        return result

    def col_letter_to_num(letter):
        num = 0
        for ch in letter:
            num = num * 26 + (ord(ch.upper()) - 64)
        return num

    # Agar start_col berilmagan bo'lsa, oxirgi to'ldirilgan ustunni topamiz
    if start_col is None:
        # Jadvaldagi barcha ma'lumotlarni olish
        all_values = await loop.run_in_executor(None, worksheet.get_all_values)

        max_col = 0
        # Har bir qatordagi ustunlar sonini tekshirib, eng katta ustun raqamini topamiz
        for row in all_values:
            if len(row) > max_col:
                max_col = len(row)

        # Oxirgi ustundan keyingi ustunni boshlang'ich deb olamiz
        start_col = max_col + 1 if max_col > 0 else 1

    col_letter = col_num_to_letter(start_col)

    # 1-qator: order_id
    await loop.run_in_executor(
        None,
        worksheet.update,
        f"{col_letter}1",
        [[str(order_id)]],
        {"valueInputOption": "USER_ENTERED"}
    )

    # 2-qator: user_name va order_name bir katakda
    await loop.run_in_executor(
        None,
        worksheet.update,
        f"{col_letter}2",
        [[f"User: {user_name}\nOrder: {order_name}"]],
        {"valueInputOption": "USER_ENTERED"}
    )

    # To'lov kunlari 3-qatrdan boshlab vertikal yoziladi
    start_row = 3
    date_strs = [str(d) for d in dates]
    values = [[d] for d in date_strs]
    end_row = start_row + len(values) - 1
    range_str = f"{col_letter}{start_row}:{col_letter}{end_row}"

    await loop.run_in_executor(None, worksheet.update, range_str, values)

    # Formatlash: yuqoridan pastga barcha kataklar uchun qora chegaralar va markazlash
    total_rows = 2 + len(values)  # 2 qator (id va user+order) + sanalar
    full_range = f"{col_letter}1:{col_letter}{total_rows}"

    cell_format = CellFormat(
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE',
        borders=Borders(
            top=Border('SOLID', Color(0,0,0)),
            bottom=Border('SOLID', Color(0,0,0)),
            left=Border('SOLID', Color(0,0,0)),
            right=Border('SOLID', Color(0,0,0))
        ),
        backgroundColor=Color(0.9, 0.95, 1)
    )

    await loop.run_in_executor(None, format_cell_range, worksheet, full_range, cell_format)

    # To'lov kunlari uchun vertikal yozuv faqat 3-qatrdan boshlanganligi uchun alohida formatlash
    if len(values) > 0:
        dates_range = f"{col_letter}{start_row}:{col_letter}{end_row}"
        dates_format = CellFormat(
            horizontalAlignment='CENTER',
            verticalAlignment='MIDDLE',
            borders=Borders(
                top=Border('SOLID', Color(0,0,0)),
                bottom=Border('SOLID', Color(0,0,0)),
                left=Border('SOLID', Color(0,0,0)),
                right=Border('SOLID', Color(0,0,0))
            ),
            backgroundColor=Color(0.9, 0.95, 1)
        )
        await loop.run_in_executor(None, format_cell_range, worksheet, dates_range, dates_format)


    return start_col + 1