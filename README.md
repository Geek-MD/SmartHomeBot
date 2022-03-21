<p align="center">
  <img width="460" height="460" src="https://user-images.githubusercontent.com/25725990/158142485-32e39afd-4f66-48bd-92b7-28c567c6b164.jpeg">
</p>

<h1 align="center">
SmartHomeBot
</h1>
A simple Telegram Bot used to automate notifications of a Smart Home. This is a work in progress.

This bot relies on [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot), so you have to install this package first.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![GitHub release](https://img.shields.io/github/release/Geek-MD/SmartHomeBot.svg)](https://GitHub.com/Geek-MD/SmartHomeBot/releases/) [![GitHub branches](https://badgen.net/github/branches/Geek-MD/SmartHomeBot)](https://github.com/Geek-MD/SmartHomeBot/) ![GitHub Stars](https://badgen.net/github/stars/Geek-MD/SmartHomeBot)


## Roadmap
- [x] Basic functionality, only */start* and */help* commands. [`v0.1.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.1.0)
- [x] Added a list of allowed users who can interact with the bot.
- [ ] Added a list of admin users who can run admin restricted commands.
- [ ] Added */reboot* command, restricted to admin users.
- [ ] Added confirmation buttons to execute */reboot* command.
- [ ] Critical data like Telegram bot token, allowed users list and admin users list are stored in external separate JSON files.
- [ ] Added */system* command so admins can check CPU temperature of server, CPU and RAM load.
- [ ] Added */adduser* command so admins can add users to the allowed users list.
- [ ] Added */makeadmin* command so admins can upgrade a user to admin list.
- [ ] Added */status* command so admins can see a list of running Docker containers.
- [ ] Added */restart* command so admins can restart a specific Docker container.

## External Functionality
- Watchtower notification for Docker container updates through Telegram.
