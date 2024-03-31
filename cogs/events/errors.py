# -*- coding: UTF-8 -*-
import discord
from discord.ext import commands
from datetime import datetime

import cogs.commands.music as music
from core.config import *
from classes import Cogs
from core.utils import colors, emojis

class Errors(Cogs):
    @commands.Cog.listener()
    async def on_command_error(self, ctx:commands.Context, error:commands.CommandError):
        print(error)

        embed=discord.Embed(color=colors.red,timestamp=datetime.now())
        embed.set_footer(text="Luminara")
        if isinstance(error, commands.MissingRequiredArgument):
            embed.add_field(name="%s | 遺失必要參數"%(emojis.errors),value="%s"%(error))
        if isinstance(error,commands.CommandNotFound):
            embed.add_field(name=":question: 未知命令",value="%s"%(error))   
        if isinstance(error,music.PlayerNotFounded):
            embed.add_field(name="%s | 未找到播放器"%(emojis.errors),value="請確保執行本命令時，機器人有在語音頻道中。")
        else:
            embed.add_field(name="%s | Unknown"%(emojis.errors),value="未知錯誤，請聯絡機器人開發者。")
            embed.add_field(name="Errors Infomations",value=f"{error}")

        return await ctx.send(embed=embed)

    

async def setup(bot):
    await bot.add_cog(Errors(bot))
