import configparser
import datetime
import json
import pytz
import discord

import database

from discord.ext import commands, tasks
from discord.utils import get

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
guilds = json.loads(c["DISCORD"]["guilds"])
e_channel = int(c["DISCORD"]["error_channel"])
intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.moderation = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")

    check_schedule.start()


@tasks.loop(minutes=1)
async def check_schedule():
    db_connection = database.get_db_connection()

    await bot.wait_until_ready()
    current_date = "tue"#datetime.datetime.now(pytz.timezone('UTC')).strftime('%a')
    current_time = "0407"#datetime.datetime.now(pytz.timezone('UTC')).strftime('%H%M')
    print(current_date, current_time)

    # results = (start, end, user, guild)
    schedules = [('0407', '0408', '<@712863455467667526>', 837853470136467517)]#database.get_scheduled_users_by_datetime(db_connection, current_date, current_time)

    for schedule in schedules:
        start = str(schedule[0])
        end = str(schedule[1])
        member_id = int(schedule[2][2:-1])
        guild_id = int(schedule[3])

        if start == current_time:
            guild = bot.get_guild(guild_id)
            member = guild.get_member(member_id)
            print(guild.members)
            role = guild.get_role(1116012502879305749)
            await member.add_roles(role)

        if end == current_time:
            guild = bot.get_guild(guild_id)
            member = guild.get_member(member_id)
            role = get(member.server.roles, name="Bots")
            await member.remove_roles(role)

    db_connection.close()
    return True


bot.run(discord_token)
