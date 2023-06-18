import configparser
import datetime
import json
import pytz
import discord

import database

from discord.ext import commands, tasks

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
guilds = json.loads(c["DISCORD"]["guilds"])
e_channel = int(c["DISCORD"]["error_channel"])
intents = discord.Intents.default()
intents.messages = True
intents.members = True
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
    current_date = datetime.datetime.now(pytz.timezone('UTC')).strftime('%a')
    current_time = datetime.datetime.now(pytz.timezone('UTC')).strftime('%H%M')
    print(current_date, current_time)

    # results = (start, end, user, guild)
    schedules = database.get_scheduled_users_by_datetime(db_connection, current_date.lower(), current_time)

    for schedule in schedules:
        start = str(schedule[0])
        end = str(schedule[1])
        member_id = int(schedule[2][2:-1])
        guild_id = int(schedule[3])

        if start == current_time:
            guild = bot.get_guild(guild_id)
            member = guild.get_member(member_id)
            role = guild.get_role(database.get_on_call_role(db_connection, guild_id))
            await member.add_roles(role)

        if end == current_time:
            guild = bot.get_guild(guild_id)
            member = guild.get_member(member_id)
            role = guild.get_role(database.get_on_call_role(db_connection, guild_id))
            await member.remove_roles(role)

    db_connection.close()
    return True


bot.run(discord_token)
