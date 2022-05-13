#!/usr/bin/env python

# SmartHomeBot v1.2.0
# A simple Telegram Bot used to automate notifications for a Smart Home.
# The bot starts automatically and runs until you press Ctrl-C on the command line.
#
# Usage:
# Use /help to list available commands.

import logging, os, time, json, psutil, re, requests
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from gpiozero import CPUTemperature

# define some bot variables
commands = ['/start', '/help', '/reboot', '/system', '/listusers', '/adduser', '/removeuser', '/makeadmin', '/revokeadmin', '/adminusers', '/join', '/requests', '/dismiss', '/version']
admin_commands = ['/reboot', '/system', '/adduser', '/removeuser', '/makeadmin', '/revokeadmin', '/requests', '/dismiss', '/version']
keyboard_dict = { 
    "yes_no" : {"y" : "yes", "n" : "no"}
}
user_callback_dict = {
    "adduser" : "User added to allowed users list.",
    "removeuser" : "User removed from allowed users list.",
    "makeadmin" : "User added to admins list.",
    "revokeadmin" : "User removed from admins list.",
    "dismiss" : "User request dismissed."
}
token_dict = users_dict = chat_dict = bot_token = allowed_users = admin_users = bot_owner = user_requests = chat_id = bot = query_data = process = None
button_click = False
user_data = method_return = ""
sleep_time = 5
version = 'v1.2.0'

# multiline markup text used for /help command.
help_command_markup = """This is a simple Telegram Bot used to automate notifications for a Smart Home\.

*Available commands*
_\/start_ \- Does nothing, bot starts automatically\.
_\/help_ \- Shows a list of all available commands\.
_\/listusers_ \- List all users allowed to use this bot\.
_\/adminusers_ \- List all users with admin capabilities\.
_\/join_ \- Lets users ask an admin to approve them into allowed users list\.

*Admin restricted commands*
_\/requests_ \- Let admins check pending requests to join allowed users list, and approve or dismiss them\.
_\/adduser_ \- Add a user to allowed users list with user\_id argument\.
_\/removeuser_ \- Remove a user from allowed users list with user\_id argument\. Bot owner can\'t be banned\.
_\/dismiss_ \- Dismiss a request for joining allowed users list\. Remember to add user\_id argument\.
_\/makeadmin_ \- Add a user to admins list with user\_id argument\.
_\/revokeadmin_ \- Remove a user from admins list with user\_id argument\. Bot owner can\'t be removed\.
_\/reboot_ \- Reboots system\. Default delay time is 5 secs\. You can configure delay time as an argument\.
_\/system_ \- Shows CPU temp\*, CPU and RAM load\.
_\/version_ \- Shows version of the installed bot instance\.

\* Available only in Linux"""
# end of multiline text

# enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# define command handlers. These usually take the two arguments update and context
def user_commands(update: Update, context: CallbackContext) -> None:
    global commands
    parsed_text = update.message['text']
    striped_text = parsed_text.strip()
    parsed_command = striped_text.split()
    if parsed_command[0] == '/start':
        start_command(update, context)
    elif parsed_command[0] == '/help':
        help_command(update, context)
    elif parsed_command[0] == '/listusers':
        listusers_command(update, context)
    elif parsed_command[0] == '/adminusers':
        adminusers_command(update, context)
    elif parsed_command[0] == '/join':
        join_command(update, context)

def administrator_commands(update: Update, context: CallbackContext) -> None:
    global admin_commands, admin_users
    parsed_text = update.message['text']
    striped_text = parsed_text.strip()
    parsed_command = striped_text.split()
    chat_info = update.message['chat']
    user_id = int(chat_info['id'])
    if user_id in admin_users:
        if parsed_command[0] == '/requests':
            requests_command(update, context)
        elif parsed_command[0] == '/adduser':
            adduser_command(update, context)
        elif parsed_command[0] == '/removeuser':
            removeuser_command(update, context)
        elif parsed_command[0] == '/dismiss':
            dismiss_command(update, context)
        elif parsed_command[0] == '/makeadmin':
            makeadmin_command(update, context)
        elif parsed_command[0] == '/revokeadmin':
            revokeadmin_command(update, context)
        elif parsed_command[0] == '/reboot':
            reboot_command(update,context)
        elif parsed_command[0] == '/system':
            system_command(update, context)
        elif parsed_command[0] == '/version':
            version_command(update, context)
    else:
        not_admin(update, context)

def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('SmartHomeBot is running. Type /help to list all available commands.')

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2(help_command_markup)

def reboot_command(update: Update, context: CallbackContext) -> None:
    global process, sleep_time
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
    global bot, bot_token, allowed_users, admin_users, chat_id
    process = "listusers"
    listusers_msg = '*List of users allowed to use this bot:*\n'
    listusers_msg += users_list(process, chat_id)
    update.message.reply_markdown_v2(listusers_msg)

def adminusers_command(update: Update, context: CallbackContext) -> None:
    global bot, bot_token, admin_users, chat_id
    process = "adminusers"
    adminusers_msg = '*List of admins:*\n'
    adminusers_msg += users_list(process, chat_id)
    update.message.reply_markdown_v2(adminusers_msg)

def anyusers_command(update: Update, context: CallbackContext) -> None:
    global process, user_data
    try:
        parsed_message = update.message['text']
        strip_message = parsed_message.strip()
        split_message = strip_message.split()
        user_data = int(split_message[1])
        keyboard_markup = keyboard_construct('yes_no')
        update.message.reply_text('Are you sure?', reply_markup=keyboard_markup)
    except (IndexError, ValueError):
        update.message.reply_text('You haven\'t provided user_id argument.')

def adduser_command(update: Update, context: CallbackContext) -> None:
    global process, user_data
    process = "adduser"
    anyusers_command(update, context)

def removeuser_command(update: Update, context: CallbackContext) -> None:
    global process, user_data
    process = "removeuser"
    anyusers_command(update, context)

def makeadmin_command(update: Update, context: CallbackContext) -> None:
    global process, user_data
    process = "makeadmin"
    anyusers_command(update, context)

def revokeadmin_command(update: Update, context: CallbackContext) -> None:
    global process, user_data
    process = "revokeadmin"
    anyusers_command(update, context)

def join_command(update: Update, context: CallbackContext) -> None:
    global process, allowed_users, user_requests
    chat_info = update.message['chat']
    user_id = chat_info['id']
    process = "join"
    if user_id in allowed_users:
        update.message.reply_text('You are already in allowed users list.')
    elif user_id in user_requests:
        update.message.reply_text('Your request is still pending for approval.')
    else:
        keyboard_markup = keyboard_construct('yes_no')
        update.message.reply_text('Are you sure?', reply_markup=keyboard_markup)

def requests_command(update: Update, context: CallbackContext) -> None:
    global bot, bot_token, user_requests, chat_id
    if len(user_requests) == 0:
        update.message.reply_text('There are not pending requests.')
    else:
        process = "requests"
        requests_msg = 'There are ' + str(len(user_requests)) + ' pending requests\.\n\n'
        requests_msg += users_list(process, chat_id)
        requests_msg += '\nUse \/adduser to add them into allowed users list, or \/dismiss user\_id to reject the request\.\n'
        update.message.reply_markdown_v2(requests_msg)

def dismiss_command(update: Update, context: CallbackContext) -> None:
    global process, user_data, user_requests
    if len(user_requests) == 0:
        update.message.reply_text('There are not pending requests.')
    else:
        process = "dismiss"
        try:
            parsed_message = update.message['text']
            strip_message = parsed_message.strip()
            split_message = strip_message.split()
            user_data = int(split_message[1])
            keyboard_markup = keyboard_construct('yes_no')
            update.message.reply_text('Are you sure?', reply_markup=keyboard_markup)
        except (IndexError, ValueError):
            update.message.reply_text('You haven\'t provided user_id argument.')
            requests_command(update, context)

def version_command(update: Update, context: CallbackContext) -> None:
    global version
    github_info = requests.get("https://api.github.com/repos/Geek-MD/SmartHomeBot/releases/latest")
    github_version = github_info.json()["name"]
    version_msg = f'Current bot version is {version}\n'
    if version < github_version:
        version_msg += f'\nThere\'s a new version of the bot available at GitHub ({github_version})\nUpdate bot version following Wiki instructions.'
    update.message.reply_text(version_msg)

# define filter callbacks
def not_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, I can\'t understand that.')

def check_command(update: Update, context: CallbackContext) -> None:
    global commands, admin_commands
    parsed_text = update.message['text']
    striped_text = parsed_text.strip()
    parsed_command = striped_text.split()
    if parsed_command[0] not in commands:
        update.message.reply_text('Sorry that\'s not a real command. Check /help for available commands.')
    elif parsed_command[0] in admin_commands:
        administrator_commands(update, context)
    else:
        user_commands(update, context)

def not_admin(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, you\'re not an admin, you can\'t use admin restricted commands.')
    
def not_allowed_users(update: Update, context: CallbackContext) -> None:
    parsed_command = update.message['text']
    if parsed_command == '/join':
        join_command(update, context)
    else:
        update.message.reply_text('Sorry you\'re not allowed to use this bot, but you can use /join command to request access to an admin.')

# define keyboard query handlers
def keyboard_query(update: Update, context: CallbackContext) -> None:
    global query_data, process, user_data, sleep_time
    button_click = False
    query = update.callback_query
    query.answer()
    from_user = query.from_user
    from_user_id = from_user["id"]
    query_data = query.data
    while button_click == False:
        if process == "reboot":
            button_click = True
            reboot_callback(query_data, query, sleep_time)
        elif process == "join":
            button_click = True
            join_callback(process, query_data, from_user_id, query)
        elif process == "adduser" or "removeuser" or "makeadmin" or "revokeadmin" or "dismiss" :
            button_click = True
            user_callback(process, query_data, user_data, query, from_user_id)

# define internal callbacks
def reboot_callback(query_data, query, reboot_time):
    global button_click, process
    if query_data == "y":
        query.edit_message_text(text=f'Rebooting in {reboot_time} secs...')
        time.sleep(reboot_time)
        os.system("sudo reboot")
    elif query_data == "n":
        query.edit_message_text(text=f'Reboot aborted.')
        button_click = False
    process = None
    query_data = None

def join_callback(method, query_data, from_user_id, query):
    global button_click, process, method_return
    if query_data == "y":
        modify_data(method, from_user_id, None, None)
        if method_return == True:
            query.edit_message_text(text=f'Request sent to admins. You have to wait for approval.')
            method_return = False
    elif query_data == "n":
        query.edit_message_text(text=f'Command aborted.')
        button_click = False
    process = None
    query_data = None

def user_callback(method, query_data, user_data, query, from_user_id):
    global button_click, process, user_callback_dict, method_return
    user_callback_answer = user_callback_dict.get(method)
    if query_data == "y":
        modify_data(method, user_data, query, from_user_id)
        if method_return == True:
            query.edit_message_text(text=user_callback_answer)
            method_return = False
    elif query_data == "n":
        query.edit_message_text(text=f'Command aborted.')
        button_click = False
    process = None
    query_data = None

def modify_data(method, data, query, from_user_id) -> None:
    global token_dict, users_dict, chat_dict, bot_token, bot, allowed_users, admin_users, bot_owner, user_requests, chat_id, config
    global method_return
    if method == 'adduser':
        if data in allowed_users:
            query.edit_message_text(text=f'The user is already on allowed users list.')
            method_return = False
            return method_return
        else:
            allowed_users.append(data)
            users_dict.update({"allowed_users" : allowed_users})
            if data in user_requests:
                user_requests.remove(data)
                users_dict.update({"user_requests" : user_requests})
            config.update({"USERS" : users_dict})
            method_return = True
    elif method == 'removeuser':
        if data in bot_owner:
            query.edit_message_text(text=f'The user is the owner of the bot, can\'t be kicked off.')
            method_return = False
            return method_return
        elif data == from_user_id:
            query.edit_message_text(text=f'Can\'t remove yourself from allowed users list.')
            method_return = False
            return method_return
        elif data in admin_users:
            query.edit_message_text(text=f'The user is an admin, can\'t be kicked off. You must remove the user from admins list first.')
            method_return = False
            return method_return
        elif data not in allowed_users:
            query.edit_message_text(text=f'The user is not in allowed users list.')
            method_return = False
            return method_return
        else:
            allowed_users.remove(data)
            users_dict.update({"allowed_users" : allowed_users})
            config.update({"USERS" : users_dict})
            method_return = True
    elif method == 'makeadmin':
        if data in admin_users:
            query.edit_message_text(text=f'The user is already on admins list.')
            method_return = False
            return method_return
        if data not in allowed_users:
            query.edit_message_text(text=f'The user is not in allowed users list. You must add the user first.')
            method_return = False
            return method_return
        else:
            admin_users.append(data)
            users_dict.update({"admin_users" : admin_users})
            config.update({"USERS" : users_dict})
            method_return = True
    elif method == 'revokeadmin':
        if data in bot_owner:
            query.edit_message_text(text=f'The user is the owner of the bot, can\'t be removed from admins list.')
            method_return = False
            return method_return
        elif data == from_user_id:
            query.edit_message_text(text=f'Can\'t ban yourself from admins list.')
            method_return = False
            return method_return
        elif data not in admin_users:
            query.edit_message_text(text=f'The user is not in admins list.')
            method_return = False
            return method_return
        else:
            admin_users.remove(data)
            users_dict.update({"admin_users" : admin_users})
            config.update({"USERS" : users_dict})
            method_return = True
    elif method == 'join':
        user_requests.append(data)
        users_dict.update({"user_requests" : user_requests})
        config.update({"USERS" : users_dict})
        method_return = True
    elif method == 'dismiss':
        user_requests.remove(data)
        user_rejects.append(data)
        users_dict.update({"user_requests" : user_requests})
        users_dict.update({"user_rejects" : user_rejects})
        config.update({"USERS" : users_dict})
        method_return = True
    store_json(config)
    read_config()

def store_json(json_config) -> None:
    global token_dict, users_dict, chat_dict, bot_token, bot, allowed_users, admin_users, bot_owner, user_requests, chat_id, config
    file = open('config.json', 'w')
    file.write(json.dumps(json_config, indent=2))
    file.close()

def users_list(method, chat_id):
    global allowed_users, admin_users, user_requests
    users_list_msg = pre = post = post_id = ""
    if method == 'listusers':
        method_list = allowed_users
    elif method == 'adminusers':
        method_list = admin_users
    elif method == 'requests':
        method_list = user_requests
    for n in range(0, len(method_list)):
        user_info = bot.getChatMember(chat_id=chat_id, user_id=method_list[n])
        user = user_info["user"]
        user_id = user["id"]
        username = user["username"]
        first_name = user["first_name"]
        last_name = user["last_name"]
        if (method == 'adminusers') and (user_id not in admin_users):
            pass
        else:
            if user_id in admin_users:
                pre = post = '_'
                if method == "listusers":
                    post_id = '\*'
            else:
                pre = post = ''
                post_id = ""
            if username == None:
                users_list_msg += f"{pre}{first_name} {last_name}{post} \– id: {user_id} {post_id}\n"
            else:
                users_list_msg += f"{pre}@{username}{post} \- id: {user_id} {post_id}\n"
    if method == "listusers":
        users_list_msg += '\n\* admins'
    return users_list_msg

def keyboard_construct(keyboard_name):
    global keyboard_dict
    buttons = []
    for key, label in keyboard_dict[keyboard_name].items():
        buttons.append(InlineKeyboardButton(text=label, callback_data=key))
    return InlineKeyboardMarkup([buttons])

def read_config():
    global token_dict, users_dict, chat_dict, bot_token, bot, allowed_users, admin_users, bot_owner, user_requests, user_rejects, chat_id, config
    file = open('config.json', 'r')
    json_data = file.read()
    file.close()

    config = json.loads(json_data)

    token_dict = config.get("AUTH_TOKEN")
    bot_token = token_dict.get("bot_token")
    users_dict = config.get("USERS")
    allowed_users = users_dict.get("allowed_users")
    admin_users = users_dict.get("admin_users")
    bot_owner = users_dict.get("bot_owner")
    user_requests = users_dict.get("user_requests")
    user_rejects = users_dict.get("user_rejects")
    chat_dict = config.get("CHATS")
    chat_id = chat_dict.get("allowed_chats")

# main module
def main() -> None:
    global token_dict, users_dict, chat_dict, bot_token, bot, allowed_users, admin_users, bot_owner, user_requests, user_rejects, chat_id, config, commands, admin_commands, dispatcher, updater
    read_config()

    # create the Updater and pass it your bot's token
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    bot = Bot(bot_token)

    # not allowed users can't interact with the bot
    dispatcher.add_handler(MessageHandler(~Filters.user(allowed_users), not_allowed_users))

    # on non command i.e message, reply with not_command function
    dispatcher.add_handler(MessageHandler(~Filters.command, not_command))
    dispatcher.add_handler(MessageHandler(Filters.command, check_command))

    # inline buttons
    dispatcher.add_handler(CallbackQueryHandler(keyboard_query))
  
    # start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
