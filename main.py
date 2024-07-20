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


def is_admin(interaction):
    for role in interaction.user.roles:
        if str(role) in ADMIN_ROLES:
            return True
    return False


@bot.command(name='version', help='')
@commands.has_any_role("Mod", "team", "admin")
async def version(ctx):
    await ctx.send("v0.1.1")


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


bot.run(discord_token)
