import configparser
from datetime import datetime, timezone
import json
import pytz
import discord

import database

from discord.ext import commands, tasks

from google_calendar_integration import update_db_from_calendar

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
guilds = json.loads(c["DISCORD"]["guilds"])
connext_core_guild_id = int(c["DISCORD"]["connext_core_guild"])
connext_public_guild_id = int(c["DISCORD"]["connext_public_guild"])
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
    check_calendar.start()


@tasks.loop(hours=1)
async def check_schedule():
    db_connection = database.get_db_connection()

    await bot.wait_until_ready()
    current_time = datetime.now().replace(tzinfo=timezone.utc)

    # results = (start, end, user)
    schedules = database.get_schedule(db_connection, connext_core_guild_id)
    connext_core_guild = bot.get_guild(connext_core_guild_id)
    connext_public_guild = bot.get_guild(connext_public_guild_id)
    core_role = connext_core_guild.get_role(database.get_on_call_role(db_connection, connext_core_guild_id))
    public_role = connext_public_guild.get_role(database.get_on_call_role(db_connection, connext_public_guild_id))
    on_call_members = []

    for schedule in schedules:
        start = datetime.strptime(schedule[0], "%Y-%m-%d %H:%M:%S%z")
        end = datetime.strptime(schedule[1], "%Y-%m-%d %H:%M:%S%z")

        member_id = int(schedule[2][2:-1])
        core_member = connext_core_guild.get_member(member_id)
        public_member = connext_public_guild.get_member(member_id)

        if start < current_time < end:
            on_call_members.append(core_member)
            await core_member.add_roles(core_role)
            await public_member.add_roles(public_role)

        elif current_time > end:
            await core_member.remove_roles(core_role)
            await public_member.remove_roles(public_role)

    for member in bot.get_guild(connext_core_guild_id).members:
        if member not in on_call_members:
            core_member = connext_core_guild.get_member(member.id)
            public_member = connext_public_guild.get_member(member.id)
            try:
                await core_member.remove_roles(core_role)
            except Exception as error:
                print('An error occurred: %s' % error)

            try:
                await public_member.remove_roles(public_role)
            except Exception as error:
                print('An error occurred: %s' % error)

    db_connection.close()
    return True


@tasks.loop(hours=4)
async def check_calendar():
    print("calendar")
    await bot.wait_until_ready()

    update_db_from_calendar()


bot.run(discord_token)
