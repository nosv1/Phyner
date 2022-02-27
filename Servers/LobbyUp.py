''' IMPORTS '''

import asyncio
from datetime import datetime
import discord
import os
import random
import re
import pickle
from PIL import Image, ImageDraw, ImageFont
from pytz import timezone
import traceback
from types import SimpleNamespace
import validators
import scipy.optimize as opt


import Database
import Embeds
import Logger
from Logger import log
import Support
from Support import delete_last_field, messageOrMsg, simple_bot_response


''' CONSTANTS '''

# IDs
lobby_up_id = 845897647444459540
# lobby_up_id = 789181254120505386 # phyner support
shorzee_id = 449751702237741077

# CHANNELS
regs_game_queue_id = 947049845087170590
# regs_game_queue_id = 789582283991678976 # phyner support
mut_game_queue_id = 947049918932086794
mmg_procedures_and_rules_id = 947050091846459402

# MESSAGES

# COLORS


''' FUNCTIONS '''

async def main(
    client: discord.Client, message: discord.Message, args: list[str], author_perms
):

    args[0] = args[0].lower()

    if args[0] == "!test":
        pass

    elif args[0] == "!regs$":

        if message.channel.id == regs_game_queue_id:
            await handle_money_game_command(message, "regs")

        else:
            await message.reply(
                f"You can only use this command in <#{regs_game_queue_id}>."
            )

    elif args[0] == "!mut$":

        if message.channel.id == mut_game_queue_id:
            await handle_money_game_command(message, "mut")

        else:
            await message.reply(
                f"You can only use this command in <#{mut_game_queue_id}>."
            )

    elif args[0] == "!cancelregs$":
            
        if message.channel.id == regs_game_queue_id:
            await remove_user_from_queue(message, "regs")

        else:
            await message.reply(
                f"You can only use this command in <#{regs_game_queue_id}>."
            )

    elif args[0] == "!cancelmut$":

        if message.channel.id == mut_game_queue_id:
            await remove_user_from_queue(message, "mut")

        else:
            await message.reply(
                f"You can only use this command in <#{mut_game_queue_id}>."
            )

    elif args[0] == "!clearregs$":

        if message.channel.id == regs_game_queue_id:
            await clear_queue(message, "regs")

        else:
            await message.reply(
                f"You can only use this command in <#{regs_game_queue_id}>."
            )

    elif args[0] == "!clearmut$":
            
        if message.channel.id == mut_game_queue_id:
            await clear_queue(message, "mut")

        else:
            await message.reply(
                f"You can only use this command in <#{mut_game_queue_id}>."
            )


async def on_reaction_add(client, message, user, payload):

    remove_reaction = False
    embed = message.embeds[0] if message.embeds else None

    if embed:

        if embed.description:
            
            embed_meta = embed.description.split("embed_meta/")

            if len(embed_meta) > 1:
                pass


    return remove_reaction


async def handle_money_game_command(message: discord.Message, game_type: str):

    # get pickled queue
    # queued IDs
    try:
        queue = pickle.load(open(f"lobby_up_{game_type}_queue.p", "rb"))

    except FileNotFoundError:
        queue = []

    users = [message.author]
    if queue:  # queue is not empty
        # get first ID
        user = discord.utils.find(
            lambda u: u.id == queue[0], message.guild.members
        )

        if user and user.id == message.author.id:  # user is author, don't add
            await message.channel.send(
                f"{user.mention} is already in the queue for a {game_type} game."
            )
            return

        elif user:  # queued user found, queue is now filled, clear queue
            users.append(user)
            queue = []

        else:  # queued user was not found
            users.append(None)
            queue = [message.author.id]

    else:  # add author to queue, queue has 1 person
        queue.append(message.author.id)

    pickle.dump(queue, open(f"lobby_up_{game_type}_queue.p", "wb"))

    # at this point, queue is either empty or contains author id
    # if queue is empty, then we're good to go
    # if queue is not empty, then we're waiting for 2nd user
    # if 2nd member in queue is None, then we need to send error message
    

    if not queue:  # create channel with users
        category: discord.CategoryChannel = message.channel.category
        
        overwrites = category.overwrites
        for user in users:
            overwrites[user] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )

        channel: discord.TextChannel = await message.guild.create_text_channel(
            f'{game_type}-{message.author.display_name}_vs_{users[-1].display_name}',
            overwrites=overwrites,
            category=category,
            position=category.channels[-1].position + 1
        )

        await channel.send(
            f"{message.author.mention} and {users[-1].mention}, this is your {game_type} money game matchup channel. Review the <#{mmg_procedures_and_rules_id}>, and then set your wager terms. Once you agree on the wager value, send your payments to $xSHORZEEx on Cash App or management@lobbyup.net on PayPal. Once both sides post a screenshot to this channel of them sending the money, you may begin the game. Be sure to post the final socre and the winner here. For any disputes and at the conclusion of the game, ping <@{shorzee_id}> to have the issue resolved or the payment sent. Good luck!"
        )

        await message.reply(
            f"Money game matchup channel created: <#{channel.id}>."
        )


    else:  # show that author was added to queue
        if users[-1] is None:
            await message.channel.send(
                f"There *was* a member in the queue, but they have been removed as they were not found in the server. {message.author.mention} has been added to the queue."
            )

        else:
            await message.channel.send(
                f"{message.author.mention} has been added to the queue."
            )


async def remove_user_from_queue(message: discord.Message, game_type: str):
    
    # get pickled queue
    # queued IDs
    try:
        queue = pickle.load(open(f"lobby_up_{game_type}_queue.p", "rb"))

    except FileNotFoundError:
        queue = []

    if message.author.id in queue:
        queue.remove(message.author.id)

    pickle.dump(queue, open(f"lobby_up_{game_type}_queue.p", "wb"))

    await message.channel.send(
        f"{message.author.mention} has been removed from the queue."
    )


async def clear_queue(message: discord.Message, game_type: str):
    
    try:
        queue = pickle.load(open(f"lobby_up_{game_type}_queue.p", "rb"))

    except FileNotFoundError:
        pass

    if not queue:
        await message.reply(
            f"There are no users queued for a {game_type} game."
        )

    else:
        user = discord.utils.find(
            lambda u: u.id == queue[0], message.guild.members
        )
        await message.reply(
            f"The {game_type} game queue has been cleared - {user.mention} removed."
        )

        pickle.dump([], open(f"lobby_up_{game_type}_queue.p", "wb"))