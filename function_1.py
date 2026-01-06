import os

import discord
from discord.ext import commands

token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()

intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command()
async def synccommands(ctx):
    await bot.tree.sync()
    await ctx.send("命令同步完成")


@bot.hybrid_command()
async def greet(ctx):
    await ctx.send("你说什么我都听不懂， 因为我只是一只奶牛猫。 我只听得懂我的主人跟我说“枣子过来”。")


@bot.hybrid_command()
async def add(ctx, a:int , b:int):
    await ctx.send(a + b)


bot.run(token)