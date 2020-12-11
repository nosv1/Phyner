# Phyner is finer.
# Mo#9991
# Main File, handles events and runs bot, the controller

''' IMPORTS '''

import discord
import asyncio
from datetime import datetime, timedelta
import random
from pytz import timezone
import traceback
import gspread
import mysql.connector
from types import SimpleNamespace
import os
import re

from dotenv import load_dotenv
load_dotenv()


import Logger
import Database
import Support


import Embed

''' CONSTANTS '''

intents = discord.Intents.all()
client = discord.Client(intents = intents)

connected = None
phyner_db = None



''' FUNCTIONS '''

@client.event
async def on_ready():

    error = None
    try:
        global connected
        connected = True
        Logger.log("Connection", "Connected")

        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="Phyner is finer. 🌹"
            )
        )
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_ready



@client.event
async def on_raw_message_edit(payload):
    if not connected: # we aint ready yet
        return

    error = False
    message = None
    try:

        pd = payload.data

        channel_id = int(pd["channel_id"])
        message_id = int(pd["id"])

        channel = client.get_channel(channel_id)
        channel = channel if channel else await client.fetch_channel(channel_id) # if DM, get_channel is none, i think

        message = await channel.fetch_message(message_id)

        if not message.author.bot and connected:
            try:
                pd["content"]
                await on_message(message)
            except KeyError: # when content was not updated
                pass

    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
  
# end on_raw_message_edit

@client.event
async def on_message(message):
    if not connected: # we aint ready yet
        return

    error = False
    try:
        # prep message content for use
        mc = message.content
        mc = re.sub(r"[“”]", '"', message.content)
        mc = re.sub(r"[\n\t\r]", ' ', message.content)
        while "  " in mc:
            mc = mc.replace("  ", " ")
        args = mc.split(" ") + [" "] # appending blank to remove index error issues

        author_perms = Support.get_member_perms(message.channel, message.author)


        ''' BEGIN CHECKS '''

        if not message.author.bot: # not a bot

            if message.mentions and message.mentions[0].id == Support.ids.phyner_id:
                Logger.log("COMMAND", f"{message.author.id}, '{message.content}'\n")

                phyner = message.mentions[0]
                is_mo = message.author.id == Support.ids.mo_id


                ''' COMMAND CHECKS '''

                if args[1] == "test" and is_mo:
                    await Support.simple_bot_response(message.channel, reply=message)
                    await message.channel.send("test done")


                elif args[1] == "embed":
                    await Embed.main(client, message, args, author_perms)
                    
                    # TODO @phyner todo, encrpyt, and how to intuitiviely remove a todo


                else:
                    ## SIMPLE HELP MESSAGE ##

                    description = f"`@{phyner} help` - general help\n"
                    description += f"`@{phyner} <command> help` - specific help\n"
                    description += f"`@{phyner} ? <search words>` - search help\n"

                    msg = await Support.simple_bot_response(
                        message.channel, 
                        title="No Comamnd Reckognized",
                        description=description
                    )
                    Logger.log("Bot reponse", "Simple Help Message")

                ''' END COMMAND CHECKS '''
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_message



Logger.create_log_file()
Logger.log("Connection", "Connecting")
client.run(os.getenv("DISCORD_TOKEN"))