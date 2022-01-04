import asyncio
import discord
from discord.ext import tasks
from dotenv import load_dotenv
import logging
import os
from random import choice

import Database

load_dotenv()

logger = logging.getLogger('discord')

HOST = os.getenv("HOST")


@tasks.loop(seconds=15)
async def loop(client):

    seconds = loop.current_loop * 30

    if seconds % (5 * 60) == 0:
        await update_status(client)


async def update_status(client, restart=False, close=False):

    activities: list[discord.Activity] = [
        discord.Activity(
            type=discord.ActivityType.watching,
            name="Phyner is finer."),
    ]

    activity = None
    if not (restart or close):  
        activity = choice(activities)

    elif restart:
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Restarting"
        )

    elif close:
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Shutting Down for Maintenance"
        )

    await client.change_presence(
        activity=activity,
        status=discord.Status.online
    )

