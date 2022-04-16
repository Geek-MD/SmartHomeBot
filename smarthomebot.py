#!/usr/bin/env python

# SmartHomeBot v0.7.1
# A simple Telegram Bot used to automate notifications for a Smart Home.
# The bot starts automatically and runs until you press Ctrl-C on the command line.
#
# Usage:
# Use /help to list available commands.

import logging, os, time, json, psutil, re
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from gpiozero import CPUTemperature

# bot variables
commands = ['/start', '/help', '/reboot', '/system', '/listusers']
admin_commands = ['/reboot', '/system']
reboot_keyboard = [[InlineKeyboardButton("yes", callback_data='y'), InlineKeyboardButton("no", callback_data='n')]]
reboot_keyboard_markup = InlineKeyboardMarkup(reboot_keyboard)
reboot_option = None
auth_token = None
allowed_users = None
allowed_users_len = None
admin_users = None
chat_id = None
bot = None

# multiline markup text used for /help command.
help_command_text = """This is a simple Telegram Bot used to automate notifications for a Smart Home\.

*Available commands*
\/start \- does nothing, bot starts automatically
\/help \- shows a list of all available commands
\/listusers \- list all users allowed to use this bot
\/reboot \- reboots system \*
\/system \- shows CPU temp\*\*, CPU and RAM load \*

\* Restricted to admins
\*\* Restricted to Linux"""
# end of multiline text

# enable logging.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# define command handlers. These usually take the two arguments update and context.
def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('SmartHomeBot is running. Type /help to list all available commands.')

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2(help_command_text)

def reboot_command(update: Update, context: CallbackContext) -> None:
    global reboot_option
    button_pressed = False
    update.message.reply_text('Reboot your system?', reply_markup=reboot_keyboard_markup)

def reboot_query(update: Update, context: CallbackContext) -> None:
    global reboot_option
    button_pressed = False
    query = update.callback_query
    query.answer()
    reboot_option = query.data
    while button_pressed == False:
        if reboot_option == "y":
            query.edit_message_text(text=f'Rebooting in 5 secs...')
            time.sleep(5)
            os.system("sudo reboot")
            break
        elif reboot_option == "n":
            query.edit_message_text(text=f'Reboot aborted.')
            button_pressed = True
            break
        elif reboot_option == None:
            continue

def system_command(update: Update, context: CallbackContext) -> None:
    if psutil.LINUX == False:
        # skip CPU temperature if OS is not Linux.
        system_msg = '*CPU temperature:* _Not available_\n'
    else:
        cpu_temp = CPUTemperature()
        cpu_temp_esc = re.escape(str(round(cpu_temp.temperature, 1)))
        system_msg = '*CPU temperature:* ' + cpu_temp_esc + '°C\n'
    cpu_load = psutil.cpu_percent(4)
    cpu_load_esc = re.escape(str(round(cpu_load, 1)))
    ram_load = psutil.virtual_memory()
    ram_load_esc = re.escape(str(round(ram_load.percent, 1)))
    system_msg += '*CPU load:* ' + cpu_load_esc + '%\n'
    system_msg += '*RAM load:* ' + ram_load_esc + '%'
    update.message.reply_markdown_v2(system_msg)

def listusers_command(update: Update, context: CallbackContext) -> None:
    global allowed_users
    global allowed_users_len
    global auth_token
    global chat_id
    listuser_msg = '*List of users allowed to use this bot:*\n\n'
    for n in range(0, allowed_users_len):
        member_info = bot.getChatMember(chat_id=chat_id, user_id=allowed_users[n])
        user = member_info["user"]
        user_id = str(user["id"])
        username = '@' + user["username"]
        first_name = user["first_name"]
        last_name = user["last_name"]
        if username == None:
            listuser_msg += first_name + ' ' + last_name
        else:
            listuser_msg += username
        listuser_msg += ' \-\- id: ' + user_id + '\n'
    update.message.reply_markdown_v2(listuser_msg)

def not_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, I can\'t understand that.')    

def not_admin(update: Update, context: CallbackContext) -> None:
    # not admin users can't run admin restricted commands.
    update.message.reply_text('Sorry, you\'re not an admin, you can\'t use admin restricted commands.')    

def not_allowed_users(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry you\'re not allowed to use this bot.')

def main() -> None:
    # import data stored on external files.
    with open('smarthomebot.json', 'r') as token:
        global auth_token
        json_token = json.load(token)
        auth_token = json_token["AUTH_TOKEN"]
    with open('allowed_users.json', 'r') as users:
        global allowed_users
        global allowed_users_len
        json_users = json.load(users)
        allowed_users = json_users["USERS"]
        allowed_users_len = len(allowed_users)
    with open('admin_users.json', 'r') as admins:
        global admin_users
        json_admins = json.load(admins)
        admin_users = json_admins["ADMINS"]
    with open('chats.json', 'r') as chats:
        global chat_id
        json_chat = json.load(chats)
        chat_id = json_chat["CHATS"]

    # create the Updater and pass it your bot's token.
    updater = Updater(auth_token)
    dispatcher = updater.dispatcher
    global bot
    bot = Bot(auth_token)

    # not allowed users can't interact with the bot.
    dispatcher.add_handler(MessageHandler(~Filters.user(allowed_users), not_allowed_users))

    # inline buttons.
    dispatcher.add_handler(CallbackQueryHandler(reboot_query))

    # on non command i.e message, reply with not_command function.
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.text(commands), not_command))

    # on admin command, run is_admin_command function.
    dispatcher.add_handler(MessageHandler(Filters.text(admin_commands) & ~Filters.user(admin_users), not_admin))

    # commands.
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("reboot", reboot_command))
    dispatcher.add_handler(CommandHandler("system", system_command))
    dispatcher.add_handler(CommandHandler("listusers", listusers_command))

    # start the bot.
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
