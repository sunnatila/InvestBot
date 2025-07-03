from aiogram import types
from aiogram.filters import CommandStart, BaseFilter

from data.config import ADMINS
from keyboards.inline import add_info_button
from loader import dp

class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return str(message.from_user.id) in ADMINS


@dp.message(CommandStart(), AdminFilter())
async def bot_start(message: types.Message):
    await message.answer(f"Assalomu Alaykum.\n"
                         f"Admin panelga xush kelibsiz.", reply_markup=add_info_button)

