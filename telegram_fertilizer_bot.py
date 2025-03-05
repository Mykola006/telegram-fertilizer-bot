import asyncio
from aiogram import Bot, Dispatcher, types
import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, PreCheckoutQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types.input_file import InputFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from dotenv import load_dotenv

# Завантаження токенів з .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")

# Ініціалізація бота і диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логування
logging.basicConfig(level=logging.INFO)

# Лічильники використання для оплати
usage_count = {}
payment_count = {}

# Класи станів для розрахунків
class FertilizerCalculation(StatesGroup):
    crop = State()
    prev_crop = State()
    moisture = State()
    yield_goal = State()
    soil_type = State()
    ph = State()
    area = State()

# Списки можливих значень
crops = ["Пшениця", "Кукурудза", "Соняшник", "Ріпак", "Ячмінь", "Соя"]
soil_types = ["Чорнозем", "Сірозем", "Піщаний", "Глинистий", "Супіщаний"]
previous_crops = ["Зернові", "Бобові", "Технічні", "Овочі", "Чистий пар"]
moisture_zones = ["Низька", "Середня", "Достатня"]

# Функція створення клавіатури
def create_keyboard(options, add_back=False, add_skip=False):
    keyboard = [[KeyboardButton(text=option)] for option in options]
    if add_back:
        keyboard.append([KeyboardButton(text="⬅️ Назад")])
    if add_skip:
        keyboard.append([KeyboardButton(text="Пропустити")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Функція для розрахунку добрив (базовий приклад)
async def calculate_fertilizer(crop, yield_goal, area, soil_type):
    nutrient_requirements = {
        "пшениця": {"N": 25, "P": 8, "K": 18},
        "кукурудза": {"N": 22, "P": 10, "K": 20},
        "соняшник": {"N": 30, "P": 15, "K": 60},
        "соя": {"N": 10, "P": 15, "K": 25},
        "ріпак": {"N": 45, "P": 12, "K": 35},
        "ячмінь": {"N": 20, "P": 8, "K": 18}
    }
    if crop not in nutrient_requirements:
        return "Помилка: невідома культура."
    needs = nutrient_requirements[crop]
    n_fertilizer = needs["N"] * yield_goal * area
    p_fertilizer = needs["P"] * yield_goal * area
    k_fertilizer = needs["K"] * yield_goal * area
    return f"🔹 Для {crop} на площі {area} га з метою {yield_goal} т/га:\n    - Азот (N): {n_fertilizer} кг\n    - Фосфор (P): {p_fertilizer} кг\n    - Калій (K): {k_fertilizer} кг"

# Функція формування PDF за допомогою reportlab
async def generate_pdf(data):
    filename = "recommendation.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, "Рекомендації по живленню")
    c.drawString(100, 730, data)
    c.save()
    return filename

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Розрахунок добрив", callback_data="calc_fertilizer")],
        [InlineKeyboardButton(text="🌱 Довідник культур", callback_data="crop_guide")],
        [InlineKeyboardButton(text="📄 Отримати PDF", callback_data="get_pdf")]
    ])
    await message.answer("Вітаю! Я бот-агроном. Оберіть дію:", reply_markup=keyboard)

# Обробник розрахунку добрив з перевіркою оплати
@dp.callback_query(lambda c: c.data == "calc_fertilizer")
async def ask_crop(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    # Перевіряємо, чи необхідна оплата
    if usage_count.get(user_id, 0) >= 1 + payment_count.get(user_id, 0):
        # Відправляємо рахунок на оплату $10
        prices = [LabeledPrice(label="Додаткова культура", amount=1000)]
        await callback_query.answer()  # закриваємо сповіщення про вибір
        await bot.send_invoice(chat_id=user_id,
                               title="Оплата розрахунку",
                               description="Оплата за розрахунок добрив для додаткової культури",
                               provider_token=PROVIDER_TOKEN,
                               currency="USD",
                               prices=prices,
                               payload="calc_payment")
        return
    # Якщо оплата не потрібна, починаємо розрахунок
    await state.set_state(FertilizerCalculation.crop)
    crop_keyboard = create_keyboard(crops)
    await callback_query.message.answer("🌾 Оберіть культуру:", reply_markup=crop_keyboard)

# Обробник вибору культури
@dp.message(FertilizerCalculation.crop)
async def ask_prev_crop(message: types.Message, state: FSMContext):
    text = message.text
    if text not in crops:
        await message.answer("❗ Будь ласка, оберіть культуру з наведених варіантів.")
        return
    # Зберігаємо вибір культури
    await state.update_data(crop=text.lower())
    # Перехід до вибору попередньої культури
    await state.set_state(FertilizerCalculation.prev_crop)
    prev_crop_kb = create_keyboard(previous_crops, add_back=True)
    await message.answer("♻️ Оберіть тип попередньої культури:", reply_markup=prev_crop_kb)

# Обробник вибору попередньої культури
@dp.message(FertilizerCalculation.prev_crop)
async def ask_moisture(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Назад":
        # Повернення до вибору культури
        await state.set_state(FertilizerCalculation.crop)
        crop_kb = create_keyboard(crops)
        await message.answer("🌾 Оберіть культуру:", reply_markup=crop_kb)
        return
    if text not in previous_crops:
        await message.answer("❗ Виберіть попередник з наведених варіантів.")
        return
    # Зберігаємо попередню культуру
    await state.update_data(prev_crop=text)
    # Перехід до вибору зони зволоження
    await state.set_state(FertilizerCalculation.moisture)
    moisture_kb = create_keyboard(moisture_zones, add_back=True)
    await message.answer("💧 Оберіть зону зволоження (низька, середня, достатня):", reply_markup=moisture_kb)

# Обробник вибору зони зволоження
@dp.message(FertilizerCalculation.moisture)
async def ask_yield(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Назад":
        # Повернення до вибору попередньої культури
        await state.set_state(FertilizerCalculation.prev_crop)
        prev_crop_kb = create_keyboard(previous_crops, add_back=True)
        await message.answer("♻️ Оберіть тип попередньої культури:", reply_markup=prev_crop_kb)
        return
    if text not in moisture_zones:
        await message.answer("❗ Оберіть зону зволоження із запропонованих варіантів.")
        return
    # Зберігаємо зону зволоження
    await state.update_data(moisture=text)
    # Запитуємо очікувану врожайність
    await state.set_state(FertilizerCalculation.yield_goal)
    yield_kb = create_keyboard([], add_back=True)
    await message.answer("📊 Введіть очікувану врожайність (т/га):", reply_markup=yield_kb)

# Обробник введення врожайності
@dp.message(FertilizerCalculation.yield_goal)
async def ask_soil(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Назад":
        # Повернення до вибору зони зволоження
        await state.set_state(FertilizerCalculation.moisture)
        moisture_kb = create_keyboard(moisture_zones, add_back=True)
        await message.answer("💧 Оберіть зону зволоження (низька, середня, достатня):", reply_markup=moisture_kb)
        return
    try:
        yield_goal = float(text.replace(',', '.'))
    except ValueError:
        await message.answer("❗ Будь ласка, введіть числове значення врожайності (можна дробове).")
        return
    # Зберігаємо врожайність
    await state.update_data(yield_goal=yield_goal)
    # Перехід до вибору типу ґрунту
    await state.set_state(FertilizerCalculation.soil_type)
    soil_kb = create_keyboard(soil_types, add_back=True)
    await message.answer("🟤 Оберіть тип ґрунту:", reply_markup=soil_kb)

# Обробник вибору типу ґрунту
@dp.message(FertilizerCalculation.soil_type)
async def ask_ph_level(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Назад":
        # Повернення до введення врожайності
        await state.set_state(FertilizerCalculation.yield_goal)
        yield_kb = create_keyboard([], add_back=True)
        await message.answer("📊 Введіть очікувану врожайність (т/га):", reply_markup=yield_kb)
        return
    if text not in soil_types:
        await message.answer("❗ Будь ласка, оберіть тип ґрунту з клавіатури.")
        return
    # Зберігаємо тип ґрунту
    await state.update_data(soil_type=text.lower())
    # Перехід до введення pH ґрунту
    await state.set_state(FertilizerCalculation.ph)
    ph_kb = create_keyboard([], add_back=True, add_skip=True)
    await message.answer("🧪 Введіть pH ґрунту або натисніть Пропустити:", reply_markup=ph_kb)

# Обробник введення pH ґрунту та формування рекомендацій
@dp.message(FertilizerCalculation.ph)
async def show_recommendations(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Назад":
        # Повернення до вибору типу ґрунту
        await state.set_state(FertilizerCalculation.soil_type)
        soil_kb = create_keyboard(soil_types, add_back=True)
        await message.answer("🟤 Оберіть тип ґрунту:", reply_markup=soil_kb)
        return
    if text == "Пропустити":
        ph_value = None
    else:
        try:
            ph_value = float(text.replace(',', '.'))
        except ValueError:
            await message.answer("❗ Введіть pH як число, наприклад 5.5.")
            return
    data = await state.get_data()
    crop = data['crop']
    yield_goal = data['yield_goal']
    prev_crop = data['prev_crop']
    moisture = data['moisture']
    soil_type = data['soil_type']
    # Розрахунки з урахуванням усіх факторів
    base_requirements = {
        "пшениця": {"N": 25, "P": 8, "K": 18},
        "кукурудза": {"N": 22, "P": 10, "K": 20},
        "соняшник": {"N": 30, "P": 15, "K": 60},
        "соя": {"N": 10, "P": 15, "K": 25},
        "ріпак": {"N": 45, "P": 12, "K": 35},
        "ячмінь": {"N": 20, "P": 8, "K": 18}
    }
    result_text = ""
    if crop not in base_requirements:
        result_text = "Помилка: невідома культура."
    else:
        # Поправки на попередник
        N_factor = P_factor = K_factor = 1.0
        if prev_crop == "Бобові":
            N_factor *= 0.8
        if prev_crop == "Чистий пар":
            N_factor *= 0.9
        if prev_crop in ["Технічні", "Овочі"]:
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        # Поправки на зону зволоження
        if moisture == "Низька":
            N_factor *= 0.9
            P_factor *= 0.9
            K_factor *= 0.9
        elif moisture == "Достатня":
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        # Поправки на тип ґрунту
        if soil_type in ["піщаний", "супіщаний"]:
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        elif soil_type == "чорнозем":
            N_factor *= 0.9
            P_factor *= 0.9
            K_factor *= 0.9
        elif soil_type in ["глинистий", "сірозем"]:
            N_factor *= 0.95
            P_factor *= 0.95
            K_factor *= 0.95
        # Остаточні норми на 1 т врожаю
        base = base_requirements[crop]
        N_rate = base["N"] * N_factor
        P_rate = base["P"] * P_factor
        K_rate = base["K"] * K_factor
        # Потреба на 1 га
        N_per_ha = N_rate * yield_goal
        P_per_ha = P_rate * yield_goal
        K_per_ha = K_rate * yield_goal
        # Формування тексту рекомендацій
        crop_name = crop.capitalize()
        result_text = f"🔹 Для культури {crop_name} при врожайності {yield_goal} т/га:\n    - Азот (N): {N_per_ha:.1f} кг/га\n    - Фосфор (P): {P_per_ha:.1f} кг/га\n    - Калій (K): {K_per_ha:.1f} кг/га\n"
        # Необхідність вапнування
        if ph_value is None:
            result_text += "ℹ️ pH ґрунту не вказано, рекомендації щодо вапнування пропущено.\n"
        elif ph_value < 5.0:
            result_text += f"⚠️ Ґрунт кислий (pH {ph_value}). Рекомендовано вапнування (~2 т/га вапна).\n"
        elif ph_value < 5.5:
            result_text += f"⚠️ Ґрунт кислий (pH {ph_value}). Рекомендовано вапнування (~1 т/га вапна).\n"
        else:
            result_text += "✅ pH ґрунту у нормі, вапнування не потрібне.\n"
        # Розподіл добрив по фазах росту
        result_text += "📈 Розподіл добрив по фазах росту:\n"
        distribution = {
            "пшениця": {
                "N": [("перед сівбою", 0.5), ("в фазі кущіння", 0.5)],
                "P": [("перед сівбою", 1.0)],
                "K": [("перед сівбою", 1.0)]
            },
            "кукурудза": {
                "N": [("перед сівбою", 0.5), ("у фазі 6-8 листків", 0.5)],
                "P": [("перед сівбою", 1.0)],
                "K": [("перед сівбою", 1.0)]
            },
            "соняшник": {
                "N": [("перед сівбою", 0.7), ("на початку бутонізації", 0.3)],
                "P": [("перед сівбою", 1.0)],
                "K": [("перед сівбою", 1.0)]
            },
            "соя": {
                "N": [("перед сівбою", 0.5), ("на початку цвітіння", 0.5)],
                "P": [("перед сівбою", 1.0)],
                "K": [("перед сівбою", 1.0)]
            },
            "ріпак": {
                "N": [("перед сівбою", 0.5), ("на початку весняної вегетації", 0.5)],
                "P": [("перед сівбою", 1.0)],
                "K": [("перед сівбою", 1.0)]
            },
            "ячмінь": {
                "N": [("перед сівбою", 0.5), ("в фазі кущіння", 0.5)],
                "P": [("перед сівбою", 1.0)],
                "K": [("перед сівбою", 1.0)]
            }
        }
        if crop in distribution:
            phases = distribution[crop]
            for nutrient, phases_list in phases.items():
                if phases_list:
                    name_ukr = "Азот" if nutrient == "N" else "Фосфор" if nutrient == "P" else "Калій"
                    portions = []
                    total_per_ha = N_per_ha if nutrient == "N" else P_per_ha if nutrient == "P" else K_per_ha
                    for phase, fraction in phases_list:
                        amount = total_per_ha * fraction
                        portions.append(f"{amount:.1f} кг - {phase}")
                    result_text += f"   - {nutrient}: " + "; ".join(portions) + "\n"
    # Додаємо рекомендовані добрива
    result_text += "💡 Рекомендовані добрива для забезпечення цієї потреби:\n"
    result_text += "   - Азотні: аміачна селітра (34% N), карбамід (46% N), КАС-32.\n"
    result_text += "   - Фосфорні: амофос (MAP), діамонійфосфат (DAP).\n"
    result_text += "   - Калійні: калій хлористий (KCl), калій сульфат.\n"
    result_text += "   - Комплексні (NPK): нітроамофоска (16:16:16), діамофоска (10:26:26).\n"
    # Надсилаємо рекомендації
    await message.answer(result_text)
    # Запитуємо площу для обчислення загальної потреби
    await state.set_state(FertilizerCalculation.area)
    area_kb = create_keyboard([], add_back=True, add_skip=True)
    await message.answer("📏 Введіть площу поля (га) для розрахунку загальної потреби або натисніть Пропустити:", reply_markup=area_kb)

# Обробник введення площі та розрахунку загальної потреби
@dp.message(FertilizerCalculation.area)
async def calculate_total(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Назад":
        # Повернення до повторного введення pH
        await state.set_state(FertilizerCalculation.ph)
        ph_kb = create_keyboard([], add_back=True, add_skip=True)
        await message.answer("🧪 Введіть pH ґрунту:", reply_markup=ph_kb)
        return
    if text == "Пропустити":
        # Завершення без розрахунку площі
        await message.answer("✅ Розрахунок завершено. Ви можете почати новий розрахунок або отримати PDF.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📊 Новий розрахунок', callback_data='calc_fertilizer')],[InlineKeyboardButton(text='📄 Отримати PDF', callback_data='get_pdf')]]))
        user_id = message.from_user.id
        usage_count[user_id] = usage_count.get(user_id, 0) + 1
        await state.clear()
        return
    try:
        area_val = float(text.replace(',', '.'))
    except ValueError:
        await message.answer("❗ Введіть числове значення площі (га) або натисніть Пропустити.")
        return
    if area_val <= 0:
        await message.answer("❗ Площа повинна бути більше 0.")
        return
    data = await state.get_data()
    yield_goal = data['yield_goal']
    crop = data['crop']
    prev_crop = data['prev_crop']
    moisture = data['moisture']
    soil_type = data['soil_type']
    base_requirements = {
        "пшениця": {"N": 25, "P": 8, "K": 18},
        "кукурудза": {"N": 22, "P": 10, "K": 20},
        "соняшник": {"N": 30, "P": 15, "K": 60},
        "соя": {"N": 10, "P": 15, "K": 25},
        "ріпак": {"N": 45, "P": 12, "K": 35},
        "ячмінь": {"N": 20, "P": 8, "K": 18}
    }
    if crop not in base_requirements:
        await message.answer("Помилка при обчисленні загальної потреби.")
    else:
        # Повторюємо ті самі поправки для розрахунку на площу
        N_factor = P_factor = K_factor = 1.0
        if prev_crop == "Бобові":
            N_factor *= 0.8
        if prev_crop == "Чистий пар":
            N_factor *= 0.9
        if prev_crop in ["Технічні", "Овочі"]:
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        if moisture == "Низька":
            N_factor *= 0.9
            P_factor *= 0.9
            K_factor *= 0.9
        elif moisture == "Достатня":
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        if soil_type in ["піщаний", "супіщаний"]:
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        elif soil_type == "чорнозем":
            N_factor *= 0.9
            P_factor *= 0.9
            K_factor *= 0.9
        elif soil_type in ["глинистий", "сірозем"]:
            N_factor *= 0.95
            P_factor *= 0.95
            K_factor *= 0.95
        base = base_requirements[crop]
        N_rate = base["N"] * N_factor
        P_rate = base["P"] * P_factor
        K_rate = base["K"] * K_factor
        total_N = N_rate * yield_goal * area_val
        total_P = P_rate * yield_goal * area_val
        total_K = K_rate * yield_goal * area_val
        total_text = f"🔸 Загальна потреба добрив на площу {area_val} га:\n    - Азот (N): {total_N:.1f} кг\n    - Фосфор (P): {total_P:.1f} кг\n    - Калій (K): {total_K:.1f} кг"
        await message.answer(total_text)
    # Завершуємо розрахунок: пропонуємо повернення до початку або PDF
    await message.answer("✅ Розрахунок завершено. Ви можете почати новий розрахунок або отримати PDF.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📊 Новий розрахунок', callback_data='calc_fertilizer')],[InlineKeyboardButton(text='📄 Отримати PDF', callback_data='get_pdf')]]))
    user_id = message.from_user.id
    usage_count[user_id] = usage_count.get(user_id, 0) + 1
    await state.clear()

# Обробник генерації PDF
@dp.callback_query(lambda c: c.data == "get_pdf")
async def send_pdf(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    pdf_content = None
    pdf_data = None
    try:
        pdf_data = await dp.storage.get_data(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
    except Exception:
        pdf_data = None
    if pdf_data and 'crop' in pdf_data:
        # Якщо є дані останнього розрахунку (припущення)
        crop = pdf_data.get('crop', '')
        pdf_content = f"Останні рекомендації по живленню для {crop}"
    if not pdf_content:
        pdf_content = "Приклад рекомендацій по живленню"
    pdf_file = await generate_pdf(pdf_content)
    await bot.send_document(callback_query.from_user.id, InputFile(pdf_file))

# Обробник довідника культур (поки що заглушка)
@dp.callback_query(lambda c: c.data == "crop_guide")
async def show_crop_guide(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("ℹ️ Довідник культур наразі недоступний.")

# Обробник запиту на підтвердження оплати
@dp.pre_checkout_query(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Обробник успішної оплати
@dp.message(lambda message: message.successful_payment is not None)
async def payment_success(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    payment_count[user_id] = payment_count.get(user_id, 0) + 1
    await message.answer("✅ Оплату отримано! Продовжуйте вибір культури для розрахунку.")
    # Після оплати автоматично переходимо до вибору культури
    await state.set_state(FertilizerCalculation.crop)
    crop_kb = create_keyboard(crops)
    await message.answer("🌾 Оберіть культуру:", reply_markup=crop_kb)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
