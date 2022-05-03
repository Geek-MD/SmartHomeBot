<p align="center">
  <img width="460" height="460" src="https://user-images.githubusercontent.com/25725990/158142485-32e39afd-4f66-48bd-92b7-28c567c6b164.jpeg">
</p>

<h1 align="center">
SmartHomeBot
</h1>
<p align="center">A simple Telegram Bot used to automate notifications of a Smart Home. This is a work in progress.</p>
<p />
<p align="center"><a href="https://www.python.org/"><img alt ="Made with Python" src="https://img.shields.io/badge/Made%20with-Python-1f425f.svg"> <a href="https://github.com/git/git-scm.com/blob/main/MIT-LICENSE.txt"><img alt="MIT License" src="https://img.shields.io/github/license/Naereen/StrapDown.js.svg"></a> <a href="https://GitHub.com/Geek-MD/SmartHomeBot/releases/"><img alt="GitHub Releases" src="https://img.shields.io/github/release/Geek-MD/SmartHomeBot.svg"> <a href="https://github.com/Geek-MD/SmartHomeBot/"><img alt="GitHub Branches" src="https://badgen.net/github/branches/Geek-MD/SmartHomeBot"></a> <img alt="GitHub Stars" src="https://badgen.net/github/stars/Geek-MD/SmartHomeBot"></p>
<p />

## Basic Installation
This bot is designed to work on a ***Raspberry Py*** and relies mainly on *[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)*, so you have to install this package first with
  
```
pip install python-telegram-bot
```

Also you have to install *gpiozero* and *psutil* library used for */system* command.

```
pip install gpiozero
pip install psutil
```

Now clone this repo with
  
```
git clone https://github.com/Geek-MD/SmartHomeBot.git
```
  
Edit ***config.json*** and add your bot Telegram token, id number of allowed and admin users, id number of bot owner, chat_id used by your bot and you're done. Now run with

```
python smarthomebot.py
```
  
If you want to run the bot at startup, or advanced configuration, check the [Wiki](https://github.com/Geek-MD/SmartHomeBot/wiki).
  
## Roadmap
- [X] Basic functionality, only */start* and */help* commands. [`v0.1.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.1.0)
- [X] Added a list of allowed users who can interact with the bot. [`v0.2.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.2.0)
- [X] Added a list of admin users who can run admin restricted commands. [`v0.3.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.3.0)
- [X] Fixed a bug with admin restricted commands. [`v0.3.1`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.3.1)
- [X] Added */reboot* command, restricted to admin users. [`v0.4.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.4.0)
- [X] Added confirmation buttons to execute */reboot* command. [`v0.4.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.4.0)
- [X] Critical data like Telegram bot token, allowed users list and admin users list are stored in external separate JSON files. [`v0.5.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.5.0)
- [X] Added */system* command so admins can check CPU temperature of server, CPU and RAM load. [`v0.6.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.6.0)
- [X] The information displayed by */system* command is grouped into one unique message. [`v0.6.1`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.6.1)
- [X] CPU Temperature is available only in Linux due to limitations of gpiozero library. Added OS check to bypass CPU Temperature measurement. [`v0.6.2`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.6.2)
- [X] Added */listusers* command so any user can check allowed users list. [`v0.7.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.7.0)
- [X] Fixed a bug with */listusers* command. Users data now is read using getChatMember API method. Deleted ***users_data.json*** so user info is not stored locally. [`v0.7.1`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.7.1)
- [X] Added *owner* tag for main user so he can't be kicked off from allowed users or admin list. [`v0.7.2`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.7.2)
- [X] Added a dynamic keyboard constructor for future commands that uses an inline keyboard. [`v0.7.2`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.7.2)
- [X] Deleted ***smarthomebot.json***, ***allowed_users.json***, ***admin_users.json*** and ***chats.json*** files, and unified them on a single file named ***config.json***. [`v0.7.2`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.7.2)
- [X] Added */adduser* command so admins can add users to the allowed users list. [`v0.8.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.8.0)
- [X] Added */banuser* command so admins can remove users from the allowed users list, with the exception of bot owner. [`v0.8.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.8.0)
- [X] Modifications to allowed users list are stored directly to ***config.json***. [`v0.8.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v0.8.0)
- [X] Added */makeadmin* command so admins can upgrade a user to admin list. [`v1.0.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v1.0.0)
- [X] Added */revokeadmin* command so an admin can downgrade a user from admin to allowed user, with the exception of bot owner. [`v1.0.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v1.0.0)
- [X] Added a specific */adminusers* command for listing users with admin capabilities. [`v1.1.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v1.1.0)
- [X] Highlight admin users at */listusers* command. [`v1.1.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v1.1.0)
- [X] Fixed a bug related to admin users filter. [`v1.1.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v1.1.0)
- [X] Added f-string to some dialogs. [`v1.1.0`](https://github.com/Geek-MD/SmartHomeBot/releases/tag/v1.1.0)
- [ ] Add */status* command so admins can see a list of running Docker containers.
- [ ] Add */restart* command so admins can restart a specific Docker container.
- [ ] Add Ring functionality thanks to [python-ring-doorbell](https://github.com/tchellomello/python-ring-doorbell).

## External Functionality
- [X] Watchtower notification for Docker container updates through Telegram.
- [X] Receive Telegram notifications from Home app.
