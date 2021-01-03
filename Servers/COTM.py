''' IMPORTS '''

from os import supports_bytes_environ
import discord
import asyncio
import traceback
from types import SimpleNamespace
import re
import validators


import Database
import Embeds
import Logger
from Logger import log
import Support
from Support import delete_last_field, messageOrMsg, simple_bot_response
import Delete



''' CONSTANTS '''
# staff_ indicates the id is in the Staff server

# IDs
templar_leagues_id = 437936224402014208
staff_templar_leagues_id = 752990198077587569

# channels
approved_results_id = 686981857379614746
staff_league_results_log_id = 753207723499192383
staff_stats_log_id = 789066825093611550

# roles
staff_moderator_id = 753005514232692737
staff_support_id = 753005661771792506
staff_stats_id = 753005951832948839

# messages
series_report_message_id = 791041462719873074


# Spreadsheets
spreadsheets = SimpleNamespace(**{
    "season_6_league_database" : SimpleNamespace(**{
        "key" : "1aqyMc6uw8cG-1qlyRwohvPKuxnxwQPe2rbUcdo45J88",
        "fixtures_template" : 1525077674,
    })
})

# embeds
series_report_embed_link = "https://discord.com/channels/437936224402014208/519260837727436810/791050164067893329"

aliases = ["", ]



''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
        @Phyner _command_
    """
    pass

# end main


async def on_reaction_add(client, message, user, payload):

    remove_reaction = False
    embed = message.embeds[0] if message.embeds else None

    if embed:

        if embed.author:

            if embed.author.url:

                if ( # series report + ok_emoji button
                    "/id=templar_leagues_series_report/" in embed.author.url and 
                    payload.emoji.name == Support.emojis.ok_emoji
                ):
                    await series_report(client, message, user)
                    remove_reaction = True

    return remove_reaction
# end on_reaction_add