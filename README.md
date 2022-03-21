<p align="center">
  <img width="460" height="460" src="https://user-images.githubusercontent.com/25725990/158142485-32e39afd-4f66-48bd-92b7-28c567c6b164.jpeg">
</p>

<h1 align="center">
SmartHomeBot
</h1>
<p>A simple Telegram Bot used to automate notifications of a Smart Home. This is a work in progress.<(p>

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](https://github.com/Naereen/StrapDown.js/blob/master/LICENSE) [![GitHub release](https://img.shields.io/github/release/Geek-MD/SmartHomeBot.svg)](https://GitHub.com/Geek-MD/SmartHomeBot/releases/) [![GitHub branches](https://badgen.net/github/branches/Geek-MD/SmartHomeBot)](https://github.com/Geek-MD/SmartHomeBot/) ![GitHub Stars](https://badgen.net/github/stars/Geek-MD/SmartHomeBot)

## Basic Installation
  This bot relies on [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot), so you have to install this package first with
  
  `pip install python-telegram-bot`
  
  Clone this repo with
  
  `git clone https://github.com/Geek-MD/SmartHomeBot.git`
  
  Edit smarthomebot.py, add your bot Telegram token, and you're done. Now run with
  
  `python smarthomebot.py`
  
  If you want the bot to run at startup, or advanced configuration, check the [Wiki](https://github.com/Geek-MD/SmartHomeBot/wiki).
  
## Roadmap
- [x] Basic functionality, only */start* and */help* commands. [`v0.1.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.1.0)
- [ ] Add a list of allowed users who can interact with the bot.
- [ ] Add a list of admin users who can run admin restricted commands.
- [ ] Add */reboot* command, restricted to admin users.
- [ ] Add confirmation buttons to execute */reboot* command.
- [ ] Critical data like Telegram bot token, allowed users list and admin users list are stored in external separate JSON files.
- [ ] Add */system* command so admins can check CPU temperature of server, CPU and RAM load.
- [ ] Add */adduser* command so admins can add users to the allowed users list.
- [ ] Add */makeadmin* command so admins can upgrade a user to admin list.
- [ ] Add */status* command so admins can see a list of running Docker containers.
- [ ] Add */restart* command so admins can restart a specific Docker container.
- [ ] Add Ring functionality thanks to [python-ring-doorbell](https://github.com/tchellomello/python-ring-doorbell).

## External Functionality
- Watchtower notification for Docker container updates through Telegram.
