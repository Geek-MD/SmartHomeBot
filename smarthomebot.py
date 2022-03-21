#!/usr/bin/env python

"""
SmartHomeBot
A simple Telegram Bot used to automate notifications for a Smart Home.
The bot starts automatically and runs until you press Ctrl-C on the command line.

Usage:
Use /help to list available commands.
"""

import logging
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# bot variables
AUTH_TOKEN = "bot_token"
commands = ['/start', '/help']

# multiline markup text used for /help command.
help_command_text = """This is a simple Telegram Bot used to automate notifications for a Smart Home\.

*Available commands*
\/start \- does nothing, bot starts automatically
\/help \- shows a list of all available commands"""
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

def not_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Sorry, I can\'t understand that.')

def main() -> None:
    # create the Updater and pass it your bot's token.
    updater = Updater(AUTH_TOKEN)

    # get the dispatcher to register handlers.
    dispatcher = updater.dispatcher

    # commands.
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message, reply with not_command function.
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.text(commands), not_command))

    # start the bot.
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
