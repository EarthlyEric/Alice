# -*- coding: UTF-8 -*-
import discord
import datetime
import time
import platform
import asyncio
import os
from datetime import datetime, timezone
import core.libs.bot as bot
from core.libs.luminara_api import LuminaraAPI
from core.config import config

bot = bot.Bot()
bot.remove_command("help")
bot.launch_time=datetime.now(timezone.utc)

async def start_up():
    luminara_api_status = await LuminaraAPI.getStatus()

    if platform.system() == "Windows": os.system("") 
    else: os.system("clear")
    print(open("./res/logo/logo.txt", "r").read())
    time.sleep(0.3)
    print("Luminara is online")
    print("Login as %s"%(bot.user))
    print("Luminara Version: %s"%(config.version))
    print("Discord API Version: %s"%(discord.__version__))
    print("Luminara API Version: %s"%(luminara_api_status.version))
    
@bot.event
async def on_ready():
    await bot.tree.sync()
    await start_up()
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.streaming, name="%shelp | 在 %s 個伺服器中"%(bot.command_prefix,str(len(bot.guilds))))
        )

async def main():
    async with bot:
        events = os.listdir("./extensions/events")
        commands = os.listdir("./extensions/commands")
        for event in events:
            if event.endswith(".py"):
                await bot.load_extension(f"extensions.events.{event[:-3]}")
        for command in commands:
            if command.endswith(".py"):
                await bot.load_extension(f"extensions.commands.{command[:-3]}")
        await bot.start(config.token)

asyncio.run(main())