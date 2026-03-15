from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove()

cancel_button = "Отмена 🚫"

def cancel(message):
    bot.send_message(message.chat.id, "❌ Действие отменено.\nЧтобы посмотреть команды, используй /info", reply_markup=hideBoard)

def no_projects(message):
    bot.send_message(message.chat.id, '📂 У тебя пока нет проектов!\nСоздай новый с помощью /new_project')

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(f"📁 {row}", callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_projects = {
    'Имя проекта': ["✏️ Введите новое имя проекта", "project_name"],
    'Описание': ["📝 Введите новое описание проекта", "description"],
    'Ссылка': ["🔗 Введите новую ссылку на проект", "url"],
    'Статус': ["📊 Выберите новый статус проекта", "status_id"]
}

def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)

    if not skills:
        skills = '🛠️ Навыки пока не добавлены'

    bot.send_message(message.chat.id, f"""
📁 *Имя проекта:* {info[0]}
📝 *Описание:* {info[1]}
🔗 *Ссылка:* {info[2]}
📊 *Статус:* {info[3]}
🛠️ *Навыки:* {skills}
""", parse_mode="Markdown")


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id,
"""
👋 Привет!

Я **бот-менеджер проектов** 📁  
Я помогу тебе хранить информацию о твоих проектах.

Используй команду /info чтобы увидеть список команд.
""")
    info(message)


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
"""
📚 *Доступные команды*

/new_project — ➕ добавить новый проект  
/projects — 📂 посмотреть проекты  
/add_skill — 🛠️ добавить навык к проекту  
/update_projects — ✏️ изменить проект  
/delete — 🗑 удалить проект  

Также ты можешь просто **написать имя проекта** и я покажу информацию о нем.
""", parse_mode="Markdown")


@bot.message_handler(commands=['new_project'])
def add_project(message):
    bot.send_message(message.chat.id, "📁 Введите название проекта:")
    bot.register_next_step_handler(message, name_project)


def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]

    bot.send_message(message.chat.id, "🔗 Введите ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)


def link_project(message, data):
    data.append(message.text)

    statuses = [x[0] for x in manager.get_statuses()]

    bot.send_message(message.chat.id, "📊 Выберите статус проекта:", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)


def callback_project(message, data, statuses):
    status = message.text

    if status == cancel_button:
        cancel(message)
        return

    if status not in statuses:
        bot.send_message(message.chat.id, "❌ Статус не из списка!", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return

    status_id = manager.get_status_id(status)
    data.append(status_id)

    manager.insert_project([tuple(data)])

    bot.send_message(message.chat.id, "✅ Проект успешно сохранён!")




@bot.message_handler(commands=['add_skill'])
def add_skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)

    if projects:
        projects = [x[2] for x in projects]

        bot.send_message(message.chat.id,
                         "🛠️ Выбери проект для добавления навыка:",
                         reply_markup=gen_markup(projects))

        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)


def skill_project(message, projects):
    project_name = message.text

    if project_name == cancel_button:
        cancel(message)
        return

    if project_name not in projects:
        bot.send_message(message.chat.id,
                         "❌ У тебя нет такого проекта.",
                         reply_markup=gen_markup(projects))

        bot.register_next_step_handler(message, skill_project, projects=projects)
        return

    skills = [x[1] for x in manager.get_skills()]

    bot.send_message(message.chat.id,
                     "🛠️ Выбери навык:",
                     reply_markup=gen_markup(skills))

    bot.register_next_step_handler(message,
                                   set_skill,
                                   project_name=project_name,
                                   skills=skills)


def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id

    if skill == cancel_button:
        cancel(message)
        return

    if skill not in skills:
        bot.send_message(message.chat.id,
                         "❌ Такого навыка нет в списке.",
                         reply_markup=gen_markup(skills))

        bot.register_next_step_handler(message,
                                       set_skill,
                                       project_name=project_name,
                                       skills=skills)
        return

    manager.insert_skill(user_id, project_name, skill)

    bot.send_message(message.chat.id,
                     f"✅ Навык *{skill}* добавлен в проект *{project_name}*",
                     parse_mode="Markdown")


@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)

    if projects:
        text = "\n".join([f"📁 *{x[2]}*\n🔗 {x[4]}\n" for x in projects])

        bot.send_message(message.chat.id,
                         text,
                         parse_mode="Markdown",
                         reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)


@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)

    if projects:
        projects = [x[2] for x in projects]

        bot.send_message(message.chat.id,
                         "🗑 Выбери проект для удаления:",
                         reply_markup=gen_markup(projects))

        bot.register_next_step_handler(message,
                                       delete_project,
                                       projects=projects)
    else:
        no_projects(message)


def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id

    if project == cancel_button:
        cancel(message)
        return

    if project not in projects:
        bot.send_message(message.chat.id,
                         "❌ У тебя нет такого проекта.",
                         reply_markup=gen_markup(projects))

        bot.register_next_step_handler(message,
                                       delete_project,
                                       projects=projects)
        return

    project_id = manager.get_project_id(project, user_id)

    manager.delete_project(user_id, project_id)

    bot.send_message(message.chat.id, f"🗑 Проект *{project}* удалён!", parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def text_handler(message):

    # игнорируем команды
    if message.text.startswith('/'):
        return

    user_id = message.from_user.id
    projects = [x[2] for x in manager.get_projects(user_id)]
    project = message.text

    if project in projects:
        info_project(message, user_id, project)
        return

    bot.reply_to(message, "🤔 Я не понял сообщение. Используй /info")


if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()