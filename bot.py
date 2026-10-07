import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# ========================================================
# НАСТРОЙКА БОТА
# ========================================================
BOT_TOKEN = "8666147992:AAEvLNXU84R1syfrOaVjYoceXN4rNnqFRgA"
ADMIN_ID = 8666147992  # Твой личный ID администратора
PAYMENT_REQUISITES = "Карта Сбер / Т-Банк: 4276 •••• •••• 1234" # Номер карты
# ========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
users_db = {}

def generate_mock_key(username):
    return f"vless://mock-uuid-12345-hestvpn@{ADMIN_ID}.com:443?security=reality&sni=google.com&fp=chrome#HestVPN_{username or 'User'}"

def get_main_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Купить подписку (100₽)", callback_data="buy_subscription")
    user_data = users_db.get(user_id, {})
    if not user_data.get("trial_used", False):
        builder.button(text="🎁 Активировать тест (24ч)", callback_data="take_trial")
    builder.button(text="👤 Мой профиль", callback_data="my_profile")
    builder.button(text="📱 Инструкция для Happ", callback_data="instructions")
    builder.adjust(1, 1, 2)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"username": message.from_user.username, "trial_used": False, "expires_at": None, "vpn_key": None}
    welcome_text = "⚡️ **Приветствуем в Hest.VPN!**\n\nНаши конфигурации отлично подходят для приложения **Happ - Proxy Utility**.\n\nВыбери нужный пункт меню ниже 👇"
    await message.answer(welcome_text, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

@dp.callback_query(F.data == "my_profile")
async def process_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = users_db.get(user_id, {"expires_at": None, "vpn_key": None})
    status = "❌ Не активна"
    expires_str = "—"
    key_info = "⚡️ Появится после активации теста или покупки."
    if user_data["expires_at"] and user_data["expires_at"] > datetime.now():
        status = "🟢 Активна"
        expires_str = user_data["expires_at"].strftime("%d.%m.%Y %H:%M")
        key_info = f"`{user_data['vpn_key']}`\n\n*(Нажми на ключ, чтобы скопировать)*"
    profile_text = f"👤 **Ваш профиль Hest.VPN**\n\n• **Ваш ID:** `{user_id}`\n• **Статус:** {status}\n• **До:** {expires_str}\n\n🔑 **VPN-ключ:**\n{key_info}"
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    await callback.message.edit_text(profile_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "take_trial")
async def process_trial(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = users_db.get(user_id)
    if not user_data or user_data.get("trial_used", False):
        await callback.answer("⚠️ Тест можно взять только 1 раз!", show_alert=True)
        return
    user_data["trial_used"] = True
    user_data["expires_at"] = datetime.now() + timedelta(days=1)
    user_data["vpn_key"] = generate_mock_key(user_data["username"])
    success_text = f"🎉 **Тестовый доступ на 24 часа активирован!**\n\n🔑 Твой ключ:\n`{user_data['vpn_key']}`\n\nСкопируй его и читай инструкцию по настройке."
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В главное меню", callback_data="back_to_menu")
    await callback.message.edit_text(success_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "buy_subscription")
async def process_buy(callback: types.CallbackQuery):
    pay_text = f"💳 **Покупка подписки Hest.VPN**\n\nСтоимость: **100 рублей на 30 дней**.\n\n📌 **Реквизиты для оплаты:**\n`{PAYMENT_REQUISITES}`\n\n📥 **Что делать дальше:**\nПереведи 100₽ и **пришли скриншот чека прямо сюда, в этот чат**. Администратор сразу проверит и включит тебе доступ!"
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Отмена", callback_data="back_to_menu")
    await callback.message.edit_text(pay_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "instructions")
async def process_instructions(callback: types.CallbackQuery):
    inst_text = "📱 **Инструкция по настройке Happ VPN**:\n\n1. Скачай приложение **Happ - Proxy Utility**.\n2. Скопируй ключ из раздела **Мой профиль** в боте.\n3. В приложении Happ нажми на **знак плюса (+)** вверху справа.\n4. Выбери добавить из буфера.\n5. Нажми кнопку **Подключить** по центру экрана."
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    await callback.message.edit_text(inst_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_menu")
async def process_back(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери интересующий раздел меню ниже 👇", reply_markup=get_main_keyboard(callback.from_user.id))

@dp.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    await message.answer("📥 **Чек отправлен создателю бота!**\nОжидайте проверки и активации подписки.")
    admin_builder = InlineKeyboardBuilder()
    admin_builder.button(text="✅ Одобрить 30 дней", callback_data=f"approve_{message.from_user.id}")
    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=f"💰 **Новый чек на 100 рублей!**\n• От: @{message.from_user.username}\n• ID: `{message.from_user.id}`", reply_markup=admin_builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("approve_"))
async def process_admin_approve(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Вы не администратор бота!", show_alert=True)
        return
    client_id = int(callback.data.split("_"))
    if client_id in users_db:
        users_db[client_id]["expires_at"] = datetime.now() + timedelta(days=30)
        if not users_db[client_id]["vpn_key"]:
            users_db[client_id]["vpn_key"] = generate_mock_key(users_db[client_id]["username"])
        try: await bot.send_message(chat_id=client_id, text="🎉 **Ура! Твоя оплата успешно проверена.**\n\nПодписка на 30 дней активирована! Твой ключ ждет тебя в меню **👤 Мой профиль**.")
        except: pass
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟢 **ПОДПИСКА ОДОБРЕНА**")
    else:
        await callback.answer("Ошибка: пользователь не найден в памяти.")

async def main():
    print("Бот успешно запущен и готов к тестам!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
