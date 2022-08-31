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

Also you have to install *gpiozero*, *psutil* and *requests* libraries used for */system* and */version* command.

```
pip install gpiozero
pip install psutil
pip install requests
```

Next step is to clone this repo with
  
```
git clone https://github.com/Geek-MD/SmartHomeBot.git
```
  
Edit ***config.json*** and add your bot Telegram token, id number of allowed and admin users, id number of bot owner, chat id used by your bot, bot id and you're done, or you just can run the program and it´ll ask you for that parameters at start.

```
python3 smarthomebot.py
```
  
If you want to run the bot at startup, or advanced configuration, check the [Wiki](https://github.com/Geek-MD/SmartHomeBot/wiki).
  
## Roadmap
Check [Changelog](https://github.com/Geek-MD/SmartHomeBot/wiki/Changelog) for information about version enhancements.
