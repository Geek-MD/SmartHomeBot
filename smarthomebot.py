#!/usr/bin/env python

"""
SmartHomeBot
A simple Telegram Bot used to automate notifications for a Smart Home.
The bot starts automatically and runs until you press Ctrl-C on the command line.

Usage:
Use /help to list available commands.
"""

import logging, os, time
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# bot variables
AUTH_TOKEN = "bot-token" # string
ALLOWED_USERS = [user_id_1, user_id_2] # integer
ADMIN_USERS = [user_id_1] #integer
commands = ['/start', '/help', '/reboot']
admin_commands = ['/reboot']
reboot_keyboard = [[InlineKeyboardButton("yes", callback_data='y'), InlineKeyboardButton("no", callback_data='n')]]
reboot_keyboard_markup = InlineKeyboardMarkup(reboot_keyboard)
reboot_option = None

# multiline markup text used for /help command.
help_command_text = """This is a simple Telegram Bot used to automate notifications for a Smart Home\.

*Available commands*
\/start \- does nothing, bot starts automatically
\/help \- shows a list of all available commands
\/reboot \- reboots system \(restricted to admins\)"""
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

def not_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, I can\'t understand that.')    

def not_admin(update: Update, context: CallbackContext) -> None:
    # not admin users can't run admin restricted commands.
    update.message.reply_text('Sorry, you\'re not an admin, you can\'t use admin restricted commands.')    

def not_allowed_users(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry you\'re not allowed to use this bot')

def main() -> None:
    # create the Updater and pass it your bot's token.
    updater = Updater(AUTH_TOKEN)

    # not allowed users can't interact with the bot.
    updater.dispatcher.add_handler(MessageHandler(~Filters.user(ALLOWED_USERS), not_allowed_users))

    # inline buttons.
    updater.dispatcher.add_handler(CallbackQueryHandler(reboot_query))

    # on non command i.e message, reply with not_command function.
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.text(commands), not_command))

    # on admin command, run is_admin_command function.
    updater.dispatcher.add_handler(MessageHandler(Filters.text(admin_commands) & ~Filters.user(ADMIN_USERS), not_admin))

    # commands.
    updater.dispatcher.add_handler(CommandHandler("start", start_command))
    updater.dispatcher.add_handler(CommandHandler("help", help_command))
    updater.dispatcher.add_handler(CommandHandler("reboot", reboot_command))

    # start the bot.
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
