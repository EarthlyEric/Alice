import discord
import ipaddress
from datetime import datetime
from discord.ext import commands
from dns.resolver import Resolver

from core.libs.bot import Cogs
from core.libs.iptools import iptools
from core.libs.luminara_api import LuminaraAPI

class Tools(Cogs):
    @commands.hybrid_command(name="address-lookup", description="查詢 網域 或 IP", with_app_command=True)
    async def address_lookup(self, ctx: commands.Context, *, query: str):
        embed=discord.Embed()
        embed.timestamp=datetime.now()
        embed.title=f"**{query}**"
        embed.set_footer(text="Luminara")
        embed.color=discord.Color.green()
        try:
            if isinstance(ipaddress.ip_address(query), ipaddress.IPv4Address):
                embed.description="IPv4"
            elif isinstance(ipaddress.ip_address(query), ipaddress.IPv6Address):
                embed.description="IPv6"
        except ValueError:
            embed.description="Domains"
            resolver =  Resolver()
            try:
                query = await resolver.resolve_name(query)
            except Exception as e:
                return await ctx.send(f"Error: {e}")
        
        async with ctx.typing():
            ipinfo = await iptools.get_ipinfo(query)
            embed.add_field(name="城市", value=ipinfo.city, inline=True)
            embed.add_field(name="國家", value=ipinfo.region, inline=True)
            embed.add_field(name="國碼", value=ipinfo.country, inline=True)
            embed.add_field(name="位置", value=ipinfo.loc, inline=True)
            embed.add_field(name="屬於於", value=ipinfo.org, inline=True)
            embed.add_field(name="時區", value=ipinfo.timezone, inline=True)
            
            image = await LuminaraAPI.getGenerateMapImages(ipinfo.loc)
            image_file = discord.File(image, filename="maps.jpg")
            embed.set_image(url="attachment://maps.jpg")
            
            return await ctx.send(embed=embed, file=image_file)
        
    @commands.hybrid_command(name="ping", description="Ping 一個目標", with_app_command=True)
    async def ping(self, ctx: commands.Context, target: str):
        embed=discord.Embed()
        embed.timestamp=datetime.now()
        embed.title=f"**{target}**"
        embed.set_footer(text="Luminara")
        embed.color=discord.Color.green()
        
        async with ctx.typing():
            ping = await iptools.ping(target)
            embed.add_field(name="Ping", value=f"{ping}ms", inline=True)
            
            return await ctx.send(embed=embed)
        
              
async def setup(bot):
    await bot.add_cog(Tools(bot))