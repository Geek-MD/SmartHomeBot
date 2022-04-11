#!/usr/bin/env python

# SmartHomeBot v0.7
# A simple Telegram Bot used to automate notifications for a Smart Home.
# The bot starts automatically and runs until you press Ctrl-C on the command line.
#
# Usage:
# Use /help to list available commands.

import logging, os, time, json, psutil, re
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
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
admin_users = None

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
    listuser_msg = '*List of users allowed to use this bot:*\n\n'
    user_info = users_info["USERS_DATA"]
    for n in user_info:
        user_id = user_info[n]
        listuser_msg += '\@' + user_id["username"] + '\n'
    listuser_msg += '\nEnd of list for allowed users\.'
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
        auth_token = json.load(token)
    with open('allowed_users.json', 'r') as users:
        global allowed_users
        allowed_users = json.load(users)
    with open('admin_users.json', 'r') as admins:
        global admin_users
        admin_users = json.load(admins)
    with open('users_data.json', 'r') as users_data:
        global users_info
        users_info = json.load(users_data)

    # create the Updater and pass it your bot's token.
    updater = Updater(auth_token["AUTH_TOKEN"])

    # not allowed users can't interact with the bot.
    updater.dispatcher.add_handler(MessageHandler(~Filters.user(allowed_users["USERS"]), not_allowed_users))

    # inline buttons.
    updater.dispatcher.add_handler(CallbackQueryHandler(reboot_query))

    # on non command i.e message, reply with not_command function.
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.text(commands), not_command))

    # on admin command, run is_admin_command function.
    updater.dispatcher.add_handler(MessageHandler(Filters.text(admin_commands) & ~Filters.user(admin_users["ADMINS"]), not_admin))

    # commands.
    updater.dispatcher.add_handler(CommandHandler("start", start_command))
    updater.dispatcher.add_handler(CommandHandler("help", help_command))
    updater.dispatcher.add_handler(CommandHandler("reboot", reboot_command))
    updater.dispatcher.add_handler(CommandHandler("system", system_command))
    updater.dispatcher.add_handler(CommandHandler("listusers", listusers_command))

    # start the bot.
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
