from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import json

# Токен бота
API_TOKEN = "7990680964:AAGunNLG6nbMnJSSJxNN3ac6hh_l6GkjHdg"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Файл для хранения данных
DATA_FILE = "votes_data.json"

# Номинации и кандидаты
nominations = {
    "Лучший игрок (Золотой мяч)": ["Дядя Коля", "Дядя Олег", "Никита Кратович", "Андрей Перегудов", "Руслан Смоляков", "Никита Сазонов", "Владимир Лугановский", "Алан Волгин", "Михаил Моряхин", "Неизвестный Контакт (Ден)", "Алексей Шамов", "Артём Синегубов", "Николаози Чкадуа", "Дмитрий Чкадуа"],
    "Лучший нападающий": ["Андрей Перегудов", "Руслан Смоляков", "Никита Сазонов", "Владимир Лугановский", "Алан Волгин", "Михаил Моряхин", "Артём Синегубов", "Николаози Чкадуа", "Дмитрий Чкадуа"],
    "Лучший ассистент": ["Никита Кратович", "Андрей Перегудов", "Никита Сазонов", "Владимир Лугановский", "Неизвестный Контакт (Ден)", "Алексей Шамов", "Артём Синегубов"],
    "Лучший вратарь": ["Руслан Смоляков", "Никита Сазонов", "Михаил Моряхин", "Артём Синегубов"],
    "Лучший молодой игрок": ["Артём Синегубов", "Николаози Чкадуа", "Дмитрий Чкадуа"],
    "Лучший пожилой игрок": ["Дядя Коля", "Дядя Олег"],
    "Пушкаш": ["Какой-то гол Русика"],
    "Главный добряк": ["Русик", "Шишаня", "Не Ден", "Дядя Коля"]
}

# Загрузка и сохранение данных
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            # Возвращаем значения, если все есть в файле
            return data.get("votes", {}), data.get("user_votes", {}), data.get("voted_users", {})
    except (FileNotFoundError, json.JSONDecodeError):
        # Если файл не существует или ошибка в формате, создаем новый
        print("Файл данных не найден или поврежден, создаем новый.")
        return {}, {}, {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump({"votes": votes, "user_votes": user_votes, "voted_users": voted_users}, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")

# Инициализация данных
votes, user_votes, voted_users = load_data()

# Если данные пустые, создаем стандартные значения
if not votes:
    votes = {nomination: {candidate: 0 for candidate in candidates} for nomination, candidates in nominations.items()}
if not user_votes:
    user_votes = {}
if not voted_users:
    voted_users = {nomination: [] for nomination in nominations.keys()}  # Храним список ID пользователей, проголосовавших в каждой номинации

# Карта коротких callback-данных
short_callback_map = {}

def generate_short_callback(data):
    short_data = f"id{len(short_callback_map)}"
    short_callback_map[short_data] = data
    return short_data

# Генерация главного меню
def get_main_menu():
    keyboard = InlineKeyboardMarkup()
    for nomination in nominations.keys():
        short_data = generate_short_callback(f"nomination:{nomination}")
        keyboard.add(InlineKeyboardButton(text=nomination, callback_data=short_data))
    keyboard.add(InlineKeyboardButton(text="Посмотреть результаты", callback_data="results"))
    return keyboard

# Генерация клавиатуры для голосования
def get_voting_keyboard(nomination):
    keyboard = InlineKeyboardMarkup()
    for candidate in nominations[nomination]:
        short_data = generate_short_callback(f"vote:{nomination}:{candidate}")
        keyboard.add(InlineKeyboardButton(text=candidate, callback_data=short_data))
    keyboard.add(InlineKeyboardButton(text="Назад к номинациям", callback_data="back_to_menu"))
    return keyboard

# Обработчик callback-запросов
@dp.callback_query_handler()
async def handle_callback(callback_query: types.CallbackQuery):
    data = callback_query.data

    if data in short_callback_map:
        data = short_callback_map[data]

    if data == "back_to_menu":
        await callback_query.message.edit_text("Выберите номинацию:", reply_markup=get_main_menu())

    elif data.startswith("nomination:"):
        nomination = data.split(":")[1]
        await callback_query.message.edit_text(f"Номинация: {nomination}\nВыберите кандидата:", reply_markup=get_voting_keyboard(nomination))

    elif data.startswith("vote:"):
        _, nomination, candidate = data.split(":")
        user_id = callback_query.from_user.id

        # Проверяем, проголосовал ли пользователь в данной номинации
        if user_id in user_votes and nomination in user_votes[user_id]:
            await callback_query.answer("Вы уже голосовали в этой номинации!", show_alert=True)
        elif user_id in voted_users[nomination]:
            await callback_query.answer("Вы уже проголосовали в этой номинации!", show_alert=True)
        else:
            if user_id not in user_votes:
                user_votes[user_id] = {}
            user_votes[user_id][nomination] = candidate
            votes[nomination][candidate] += 1
            voted_users[nomination].append(user_id)  # Добавляем ID пользователя в список проголосовавших
            save_data()
            await callback_query.answer(f"Ваш голос за '{candidate}' засчитан!", show_alert=True)
            await callback_query.message.edit_text(f"Спасибо за ваш голос!\nВыберите следующую номинацию:", reply_markup=get_main_menu())

    elif data == "results":
        results_text = "Результаты голосования:\n\n"
        for nomination, candidates in votes.items():
            results_text += f"{nomination}:\n"
            for candidate, count in candidates.items():
                results_text += f"  {candidate}: {count} голос(ов)\n"
            results_text += "\n"
        await callback_query.message.edit_text(results_text, reply_markup=get_main_menu())

# Команда /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await bot.send_message(message.chat.id, "Добро пожаловать на голосование!\nВыберите номинацию:", reply_markup=get_main_menu())

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
