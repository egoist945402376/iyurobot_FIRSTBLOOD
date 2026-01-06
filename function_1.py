import os

import discord
from discord.ext import commands
from typing import Dict, Tuple, List



token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()

intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

bindings: Dict[Tuple[int, int], List[int]] = {}



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



@bot.hybrid_command(name="bind_10", with_app_command=True)
async def bind_10(
    ctx: commands.Context,
    user1: discord.Member,
    user2: discord.Member,
    user3: discord.Member,
    user4: discord.Member,
    user5: discord.Member,
    user6: discord.Member,
    user7: discord.Member,
    user8: discord.Member,
    user9: discord.Member,
    user10: discord.Member,
):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    binder_id = ctx.author.id
    guild_id = ctx.guild.id
    key = (guild_id, binder_id)

    users = [user1, user2, user3, user4, user5, user6, user7, user8, user9, user10]
    user_ids = [u.id for u in users]

    # 可选：去重（避免选到重复的人）
    seen = set()
    deduped = []
    for uid in user_ids:
        if uid not in seen:
            seen.add(uid)
            deduped.append(uid)

    bindings[key] = deduped
    await ctx.send("绑定完成！")





bot.run(token)