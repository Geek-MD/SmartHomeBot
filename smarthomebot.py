#!/usr/bin/env python

# SmartHomeBot v1.4.0
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
commands = ['/start', '/help', '/listusers', '/adminusers', '/chatmembers', '/join', '/requests', '/dismiss', '/adduser', '/removeuser', '/banuser', '/unban', '/makeadmin', '/revokeadmin', '/banlist', '/version', '/system', '/reboot']
super_commands = ['/requests', '/dismiss', '/adduser', '/removeuser', '/banuser', '/unban', '/makeadmin', '/revokeadmin', '/banlist', '/version', '/system', '/reboot']
keyboard_dict = { 
    "yes_no" : {"y" : "yes", "n" : "no"}
}
user_callback_dict = {
    "/dismiss" : "User request dismissed.",
    "/adduser" : "User added to allowed users list.",
    "/removeuser" : "User removed from allowed users list.",
    "/banuser" : "User added to banned users list.",
    "/unban" : "User removed from banned users list.",
    "/makeadmin" : "User added to admins list.",
    "/revokeadmin" : "User removed from admins list."
}
version = 'v1.4.0'
parsed_command = parsed_command_arg = ''

# multiline markup text used for /help command.
help_command_markup = """This is a simple Telegram Bot used to automate notifications for a Smart Home\.

*Available commands*
_\/start_ \- Does nothing, bot starts automatically\.
_\/help_ \- Shows a list of all available commands\.
_\/listusers_ \- List all users allowed to use this bot\.
_\/adminusers_ \- List all users with admin capabilities\.
_\/chatmembers_ \- List members of the chat, including allowed users, admins and bot\.
_\/join_ \- Lets users ask an admin to approve them into allowed users list\.

*Admin restricted commands*
_\/requests_ \- Let admins check pending requests to join allowed users list, and approve or dismiss them\.
_\/dismiss_ \- Dismiss a request for joining allowed users list\. Remember to add user\_id argument\.
_\/adduser_ \- Add a user to allowed users list with user\_id argument\.
_\/removeuser_ \- Remove a user from allowed users list with user\_id argument\. Bot owner can\'t be banned\.
_\/banuser_ \- Add a user to banned users list so he can\'t request joining allowed users list\.  Remember to add user\_id argument\.
_\/unban_ \- Remove a user from banned users list\.  Remember to add user\_id argument\.
_\/makeadmin_ \- Add a user to admins list with user\_id argument\.
_\/revokeadmin_ \- Remove a user from admins list with user\_id argument\. Bot owner can\'t be removed\.
_\/banlist_ \- List all users banned from using the bot\. This users can\'t use join command\.
_\/version_ \- Shows version of the installed bot instance\.
_\/system_ \- Shows CPU temp\*, CPU and RAM load\.
_\/reboot_ \- Reboots system\. Default delay time is 5 secs\. You can configure delay time as an argument\.

\* Available only in Linux"""
# end of multiline text

# enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# filter handlers
def not_allowed_users(update: Update, context: CallbackContext) -> None:
    parsed_command, parsed_command_arg, parsed_command_error, user_id, chat_id = command_parser(update, context)
    if parsed_command == '/join' and parsed_command_arg not in banned_users:
        check_chatmember(user_id)
        join_command(update, context)
    else:
        check_chatmember(user_id)
        update.message.reply_text('Sorry you\'re not allowed to use this bot, but you can use /join command to request access to an admin.')

def not_command(update: Update, context: CallbackContext) -> None:
    parsed_command, parsed_command_arg, parsed_command_error, user_id, chat_id = command_parser(update, context)
    check_chatmember(user_id)
    update.message.reply_text('Sorry, I can\'t understand that.')

def check_command(update: Update, context: CallbackContext) -> None:
    parsed_command, parsed_command_arg, parsed_command_error, user_id, chat_id = command_parser(update, context)
    if parsed_command_error == True:
        return
    elif parsed_command not in commands:
        update.message.reply_text('Sorry that\'s not a real command. Check /help for available commands.')
    elif parsed_command in super_commands:
        if user_id in admin_users:
            admin_commands(update, context, parsed_command, parsed_command_arg, chat_id)
        else:
            not_admin(update, context)
    elif parsed_command in commands:
        user_commands(update, context, parsed_command, parsed_command_arg, chat_id)

def not_admin(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, you\'re not an admin, you can\'t use admin restricted commands.')

# command handlers
def user_commands(update: Update, context: CallbackContext, parsed_command, parsed_command_arg, chat_id) -> None:
    if parsed_command == '/start':
        start_command(update, context)
    elif parsed_command == '/help':
        help_command(update, context)
    elif parsed_command == '/listusers':
        listusers_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/adminusers':
        adminusers_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/chatmembers':
        chatmembers_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/join':
        join_command(update, context, parsed_command)

def admin_commands(update: Update, context: CallbackContext, parsed_command, parsed_command_arg, chat_id) -> None:
    if parsed_command == '/requests':
        requests_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/dismiss':
        dismiss_command(update, context, parsed_command, parsed_command_arg)
    elif parsed_command == '/adduser' or parsed_command == '/removeuser' or parsed_command == '/banuser' or parsed_command == '/unban' or parsed_command == '/makeadmin' or parsed_command == '/revokeadmin':
        anyuser_command(update, context, parsed_command, parsed_command_arg)
    elif parsed_command == '/banlist':
        banlist_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/version':
        version_command(update, context, parsed_command)
    elif parsed_command == '/system':
        system_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/reboot':
        reboot_command(update, context, parsed_command, parsed_command_arg)

def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('SmartHomeBot is running. Type /help to list all available commands.')

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2(help_command_markup)

def listusers_command(update: Update, context: CallbackContext, parsed_command, chat_id) -> None:
    listusers_msg = '*List of users allowed to use this bot:*\n'
    listusers_msg += users_list(update, parsed_command, chat_id)
    update.message.reply_markdown_v2(listusers_msg)

def adminusers_command(update: Update, context: CallbackContext, parsed_command, chat_id) -> None:
    adminusers_msg = '*List of admins:*\n'
    adminusers_msg += users_list(update, parsed_command, chat_id)
    update.message.reply_markdown_v2(adminusers_msg)

def chatmembers_command(update: Update, context: CallbackContext, parsed_command, chat_id) -> None:
    chatmembers_msg = '*List of chat members:*\n'
    chatmembers_msg += users_list(update, parsed_command, chat_id)
    update.message.reply_markdown_v2(chatmembers_msg)

def join_command(update: Update, context: CallbackContext, parsed_command) -> None:
    chat_info = update.message['chat']
    user_id = chat_info['id']
    if user_id in allowed_users:
        update.message.reply_text('You are already in allowed users list.')
    elif user_id in user_requests:
        update.message.reply_text('Your request is still pending for approval.')
    else:
        keyboard_markup = keyboard_construct('yes_no')
        update.message.reply_text('Are you sure?', reply_markup=keyboard_markup)

def requests_command(update: Update, context: CallbackContext, parsed_command, chat_id) -> None:
    if len(user_requests) == 0:
        update.message.reply_text('There are not pending requests.')
    else:
        requests_msg = 'There are ' + str(len(user_requests)) + ' pending requests\.\n\n'
        requests_msg += users_list(parsed_command, chat_id)
        requests_msg += '\nUse \/adduser to add them into allowed users list, or \/dismiss user\_id to reject the request\.\n'
        update.message.reply_markdown_v2(requests_msg)

def dismiss_command(update: Update, context: CallbackContext, parsed_command, parsed_command_arg) -> None:
    if len(user_requests) == 0:
        update.message.reply_text('There are not pending requests.')
    else:
        anyuser_command(update, context, parsed_command, parsed_command_arg)
        requests_command(update, context, parsed_command, parsed_command_arg)

def anyuser_command(update: Update, context: CallbackContext, parsed_command, parsed_command_arg) -> None:
    if parsed_command_arg == None:
        update.message.reply_text('You haven\'t provided user_id argument.')
    else:
        keyboard_markup = keyboard_construct('yes_no')
        update.message.reply_text('Are you sure?', reply_markup=keyboard_markup)

def reboot_command(update: Update, context: CallbackContext, parsed_command, *parsed_command_arg) -> None:
    keyboard_markup = keyboard_construct('yes_no')
    update.message.reply_text('Reboot your system?', reply_markup=keyboard_markup)

def system_command(update: Update, context: CallbackContext, parsed_command, chat_id) -> None:
    # skip CPU temperature if OS is not Linux.
    if psutil.LINUX == False:
        system_msg = '*CPU temperature:* _Not available_\n'
    else:
        Bot.SetChatAction(chat_id, 'typing')
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

def banlist_command(update: Update, context: CallbackContext, parsed_command, chat_id):
    banlist_msg = '*List of banned users:*\n'
    banlist_msg += users_list(update, parsed_command, chat_id)
    update.message.reply_markdown_v2(banlist_msg)

def version_command(update: Update, context: CallbackContext, parsed_command) -> None:
    github_info = requests.get("https://api.github.com/repos/Geek-MD/SmartHomeBot/releases/latest")
    github_version = github_info.json()["name"]
    version_msg = f'Local bot version is {version}.\n'
    version_msg += f'Github bot version is {github_version}.\n'
    if version < github_version:
        version_msg += f'\nThere\'s a new version of the bot available at GitHub ({github_version})\nUpdate bot version following Wiki instructions.'
    elif version == github_version:
        version_msg += f'\nBot version is up to date'
    update.message.reply_text(version_msg)

# internal callbacks
def reboot_callback(query, reboot_time=5):
    query.edit_message_text(text=f'Rebooting in {reboot_time} secs...')
    time.sleep(reboot_time)
    os.system("sudo reboot")

def join_callback(query, parsed_command, from_user_id):
    modify_data(query, parsed_command, from_user_id, None)

def user_callback(query, parsed_command, parsed_command_arg, from_user_id) -> None:
    user_callback_answer = user_callback_dict.get(parsed_command)
    if parsed_command == '/adduser':
        if parsed_command_arg in allowed_users:
            query.edit_message_text(text=f'The user is already on allowed users list.')
        elif parsed_command_arg in banned_users:
            query.edit_message_text(text=f'The user is on banned users list. You must unban the user first.')
        else:
            allowed_users.append(parsed_command_arg)
            users_dict.update({"allowed_users" : allowed_users})
            if parsed_command_arg in user_requests:
                user_requests.remove(parsed_command_arg)
                users_dict.update({"user_requests" : user_requests})
            config.update({"USERS" : users_dict})
            store_config(config)
            read_config()
            query.edit_message_text(text=user_callback_answer)
    elif parsed_command == '/removeuser':
        if parsed_command_arg in bot_owner:
            query.edit_message_text(text=f'The user is the owner of the bot, can\'t be kicked off.')
        elif parsed_command_arg == from_user_id:
            query.edit_message_text(text=f'Can\'t remove yourself from allowed users list.')
        elif parsed_command_arg in admin_users:
            query.edit_message_text(text=f'The user is an admin, can\'t be kicked off. You must remove the user from admins list first.')
        elif parsed_command_arg not in allowed_users:
            query.edit_message_text(text=f'The user is not in allowed users list.')
        else:
            allowed_users.remove(parsed_command_arg)
            users_dict.update({"allowed_users" : allowed_users})
            config.update({"USERS" : users_dict})
            store_config(config)
            read_config()
            query.edit_message_text(text=user_callback_answer)
    elif parsed_command == '/makeadmin':
        if parsed_command_arg in admin_users:
            query.edit_message_text(text=f'The user is already on admins list.')
        if parsed_command_arg not in allowed_users:
            query.edit_message_text(text=f'The user is not in allowed users list. You must add the user first.')
        else:
            admin_users.append(parsed_command_arg)
            users_dict.update({"admin_users" : admin_users})
            config.update({"USERS" : users_dict})
            store_config(config)
            read_config()
            query.edit_message_text(text=user_callback_answer)
    elif parsed_command == '/revokeadmin':
        if parsed_command_arg in bot_owner:
            query.edit_message_text(text=f'The user is the owner of the bot, can\'t be removed from admins list.')
        elif parsed_command_arg == from_user_id:
            query.edit_message_text(text=f'Can\'t ban yourself from admins list.')
        elif parsed_command_arg not in admin_users:
            query.edit_message_text(text=f'The user is not in admins list.')
        else:
            admin_users.remove(parsed_command_arg)
            users_dict.update({"admin_users" : admin_users})
            config.update({"USERS" : users_dict})
            store_config(config)
            read_config()
            query.edit_message_text(text=user_callback_answer)
    elif parsed_command == '/banuser':
        if parsed_command_arg in bot_owner:
            query.edit_message_text(text=f'The user is the owner of the bot, can\'t be banned.')
        elif parsed_command_arg == from_user_id:
            query.edit_message_text(text=f'Can\'t ban yourself.')
        elif parsed_command_arg in admin_users:
            query.edit_message_text(text=f'The user is an admin. You must remove the user from admins list first.')
        else:
            if parsed_command_arg in allowed_users:
                allowed_users.remove(parsed_command_arg)
                users_dict.update({"allowed_users" : allowed_users})
            banned_users.append(parsed_command_arg)
            users_dict.update({"banned_users" : banned_users})
            config.update({"USERS" : users_dict})
            store_config(config)
            read_config()
            query.edit_message_text(text=user_callback_answer)
    elif parsed_command == '/unban':
        banned_users.remove(parsed_command_arg)
        users_dict.update({"banned_users" : banned_users})
        config.update({"USERS" : users_dict})
        store_config(config)
        read_config()
        query.edit_message_text(text=user_callback_answer)
    elif parsed_command == '/join':
        user_requests.append(parsed_command_arg)
        users_dict.update({"user_requests" : user_requests})
        config.update({"USERS" : users_dict})
        store_config(config)
        read_config()
        query.edit_message_text(text=user_callback_answer)
    elif parsed_command == '/dismiss':
        user_requests.remove(parsed_command_arg)
        user_rejects.append(parsed_command_arg)
        users_dict.update({"user_requests" : user_requests})
        users_dict.update({"user_rejects" : user_rejects})
        config.update({"USERS" : users_dict})
        store_config(config)
        read_config()
        query.edit_message_text(text=user_callback_answer)

# internal modules
def check_chatmember(user_id) -> None:
    if user_id not in allowed_users and user_id not in chat_members:
        chat_members.append(user_id)
        users_dict.update({"chat_members" : chat_members})
        config.update({"USERS" : users_dict})
        store_config(config)
        read_config()

def command_parser(update: Update, context: CallbackContext) -> None:
    parsed_command_error = False
    parsed_message = update.message
    chat_info = update.message['chat']
    user_id = int(chat_info['id'])
    parsed_text = parsed_message['text']
    striped_text = parsed_text.strip()
    splitted_text = striped_text.split()
    if len(splitted_text) > 2:
        update.message.reply_markdown_v2('The command is malformed\. The correct format is _/command \*argument_\.')
        parsed_command = parsed_command_arg = None
        parsed_command_error = True
    elif len(splitted_text) == 1:
        parsed_command = splitted_text[0]
        parsed_command_arg = None
    else:
        parsed_command = splitted_text[0]
        parsed_command_arg = splitted_text[1]
    return parsed_command, parsed_command_arg, parsed_command_error, user_id, chat_id

def users_list(update: Update, parsed_command, chat_id) -> None:
    users_list_msg = pre = post = post_id = ""
    if parsed_command == '/listusers':
        method_list = allowed_users
    elif parsed_command == '/adminusers':
        method_list = admin_users
    elif parsed_command == '/chatmembers':
        method_list = allowed_users + chat_members
    elif parsed_command == '/requests':
        method_list = user_requests
    elif parsed_command == '/banlist':
        method_list = banned_users
    if len(method_list) == 0:
        users_list_msg += f"List is empty\."
    else:
        for n in range(0, len(method_list)):
            user_info = bot.getChatMember(chat_id=chat_id, user_id=method_list[n])
            user = user_info["user"]
            user_id = user["id"]
            username = user["username"]
            first_name = user["first_name"]
            last_name = user["last_name"]
            if parsed_command == '/adminusers' and user_id not in admin_users:
                pass
            else:
                if user_id in admin_users:
                    pre = post = '_'
                    if parsed_command == "/listusers" or parsed_command == "/chatmembers":
                        post_id = '\*'
                else:
                    pre = post = ''
                    if parsed_command == "/chatmembers" and user_id in allowed_users:
                        post_id = "\+"
                    elif parsed_command == "/chatmembers" and user_id in bot_id:
                        post_id = "\@"
                    else:
                        post_id = ""
                if username == None:
                    users_list_msg += f"{pre}{first_name} {last_name}{post} \– id: {user_id} {post_id}\n"
                else:
                    users_list_msg += f"{pre}@{username}{post} \- id: {user_id} {post_id}\n"
        if parsed_command == "/listusers" or parsed_command == "/chatmembers":
            users_list_msg += '\n\* admins'
        if parsed_command == "/chatmembers":
            users_list_msg += '\n\+ allowed users\n\@ bot'
    return users_list_msg

def keyboard_construct(keyboard_name):
    buttons = []
    for key, label in keyboard_dict[keyboard_name].items():
        buttons.append(InlineKeyboardButton(text=label, callback_data=key))
    return InlineKeyboardMarkup([buttons])

def keyboard_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    answer = query.answer()
    query_answer = query.data
    from_user = query.from_user
    from_user_id = from_user["id"]
    while answer == False:
        continue
    else:
        if query_answer == "y":
            if parsed_command == '/reboot':
                if parsed_command_arg == None:
                    reboot_callback(query)
                else:
                    reboot_callback(query, parsed_command_arg)
            elif parsed_command == '/join':
                join_callback(query, parsed_command, from_user_id)
            elif parsed_command == '/adduser' or parsed_command == '/removeuser' or parsed_command == '/makeadmin' or parsed_command == '/revokeadmin' or parsed_command == '/dismiss' or parsed_command == '/banuser' or parsed_command == '/unban' :
                user_callback(query, parsed_command, int(parsed_command_arg), from_user_id)
        elif query_answer == "n":
            if parsed_command == '/reboot':
                query.edit_message_text(text=f'Reboot aborted.')
            else:
                query.edit_message_text(text=f'Command aborted.')

def store_config(json_config) -> None:
    file = open('config.json', 'w')
    file.write(json.dumps(json_config, indent=2))
    file.close()

def read_config() -> None:
    global config, token_dict, bot_token, users_dict, allowed_users, admin_users, bot_owner, chat_members, user_requests, user_rejects, banned_users, bot_id, chat_dict, chat_id
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
    chat_members = users_dict.get("chat_members")
    user_requests = users_dict.get("user_requests")
    user_rejects = users_dict.get("user_rejects")
    banned_users = users_dict.get("banned_users")
    bot_id = users_dict.get("bot_id")
    chat_dict = config.get("CHATS")
    chat_id = chat_dict.get("allowed_chats")

# main module
def main() -> None:
    global updater, dispatcher, bot
    read_config()

    # create the Updater and pass it your bot's token
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    bot = Bot(bot_token)

    # not allowed users can't interact with the bot
    dispatcher.add_handler(MessageHandler(Filters.user(banned_users), not_allowed_users))
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
