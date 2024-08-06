# -*- coding: UTF-8 -*-
import typing
import discord
import wavelink
from datetime import datetime, timezone
from discord.ext import commands
from typing import Optional, cast
from reactionmenu import ViewButton,ViewMenu

from core.libs.bot import Cogs
from core.utils import colors,emojis

class PlayerNotFounded(Exception):
    pass

class Music(Cogs):
    def __init__(self, bot):
        super().__init__(bot)
      
    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        await player.home.send(f"{emojis.sleep} | 播放器已經閒置超過 {player.inactive_timeout} 秒，即將自動離開語音頻道 !")
        await player.disconnect()
        
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
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
        
        embed.add_field(name="FROM", value=f"[點擊這裡]({track.uri})")

        try:
            await player.home.send(embed=embed)
        except Exception as e:
            print(e)

    @commands.hybrid_command(name="play", description="播放音樂", with_app_command=True)
    async def play(self,ctx: commands.Context, *, query: str):
        embed = discord.Embed()
        embed.set_footer(text="Luminara")
        embed.timestamp=datetime.now(timezone.utc)

        if not ctx.guild:
            embed.color=discord.Color.red()
            embed.title="%s | 無法在私人訊息中使用此命令 !" % (emojis.errors)
            return await ctx.send(embed=embed)
        
        player : wavelink.Player
        player = cast(wavelink.Player, ctx.voice_client)
        
        async with ctx.typing():  
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
                
            player.autoplay = wavelink.AutoPlayMode.partial
            
            if not hasattr(player, "home"):
                player.home = ctx.channel
            elif player.home != ctx.channel:
                embed.color=discord.Color.red()
                embed.title="%s | 只能在 %s 執行本命令 !" % (emojis.errors,player.home.mention)
                return await ctx.send(embed=embed)
        
            tracks: wavelink.Search = await wavelink.Playable.search(query)

            if not tracks:
                embed.color=discord.Color.red()
                embed.title=f"{emojis.errors} | 找不到任何與您的查詢相符的結果 !" 
                await ctx.send(ctx.author.mention)
                return await ctx.send(embed=embed)

            if isinstance(tracks, wavelink.Playlist):
                added: int = await player.queue.put_wait(tracks)
                await ctx.send(f"{emojis.success} | 已將播放清單 **`{tracks.name}`** (共{added} 首) 加入序列")
            else:
                track: wavelink.Playable = tracks[0]
                await player.queue.put_wait(track)
                await ctx.send(f"{emojis.success} | 已將 **`{track}`** 加入序列")

            if not player.playing:
                return await player.play(player.queue.get())
    
    @commands.hybrid_command(name="disconnect", description="離開語音頻道", with_app_command=True)
    async def disconnect(self, ctx: commands.Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerNotFounded
        
        embed=discord.Embed()
        embed.color=colors.red
        embed.title=f"{emojis.success} | 已離開{player.channel.mention} !"
        embed.set_footer(text="Luminara")
        embed.timestamp=datetime.now(timezone.utc)
        
        await ctx.reply(embed=embed)
        return await player.disconnect()
    

    @commands.hybrid_command(name="queue", description="顯示播放序列", with_app_command=True)
    async def queue(self, ctx: commands.Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerNotFounded

        if player.queue.is_empty:
            return await ctx.reply(f"{emojis.errors} | 播放序列已經空了 !")
        
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

        back_button = ViewButton(style=discord.ButtonStyle.primary, label=None, emoji=emojis.back, custom_id=ViewButton.ID_PREVIOUS_PAGE)
        next_button = ViewButton(style=discord.ButtonStyle.primary, label=None, emoji=emojis.next, custom_id=ViewButton.ID_NEXT_PAGE)

        menu.add_button(back_button)
        menu.add_button(next_button)

        for page in range(1,(player.queue.count//10)+2):
            embed = discord.Embed()
            embed.set_footer(text=f"共{player.queue.count}首 • Luminara")
            embed.timestamp=datetime.now(timezone.utc)
            embed.color=discord.Color.purple()
            embed.title="%s | 播放序列" % (emojis.music)
            
            embed.description="```ini\n"
            start_index =(page- 1) * 10
            end_index = start_index + 10

            for index, track in enumerate(player.queue[start_index:end_index], start=start_index+1):
                embed.description += f"{index}. {track.title} by {track.author}\n"

            embed.description += "```"

            menu.add_page(embed)
    
        return await menu.start()
        
    
    @commands.hybrid_command(name="pasue", description="暫停播放", with_app_command=True)
    async def pasue(self, ctx: commands.Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerNotFounded
            
        if player.playing:
            await player.pause(True)
            return await ctx.reply(":pause_button: | 已暫停播放 !")
        
    @commands.hybrid_command(name="resume", description="恢復播放", with_app_command=True)
    async def resume(self, ctx: commands.Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerNotFounded

        if player.paused:
            await player.pause(False)
            return await ctx.reply(":play_pause: | 已恢復播放 !")
        
    @commands.hybrid_command(name="skip", description="跳過當前曲目", with_app_command=True)
    async def skip(self, ctx: commands.Context, index:Optional[int] = None):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)

        if not player:
            raise PlayerNotFounded
        
        if player.queue.is_empty:
            return await ctx.reply(f"{emojis.errors} | 播放序列已經空了，無法進行操作!")
        elif player.paused:
            return await ctx.reply(":pause_button: | 播放器已經暫停，無法進行操作 !")
        elif player.playing:
            if index==None:
                return await player.play(player.queue.get())
            elif index > player.queue.count:
                return await ctx.reply(f"{emojis.errors} | 請輸入有效的曲目編號 !")
            else:
                track:wavelink.Playable = player.queue.get_at(index-1)

                await player.play(track=track)
                return await ctx.reply(f":track_next: | 已跳過當前曲目 !即將播放。`{track.title}`")

    @commands.hybrid_command(name="effect",with_app_command=True,description="音樂效果操作") 
    async def effect(self,ctx: commands.Context, type:str):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerNotFounded

        if type == "clear":
            filters: wavelink.Filters = player.filters
            filters.timescale.set(speed=1, pitch=1, rate=1)
            await player.set_filters(filters)

            return await ctx.send(":musical_note: | 已清除所有音樂效果 !")
        elif type == "nightcore":
            filters: wavelink.Filters = player.filters
            filters.timescale.set(speed=1.25, pitch=1.2, rate=1)
            await player.set_filters(filters)

            return await ctx.reply(":musical_note: | 已啟用 Nightcore 效果 !")
    
    @effect.autocomplete("type")
    async def effect_autocomplete(self, ctx:commands.Context, current:str) -> typing.List[discord.app_commands.Choice]:
        return [discord.app_commands.Choice(name="Clear All", value="clear"),
                discord.app_commands.Choice(name="Nightcore", value="nightcore")]

    @commands.hybrid_command(name="volume", description="調整音量", with_app_command=True)
    async def volume(self, ctx: commands.Context, volume: int):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerNotFounded
        
        if volume > 100:
                volume = 100
        elif volume < 0:
            volume = 0

        await player.set_volume(volume)

        return await ctx.reply(f":loud_sound: | 已將音量調整至 {volume}% !")
        
    @volume.autocomplete("volume")
    async def volume_autocomplete(self, ctx:commands.Context, current:str) -> typing.List[discord.app_commands.Choice]:
        return [discord.app_commands.Choice(name="0%", value=0),
                discord.app_commands.Choice(name="25%", value=25),
                discord.app_commands.Choice(name="50%", value=50),
                discord.app_commands.Choice(name="75%", value=75),
                discord.app_commands.Choice(name="100%", value=100)]
    
    @commands.hybrid_command(name="nowplaying", description="顯示當前播放曲目", with_app_command=True)
    async def nowplaying(self, ctx: commands.Context):
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            raise PlayerNotFounded

        if not player.playing:
            return await ctx.reply(f"{emojis.errors} | 播放序列已經空了 !")
        
        track: wavelink.Playable = player.current
        embed = discord.Embed()
        embed.set_footer(text="Luminara")
        embed.timestamp=datetime.now(timezone.utc)
        embed.color=discord.Color.purple()
        embed.title="%s | 現正播放" % (emojis.music)
        embed.description=f"**{track.title}** by `{track.author}`"
        embed.set_thumbnail(url=track.artwork)
        embed.add_field(name="FROM", value=f"[點擊這裡]({track.uri})")

        return await ctx.reply(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Music(bot))