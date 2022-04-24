#!/usr/bin/env python

# SmartHomeBot v0.8.0
# A simple Telegram Bot used to automate notifications for a Smart Home.
# The bot starts automatically and runs until you press Ctrl-C on the command line.
#
# Usage:
# Use /help to list available commands.

import logging, os, time, json, psutil, re
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from gpiozero import CPUTemperature

# define some bot variables
commands = ['/start', '/help', '/reboot', '/system', '/listusers', '/adduser', '/banuser']
admin_commands = ['/reboot', '/system', '/adduser', '/banuser']
keyboard_dict = { 
    "yes_no" : {"y" : "yes", "n" : "no"}
}
user_callback_dict = {
    "adduser" : "User added to allowed users list.",
    "banuser" : "User removed from allowed users list."
}
token_dict = None
users_dict = None
chat_dict = None
bot_token = None
allowed_users = None
admin_users = None
bot_owner = None
chat_id = None
bot = None
query_data = None
button_click = False
process = None
user_data = ""
sleep_time = 5

# multiline markup text used for /help command.
help_command_markup = """This is a simple Telegram Bot used to automate notifications for a Smart Home\.

*Available commands*
\/start \- does nothing, bot starts automatically\.
\/help \- shows a list of all available commands\.
\/listusers \- list all users allowed to use this bot\.
\/adduser \- add a user to allowed users list with user\_id argument\. \*
\/banuser \- remove user from allowed users list with user\_id argument\. Bot owner can\'t be banned\. \*
\/reboot \- reboots system\. \*
\/system \- shows CPU temp\*\*, CPU and RAM load\. \*

\* Restricted to admins
\*\* Restricted to Linux"""
# end of multiline text

# enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# define command handlers. These usually take the two arguments update and context
def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('SmartHomeBot is running. Type /help to list all available commands.')

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2(help_command_markup)

def reboot_command(update: Update, context: CallbackContext) -> None:
    global process
    global sleep_time
    process = "reboot"
    try:
        sleep_time = int(context.args[0])
    except (IndexError, ValueError):
        sleep_time = 5
    keyboard_markup = keyboard_construct('yes_no')
    update.message.reply_text('Reboot your system?', reply_markup=keyboard_markup)

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
    global bot
    global bot_token
    global allowed_users
    global chat_id
    listusers_msg = '*List of users allowed to use this bot:*\n\n'
    listusers_msg += users_list(chat_id, allowed_users, allowed_users)
    update.message.reply_markdown_v2(listusers_msg)

def adduser_command(update: Update, context: CallbackContext) -> None:
    global process
    global user_data
    process = "adduser"
    try:
        user_id = int(context.args[0])
        user_data = user_id
        keyboard_markup = keyboard_construct('yes_no')
        update.message.reply_text('Are you sure?', reply_markup=keyboard_markup)
    except (IndexError, ValueError):
        update.message.reply_text('You haven\'t provided user_id argument.')

def banuser_command(update: Update, context: CallbackContext) -> None:
    global process
    global user_data
    process = "banuser"
    try:
        user_id = int(context.args[0])
        user_data = user_id
        keyboard_markup = keyboard_construct('yes_no')
        update.message.reply_text('Are you sure?', reply_markup=keyboard_markup)
    except (IndexError, ValueError):
        update.message.reply_text('You haven\'t provided user_id argument.')
    
# define filter callbacks
def not_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, I can\'t understand that.')    

def not_admin(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, you\'re not an admin, you can\'t use admin restricted commands.')    

def not_allowed_users(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry you\'re not allowed to use this bot.')

# define keyboard query handlers
def keyboard_query(update: Update, context: CallbackContext) -> None:
    global query_data
    global process
    global user_data
    global sleep_time
    button_click = False
    query = update.callback_query
    query.answer()
    query_data = query.data
    while button_click == False:
        if process == "reboot":
            button_click = True
            reboot_callback(query_data, query, sleep_time)
        elif process == "adduser" or process == "banuser":
            button_click = True
            user_callback(process, query_data, user_data, query)

# define internal callbacks
def reboot_callback(query_data, query, reboot_time):
    global button_click
    global process
    if query_data == "y":
        query.edit_message_text(text=f'Rebooting in' + reboot_time + ' secs...')
        time.sleep(reboot_time)
        os.system("sudo reboot")
    elif query_data == "n":
        query.edit_message_text(text=f'Reboot aborted.')
        button_click = False
    process = None
    query_data = None

def user_callback(method, query_data, user_data, query):
    global button_click
    global process
    global user_callback_dict
    user_callback_answer = user_callback_dict.get(method)
    if query_data == "y":
        modify_data(method, user_data, query)
        query.edit_message_text(text=user_callback_answer)
    elif query_data == "n":
        query.edit_message_text(text=f'Command abborted.')
        button_click = False
    process = None
    query_data = None

def modify_data(method, data, query) -> None:
    global allowed_users
    global admin_users
    global bot_owner
    global users_dict
    global json_config
    if method == 'adduser':
        if data in allowed_users:
            query.edit_message_text(text=f'User is already on allowed users list.')
        else:
            allowed_users.append(data)
            users_dict.update({"allowed_users": allowed_users})
            json_config.update({"USERS": users_dict})
    elif method == 'banuser':
        if data in admin_users:
            query.edit_message_text(text=f'The user is an admin, can\'t be kicked off. You must remove him/her from admin list first.')
        elif data in bot_owner:
            query.edit_message_text(text=f'The user is the owner of the bot, can\'t be kicked off.')
        elif data not in allowed_users:
            query.edit_message_text(text=f'The user is not in allowed users list.')
        else:
            allowed_users.remove(data)
            users_dict.update({"allowed_users": allowed_users})
            json_config.update({"USERS": users_dict})
    store_json(json_config)

def store_json(data) -> None:
    file = open('config.json', 'w')
    file.write(json.dumps(data, indent=2))
    file.close()

def users_list(chat_id, allowed_users, members):
    users_list_msg = ""
    for n in range(0, len(members)):
        user_info = bot.getChatMember(chat_id=chat_id, user_id=members[n])
        user = user_info["user"]
        user_id = str(user["id"])
        username = user["username"]
        first_name = user["first_name"]
        last_name = user["last_name"]
        if username == None:
            users_list_msg += first_name + ' ' + last_name
        else:
            users_list_msg += '@' + username
        users_list_msg += ' \-\- id: ' + user_id
        users_list_msg += '\n'        
    return users_list_msg

def keyboard_construct(keyboard_name):
    global keyboard_dict
    buttons = []
    for key, label in keyboard_dict[keyboard_name].items():
        buttons.append(InlineKeyboardButton(text=label, callback_data=key))
    return InlineKeyboardMarkup([buttons])

# main module
def main() -> None:
    global token_dict
    global users_dict
    global chat_dict
    global bot_token
    global bot
    global allowed_users
    global admin_users
    global bot_owner
    global chat_id
    global json_config
    global process

    file = open('config.json', 'r')
    json_data = file.read()
    file.close()

    json_config = json.loads(json_data)

    token_dict = json_config.get("AUTH_TOKEN")
    bot_token = token_dict.get("bot_token")
    users_dict = json_config.get("USERS")
    allowed_users = users_dict.get("allowed_users")
    admin_users = users_dict.get("admin_users")
    bot_owner = users_dict.get("bot_owner")
    chat_dict = json_config.get("CHATS")
    chat_id = chat_dict.get("allowed_chats")
    
    # create the Updater and pass it your bot's token
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    bot = Bot(bot_token)

    # not allowed users can't interact with the bot
    dispatcher.add_handler(MessageHandler(~Filters.user(allowed_users), not_allowed_users))

    # inline buttons
    dispatcher.add_handler(CallbackQueryHandler(keyboard_query))

    # on non command i.e message, reply with not_command function
    dispatcher.add_handler(MessageHandler(~Filters.command, not_command))

    # on admin command, run is_admin_command function
    dispatcher.add_handler(MessageHandler(Filters.text(admin_commands) & ~Filters.user(admin_users), not_admin))

    # commands
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("reboot", reboot_command))
    dispatcher.add_handler(CommandHandler("system", system_command))
    dispatcher.add_handler(CommandHandler("listusers", listusers_command))
    dispatcher.add_handler(CommandHandler("adduser", adduser_command))
    dispatcher.add_handler(CommandHandler("banuser", banuser_command))
  
    # start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
