''' IMPORTS '''

import discord
import asyncio
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random
from pytz import timezone
import traceback
import gspread
import mysql.connector
from types import SimpleNamespace
import re

import os
from dotenv import load_dotenv
load_dotenv()


import Logger
from Logger import log
import Database
import Support
import Help
import Embed
import General
import Delete
import Guilds
import CustomCommands
import Events
import Role


Logger.create_log_file()


''' CONSTANTS '''

intents = discord.Intents.all()
client = discord.Client(intents = intents)

connected = None
host = os.getenv("HOST")

guild_prefixes = Guilds.get_guild_prefixes()
log("startup", f"Guild Prefixes: {len(guild_prefixes)}")

events = Events.get_events()
log("startup", f"Events: {len(events)}")

phyner_webhook_ids = Events.get_object_ids(events, "webhook")
log("startup", f"Phyner Webhook IDs: {len(phyner_webhook_ids)}")

phyner_emoji_ids = Events.get_object_ids(events, "emoji")
log("startup", f"Phyner Emoji IDs: {len(phyner_emoji_ids)}")

restart = 0 # the host runs this Controller.py in a loop, when Controller disconnects, it returns 1 or 0 depending if @Phyner restart is called, 1 being restart, 0 being exit loop
restart_time = datetime.utcnow() # used to not allow commands {restart_interval} seconds before restart happens
restart_interval = 60 # time between restart/shutdown command and action



''' FUNCTIONS '''

''' can't edit message after command
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

    except discord.errors.NotFound:
        await log("message edit erorr", traceback.format_exc())
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_raw_message_edit
'''


@client.event
async def on_message(message):
    global restart 
    global restart_time
    global guild_prefixes
    global phyner_webhook_ids

    if not connected: # we aint ready yet
        return

    error = False
    try:
        # prep message content for use
        mc = message.content 
        mc = re.sub(r"[“”]", '"', message.content)
        mc = re.sub(r"[\n\t\r]", ' ', message.content)
        mc += " "
        while "  " in mc:
            mc = mc.replace("  ", " ")
        args = mc.split(" ")


        ## BEGIN CHECKS ##

        try:
            is_webhook = message.webhook_id in phyner_webhook_ids
        except:
            log("webhook error", traceback.format_exc())
            return

        if not message.author.bot or is_webhook: # not a bot and webhook we care about
                

            try:
                guild_prefix = guild_prefixes[message.guild.id if message.guild else message.author.id]
            except KeyError:
                guild_prefix = None

            if (
                (
                    host == "PI4" and # is PI4
                    (
                        (message.mentions and message.mentions[0].id == Support.ids.phyner_id) or # @Phyner command
                        mc[:len(str(guild_prefix))+1] == guild_prefix + " " # start of content = guild prefix
                    )
                ) or (
                    host == "PC" and # is PC
                        (args[0] == "``p") # ..p command
                )
            ):
                log("COMMAND", f"{message.author.id}, '{message.content}'\n")

                phyner = Support.get_phyner_from_channel(message.channel)
                is_mo = message.author.id == Support.ids.mo_id

                message.author = phyner if is_webhook else message.author
                author_perms = Support.get_member_perms(message.channel, message.author)


                ## COMMAND CHECKS ##
                    
                # \TODO @phyner todo, encrpyt, and how to intuitiviely remove a todo
                # TODO Invite Phyner Support
                # TODO request feature for money
                # TODO Donations
                # TODO @Phyner ids
                # TODO @Phyner copy
                # TODO @Phyner replace
                # TODO @Phyner command create/edit


                ## CHECK FOR UPCOMING RESTART ##

                restart_delta = (restart_time - datetime.utcnow()).seconds
                if restart_delta < restart_interval:
                    description = f"**{phyner.mention} is about to {'restart' if restart else 'shut down'}. "
                    if restart:
                        description += f"Try again in {restart_delta + restart_interval} seconds, or watch for its status to change.**" 
                    else:
                        description += "Try again when it comes back online.**"

                    await Support.simple_bot_response(message.channel, description=description, reply_message=message)
                    return

                ## MO ##

                if is_mo:
                    if args[1] == "test":
                        import Test
                        await Test.test(message, args)
                        return
                        
                    elif args[1] == "setavatar":
                        with open('Images/9a9c9f.png', 'rb') as f:
                            await client.user.edit(avatar=f.read())
                        return

                    elif args[1] in ["close", "shutdown", "stop", "restart"]:
                        restart = await Support.restart(client, message, restart_interval, restart=args[1] == "restart")
                        restart_time = datetime.utcnow() + relativedelta(seconds=restart_interval) # set new restart time
                        await asyncio.sleep(restart_interval)
                        await client.close()
                        
                
                ## HELP + GENERAL ##

                if args[1] in ["?", "search"]:
                    await Help.search(message, args)

                elif args[1] in ["help", "h"]:
                    await Help.help(message)

                elif args[1] == "ping":
                    await General.send_ping(client, message.channel)

                elif args[1] in Delete.delete_aliases:
                    await Delete.main(client, message, args, author_perms)

                elif args[1] in General.say_aliases:
                    await General.say(message, args)



                ## EMBED ##

                elif args[1] in Embed.embed_aliases:
                    await Embed.main(client, message, args, author_perms)



                ## GUILDS ##

                elif args[1] == "prefix":
                    phyner_guild, guild_prefixes = await Guilds.set_prefix(message, args, author_perms)

                
                ## CUSTOM COMMANDS ##

                # elif args[1] in CustomCommands.custom_command_aliases:
                    # await CustomCommands.main(args, author_perms)


                ## WATCH ##

                elif args[1] in Events.events_aliases + Events.watching_aliases:
                    event = await Events.main(client, message, args[1:], author_perms)
                    if event:
                        if event.object.type == "webhook":
                            phyner_webhook_ids = Events.get_object_ids(Events.get_events(), "webhook")


                ## ROLE ##

                elif args[1] in Role.role_aliases:
                    await Role.main(client, message, args[2:], author_perms)



                else:
                    await Help.simple_help(message)

                ''' END COMMAND CHECKS '''

    except RuntimeError:
        log("Connection", f"{host} Disconnected")
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_message


@client.event
async def on_raw_reaction_add(payload):
    global restart 
    global restart_time

    if not connected: # we aint ready yet
        return

    user_id = payload.user_id
    channel_id = payload.channel_id
    channel = client.get_channel(channel_id)
    message_id = payload.message_id

    msg = None
    user = None
    is_dm = None
    error = False
    try:

        msg = await channel.fetch_message(message_id)
        if not msg:
            return

        is_dm = msg.channel.type == discord.ChannelType.private

        user = [user for user in (msg.channel.members if not is_dm else [msg.channel.recipient]) if user.id == user_id]
        user = user[0] if user else user

        remove_reaction = False
        if msg and user:

            if not user.bot: # not bot reaction

                # TODO check if emoji object + message condition + reaction_add event
                restart_delta = (restart_time - datetime.utcnow()).seconds
                if restart_delta < restart_interval:
                    return

                embed = msg.embeds[0] if msg.embeds else []

                if embed: # has embed
                    pass

                    if embed.title: # has title 
                        pass
    

        if remove_reaction and not is_dm:
            await msg.remove_reaction(payload.emoji, user)

    except AttributeError: # possibly NoneType.fetch_message, happens in DMs after bot is restarted
        error = traceback.format_exc()

    #except discord.errors.NotFound: # bot aint finding messages...
     #   Logger.log_error(traceback.format_exc())
      #  return

    except discord.errors.Forbidden:
        error = traceback.format_exc()
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_reaction_add



''' STARTUP '''

''' 
@client.event this appears to simply not be needed
async def on_ready():
    error = None
    try:
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_ready
'''

async def startup():
    global connected
    global restart
    await client.wait_until_ready()

    connected = True
    restart = 1
    log("Connection", f"{host} Controller Connected")

    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing, name="@Phyner is finer."
        )
    )
# end startup

log("Connection", f"{host} Controller Connecting")

client.loop.create_task(startup())

client.run(os.getenv("TOKEN"))
print(restart)