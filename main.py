import configparser
import json
import re
from datetime import datetime, timezone

import pytz

import discord
from discord import app_commands
from discord.ext import commands, tasks

import database

# Load config
c = configparser.ConfigParser()
c.read("config.ini", encoding='utf-8')

discord_token = str(c["DISCORD"]["token"])
ADMIN_ROLES = c["DISCORD"]["admin_roles"]
connext_core_guild_id = int(c["DISCORD"]["connext_core_guild"])
ephemeral = bool(True if str(c["DISCORD"]["ephemeral"]) == "True" else False)
# e_channel = int(c["DISCORD"]["error_channel"])
intents = discord.Intents.default()
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----------------')
    print("ready")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")


# def is_user_scheduled(day, time, user_id):
#     db_connection = database.get_db_connection()
#     schedules = database.get_scheduled_users_by_datetime(db_connection, day.lower(), time)
#
#     for schedule in schedules:
#         member_id = int(schedule[2][2:-1])
#
#         if user_id == member_id:
#             return True
#
#     return False
#
#
def is_admin(interaction):
    for role in interaction.user.roles:
        if str(role) in ADMIN_ROLES:
            return True
    return False
#
#
# # @bot.tree.command(name="add-to-schedule", description="Add a user and on-call time to the schedule.")
# @bot.tree.command(name="add-to-schedule", description="Currently under maintenance.")
# @app_commands.describe(user="The on-call user.", day_of_week="The day of the week", start="The start time in UTC [0000 - 2358].", end="The end time in UTC [0001 - 2359].")
# async def add_user(interaction: discord.Interaction, user: str, day_of_week: str, start: str, end: str):
#     # if not is_admin(interaction):
#     #     await interaction.response.send_message(f"This command is only available for admins.", ephemeral=ephemeral)
#     #     return
#
#     await interaction.response.send_message(f"This command is currently paused.", ephemeral=ephemeral)
#     return
#
#     db_connection = database.get_db_connection()
#     time_pattern = re.compile("^([0-1][0-9]|2[0-3])[0-5][0-9]$")
#
#     if user[:2] != "<@" or user[-1:] != ">":
#         await interaction.response.send_message(f"Please tag a specific user.", ephemeral=ephemeral)
#         db_connection.close()
#         return
#
#     if not time_pattern.match(start):
#         await interaction.response.send_message(f"Please enter a start UTC time in the range 0000 - 2358.", ephemeral=ephemeral)
#         db_connection.close()
#         return
#
#     if not time_pattern.match(end):
#         await interaction.response.send_message(f"Please enter an end UTC time in the range 0001 - 2359.", ephemeral=ephemeral)
#         db_connection.close()
#         return
#
#     if int(start) > int(end):
#         await interaction.response.send_message(f"The end time should be later than the start time.", ephemeral=ephemeral)
#         db_connection.close()
#         return
#
#     if day_of_week[:3].lower() not in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
#         await interaction.response.send_message(f"Please use the full name (Monday) or abbreviation (Mon) for the Day of the Week.", ephemeral=ephemeral)
#         db_connection.close()
#         return
#
#     success = database.add_to_schedule(db_connection, user, day_of_week[:3].lower(), start, end, interaction.guild_id)
#
#     current_date = datetime.now(pytz.timezone('UTC')).strftime('%a')
#     current_time = datetime.now(pytz.timezone('UTC')).strftime('%H%M')
#
#     try:
#         if current_date.lower() == day_of_week[:3].lower() and start <= current_time < end:
#             member_id = int(user[2:-1])
#             member = interaction.guild.get_member(member_id)
#             role = interaction.guild.get_role(database.get_on_call_role(db_connection, interaction.guild_id))
#             db_connection.close()
#             await member.add_roles(role)
#             await interaction.response.send_message(f"{user} was added to the schedule and is currently on call.", ephemeral=ephemeral)
#             return
#
#         if success:
#             await interaction.response.send_message(f"{user} was added to the schedule.", ephemeral=ephemeral)
#             return
#
#         if not success:
#             await interaction.response.send_message(f"The user wasn't saved in the database. cc: <@712863455467667526>", ephemeral=ephemeral)
#             return
#     except Exception as e:
#         print(e)
#         await interaction.response.send_message(f"Please make sure the on call role is defined (`/set-role`), and the bot's role is moved above the on call role.",
#                                                 ephemeral=ephemeral)
#         return
#
#
# #@bot.tree.command(name="remove-from-schedule", description="Remove a user's on-call time from the schedule.")
# @bot.tree.command(name="remove-from-schedule", description="Currently under maintenance.")
# @app_commands.describe(schedule_id="Schedule ID to remove.")
# async def remove_from_schedule(interaction: discord.Interaction, schedule_id: int):
#     # if not is_admin(interaction):
#     #     await interaction.response.send_message(f"This command is only available for admins.", ephemeral=ephemeral)
#     #     return
#
#     await interaction.response.send_message(f"This command is currently paused.", ephemeral=ephemeral)
#     return
#
#     db_connection = database.get_db_connection()
#
#     if not database.get_from_schedule(db_connection, schedule_id, interaction.guild_id):
#         await interaction.response.send_message(f"That schedule ID wasn't found.", ephemeral=ephemeral)
#         return False
#
#     result = database.get_from_schedule(db_connection, schedule_id, interaction.guild_id)
#     user_id = int(result[0][1][2:-1])
#
#     success = database.remove_from_schedule(db_connection, schedule_id, interaction.guild_id)
#
#     try:
#         # if the user is not schedule for this moment, remove the tag
#         current_date = datetime.now(pytz.timezone('UTC')).strftime('%a')
#         current_time = datetime.now(pytz.timezone('UTC')).strftime('%H%M')
#         if not is_user_scheduled(current_date, current_time, user_id):
#             member = interaction.guild.get_member(user_id)
#             role = interaction.guild.get_role(database.get_on_call_role(db_connection, interaction.guild_id))
#             await member.remove_roles(role)
#             db_connection.close()
#
#         if success:
#             await interaction.response.send_message(f"Schedule ID {schedule_id} was removed from the schedule.", ephemeral=ephemeral)
#
#         if not success:
#             await interaction.response.send_message(f"There was an issue. cc: <@712863455467667526>", ephemeral=ephemeral)
#     except Exception as e:
#         await interaction.response.send_message(f"Please make sure the on call role is defined (`/set-role`), and the bot's role is moved above the on call role.",
#                                                 ephemeral=ephemeral)
#         return


@bot.tree.command(name="show-schedule", description="Show the current schedule.")
@app_commands.describe()
async def get_schedule(interaction: discord.Interaction):
    # if not is_admin(interaction):
    #     await interaction.response.send_message(f"This command is only available for admins.", ephemeral=ephemeral)
    #     return

    db_connection = database.get_db_connection()
    db_response = database.list_schedule(db_connection, interaction.guild_id)
    response = f"**ID** \t **start time** \t\t\t\t\t\t\t\t\t\t **end time** \t\t\t\t\t\t\t\t\t\t **user on call**\n"
    for line in db_response:
        response += f"{line[0]}\t\t{line[1]}\t{line[2]}\t{line[3]}\n"

    if not response:
        await interaction.response.send_message(f"The schedule is empty.", ephemeral=ephemeral)
    else:
        await interaction.response.send_message(response, ephemeral=ephemeral)


@bot.tree.command(name="show-active-on-call", description="Show who is currently on call.")
@app_commands.describe()
async def get_who_is_on_call(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message(f"This command is only available for admins.", ephemeral=ephemeral)
        return

    db_connection = database.get_db_connection()

    schedules = database.get_schedule(db_connection, connext_core_guild_id)
    active_users = ""

    for schedule in schedules:
        current_time = datetime.now().replace(tzinfo=timezone.utc)
        start = datetime.strptime(schedule[0], "%Y-%m-%d %H:%M:%S%z")
        end = datetime.strptime(schedule[1], "%Y-%m-%d %H:%M:%S%z")

        if start < current_time < end:
            active_users += f"{schedule[2]} \t "

    await interaction.response.send_message(active_users, ephemeral=ephemeral)


@bot.tree.command(name="set-role", description="Set a new on-call role.")
@app_commands.describe(role_id="The role ID of the new on-call role.")
async def set_role(interaction: discord.Interaction, role_id: str):
    if not is_admin(interaction):
        await interaction.response.send_message(f"This command is only available for admins.", ephemeral=ephemeral)
        return

    role_id = int(role_id)

    try:
        guild = bot.get_guild(interaction.guild_id)
        role = guild.get_role(role_id)
        role_name = role.name
    except Exception as e:
        print(e)
        await interaction.response.send_message("This ID is not recognized as a role.", ephemeral=ephemeral)
        return False

    db_connection = database.get_db_connection()
    success = database.set_on_call_role(db_connection, interaction.guild_id, role_id)

    if success:
        await interaction.response.send_message(f"The new role is {role_name}. \n"
                                            f"**Please make sure the bot's role is above the on-call role in the settings.**", ephemeral=ephemeral)
        return True
    if not success:
        await interaction.response.send_message(f"The role wasn't saved in the database. cc: <@712863455467667526>", ephemeral=ephemeral)
        return False


# @bot.tree.command(name="clear-schedule", description="Clear the full schedule.")
# @bot.tree.command(name="clear-schedule", description="Currently under maintenance.")
# @app_commands.describe()
# async def clear_schedule(interaction: discord.Interaction):
#
#     await interaction.response.send_message(f"This command is currently paused.", ephemeral=ephemeral)
#     return
#
#     db_connection = database.get_db_connection()
#
#     users = database.get_all_users_on_schedule(db_connection, interaction.guild_id)
#     for user in users:
#         user_id = int(user[0][2:-1])
#         member = interaction.guild.get_member(user_id)
#         role = interaction.guild.get_role(database.get_on_call_role(db_connection, interaction.guild_id))
#         await member.remove_roles(role)
#
#     success = database.clear_schedule(db_connection, interaction.guild_id)
#
#     if success:
#         await interaction.response.send_message(f"The schedule was cleared. No one is on call.", ephemeral=ephemeral)
#         return True
#     if not success:
#         await interaction.response.send_message(f"The schedule wasn't cleared. cc: <@712863455467667526>", ephemeral=ephemeral)
#         return False


bot.run(discord_token)
