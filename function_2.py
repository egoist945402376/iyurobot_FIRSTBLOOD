import os
import random
from typing import Dict, Tuple, List, Optional, Set
from dataclasses import dataclass, field

import discord
from discord.ext import commands


# 任务池
TASK_POOL = [
    "补兵最多", "补兵最少",
    "控制得分最高", "控制得分最低",
    "助攻数最高", "助攻数最低",
    "抗伤最高", "抗伤最低",
]

Key = Tuple[int, int] 

host_binding: Dict[int, int] = {}

@dataclass
class RoundState:
    team1: List[int] = field(default_factory=list)
    team2: List[int] = field(default_factory=list)

    imposter_team1: Optional[int] = None
    imposter_team2: Optional[int] = None

    tasker_team1: Optional[int] = None
    tasker_team2: Optional[int] = None
    task_team1: Optional[str] = None
    task_team2: Optional[str] = None

    blocker_team1: Optional[int] = None
    blocker_team2: Optional[int] = None

    # 哪些内鬼已经 /accept 了
    accepted_imposters: Set[int] = field(default_factory=set)


# 每一局的状态：key=(服务器, 发起者)
round_state: Dict[Key, RoundState] = {}

pending_imposter_accept: Dict[Tuple[int, int], int] = {}



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


def mention_from_id(guild: discord.Guild, uid: int) -> str:
    m = guild.get_member(uid)
    return m.mention if m else f"<@{uid}>"



async def display_name_from_id(
    guild: discord.Guild,
    uid: int,
) -> str:
    # 1)
    member = guild.get_member(uid)
    if member:
        return member.display_name

    # 2)fetch_member
    try:
        member = await guild.fetch_member(uid)
        return member.display_name
    except discord.NotFound:
        pass
    except discord.Forbidden:
        pass

    # 3)
    try:
        user = await bot.fetch_user(uid)
        return user.name
    except Exception:
        return str(uid)


def name_from_id(guild: discord.Guild, uid: int) -> str:
    m = guild.get_member(uid)
    return m.display_name if m else str(uid)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")

    # 开发阶段建议：同步到指定测试服务器，立刻生效
    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        #await bot.tree.sync(guild=guild)
        print(f"Synced commands to guild {guild_id}.")
    else:
        # 没设置就全局同步（可能会慢）
        await bot.tree.sync()
        print("Synced commands globally (may take time to appear).")


'''@bot.command()
async def synccommands(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("请在服务器里用这个命令。")
        return
    guild = discord.Object(id=ctx.guild.id)
    synced = await bot.tree.sync(guild=guild)
    await ctx.send("本服务器已同步命令： " + ", ".join([c.name for c in synced]))'''


@bot.command()
async def synccommands(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("请在服务器里用这个命令。")
        return

    guild = discord.Object(id=ctx.guild.id)

    # ✅ 关键：把全局命令复制到这个服务器，方便立刻看到 /
    bot.tree.copy_global_to(guild=guild)

    synced = await bot.tree.sync(guild=guild)
    await ctx.send("本服务器已同步命令： " + ", ".join([c.name for c in synced]))

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


@bot.hybrid_command(name="assign_imposter_task", with_app_command=True)
async def assign_imposter_task(ctx: commands.Context):
    await ctx.defer()

    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    key: Key = (ctx.guild.id, ctx.author.id)

    # 必须先 roll_team
    if key not in team_1 or key not in team_2 or not team_1[key] or not team_2[key]:
        await ctx.send("老大你还没有 roll_team 喵，请先用 /roll_team 分好组。")
        return

    t1 = team_1[key][:]
    t2 = team_2[key][:]

    if len(t1) < 2 or len(t2) < 2:
        await ctx.send("队伍人数太少喵（每队至少要 2 人才能抽 tasker+blocker）。")
        return

    state = RoundState(team1=t1, team2=t2)

    # 1) 抽内鬼（每队1人）
    state.imposter_team1 = random.choice(t1)
    state.imposter_team2 = random.choice(t2)

    # 2) 抽 tasker（每队1人）+ 分任务
    state.tasker_team1 = random.choice(t1)
    state.tasker_team2 = random.choice(t2)
    state.task_team1 = random.choice(TASK_POOL)
    state.task_team2 = random.choice(TASK_POOL)

    # 3) 抽 blocker（每队1人），不能和 tasker 同一个人
    t1_blocker_candidates = [uid for uid in t1 if uid != state.tasker_team1]
    t2_blocker_candidates = [uid for uid in t2 if uid != state.tasker_team2]
    if not t1_blocker_candidates or not t2_blocker_candidates:
        await ctx.send("老大，有一队人太少导致 blocker 无法避开 tasker 喵。")
        return

    state.blocker_team1 = random.choice(t1_blocker_candidates)
    state.blocker_team2 = random.choice(t2_blocker_candidates)

    # 写入状态
    round_state[key] = state

    # 写入“待 accept”索引（每队内鬼各一条）
    pending_imposter_accept[(ctx.guild.id, state.imposter_team1)] = ctx.author.id
    pending_imposter_accept[(ctx.guild.id, state.imposter_team2)] = ctx.author.id

    # ====== 发送 DM ======
    async def safe_dm(user_id: int, content: str) -> tuple[bool, str]:
        try:
            user = await bot.fetch_user(user_id)
            dm = await user.create_dm() 
            await dm.send(content)
            return True, "ok"
        except discord.Forbidden:
            return False, "forbidden"
        except discord.NotFound:
            return False, "not_found"
        except discord.HTTPException as e:
            return False, f"http_{getattr(e, 'status', 'na')}"
        except Exception as e:
            return False, f"err_{type(e).__name__}"

    # 内鬼 DM
    imposter_msg = (
        "老大你是本局游戏的内鬼喵, 请在不被发现的基础上尽可能让你的基地爆炸\n"
        "收到请回复 /accept"
    )

    # tasker DM
    tasker_msg_t1 = f"你是任务者喵老大, 你本局的任务是：{state.task_team1}"
    tasker_msg_t2 = f"你是任务者喵老大, 你本局的任务是：{state.task_team2}"

    # blocker DM
    tasker_name_t1 = await display_name_from_id(ctx.guild, state.tasker_team1)
    tasker_name_t2 = await display_name_from_id(ctx.guild, state.tasker_team2)
    blocker_msg_t1 = (
        f"老大你是本局的阻止者喵！本局的任务者是：{tasker_name_t1}， ta的任务是{state.task_team1}"
        "你需要阻止他们喵！"
    )

    blocker_msg_t2 = (
        f"老大你是blocker喵！本局的任务者是：{tasker_name_t2}，ta的任务是{state.task_team2}"
        "你需要阻止他们喵！"
    )
    ok_i1, r_i1 = await safe_dm(state.imposter_team1, imposter_msg)
    ok_i2, r_i2 = await safe_dm(state.imposter_team2, imposter_msg)

    ok_t1, r_t1 = await safe_dm(state.tasker_team1, tasker_msg_t1)
    ok_t2, r_t2 = await safe_dm(state.tasker_team2, tasker_msg_t2)

    ok_b1, r_b1 = await safe_dm(state.blocker_team1, blocker_msg_t1)
    ok_b2, r_b2 = await safe_dm(state.blocker_team2, blocker_msg_t2)

    # 给主持人一个汇总（不暴露身份，只告诉是否发出去成功）
    fail = []
    if not ok_i1: fail.append(f"Team1 内鬼 DM 失败：{mention_from_id(ctx.guild, state.imposter_team1)}")
    if not ok_i2: fail.append(f"Team2 内鬼 DM 失败：{mention_from_id(ctx.guild, state.imposter_team2)}")
    if not ok_t1: fail.append(f"Team1 tasker DM 失败：{mention_from_id(ctx.guild, state.tasker_team1)}")
    if not ok_t2: fail.append(f"Team2 tasker DM 失败：{mention_from_id(ctx.guild, state.tasker_team2)}")
    if not ok_b1: fail.append(f"Team1 blocker DM 失败：{mention_from_id(ctx.guild, state.blocker_team1)}")
    if not ok_b2: fail.append(f"Team2 blocker DM 失败：{mention_from_id(ctx.guild, state.blocker_team2)}")

    if fail:
        await ctx.send("分配完成，但有私信发送失败喵：\n" + "\n".join(fail))
    else:
        await ctx.send("分配完成喵！我已经把身份和任务都私信发出去了。")
    
    host_id = host_binding.get(ctx.guild.id, ctx.author.id) 

    def mention(uid: Optional[int]) -> str:
        if uid is None:
            return "（无）"
        return f"<@{uid}>"

    host_summary = (
        "📌 本局身份与任务汇总\n\n"
        "【Team 1】\n"
        f"- 内鬼: {mention(state.imposter_team1)}\n"
        f"- 任务者: {mention(state.tasker_team1)} ｜ Task: {state.task_team1}\n"
        f"- 阻止者: {mention(state.blocker_team1)}\n\n"
        "【Team 2】\n"
        f"- 内鬼: {mention(state.imposter_team2)}\n"
        f"- 任务者: {mention(state.tasker_team2)} ｜ Task: {state.task_team2}\n"
        f"- 阻止者: {mention(state.blocker_team2)}\n"
    )

    ok_h, r_h = await safe_dm(host_id, host_summary)


@bot.hybrid_command(name="show_impo_task", with_app_command=True)
async def show_impo_task(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    key: Key = (ctx.guild.id, ctx.author.id)

    state = round_state.get(key)
    if not state:
        await ctx.send("老大你这边还没有本局记录喵，请先用 /assign_imposter_task 开局。")
        return

    # mention helper
    def m(uid: Optional[int]) -> str:
        if uid is None:
            return "（无）"
        member = ctx.guild.get_member(uid)
        return member.mention if member else f"<@{uid}>"

    # 任务字符串可能是 None，做一下兜底
    t1_task = state.task_team1 or "（无任务）"
    t2_task = state.task_team2 or "（无任务）"

    msg = (
        "**本局身份与任务汇总：**\n"
        f"**Team 1**\n"
        f"- 内鬼: {m(state.imposter_team1)}\n"
        f"- 任务者: {m(state.tasker_team1)} ｜ Task: {t1_task}\n"
        f"- 阻止者: {m(state.blocker_team1)}\n\n"
        f"**Team 2**\n"
        f"- 内鬼: {m(state.imposter_team2)}\n"
        f"- 任务者: {m(state.tasker_team2)} ｜ Task: {t2_task}\n"
        f"- 阻止者: {m(state.blocker_team2)}\n"
    )

    await ctx.send(msg)

@bot.hybrid_command(name="bind_host", with_app_command=True)
async def bind_host(ctx: commands.Context, host: Optional[discord.Member] = None):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    host_member = host or ctx.author  # default to the invoker
    host_binding[ctx.guild.id] = host_member.id

    await ctx.send(f"主持人已绑定为：{host_member.mention}")

@bot.hybrid_command(name="unbind_host", with_app_command=True)
async def unbind_host(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    if ctx.guild.id not in host_binding:
        await ctx.send("当前服务器还没有绑定主持人喵。")
        return

    host_binding.pop(ctx.guild.id, None)
    await ctx.send("主持人已解绑喵 ✅")

@bot.hybrid_command(name="check_host", with_app_command=True)
async def check_host(ctx: commands.Context):
    if ctx.guild is None:
        await ctx.send("该指令只能在服务器内使用。")
        return

    host_id = host_binding.get(ctx.guild.id)
    if not host_id:
        await ctx.send("当前服务器还没有绑定主持人喵。")
        return

    member = ctx.guild.get_member(host_id)
    mention = member.mention if member else f"<@{host_id}>"
    await ctx.send(f"当前主持人是：{mention}")

bot.run(token)
