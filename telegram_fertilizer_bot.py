import asyncio
from aiogram import Bot, Dispatcher, types
import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types.input_file import InputFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from dotenv import load_dotenv

# Завантаження токенів з .env (токен бота та LiqPay провайдера)
load_dotenv()
TOKEN = os.getenv('TOKEN')
PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN')

# Ініціалізація бота і диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логування
logging.basicConfig(level=logging.INFO)

# Дані для відстеження використання і оплат
usage_count = {}    # лічильник розрахунків для кожного користувача
payment_count = {}  # лічильник успішних оплат для кожного користувача
final_recommendations = {}  # останні сформовані рекомендації для кожного користувача

# Адміністраторські налаштування (ID користувачів з необмеженим доступом)
ADMIN_IDS = []  # заповнити список ID адміністраторів, що мають безкоштовний доступ

# Визначення станів для FSM (кроки сценарію взаємодії)
class FertilizerCalculation(StatesGroup):
    crop = State()       # вибір культури
    prev_crop = State()  # вибір попередньої культури
    region = State()     # вибір регіону
    yield_goal = State() # введення запланованої врожайності
    soil_type = State()  # вибір типу ґрунту
    ph = State()         # введення pH ґрунту
    form_choice = State() # вибір зміни форми добрив чи продовження
    choose_n = State()    # вибір форми азотного добрива
    choose_p = State()    # вибір форми фосфорного добрива
    choose_k = State()    # вибір форми калійного добрива
    area = State()        # введення площі поля для фінального розрахунку

# Довідкові списки та словники для варіантів вибору
crops = ['Пшениця', 'Кукурудза', 'Соняшник', 'Ріпак', 'Ячмінь', 'Соя']
soil_types = ['Чорнозем', 'Сірозем', 'Піщаний', 'Глинистий', 'Супіщаний']
previous_crops = ['Зернові', 'Бобові', 'Технічні', 'Овочі', 'Чистий пар']
regions = [
    'Вінницька', 'Волинська', 'Дніпропетровська', 'Донецька', 'Житомирська',
    'Закарпатська', 'Запорізька', 'Івано-Франківська', 'Київська', 'Кіровоградська',
    'Луганська', 'Львівська', 'Миколаївська', 'Одеська', 'Полтавська',
    'Рівненська', 'Сумська', 'Тернопільська', 'Харківська', 'Херсонська',
    'Хмельницька', 'Черкаська', 'Чернівецька', 'Чернігівська'
]

# Класифікація регіонів за зонами зволоження (на основі історичних даних опадів)
region_to_zone = {
    # Низька зволоженість (південь, частково схід)
    'Одеська': 'Низька', 'Миколаївська': 'Низька', 'Херсонська': 'Низька',
    'Запорізька': 'Низька', 'Донецька': 'Низька', 'Луганська': 'Низька',
    'Дніпропетровська': 'Низька', 'Кіровоградська': 'Низька',
    # Середня зволоженість (центр, частково схід/захід)
    'Харківська': 'Середня', 'Полтавська': 'Середня', 'Черкаська': 'Середня',
    'Київська': 'Середня', 'Тернопільська': 'Середня', 'Хмельницька': 'Середня',
    'Вінницька': 'Середня',
    # Достатня зволоженість (захід, північ)
    'Львівська': 'Достатня', 'Івано-Франківська': 'Достатня', 'Закарпатська': 'Достатня',
    'Чернівецька': 'Достатня', 'Волинська': 'Достатня', 'Рівненська': 'Достатня',
    'Житомирська': 'Достатня', 'Чернігівська': 'Достатня', 'Сумська': 'Достатня'
}
# Примітка: Регіони, не вказані у словнику, за замовчуванням вважаються середньозволоженими.

# Середня врожайність по Україні (Мінагрополітики, 2024) для основних культур, т/га
national_yield_2024 = {
    'пшениця': 4.47,    # 44.7 ц/га
    'кукурудза': 6.40,  # 64.0 ц/га
    'соняшник': 2.30,   # ~23 ц/га
    'ріпак': 2.74,      # 27.4 ц/га
    'ячмінь': 3.81,     # 38.1 ц/га
    'соя': 2.28         # 22.8 ц/га
}

# Функція створення клавіатури з опціональними кнопками "Назад" та "Пропустити"
def create_keyboard(options, add_back=False, add_skip=False):
    keyboard = [[KeyboardButton(text=option)] for option in options]
    if add_back:
        keyboard.append([KeyboardButton(text='⬅️ Назад')])
    if add_skip:
        keyboard.append([KeyboardButton(text='Пропустити')])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Функція генерації PDF із рекомендаціями
async def generate_pdf(recommendation_text: str):
    filename = 'recommendation.pdf'
    c = canvas.Canvas(filename, pagesize=letter)
    # Розбиваємо текст рекомендацій на рядки
    lines = recommendation_text.split('\n')
    y = 750  # початкова висота для першого рядка
    c.setFont('Helvetica', 12)
    c.drawString(50, y + 20, 'Рекомендації по живленню')  # заголовок
    for line in lines:
        c.drawString(50, y, line)
        y -= 20  # зміщуємося вниз для наступного рядка
    c.save()
    return filename

# Команда /start - стартове повідомлення з меню
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Розрахунок добрив', callback_data='calc_fertilizer')],
        [InlineKeyboardButton(text='🌱 Довідник культур', callback_data='crop_guide')],
        [InlineKeyboardButton(text='📄 Отримати PDF', callback_data='get_pdf')]
    ])
    await message.answer('Вітаю! Я бот-агроном. Оберіть дію:', reply_markup=keyboard)

# Обробник вибору "Розрахунок добрив" з перевіркою ліміту і оплати
@dp.callback_query(lambda c: c.data == 'calc_fertilizer')
async def start_calculation(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    # Перевірка ліміту безкоштовних розрахунків (1 безкоштовний + кожен оплачений додає ще 1)
    if user_id not in ADMIN_IDS:
        if usage_count.get(user_id, 0) >= 1 + payment_count.get(user_id, 0):
            # Вимагаємо оплату через LiqPay (ціна в копійках: 1000 = 10.00 USD)
            prices = [LabeledPrice(label='Додатковий розрахунок', amount=1000)]
            await callback_query.answer()  # закриваємо сповіщення вибору
            await bot.send_invoice(
                chat_id=user_id,
                title='Оплата розрахунку',
                description='Оплата за додатковий розрахунок добрив',
                provider_token=PROVIDER_TOKEN,
                currency='USD',
                prices=prices,
                payload='calc_payment'
            )
            return
    # Якщо оплата не потрібна – починаємо сценарій розрахунку
    await state.set_state(FertilizerCalculation.crop)
    crop_keyboard = create_keyboard(crops)
    await callback_query.message.answer('🌾 Оберіть культуру:', reply_markup=crop_keyboard)

# Обробник вибору культури
@dp.message(FertilizerCalculation.crop)
async def select_crop(message: types.Message, state: FSMContext):
    text = message.text
    if text not in crops:
        await message.answer('❗ Будь ласка, оберіть культуру з наведених варіантів.')
        return
    # Зберігаємо вибір культури (у нижньому регістрі для використання в словниках)
    await state.update_data(crop=text.lower())
    # Переходимо до вибору попередньої культури
    await state.set_state(FertilizerCalculation.prev_crop)
    prev_crop_kb = create_keyboard(previous_crops, add_back=True)
    await message.answer('♻️ Оберіть тип попередньої культури:', reply_markup=prev_crop_kb)

# Обробник вибору попередньої культури
@dp.message(FertilizerCalculation.prev_crop)
async def select_prev_crop(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до вибору культури
        await state.set_state(FertilizerCalculation.crop)
        crop_kb = create_keyboard(crops)
        await message.answer('🌾 Оберіть культуру:', reply_markup=crop_kb)
        return
    if text not in previous_crops:
        await message.answer('❗ Виберіть попередник з наведених варіантів.')
        return
    # Зберігаємо попередню культуру
    await state.update_data(prev_crop=text)
    # Перехід до вибору регіону
    await state.set_state(FertilizerCalculation.region)
    region_kb = create_keyboard(regions, add_back=True)
    await message.answer('📍 Оберіть регіон вирощування:', reply_markup=region_kb)

# Обробник вибору регіону
@dp.message(FertilizerCalculation.region)
async def select_region(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до вибору попередньої культури
        await state.set_state(FertilizerCalculation.prev_crop)
        prev_crop_kb = create_keyboard(previous_crops, add_back=True)
        await message.answer('♻️ Оберіть тип попередньої культури:', reply_markup=prev_crop_kb)
        return
    if text not in regions:
        await message.answer('❗ Будь ласка, оберіть регіон з наведених варіантів.')
        return
    # Зберігаємо регіон
    await state.update_data(region=text)
    # Визначаємо зону зволоження для цього регіону
    zone = region_to_zone.get(text, 'Середня')
    await state.update_data(moisture=zone)
    # Запитуємо очікувану врожайність
    await state.set_state(FertilizerCalculation.yield_goal)
    yield_kb = create_keyboard([], add_back=True)
    await message.answer('📊 Вкажіть очікувану врожайність (т/га):', reply_markup=yield_kb)

# Обробник введення запланованої врожайності
@dp.message(FertilizerCalculation.yield_goal)
async def input_yield(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до вибору регіону
        await state.set_state(FertilizerCalculation.region)
        region_kb = create_keyboard(regions, add_back=True)
        await message.answer('📍 Оберіть регіон вирощування:', reply_markup=region_kb)
        return
    # Обробляємо введення числового значення врожайності
    try:
        yield_goal = float(text.replace(',', '.'))
    except ValueError:
        await message.answer('❗ Введіть числове значення врожайності (можна дробове).')
        return
    if yield_goal <= 0:
        await message.answer('❗ Врожайність повинна бути більше 0.')
        return
    # Зберігаємо врожайність
    await state.update_data(yield_goal=yield_goal)
    # Перехід до вибору типу ґрунту
    await state.set_state(FertilizerCalculation.soil_type)
    soil_kb = create_keyboard(soil_types, add_back=True)
    await message.answer('🟤 Оберіть тип ґрунту:', reply_markup=soil_kb)

# Обробник вибору типу ґрунту
@dp.message(FertilizerCalculation.soil_type)
async def select_soil(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до введення врожайності
        await state.set_state(FertilizerCalculation.yield_goal)
        yield_kb = create_keyboard([], add_back=True)
        await message.answer('📊 Вкажіть очікувану врожайність (т/га):', reply_markup=yield_kb)
        return
    if text not in soil_types:
        await message.answer('❗ Будь ласка, оберіть тип ґрунту з клавіатури.')
        return
    # Зберігаємо тип ґрунту (у нижньому регістрі для використання в словниках)
    await state.update_data(soil_type=text.lower())
    # Перехід до введення pH ґрунту
    await state.set_state(FertilizerCalculation.ph)
    ph_kb = create_keyboard([], add_back=True)
    await message.answer('🧪 Введіть pH ґрунту:', reply_markup=ph_kb)

# Обробник введення pH ґрунту та обчислення рекомендацій
@dp.message(FertilizerCalculation.ph)
async def compute_recommendations(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до вибору типу ґрунту
        await state.set_state(FertilizerCalculation.soil_type)
        soil_kb = create_keyboard(soil_types, add_back=True)
        await message.answer('🟤 Оберіть тип ґрунту:', reply_markup=soil_kb)
        return
    # Обробка введення pH як числа
    try:
        ph_value = float(text.replace(',', '.'))
    except ValueError:
        await message.answer('❗ Введіть pH як число, наприклад 5.5.')
        return
    # Отримуємо всі зібрані раніше дані із FSM
    data = await state.get_data()
    crop = data['crop']
    yield_goal = data['yield_goal']
    prev_crop = data['prev_crop']
    moisture = data['moisture']
    soil_type = data['soil_type']
    region = data.get('region', '')
    # Базові вимоги до елементів (кг елемента на 1 т урожаю) для різних культур
    base_requirements = {
        'пшениця': {'N': 30, 'P': 10, 'K': 20},
        'кукурудза': {'N': 25, 'P': 12, 'K': 25},
        'соняшник': {'N': 42, 'P': 18, 'K': 85},
        'соя': {'N': 15, 'P': 20, 'K': 30},
        'ріпак': {'N': 50, 'P': 15, 'K': 40},
        'ячмінь': {'N': 25, 'P': 10, 'K': 20}
    }
    result_text = ''
    if crop not in base_requirements:
        result_text = 'Помилка: невідома культура.'
    else:
        # Коефіцієнти коригування залежно від попередника, зони зволоження і типу ґрунту
        N_factor = P_factor = K_factor = 1.0
        # Попередня культура
        if prev_crop == 'Бобові':
            N_factor *= 0.8  # після бобових залишається більше азоту в ґрунті
        if prev_crop == 'Чистий пар':
            N_factor *= 0.9  # після пару потрібне трохи менше азоту
        if prev_crop in ['Технічні', 'Овочі']:
            # після технічних та овочевих культур можливе виснаження ґрунту
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        # Зона зволоження
        if moisture == 'Низька':
            # У посушливих умовах зменшуємо норми (~ -10%)
            N_factor *= 0.9
            P_factor *= 0.9
            K_factor *= 0.9
        elif moisture == 'Достатня':
            # У вологих умовах збільшуємо норми (~ +10%)
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        # Тип ґрунту
        if soil_type in ['піщаний', 'супіщаний']:
            # Легкі ґрунти (піски) гірше утримують елементи – збільшуємо норму
            N_factor *= 1.1
            P_factor *= 1.1
            K_factor *= 1.1
        elif soil_type == 'чорнозем':
            # Родючі чорноземи – трохи зменшуємо норму, частина потреби забезпечиться ґрунтом
            N_factor *= 0.9
            P_factor *= 0.9
            K_factor *= 0.9
        elif soil_type in ['глинистий', 'сірозем']:
            # Глинисті та сіроземи – незначне зменшення норм
            N_factor *= 0.95
            P_factor *= 0.95
            K_factor *= 0.95
        # Розрахунок потреби елементів на 1 га для планової врожайності
        base = base_requirements[crop]
        N_rate = base['N'] * N_factor   # кг N на 1 т урожаю з урахуванням поправок
        P_rate = base['P'] * P_factor   # кг P2O5 на 1 т урожаю
        K_rate = base['K'] * K_factor   # кг K2O на 1 т урожаю
        N_per_ha = N_rate * yield_goal  # кг N на 1 га
        P_per_ha = P_rate * yield_goal  # кг P2O5 на 1 га
        K_per_ha = K_rate * yield_goal  # кг K2O на 1 га
        crop_name = crop.capitalize()
        result_text += f'🔹 Для культури {crop_name} при врожайності {yield_goal:.1f} т/га:\n'
        result_text += f'   - Азот (N): {N_per_ha:.1f} кг/га\n'
        result_text += f'   - Фосфор (P): {P_per_ha:.1f} кг/га\n'
        result_text += f'   - Калій (K): {K_per_ha:.1f} кг/га\n'
        # Додаємо інформацію про середню врожайність у регіоні (2024) для довідки
        if region:
            avg_yield = None
            if crop in national_yield_2024:
                base_avg = national_yield_2024[crop]
                zone_factor = 1.0
                if moisture == 'Достатня':
                    zone_factor = 1.3  # вологий регіон ~30% вище середнього
                elif moisture == 'Низька':
                    zone_factor = 0.7  # посушливий регіон ~30% нижче середнього
                avg_yield = base_avg * zone_factor
            if avg_yield:
                result_text += f'   (Середня врожайність {crop_name} в {region} у 2024 р. ~ {avg_yield:.1f} т/га)\n'
        # Рекомендації щодо вапнування при низькому pH
        if ph_value < 5.0:
            result_text += f'⚠️ Ґрунт кислий (pH {ph_value}). Рекомендовано вапнування (~2 т/га вапна).\n'
        elif ph_value < 5.5:
            result_text += f'⚠️ Ґрунт кислий (pH {ph_value}). Рекомендовано вапнування (~1 т/га вапна).\n'
        else:
            result_text += '✅ pH ґрунту в нормі, вапнування не потрібне.\n'
        # Розподіл добрив по фазах росту (частка від загальної норми по кожному елементу)
        phase_distribution = {
            'пшениця': {
                'N': [('перед сівбою', 0.5), ('у фазі кущіння', 0.5)],
                'P': [('перед сівбою', 1.0)],
                'K': [('перед сівбою', 1.0)]
            },
            'кукурудза': {
                'N': [('перед сівбою', 0.5), ('у фазі 6-8 листків', 0.5)],
                'P': [('перед сівбою', 1.0)],
                'K': [('перед сівбою', 1.0)]
            },
            'соняшник': {
                'N': [('перед сівбою', 0.7), ('на початку бутонізації', 0.3)],
                'P': [('перед сівбою', 1.0)],
                'K': [('перед сівбою', 1.0)]
            },
            'соя': {
                'N': [('перед сівбою', 0.5), ('на початку цвітіння', 0.5)],
                'P': [('перед сівбою', 1.0)],
                'K': [('перед сівбою', 1.0)]
            },
            'ріпак': {
                'N': [('перед сівбою', 0.5), ('на початку весняної вегетації', 0.5)],
                'P': [('перед сівбою', 1.0)],
                'K': [('перед сівбою', 1.0)]
            },
            'ячмінь': {
                'N': [('перед сівбою', 0.5), ('у фазі кущіння', 0.5)],
                'P': [('перед сівбою', 1.0)],
                'K': [('перед сівбою', 1.0)]
            }
        }
        result_text += '📈 Розподіл добрив по фазах росту:\n'
        if crop in phase_distribution:
            phases = phase_distribution[crop]
            for nutrient, phases_list in phases.items():
                if phases_list:
                    name_ukr = 'Азот' if nutrient == 'N' else 'Фосфор' if nutrient == 'P' else 'Калій'
                    portions = []
                    total_per_ha = N_per_ha if nutrient == 'N' else P_per_ha if nutrient == 'P' else K_per_ha
                    for phase, fraction in phases_list:
                        amount = total_per_ha * fraction
                        portions.append(f'{amount:.1f} кг - {phase}')
                    result_text += f'   - {name_ukr}: ' + '; '.join(portions) + '\n'
        # Зберігаємо розраховані потреби (для подальших кроків)
        await state.update_data(N_per_ha=N_per_ha, P_per_ha=P_per_ha, K_per_ha=K_per_ha)
    # Надсилаємо користувачу сформований текст рекомендацій (норми і фази)
    await message.answer(result_text)
    data = await state.get_data()
    # Вибір форми азотного добрива за замовчуванням залежно від зони зволоження
    if moisture == 'Низька':
        N_form = 'Амміачна селітра (34% N)'
        N_content = 0.34
    else:
        N_form = 'Карбамід (46% N)'
        N_content = 0.46
    # Форма фосфорного добрива (DAP за замовчуванням)
    P_form = 'Діамофосфат (DAP, 46% P2O5)'
    P_content = 0.46
    # Форма калійного добрива (хлористий калій за замовчуванням)
    K_form = 'Калій хлористий (KCl, 60% K2O)'
    K_content = 0.60
    # Зберігаємо вибір форм і вміст діючої речовини (%) для кожного добрива
    await state.update_data(N_form=N_form, P_form=P_form, K_form=K_form,
                             N_content=N_content, P_content=P_content, K_content=K_content)
    # Обчислюємо рекомендовану кількість кожного добрива на 1 га
    N_per_ha = data['N_per_ha']
    P_per_ha = data['P_per_ha']
    K_per_ha = data['K_per_ha']
    N_fert_per_ha = N_per_ha / N_content
    P_fert_per_ha = P_per_ha / P_content
    K_fert_per_ha = K_per_ha / K_content
    fert_text = '💊 Рекомендовані добрива (на 1 га):\n'
    fert_text += f'   - Азот: {N_fert_per_ha:.1f} кг — {N_form}\n'
    fert_text += f'   - Фосфор: {P_fert_per_ha:.1f} кг — {P_form}\n'
    fert_text += f'   - Калій: {K_fert_per_ha:.1f} кг — {K_form}\n'
    fert_text += '💡 Ви можете змінити тип добрив перед фінальним розрахунком.'
    # Переходимо до стану вибору дії (змінити форму або продовжити)
    await state.set_state(FertilizerCalculation.form_choice)
    form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
    await message.answer(fert_text, reply_markup=form_kb)

# Обробник вибору дії на етапі вибору форм добрив
@dp.message(FertilizerCalculation.form_choice)
async def change_or_continue(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до повторного введення pH
        await state.set_state(FertilizerCalculation.ph)
        ph_kb = create_keyboard([], add_back=True)
        await message.answer('🧪 Введіть pH ґрунту:', reply_markup=ph_kb)
        return
    text_lower = text.lower()
    if 'азот' in text_lower:
        # Користувач хоче змінити азотне добриво
        await state.set_state(FertilizerCalculation.choose_n)
        n_options = ['Амміачна селітра (34% N)', 'Карбамід (46% N)', 'КАС (32% N)']
        n_kb = create_keyboard(n_options, add_back=True)
        await message.answer('🔄 Оберіть форму азотного добрива:', reply_markup=n_kb)
    elif 'фосфор' in text_lower:
        # Змінити фосфорне добриво
        await state.set_state(FertilizerCalculation.choose_p)
        p_options = ['Діамофосфат (DAP, 46% P2O5)', 'Суперфосфат (46% P2O5)']
        p_kb = create_keyboard(p_options, add_back=True)
        await message.answer('🔄 Оберіть форму фосфорного добрива:', reply_markup=p_kb)
    elif 'калій' in text_lower:
        # Змінити калійне добриво
        await state.set_state(FertilizerCalculation.choose_k)
        k_options = ['Калій хлористий (60% K2O)', 'Калій сульфат (50% K2O)']
        k_kb = create_keyboard(k_options, add_back=True)
        await message.answer('🔄 Оберіть форму калійного добрива:', reply_markup=k_kb)
    elif 'продовжити' in text_lower:
        # Продовжуємо до введення площі поля (фінальний етап)
        await state.set_state(FertilizerCalculation.area)
        area_kb = create_keyboard([], add_back=True, add_skip=True)
        await message.answer('📏 Введіть площу поля (га) для розрахунку загальної потреби або натисніть "Пропустити":', reply_markup=area_kb)
    else:
        await message.answer('❗ Оберіть дію із клавіатури: змінити форму добрива або продовжити.')
        return

# Обробник вибору нової форми азотного добрива
@dp.message(FertilizerCalculation.choose_n)
async def choose_n_form(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до меню форм добрив
        await state.set_state(FertilizerCalculation.form_choice)
        form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
        await message.answer('↩️ Повернення. Виберіть подальшу дію:', reply_markup=form_kb)
        return
    # Можливі варіанти азотних добрив і їх N-вміст
    options = {'Амміачна селітра': (0.34, 'Амміачна селітра (34% N)'),
               'Карбамід': (0.46, 'Карбамід (46% N)'),
               'КАС': (0.32, 'КАС (32% N)')}
    chosen = None
    for key in options:
        if key in text:
            chosen = options[key]
            break
    if not chosen:
        await message.answer('❗ Оберіть варіант азотного добрива з наведених.')
        return
    N_content, N_form = chosen
    # Оновлюємо вибір форми азотного добрива
    await state.update_data(N_content=N_content, N_form=N_form)
    # Перераховуємо кількість добрив з урахуванням нової форми
    data = await state.get_data()
    N_per_ha = data['N_per_ha']
    P_per_ha = data['P_per_ha']
    K_per_ha = data['K_per_ha']
    P_content = data['P_content']
    K_content = data['K_content']
    P_form = data['P_form']
    K_form = data['K_form']
    N_fert_per_ha = N_per_ha / N_content
    P_fert_per_ha = P_per_ha / P_content
    K_fert_per_ha = K_per_ha / K_content
    fert_text = '✅ Оновлені добрива (на 1 га):\n'
    fert_text += f'   - Азот: {N_fert_per_ha:.1f} кг — {N_form}\n'
    fert_text += f'   - Фосфор: {P_fert_per_ha:.1f} кг — {P_form}\n'
    fert_text += f'   - Калій: {K_fert_per_ha:.1f} кг — {K_form}\n'
    # Повертаємося до меню вибору дії (можливість змінити інші добрива або продовжити)
    await state.set_state(FertilizerCalculation.form_choice)
    form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
    await message.answer(fert_text, reply_markup=form_kb)

# Обробник вибору нової форми фосфорного добрива
@dp.message(FertilizerCalculation.choose_p)
async def choose_p_form(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до меню форм добрив
        await state.set_state(FertilizerCalculation.form_choice)
        form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
        await message.answer('↩️ Повернення. Виберіть подальшу дію:', reply_markup=form_kb)
        return
    options = {'Діамофосфат': (0.46, 'Діамофосфат (DAP, 46% P2O5)'),
               'Суперфосфат': (0.46, 'Суперфосфат (46% P2O5)')}
    chosen = None
    for key in options:
        if key in text:
            chosen = options[key]
            break
    if not chosen:
        await message.answer('❗ Оберіть варіант фосфорного добрива з наведених.')
        return
    P_content, P_form = chosen
    await state.update_data(P_content=P_content, P_form=P_form)
    # Перерахунок кількості добрив з новою формою фосфору
    data = await state.get_data()
    N_per_ha = data['N_per_ha']
    P_per_ha = data['P_per_ha']
    K_per_ha = data['K_per_ha']
    N_content = data['N_content']
    K_content = data['K_content']
    N_form = data['N_form']
    K_form = data['K_form']
    N_fert_per_ha = N_per_ha / N_content
    P_fert_per_ha = P_per_ha / P_content
    K_fert_per_ha = K_per_ha / K_content
    fert_text = '✅ Оновлені добрива (на 1 га):\n'
    fert_text += f'   - Азот: {N_fert_per_ha:.1f} кг — {N_form}\n'
    fert_text += f'   - Фосфор: {P_fert_per_ha:.1f} кг — {P_form}\n'
    fert_text += f'   - Калій: {K_fert_per_ha:.1f} кг — {K_form}\n'
    await state.set_state(FertilizerCalculation.form_choice)
    form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
    await message.answer(fert_text, reply_markup=form_kb)

# Обробник вибору нової форми калійного добрива
@dp.message(FertilizerCalculation.choose_k)
async def choose_k_form(message: types.Message, state: FSMContext):
    text = message.text
    if text.endswith('Назад'):
        # Повернення до меню форм добрив
        await state.set_state(FertilizerCalculation.form_choice)
        form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
        await message.answer('↩️ Повернення. Виберіть подальшу дію:', reply_markup=form_kb)
        return
    options = {'хлористий': (0.60, 'Калій хлористий (KCl, 60% K2O)'),
               'сульфат': (0.50, 'Калій сульфат (50% K2O)')}
    chosen = None
    for key in options:
        if key in text:
            chosen = options[key]
            break
    if not chosen:
        await message.answer('❗ Оберіть варіант калійного добрива з наведених.')
        return
    K_content, K_form = chosen
    await state.update_data(K_content=K_content, K_form=K_form)
    # Перерахунок кількості добрив з новою формою калію
    data = await state.get_data()
    N_per_ha = data['N_per_ha']
    P_per_ha = data['P_per_ha']
    K_per_ha = data['K_per_ha']
    N_content = data['N_content']
    P_content = data['P_content']
    N_form = data['N_form']
    P_form = data['P_form']
    N_fert_per_ha = N_per_ha / N_content
    P_fert_per_ha = P_per_ha / P_content
    K_fert_per_ha = K_per_ha / K_content
    fert_text = '✅ Оновлені добрива (на 1 га):\n'
    fert_text += f'   - Азот: {N_fert_per_ha:.1f} кг — {N_form}\n'
    fert_text += f'   - Фосфор: {P_fert_per_ha:.1f} кг — {P_form}\n'
    fert_text += f'   - Калій: {K_fert_per_ha:.1f} кг — {K_form}\n'
    await state.set_state(FertilizerCalculation.form_choice)
    form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
    await message.answer(fert_text, reply_markup=form_kb)

# Обробник введення площі та розрахунку загальної потреби
@dp.message(FertilizerCalculation.area)
async def calculate_total_need(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    if text.endswith('Назад'):
        # Повернення до меню зміни форм добрив
        await state.set_state(FertilizerCalculation.form_choice)
        form_kb = create_keyboard(['Змінити азот', 'Змінити фосфор', 'Змінити калій', 'Продовжити'], add_back=True)
        await message.answer('↩️ Повернення до вибору дії перед розрахунком площі:', reply_markup=form_kb)
        return
    if text == 'Пропустити':
        # Завершуємо без вказання площі (залишаємо дані на 1 га)
        await message.answer('✅ Розрахунок завершено. Ви можете почати новий розрахунок або отримати PDF звіт.')
        usage_count[user_id] = usage_count.get(user_id, 0) + 1
        data = await state.get_data()
        final_recommendation = ''
        crop = data.get('crop', '')
        if crop:
            crop_name = crop.capitalize()
            final_recommendation += f'Рекомендації для {crop_name}\n'
        if 'N_per_ha' in data:
            N_per_ha = data['N_per_ha']; P_per_ha = data['P_per_ha']; K_per_ha = data['K_per_ha']
            final_recommendation += f'Азот: {N_per_ha:.1f} кг/га; Фосфор: {P_per_ha:.1f} кг/га; Калій: {K_per_ha:.1f} кг/га\n'
        if 'N_form' in data:
            N_content = data['N_content']; P_content = data['P_content']; K_content = data['K_content']
            N_fert = data['N_per_ha'] / N_content
            P_fert = data['P_per_ha'] / P_content
            K_fert = data['K_per_ha'] / K_content
            final_recommendation += 'Рекомендовані форми добрив на 1 га:\n'
            final_recommendation += ' - ' + data['N_form'] + ': ' + '{:.1f}'.format(N_fert) + ' кг/га\n'
            final_recommendation += ' - ' + data['P_form'] + ': ' + '{:.1f}'.format(P_fert) + ' кг/га\n'
            final_recommendation += ' - ' + data['K_form'] + ': ' + '{:.1f}'.format(K_fert) + ' кг/га\n'
        final_recommendations[user_id] = final_recommendation
        await state.clear()
        return
    # Обробка введення площі (га) як числа
    try:
        area_val = float(text.replace(',', '.'))
    except ValueError:
        await message.answer('❗ Введіть числове значення площі (га) або натисніть "Пропустити".')
        return
    if area_val <= 0:
        await message.answer('❗ Площа повинна бути більше 0.')
        return
    data = await state.get_data()
    crop = data.get('crop', '')
    N_per_ha = data.get('N_per_ha'); P_per_ha = data.get('P_per_ha'); K_per_ha = data.get('K_per_ha')
    N_content = data.get('N_content'); P_content = data.get('P_content'); K_content = data.get('K_content')
    N_form = data.get('N_form'); P_form = data.get('P_form'); K_form = data.get('K_form')
    if N_per_ha is None:
        await message.answer('Помилка: дані для розрахунку не знайдено.')
    else:
        # Обчислюємо загальну потребу по елементах на вказану площу
        total_N = N_per_ha * area_val
        total_P = P_per_ha * area_val
        total_K = K_per_ha * area_val
        total_text = f'🔸 Загальна потреба на площу {area_val:.1f} га:\n'
        total_text += f'   - Азот (N): {total_N:.1f} кг\n'
        total_text += f'   - Фосфор (P): {total_P:.1f} кг\n'
        total_text += f'   - Калій (K): {total_K:.1f} кг\n'
        # Переводимо в фізичну масу добрив відповідно до обраних форм
        total_N_fert = total_N / N_content
        total_P_fert = total_P / P_content
        total_K_fert = total_K / K_content
        total_text += '💰 У фізичній масі добрив це приблизно:\n'
        total_text += f'   - {N_form}: {total_N_fert:.1f} кг\n'
        total_text += f'   - {P_form}: {total_P_fert:.1f} кг\n'
        total_text += f'   - {K_form}: {total_K_fert:.1f} кг'
        await message.answer(total_text)
        # Формуємо текст для PDF звіту
        crop_name = crop.capitalize() if crop else ''
        final_recommendation = f'Рекомендації для {crop_name} (на {area_val:.1f} га):\n'
        final_recommendation += f'Вміст елементів на 1 га: N {N_per_ha:.1f} кг, P {P_per_ha:.1f} кг, K {K_per_ha:.1f} кг.\n'
        final_recommendation += f'Рекомендовані добрива на 1 га: {N_form} {(N_per_ha/N_content):.1f} кг, {P_form} {(P_per_ha/P_content):.1f} кг, {K_form} {(K_per_ha/K_content):.1f} кг.\n'
        final_recommendation += f'Загальна потреба на {area_val:.1f} га: {N_form} {total_N_fert:.1f} кг, {P_form} {total_P_fert:.1f} кг, {K_form} {total_K_fert:.1f} кг.'
        final_recommendations[user_id] = final_recommendation
    usage_count[user_id] = usage_count.get(user_id, 0) + 1
    await state.clear()
    await message.answer('✅ Розрахунок завершено. Ви можете почати новий розрахунок або отримати PDF звіт командою /start.')

# Обробник генерації PDF звіту
@dp.callback_query(lambda c: c.data == 'get_pdf')
async def send_pdf(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    pdf_content = final_recommendations.get(user_id, '')
    if not pdf_content:
        pdf_content = 'Немає даних для формування рекомендацій. Виконайте розрахунок спочатку.'
    pdf_file = await generate_pdf(pdf_content)
    from aiogram.types import FSInputFile

await bot.send_document(chat_id=user_id, document=FSInputFile(pdf_file))

# Обробник довідника культур (поки що заглушка)
@dp.callback_query(lambda c: c.data == 'crop_guide')
async def show_crop_guide(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer('ℹ️ Довідник культур наразі недоступний.')

# Обробник передперевірки оплати (LiqPay)
@dp.pre_checkout_query(lambda query: True)
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Обробник підтвердження успішної оплати
@dp.message(lambda message: message.successful_payment is not None)
async def payment_successful(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    payment_count[user_id] = payment_count.get(user_id, 0) + 1
    await message.answer('✅ Оплату отримано! Ви отримали додатковий розрахунок.')
    # Після оплати автоматично переходимо до вибору культури для нового розрахунку
    await state.set_state(FertilizerCalculation.crop)
    crop_kb = create_keyboard(crops)
    await message.answer('🌾 Оберіть культуру:', reply_markup=crop_kb)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
