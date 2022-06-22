#!/usr/bin/env python

# SmartHomeBot v1.5.0
# A simple Telegram Bot used to automate notifications for a Smart Home.
# The bot starts automatically and runs until you press Ctrl-C on the command line.
#
# Usage:
# Use /help to list available commands.

import logging, os, time, json, psutil, re, requests, threading, math
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from gpiozero import CPUTemperature
from datetime import datetime

# define some bot variables
commands = ['/start', '/help', '/listusers', '/adminusers', '/chatmembers', '/join', '/time', '/timer', '/alarm', '/admincommands', '/requests', '/dismiss', '/adduser', '/removeuser', '/banuser', '/unban', '/makeadmin', '/revokeadmin', '/banlist', '/version', '/system', '/reboot']
super_commands = ['/admincommands', '/requests', '/dismiss', '/adduser', '/removeuser', '/banuser', '/unban', '/makeadmin', '/revokeadmin', '/banlist', '/version', '/system', '/reboot']
keyboard_dict = { 
    "yes_no" : {"y" : "yes", "n" : "no"}
}
callback_dict = {
    "/dismiss" : "User request dismissed.",
    "/adduser" : "User added to allowed users list.",
    "/removeuser" : "User removed from allowed users list.",
    "/banuser" : "User added to banned users list.",
    "/unban" : "User removed from banned users list.",
    "/makeadmin" : "User added to admins list.",
    "/revokeadmin" : "User removed from admins list."
}
listusers_dict = {
    '/listusers' : '*List of users allowed to use this bot:*\n',
    '/adminusers' : '*List of admins:*\n',
    '/chatmembers' : '*List of chat members:*\n',
    '/banlist' : '*List of banned users:*\n'
}
timers_dict = {
    '/timer' : {
        'timer_start' : 'timer started.',
        'timer_stop' : 'timer has ended.'
    },
    '/alarm' : {
        'timer_start' : 'Alarm configured at',
        'timer_stop' : 'alarm has ended.'
    }
}

# multiline markup text used for /help command.
help_str = """
This is a simple Telegram Bot used to automate notifications for a Smart Home\.

*Available commands*
``\/start`` \- Does nothing, bot starts automatically\.
``\/help`` \- Shows a list of all available commands\.
``\/listusers`` \- List all users allowed to use this bot\.
``\/adminusers`` \- List all users with admin capabilities\.
``\/chatmembers`` \- List members of the chat, including allowed users, admins and bot\.
``\/join`` \- Lets users ask an admin to approve them into allowed users list\.
``\/time`` \- Display local time\.
``\/timer`` \- Sets a timer and notifies when it\'s over\.
``\/alarm`` \- Sets an alarm and notifies when it\'s over\.

For admin restricted commands use ``\/admincommands``\.
"""

help_admin_str = """
*Admin restricted commands*
``\/requests`` \- Let admins check pending requests to join allowed users list, and approve or dismiss them\.
``\/dismiss`` \- Dismiss a request for joining allowed users list\. Remember to add user\_id argument\.
``\/adduser`` \- Add a user to allowed users list with user\_id argument\.
``\/removeuser`` \- Remove a user from allowed users list with user\_id argument\. Bot owner can\'t be banned\.
``\/banuser`` \- Add a user to banned users list so he can\'t request joining allowed users list\.  Remember to add user\_id argument\.
``\/unban`` \- Remove a user from banned users list\.  Remember to add user\_id argument\.
``\/makeadmin`` \- Add a user to admins list with user\_id argument\.
``\/revokeadmin`` \- Remove a user from admins list with user\_id argument\. Bot owner can\'t be removed\.
``\/banlist`` \- List all users banned from using the bot\. This users can\'t use join command\.
``\/version`` \- Shows version of the installed bot instance\.
``\/system`` \- Shows CPU temp\*, CPU and RAM load\.
``\/reboot`` \- Reboots system\. Default delay time is 5 secs\. You can configure delay time as an argument\.

\* Available only in Linux
"""

help_timer_str = """
*Timer help*
``\/timer`` \- Checks if there are any configured timers\.
``\/timer hh:mm`` \- Sets a timer for hh hours and mm minutes\. hh must be above 0, and mm must be between 0 and 59\.
``\/timer xxxs`` \- Sets a timer for xxx seconds\. Value can be greater than 59 seconds and you must use integers\.
``\/timer xxxm`` \- Sets a timer for xxx minutes\. Value can be greater than 59 minutes and you must use integers\.
``\/timer xxxh`` \- Sets a timer for xxx hours\. Value can be greater than 23 hours and you must use integers\.
"""

help_alarm_str = """
*Alarm help*
``\/alarm`` \- Checks if there are any configured timers\.
``\/alarm hh:mm`` \- Sets a timer for hh hour and mm minutes in 24 hour format\. hh must be between 0 and 23, and mm must be between 0 and 59\.
"""
# end of multiline text

parsed_command = parsed_command_arg = ''

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
        help_command(update, context, parsed_command_arg)
    elif parsed_command == '/listusers' or parsed_command == '/adminusers' or parsed_command == '/chatmembers':
        listusers_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/join':
        join_command(update, context, parsed_command)
    elif parsed_command == '/time':
        time_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/timer' or parsed_command == '/alarm':
        timer_command(update, context, parsed_command, parsed_command_arg)

def admin_commands(update: Update, context: CallbackContext, parsed_command, parsed_command_arg, chat_id) -> None:
    if parsed_command == '/admincommands':
        help_admin_command(update, context)
    elif parsed_command == '/requests':
        requests_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/dismiss':
        dismiss_command(update, context, parsed_command, parsed_command_arg)
    elif parsed_command == '/adduser' or parsed_command == '/removeuser' or parsed_command == '/banuser' or parsed_command == '/unban' or parsed_command == '/makeadmin' or parsed_command == '/revokeadmin':
        anyuser_command(update, context, parsed_command, parsed_command_arg)
    elif parsed_command == '/banlist':
        listusers_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/version':
        version_command(update, context)
    elif parsed_command == '/system':
        system_command(update, context, parsed_command, chat_id)
    elif parsed_command == '/reboot':
        reboot_command(update, context, parsed_command, parsed_command_arg)

def start_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('SmartHomeBot is running. Type /help to list all available commands.')

def help_command(update: Update, context: CallbackContext, parsed_command_arg) -> None:
    if parsed_command_arg is None:
        update.message.reply_markdown_v2(help_str)
    elif parsed_command_arg == 'timer':
        update.message.reply_markdown_v2(help_timer_str)
    elif parsed_command_arg == 'alarm':
        update.message.reply_markdown_v2(help_alarm_str)

def help_admin_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2(help_admin_str)

def listusers_command(update: Update, context: CallbackContext, parsed_command, chat_id) -> None:
    listusers_msg = ''
    if parsed_command == '/listusers' or parsed_command == '/adminusers' or parsed_command == '/chatmembers' or parsed_command == '/banlist':
        listusers_msg = listusers_dict.get(parsed_command)
    listusers_msg += users_list(update, parsed_command, chat_id)
    update.message.reply_markdown_v2(listusers_msg)

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

def time_command(update: Update, context: CallbackContext, parsed_command, chat_id) -> None:
    time_msg = time.strftime("%a %d/%m/%Y %H:%M %z", time.localtime())
    update.message.reply_text(time_msg)

def timer_command(update: Update, context: CallbackContext, parsed_command, parsed_command_arg) -> None:
    def timer_callback():
        timer_string, timer_start, timer_stop = timer_stringify(parsed_command, parsed_command_arg)
        update.message.reply_text(f'{timer_stop}')
        if parsed_command == '/timer':
            timers.remove(timer_string)
            timers_data.update({"timers" : timers})
        elif parsed_command == '/alarm':
            alarms.remove(timer_string)
            timers_data.update({"alarms" : alarms})
        config.update({"TIMERS" : timers_data})
        store_config(config)
        read_config()

    def timer_stringify(parsed_command, parsed_command_arg):
        timer_callback_answer = timers_dict.get(parsed_command)
        timer_start_string = timer_callback_answer.get('timer_start')
        timer_stop_string = timer_callback_answer.get('timer_stop')
        if parsed_command == '/timer':
            if parsed_command_arg.find(':') > -1:
                parsed_time = parsed_command_arg.rsplit(":")
                if int(parsed_time[0]) > 0:
                    time_hour_str = str(int(parsed_time[0])) + 'h'
                else:
                    time_hour_str = ''
                if int(parsed_time[1]) > 0:
                    time_minute_str = str(int(parsed_time[1])) + 'm'
                else:
                    time_minute_str = ''
                timer_string = time_hour_str + time_minute_str
            else:
                timer_string = parsed_command_arg
            timer_start = f'{timer_string} {timer_start_string}'
        elif parsed_command == '/alarm':
            alarm_day = later.day
            alarm_month = later.month
            alarm_year = later.year
            if alarm_day == now.day:
                timer_string = f'{time_hour:02d}:{time_minute:02d}'
            else:
                timer_string = f'{alarm_day:02d}/{alarm_month:02d}/{alarm_year:04d} {time_hour:02d}:{time_minute:02d}'
            timer_start = f'{timer_start_string} {timer_string}'
        timer_stop = f'{timer_string} {timer_stop_string}'
        return timer_string, timer_start, timer_stop

    def timer_error(parsed_command):
        if parsed_command == '/timer':
            timer_error_msg = '``/help timer``'
        if parsed_command == '/alarm':
            timer_error_msg = '``/help alarm``'
        update.message.reply_markdown_v2(f'Time argument is malformed\. Check {timer_error_msg} for more info\.')
        return True

    def timer_list(parsed_command, later):
        timers_data = config.get("TIMERS")
        timers = timers_data.get("timers")
        alarms = timers_data.get("alarms")
        timer_count = len(timers)
        alarm_count = len(alarms)
        timer_data = ''
        if parsed_command == '/timer':
            timer_type = 'timers'
            timer_type_single = f'is a timer'
            timer_type_plural = f'are {timer_count} timers'
            for x in timers:
                if timer_count > 2 and timers.index(x) < timer_count-2:
                    timer_data += f'{x}, '
                if timer_count-2 == timers.index(x):
                    timer_data += f'{x} and '
                if timer_count-1 == timers.index(x):
                    timer_data += f'{x}'
        elif parsed_command == '/alarm':
            timer_type = 'alarms'
            timer_type_single = 'is an alarm'
            timer_type_plural = f'are {alarm_count} alarms'
            for x in alarms:
                if alarm_count > 2 and alarms.index(x) < alarm_count-2:
                    timer_data += f'{x}, '
                if alarm_count-2 == alarms.index(x):
                    timer_data += f'{x} and '
                if alarm_count-1 == alarms.index(x):
                    timer_data += f'{x}'
        if timer_count == 0 and parsed_command == '/timer':
            update.message.reply_text(f'There aren\'t configured {timer_type} at all.')
        elif timer_count == 1 and parsed_command == '/timer':
            update.message.reply_text(f'There {timer_type_single} configured for {timer_data}')
        elif alarm_count == 0 and parsed_command == '/alarm':
            update.message.reply_text(f'There aren\'t configured {timer_type} at all.')
        elif alarm_count == 1 and parsed_command == '/alarm':
            update.message.reply_text(f'There {timer_type_single} configured for {timer_data}')    
        else:
            update.message.reply_text(f'There {timer_type_plural} configured for {timer_data}')

    def timer_check(parsed_command, parsed_command_arg):
        global timer
        time_error = False
        time_day = now.day
        time_hour = now.hour
        time_minute = now.minute
        time_second = now.second
        if time_error == False:
            if parsed_command_arg.find(':') > -1:
                parsed_time = parsed_command_arg.rsplit(":")
                if len(parsed_time) > 2:
                    time_error = timer_error(parsed_command)
                elif parsed_command == '/timer':
                    time_hour = now.hour + int(parsed_time[0])
                    time_minute = now.minute + int(parsed_time[1])
                elif parsed_command == '/alarm':
                    time_hour = int(parsed_time[0])
                    time_minute = int(parsed_time[1])
                    time_second = 0
                    if time_minute > 59 or time_hour > 23:
                        time_error = timer_error(parsed_command)
                    elif time_hour < now.hour:
                        time_day = now.day + 1
            elif parsed_command == "/timer":
                if parsed_command_arg.endswith("s") == True:
                    time_second = now.second + int(parsed_command_arg.replace("s", ""))
                elif parsed_command_arg.endswith("m") == True:
                    time_minute = now.minute + int(parsed_command_arg.replace("m", ""))
                elif parsed_command_arg.endswith("h") == True:
                    time_hour = now.hour + int(parsed_command_arg.replace("h", ""))
                else:
                    time_error = timer_error(parsed_command)
            if time_second > 59:
                corrected_minute = math.floor(time_second/60)
                time_second = math.floor(time_second - corrected_minute*60)
                time_minute = now.minute + corrected_minute
            if time_minute > 59:
                corrected_hour = math.floor(time_minute/60)
                time_minute = math.floor(time_minute - corrected_hour*60)
                time_hour = now.hour + corrected_hour
            if time_hour > 23:
                time_day = now.day + math.floor(time_hour/24)
                time_hour = math.floor(time_hour - time_day*24)
            return time_day, time_hour, time_minute, time_second, time_error
        elif time_error == True:
            return time_day, time_hour, time_minute, time_second, time_error

    def timer_start(total_secs, later, parsed_command, parsed_command_arg):
        timer_string, timer_start, timer_stop = timer_stringify(parsed_command, parsed_command_arg)
        timer = threading.Timer(total_secs, timer_callback)
        update.message.reply_text(f'{timer_start}')
        timer.start()
        if parsed_command == '/timer':
            timers.append(timer_string)
            timers_data.update({"timers" : timers})
        elif parsed_command == '/alarm':
            alarms.append(timer_string)
            timers_data.update({"alarms" : alarms})
        config.update({"TIMERS" : timers_data})
        store_config(config)
        read_config()
        return timer
    
    global timer
    if parsed_command_arg is None:
        timer_list(parsed_command, None)
    else:
        now = datetime.now()
        time_day, time_hour, time_minute, time_second, time_error = timer_check(parsed_command, parsed_command_arg)
        later = datetime(now.year, now.month, time_day, hour=time_hour, minute=time_minute, second=time_second)
        if time_error == False:
            difference = (later - now)
            total_secs = round(difference.total_seconds())
            timer = timer_start(total_secs, later, parsed_command, parsed_command_arg)
        else:
            pass

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

def version_command(update: Update, context: CallbackContext) -> None:
    github_info = requests.get("https://api.github.com/repos/Geek-MD/SmartHomeBot/releases/latest")
    github_version = github_info.json()["name"]
    version_msg = f'Local version is {bot_version}\n'
    version_msg += f'Github version is {github_version}\n'
    if bot_version < github_version:
        version_msg += f'\nThere\'s a new version of the bot available at GitHub ({github_version})\nUpdate bot version following Wiki instructions.'
    elif bot_version == github_version:
        version_msg += f'\nBot version is up to date'
    elif bot_version > github_version:
        version_msg += f'\nLocal version is ahead of GitHub version.'
    update.message.reply_text(version_msg)

# internal callbacks
def reboot_callback(query, reboot_time=5):
    query.edit_message_text(text=f'Rebooting in {reboot_time} secs...')
    time.sleep(reboot_time)
    os.system("sudo reboot")

def join_callback(query, parsed_command, from_user_id):
    user_callback(query, parsed_command, from_user_id, None)

def user_callback(query, parsed_command, parsed_command_arg, from_user_id) -> None:
    callback_answer = callback_dict.get(parsed_command)
    if parsed_command == '/adduser':
        if parsed_command_arg in allowed_users:
            query.edit_message_text(text=f'The user is already on allowed users list.')
        elif parsed_command_arg in banned_users:
            query.edit_message_text(text=f'The user is on banned users list. You must unban the user first.')
        else:
            allowed_users.append(parsed_command_arg)
            users_data.update({"allowed_users" : allowed_users})
            if parsed_command_arg in user_requests:
                user_requests.remove(parsed_command_arg)
                users_data.update({"user_requests" : user_requests})
            config.update({"USERS" : users_data})
            store_config(config)
            read_config()
            query.edit_message_text(text=callback_answer)
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
            users_data.update({"allowed_users" : allowed_users})
            config.update({"USERS" : users_data})
            store_config(config)
            read_config()
            query.edit_message_text(text=callback_answer)
    elif parsed_command == '/makeadmin':
        if parsed_command_arg in admin_users:
            query.edit_message_text(text=f'The user is already on admins list.')
        if parsed_command_arg not in allowed_users:
            query.edit_message_text(text=f'The user is not in allowed users list. You must add the user first.')
        else:
            admin_users.append(parsed_command_arg)
            users_data.update({"admin_users" : admin_users})
            config.update({"USERS" : users_data})
            store_config(config)
            read_config()
            query.edit_message_text(text=callback_answer)
    elif parsed_command == '/revokeadmin':
        if parsed_command_arg in bot_owner:
            query.edit_message_text(text=f'The user is the owner of the bot, can\'t be removed from admins list.')
        elif parsed_command_arg == from_user_id:
            query.edit_message_text(text=f'Can\'t ban yourself from admins list.')
        elif parsed_command_arg not in admin_users:
            query.edit_message_text(text=f'The user is not in admins list.')
        else:
            admin_users.remove(parsed_command_arg)
            users_data.update({"admin_users" : admin_users})
            config.update({"USERS" : users_data})
            store_config(config)
            read_config()
            query.edit_message_text(text=callback_answer)
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
                users_data.update({"allowed_users" : allowed_users})
            banned_users.append(parsed_command_arg)
            users_data.update({"banned_users" : banned_users})
            config.update({"USERS" : users_data})
            store_config(config)
            read_config()
            query.edit_message_text(text=callback_answer)
    elif parsed_command == '/unban':
        banned_users.remove(parsed_command_arg)
        users_data.update({"banned_users" : banned_users})
        config.update({"USERS" : users_data})
        store_config(config)
        read_config()
        query.edit_message_text(text=callback_answer)
    elif parsed_command == '/join':
        user_requests.append(parsed_command_arg)
        users_data.update({"user_requests" : user_requests})
        config.update({"USERS" : users_data})
        store_config(config)
        read_config()
        query.edit_message_text(text=callback_answer)
    elif parsed_command == '/dismiss':
        user_requests.remove(parsed_command_arg)
        user_rejects.append(parsed_command_arg)
        users_data.update({"user_requests" : user_requests})
        users_data.update({"user_rejects" : user_rejects})
        config.update({"USERS" : users_data})
        store_config(config)
        read_config()
        query.edit_message_text(text=callback_answer)

# internal modules
def check_chatmember(user_id) -> None:
    if user_id not in allowed_users and user_id not in chat_members:
        chat_members.append(user_id)
        users_data.update({"chat_members" : chat_members})
        config.update({"USERS" : users_data})
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
                    elif parsed_command == "/chatmembers" and user_id == bot_id:
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
    global config, bot_data, bot_token, bot_id, bot_version, users_data, allowed_users, admin_users, bot_owner, chat_members, user_requests, user_rejects, banned_users, chats_data, chat_id, timers_data, timers, alarms
    file = open('config.json', 'r')
    json_data = file.read()
    file.close()

    config = json.loads(json_data)

    config = json.loads(json_data)
    bot_data = config.get("BOT_DATA")
    users_data = config.get("USERS")
    chats_data = config.get("CHATS")
    timers_data = config.get("TIMERS")
    bot_token = bot_data.get("bot_token")
    bot_id = bot_data.get("bot_id")
    bot_version = bot_data.get("bot_version")
    allowed_users = users_data.get("allowed_users")
    admin_users = users_data.get("admin_users")
    bot_owner = users_data.get("bot_owner")
    chat_members = users_data.get("chat_members")
    user_requests = users_data.get("user_requests")
    user_rejects = users_data.get("user_rejects")
    banned_users = users_data.get("banned_users")
    chat_id = chats_data.get("allowed_chats")
    timers = timers_data.get("timers")
    alarms = timers_data.get("alarms")

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
