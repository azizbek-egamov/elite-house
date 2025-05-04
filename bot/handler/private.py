import os
import django
from aiogram import Router, F, Bot, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import CommandStart, Command
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    FSInputFile,
)
from asgiref.sync import sync_to_async
from main.models import *
from ..settings.states import *
from ..settings.buttons import *
from datetime import datetime, timedelta
from core.settings import ADMIN, BOT_TOKEN, domain
from xhtml2pdf import pisa

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

user_private_router = Router()
dp = user_private_router


@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await message.answer(
        text="<b>Assalomu alaykum. Ma'lumotlarni ko'rish uchun Passport seriyasi va raqamini yuboring\n\n<i>Masalan: AD1122333.</i></b>"
    )
    await state.set_state(Passport.passport)


@dp.message(F.text, Passport.passport)
async def PassportCheck(message: Message, state: FSMContext):
    passport = message.text
    if len(passport) == 9:
        if await sync_to_async(Client.objects.filter(passport=passport).exists)():
            client = await sync_to_async(list)(Client.objects.filter(passport=passport))
            btn = InlineKeyboardBuilder()
            for i in client:
                btn.add(
                    InlineKeyboardButton(
                        text=f"#00{i.pk}", callback_data=f"contract::{i.pk}"
                    )
                )
            await message.answer(
                "<b>Passport raqam bo'yicha shartnomalar ro'yxati:</b>",
                reply_markup=btn.as_markup(),
            )
            await state.clear()
        else:
            await message.answer(
                text="<b>Bu passport bo'yicha shartnoma topilmadi.</b>"
            )
    else:
        await message.answer("<b>Passport raqami noto'g'ri formatda kiritildi.</b>")


@dp.callback_query(F.data.startswith("contract::"))
async def ContractId(callback: CallbackQuery, state: FSMContext):
    id = callback.data.split("::")[1]
    a = await sync_to_async(Client.objects.filter(pk=id).exists)()
    if a:
        await callback.message.delete()
        contract = await sync_to_async(Client.objects.filter(pk=id).first)()
        client = await sync_to_async(lambda: contract.client)()
        homee = await sync_to_async(lambda: contract.home)()
        home = await sync_to_async(lambda: homee.home)()
        building = await sync_to_async(lambda: homee.building)()
        city = await sync_to_async(lambda: building.city)()
        btn = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="To'lov qilish",
                        callback_data=f"payment::{contract.pk}",
                    )
                ]
            ]
        )

        if contract.debt:
            debt = "Bor"
        else:
            debt = "Yo'q"
        await callback.message.answer(
            text=f"""<b>Shartnoma haqida batafsil ma'lumotlar:
                
Shartnoma raqami: #00{id},
Ism familiya: {client.full_name},
Passport raqami: {contract.passport},
Xonadon joylashuvi: {city.name} - {building.name}, {home.home_number} - Uy,
Shartnoma yatarilgan sana: {contract.created.date()},
Umumiy to'lov miqdori: {home.price * contract.term} so'm,
To'lov muddati: {contract.term},
Qolgan to'lov muddati: {contract.count_month} oy,
To'langan muddat: {contract.term - contract.count_month} oy,
Qolgan to'lov miqdori: {contract.residual} so'm,
Oylik to'lov: {contract.oylik_tolov} so'm,
Keyingi oy uchun to'langan miqdor: {contract.residu} so'm,
Keyingi oyda to'lanadigan summa: {contract.oylik_tolov - contract.residu} so'm.

Shartnoma holati: {contract.status},
Qarzdorlik: {debt}.</b>""",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="To'lovlar jadvali", callback_data=f"paylist={id}"
                        )
                    ]
                ]
            ),
        )
    else:
        await callback.answer(
            text="Bunday raqamdagi shartnoma mavjud emas.", show_alert=True
        )
    await state.clear()

from django.db.models import Sum
@dp.callback_query(F.data.startswith("paylist="))
async def paylist(callback: CallbackQuery):
    id = callback.data.split("=")[1]
    contract = await sync_to_async(Client.objects.filter(pk=id).first)()

    # Agar shartnoma mavjud bo'lmasa
    if not contract:
        await callback.answer(text="Shartnoma topilmadi", show_alert=True)
        return

    oylar = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentabr", "Oktyabr", "Noyabr", "Dekabr"
    ]

    rasrochka = await sync_to_async(list)(Rasrochka.objects.filter(client_id=id))
    summa = 0
    if len(rasrochka) != 0:
        for r in rasrochka:
            print("SS")
            summa += r.amount
    print(summa)
    if summa != 0:
        tolangan_oy = summa / contract.oylik_tolov
        print(tolangan_oy)


    # HTML kodini yaratish
    html_code = f"""
    <html>
        <head>
            <style>
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12.5px;
                }}
                th, td {{
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #dddddd;
                }}
            </style>
        </head>
        <body>
            <h2 align='center'>To'lovlar jadvali #00{id}</h2>
            <table>
                <tr>
                    <th>#</th>
                    <th>To'lov sanasi</th>
                    <th>Summa</th>
                    <th>Holat</th>
                </tr>"""

    start_date = contract.created  # To'lovlar boshlanish sanasi

    for c in range(1, contract.term + 1):
        payment_date = start_date + timedelta(weeks=4 * (c - 1))
        month_name = oylar[payment_date.month - 1]

        # Jadvalga satr qo'shish
        html_code += f"""
        <tr>
            <td>{c}</td>
            <td>{payment_date.day} - {month_name}</td>
            <td>{contract.oylik_tolov}</td>
        </tr>"""

    html_code += """
            </table>
        </body>
    </html>
    """

    # PDF faylga saqlash
    def html_to_pdf(html_code, output_filename):
        with open(output_filename, "wb") as pdf_file:
            pisa_status = pisa.pisaDocument(html_code, pdf_file)
            return pisa_status.err

    # PDF yaratish
    output_filename = "jadval.pdf"
    error = html_to_pdf(html_code, output_filename)

    if error:
        print("Xatolik yuz berdi.")
    else:
        print(f"PDF fayl {output_filename} sifatida yaratildi.")
        await callback.message.answer_document(document=FSInputFile(output_filename))
        
        
        
        
        
        
        
        
        
        
        
        