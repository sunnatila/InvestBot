from loader import db
import asyncio
async def show_dates():
    payment_data = await db.get_payment_dates(1)
    payment_dates = []
    for payment_date in payment_data:
        payment_dates.append(payment_date[1])
    print([[date] for date in payment_dates])
    return payment_dates
print(asyncio.run(db.get_order_by_id(1)))
