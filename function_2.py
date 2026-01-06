import os
import random
from typing import Dict, Tuple, List

import discord
from discord.ext import commands

token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set. Please set env var first.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 绑定存储：key=(guild_id, binder_id) -> value=[member_id, ...]
bindings: Dict[Tuple[int, int], List[int]] = {}

team_1: Dict[Tuple[int, int], List[int]] = {}
team_2: Dict[Tuple[int, int], List[int]] = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")

    # 开发阶段建议：同步到指定测试服务器，立刻生效
    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        await bot.tree.sync(guild=guild)
        print(f"Synced commands to guild {guild_id}.")
    else:
        # 没设置就全局同步（可能会慢）
        await bot.tree.sync()
        print("Synced commands globally (may take time to appear).")


@bot.command()
async def synccommands(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("请在服务器里用这个命令。")
        return
    guild = discord.Object(id=ctx.guild.id)
    await bot.tree.sync(guild=guild)
    await ctx.send("命令同步完成（本服务器）")


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


@bot.hybrid_command(name="unbind", with_app_command=True)
async def unbind(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    key = (ctx.guild.id, ctx.author.id)

    if key not in bindings or not bindings[key]:
        await ctx.send("老大现在你还没有绑定任何人喵")
        return

    bindings.pop(key)
    await ctx.send("解绑成功!")

@bot.hybrid_command(name="check_bind", with_app_command=True)
async def check_bind(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    key = (ctx.guild.id, ctx.author.id)

    if key not in bindings or not bindings[key]:
        await ctx.send("老大现在你还没有绑定任何人喵")
        return

    user_ids = bindings[key]

    mentions = []
    for uid in user_ids:
        member = ctx.guild.get_member(uid)
        if member:
            mentions.append(member.mention)
        else:
            mentions.append(f"<@{uid}>")  # fallback（用户不在缓存里）

    msg = "老大，你当前绑定的是：\n" + " ".join(mentions)
    await ctx.send(msg)



@bot.hybrid_command(name="greet", with_app_command=True)
async def greet(ctx: commands.Context):
    await ctx.send("你说什么我都听不懂， 因为我只是一只奶牛猫。 我只听得懂我的主人跟我说“枣子过来”。")

@bot.hybrid_command(name="greeting", with_app_command=True)
async def greeting(ctx: commands.Context):
    await ctx.send("你说什么我都听不懂， 因为我只是一只奶牛猫。 我只听得懂我的主人跟我说“枣子过来”。")


@bot.hybrid_command(name="add", with_app_command=True)
async def add(ctx: commands.Context, a: int, b: int):
    await ctx.send(a + b)


@bot.hybrid_command(name="roll_team", with_app_command=True)
async def roll_team(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    key = (ctx.guild.id, ctx.author.id)

    # 1) 必须先有绑定
    if key not in bindings or not bindings[key]:
        await ctx.send("老大现在你还没有绑定任何人喵")
        return

    user_ids = bindings[key]

    # 2) 你说的是绑定的10个人：强制检查一下
    if len(user_ids) != 10:
        await ctx.send(f"老大你当前绑定了 {len(user_ids)} 个人喵，需要刚好 10 个才能 roll_team。")
        return

    # 3) 随机分组：打乱后切一半（5/5）
    shuffled = user_ids[:]  # copy
    random.shuffle(shuffled)

    t1 = shuffled[:5]
    t2 = shuffled[5:]

    # 4) 写入“新的变量”供后续功能使用
    team_1[key] = t1
    team_2[key] = t2

    # 5) 输出成员（@）
    def mention_list(ids: List[int]) -> str:
        parts = []
        for uid in ids:
            member = ctx.guild.get_member(uid)
            parts.append(member.mention if member else f"<@{uid}>")
        return " ".join(parts)

    msg = (
        "分组完成！\n"
        f"Team_1: {mention_list(t1)}\n"
        f"Team_2: {mention_list(t2)}"
    )
    await ctx.send(msg)


@bot.hybrid_command(name="check_team", with_app_command=True)
async def check_team(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    key = (ctx.guild.id, ctx.author.id)

    # 检查是否已经分队
    if key not in team_1 or key not in team_2 or not team_1[key] or not team_2[key]:
        await ctx.send("老大你还没分分队喵 请输入/roll_team 分队喵")
        return

    # 获取两队成员
    t1_ids = team_1[key]
    t2_ids = team_2[key]

    # 生成 mention 列表
    def mention_list(ids: List[int]) -> str:
        parts = []
        for uid in ids:
            member = ctx.guild.get_member(uid)
            parts.append(member.mention if member else f"<@{uid}>")
        return " ".join(parts)

    msg = (
        "当前分队情况：\n"
        f"**Team_1**: {mention_list(t1_ids)}\n"
        f"**Team_2**: {mention_list(t2_ids)}"
    )
    await ctx.send(msg)




bot.run(token)
