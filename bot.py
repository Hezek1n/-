import time
import gspread
import telebot
import json
import os

# === НАСТРОЙКИ ===
TOKEN = "BOTFATHER TOKEN"  # вставь токен из BotFather
CHANNEL_ID = "@Your channel ID"  # канал или чат
SPREADSHEET_URL = "LINK TO GOOGLE SPREADSHEET"
CHECK_INTERVAL = 5  # каждые 5 секунд

bot = telebot.TeleBot(TOKEN)

# Авторизация Google Sheets
gc = gspread.service_account(filename="credentials.json")
sheet = gc.open_by_url(SPREADSHEET_URL).sheet1

DATA_FILE = "data.json"

def get_data():
    """Считывает данные каждые 2 строки, берёт A+B и I."""
    values = sheet.get_all_values()
    data = []

    # Начинаем с 3 строки (индекс 2) — пропускаем заголовки
    for i in range(2, len(values), 2):
        row1 = values[i]
        row2 = values[i + 1] if i + 1 < len(values) else [""] * 9

        # Название клиента из A и B
        name_a = row1[0].strip() if len(row1) > 0 else ""
        name_b = row1[1].strip() if len(row1) > 1 else ""
        name = (name_a + " " + name_b).strip() or (row2[0] + " " + row2[1]).strip()

        # Итог (I)
        try:
            total = float(row1[8]) if len(row1) > 8 and row1[8] else 0
        except ValueError:
            total = 0

        if name:  # только непустые строки
            data.append({"name": name, "total": total})
    return data


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"rows": [], "messages": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sync_to_telegram():
    """Основная логика синхронизации с Telegram-каналом."""
    state = load_data()
    old_rows = state["rows"]
    messages = state["messages"]

    new_rows = get_data()

    # Удаляем лишние сообщения, если строк стало меньше
    if len(new_rows) < len(messages):
        for i in range(len(new_rows), len(messages)):
            try:
                bot.delete_message(CHANNEL_ID, messages[i])
            except Exception:
                pass
        messages = messages[:len(new_rows)]

    # Обновляем или создаём новые
    for i, row in enumerate(new_rows):
        text = (
            f"📦 <b>{row['name']}</b>\n"
            f"💰 <b>{int(row['total'])}</b>"
        )

        if i < len(messages):
            if i >= len(old_rows) or old_rows[i] != row:
                try:
                    bot.edit_message_text(text, CHANNEL_ID, messages[i], parse_mode="HTML")
                except Exception:
                    pass
        else:
            msg = bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
            messages.append(msg.message_id)

    state["rows"] = new_rows
    state["messages"] = messages
    save_data(state)


def main():
    print("Бот запущен и отслеживает таблицу...")
    while True:
        try:
            sync_to_telegram()
        except Exception as e:
            print("Ошибка:", e)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
