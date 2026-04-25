import os
import json
import urllib.parse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

# ===== НАСТРОЙКИ =====
API_TOKEN = os.environ.get("BOT_TOKEN", "8752199180:AAFE36XSBYeYeQF5Y-OJgTJDWsN3nDdV0XY")
YOUR_USERNAME = "PyotrAleksandrovich"

# Если хотите использовать Cloudflare Worker (необязательно), раскомментируйте:
# WORKER_URL = "https://wandering-credit-9614.petakasatkin31.workers.dev"
# custom_api = TelegramAPIServer.from_base(WORKER_URL)
# session = AiohttpSession(api=custom_api)
# bot = Bot(token=API_TOKEN, session=session)
# Если нет – используйте прямое подключение (бот будет на сервере Bothost, который в РФ, так что проблем с доступом к API быть не должно)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ===== ПРАЙС-ЛИСТ (как у вас) =====
SERVICES = {
    "Диагностика": 250,
    "Детейлинг (чистка+диагностика)": 500,
    "Замена дисплея": 1000,
    "Замена аккумулятора": 750,
    "Замена динамика": 500,
    "Замена основной камеры": 500,
    "Замена фронтальной камеры": 500,
    "Замена стекла камеры": 500,
    "Замена задней крышки": 750,
    "Замена корпуса": 1000,
    "Замена платы": 1000,
    "Замена кнопок": 500,
    "Наклейка защитного стекла": 150,
}
service_list = list(SERVICES.keys())

problems = [
    "Разбит экран",
    "Не заряжается телефон",
    "Не включается телефон",
    "Проблема с камерой",
    "Залит водой"
]

brands = ["iPhone", "Samsung", "Xiaomi", "Huawei", "Другое"]
part_types = ["Оригинал", "Качественная копия"]

class RepairState(StatesGroup):
    problem = State()
    brand = State()
    custom_brand = State()
    model = State()
    service = State()
    part_type = State()

# ===== ХЕНДЛЕРЫ (ваши, без изменений) =====
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=p, callback_data=f"prob_{i}")] for i, p in enumerate(problems)
    ])
    await message.answer("Привет! Выберите проблему с телефоном:", reply_markup=kb)
    await state.set_state(RepairState.problem)

@dp.callback_query(RepairState.problem)
async def problem_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("prob_"):
        idx = int(callback.data.split("_")[1])
        chosen = problems[idx]
        await state.update_data(problem=chosen)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=b, callback_data=f"brand_{i}")] for i, b in enumerate(brands)
        ])
        await callback.message.edit_text("Выберите марку телефона:", reply_markup=kb)
        await state.set_state(RepairState.brand)
    await callback.answer()

@dp.callback_query(RepairState.brand)
async def brand_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("brand_"):
        idx = int(callback.data.split("_")[1])
        chosen = brands[idx]
        if chosen == "Другое":
            await callback.message.delete()
            await callback.message.answer("Напишите марку телефона (например, Google Pixel, OnePlus):")
            await state.set_state(RepairState.custom_brand)
        else:
            await state.update_data(brand=chosen)
            await callback.message.delete()
            await callback.message.answer("Напишите модель телефона:")
            await state.set_state(RepairState.model)
    await callback.answer()

@dp.message(RepairState.custom_brand)
async def custom_brand(message: types.Message, state: FSMContext):
    await state.update_data(brand=message.text)
    await message.answer("Напишите модель телефона:")
    await state.set_state(RepairState.model)

@dp.message(RepairState.model)
async def get_model(message: types.Message, state: FSMContext):
    await state.update_data(model=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=s, callback_data=f"serv_{i}")] for i, s in enumerate(service_list)
    ])
    await message.answer("Какую услугу нужно выполнить?", reply_markup=kb)
    await state.set_state(RepairState.service)

@dp.callback_query(RepairState.service)
async def service_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("serv_"):
        idx = int(callback.data.split("_")[1])
        chosen = service_list[idx]
        price = SERVICES[chosen]
        await state.update_data(service=chosen, price_of_work=price)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=p, callback_data=f"part_{i}")] for i, p in enumerate(part_types)
        ])
        await callback.message.edit_text("Какую деталь поставить? (оригинал или копия)", reply_markup=kb)
        await state.set_state(RepairState.part_type)
    await callback.answer()

@dp.callback_query(RepairState.part_type)
async def part_callback(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("part_"):
        idx = int(callback.data.split("_")[1])
        chosen = part_types[idx]
        await state.update_data(part_type=chosen)
        data = await state.get_data()
        brand_model = f"{data['brand']} {data['model']}"
        text = (f"Здравствуйте! У меня {data['problem']}, "
                f"телефон {brand_model}, "
                f"нужна услуга: {data['service']}. "
                f"Деталь: {data['part_type']}. "
                f"Сколько будет стоить?")
        encoded_text = urllib.parse.quote(text)
        link = f"https://t.me/{YOUR_USERNAME}?text={encoded_text}"
        await callback.message.delete()
        await callback.message.answer(
            f"✅ Спасибо! Нажмите сюда, чтобы написать мастеру:\n👉 [Мастер Пётр]({link})",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        await state.clear()
    await callback.answer()

@dp.message(Command("price"))
async def show_price(message: types.Message):
    price_text = "📋 *Прайс-лист на услуги ремонта:*\n\n"
    for service, cost in SERVICES.items():
        price_text += f"• {service} — {cost}₽\n"
    price_text += "\n🛡 Гарантия на работу 1 месяц\n⏱ Среднее время ремонта: 3 дня\n📞 Пётр Саныч | Ремонт и продажа смартфонов"
    await message.answer(price_text, parse_mode="Markdown")

# ===== ВЕБХУК (для Bothost) =====
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    update_data = await request.json()
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)
    return JSONResponse(content={"ok": True})

@app.get("/")
async def root():
    return {"status": "ok"}

# Функция для установки вебхука (вызывается один раз при старте)
async def set_webhook():
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        await bot.set_webhook(webhook_url)
        print(f"Webhook set to {webhook_url}")

# При запуске uvicorn (Bothost сам вызывает app)
# Вам не нужен asyncio.run(), платформа сама запускает веб-сервер