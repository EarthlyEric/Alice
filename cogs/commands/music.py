# -*- coding: UTF-8 -*-
import asyncio
import discord
import wavelink
from datetime import datetime, timezone
from core.utils import colors,icon,utils,emojis
from discord.ext import commands
from typing import cast

from classes import Cogs
from core.config import config
from ui.view import *
from ui.musiccontroller import MusicController

class Music(Cogs):
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        player: wavelink.Player | None = await self.bot.get_player(member.guild)
        if not player:
            return

        if len(player.channel.members) == 1 and player.connected:
            await player.home.channel.send("沒有人在語音頻道中，將在 10 秒後自動離開 !")
            await asyncio.sleep(10)
            return await player.disconnect()

    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            # Handle edge cases...
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed: discord.Embed = discord.Embed()
        embed.title = "%s | 現正放送 !" % (emojis.music)
        embed.color = discord.Color.purple()
        embed.timestamp=datetime.now(timezone.utc)
        embed.description = f"**{track.title}** by `{track.author}`"
        embed.set_footer(text="Luminara")
        
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        if original and original.recommended:
            embed.description += f"\n\n`本曲目來自 {track.source} 自動推薦`"

        if track.album.name:
            embed.add_field(name="專輯", value=track.album.name)

        now_playing_embed = await player.home.send(embed=embed)
        await now_playing_embed.delete(delay=60)

        musciController=MusicController(timestamp=datetime.now(timezone.utc),track=track)
        
    """
        Wait to build the music controller embed class.
    
        if not hasattr(player, "musicController_id"):
            musciController_id = await player.home.send(embed=musciController)
            player.musicController_id = musciController_id.id
        else:
            message = await player.channel.fetch_message(player.musicController_id)
            musciController_id = await message.edit(embed=musciController)
            player.musicController_id = musciController_id.id
    """

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            # Handle edge cases...
            return

        if player.queue.is_empty:
            return await player.play(player.auto_queue.get())
        else:
            return await player.play(player.queue.get())
    
    @commands.command(name="play")
    async def play(self,ctx: commands.Context, *, query: str):
        embed = discord.Embed()
        embed.set_footer(text="Luminara")
        embed.timestamp=datetime.now(timezone.utc)
        if not ctx.guild:
            embed.color=discord.Color.red()
            embed.title="%s | 無法在私人訊息中使用此命令 !" % (emojis.errors)
            return await ctx.send(embed=embed)
        
        loading = await ctx.reply("%s | 正在處理您的請求，請稍後..." % (emojis.loading))
    
        player : wavelink.Player
        player = cast(wavelink.Player, ctx.voice_client)
        
        if not player:
            try:
                embed.color=colors.green
                embed.title="%s | 成功加入您所處的語音頻道 %s !" % (emojis.success,ctx.author.voice.channel.mention)
                
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
                await ctx.send(embed=embed)
            except AttributeError:
                embed.color=discord.Color.red()
                embed.title="%s | 請先加入任一語音頻道後，再執行本命令 !" % (emojis.errors)
                return await ctx.send(embed=embed)   
            except discord.ClientException:
                embed.color=discord.Color.red()
                embed.title="%s | 未知原因，無法加入您所處的語音頻道 !" % (emojis.errors)
                return await ctx.send(embed=embed)
            
        player.autoplay = wavelink.AutoPlayMode.enabled

        if not hasattr(player, "home"):
            player.home = ctx.channel
        elif player.home != ctx.channel:
            embed.color=discord.Color.red()
            embed.title="%s | 只能在 %s 執行本命令 !" % (emojis.errors,player.home.mention)
            return await ctx.send(embed=embed)
        
        tracks: wavelink.Search = await wavelink.Playable.search(query)

        if not tracks:
            await loading.delete(delay=1.5)

            embed.color=discord.Color.red()
            embed.title="%s | 找不到任何與您的查詢相符的結果 !" % (emojis.errors)
            await ctx.send(ctx.author.mention)
            return await ctx.send(embed=embed)

        if isinstance(tracks, wavelink.Playlist):
            await loading.delete(delay=1.5)

            added: int = await player.queue.put_wait(tracks)
            await ctx.send(f"已將播放清單 **`{tracks.name}`** (共{added} 首) 加入序列")
        else:
            await loading.delete(delay=1.5)

            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await ctx.send(f"已將 **`{track}`** 加入序列")

        if not player.playing:
            await player.play(player.queue.get())

        @commands.command(name="pasue",aliases=["stop"])
        async def pasue(ctx: commands.Context):
            player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
            if not player:
                return
            

async def setup(bot):
    await bot.add_cog(Music(bot))