''' IMPORTS '''

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
cotm_id = 527156310366486529

# channels
bot_stuff_id = 527168346404159488
signup_id = 796401927411728414

# roles
staff_moderator_id = 753005514232692737
staff_support_id = 753005661771792506
staff_stats_id = 753005951832948839

# messages
series_report_message_id = 791041462719873074


# Spreadsheets
spreadsheets = SimpleNamespace(**{
    "season_7" : SimpleNamespace(**{
        "key" : "1BIFN9DlU50pWOZqQrz4C44Dk-neDCteZMimTSblrR5U",
        "fixtures_template" : 1525077674,
    }),

    "season_6" : SimpleNamespace(**{
        "key" : "1WgGMgiUF4NVZyFCo-8DW2gnY3kwhXB8l02ov0Cp4pRQ",
        "roster" : 1284096187,
        "driver_history" : 744645833,
        "driver_stats" : 1734830265,
    }),
})

# embeds
series_report_embed_link = "https://discord.com/channels/437936224402014208/519260837727436810/791050164067893329"

aliases = ["", ]



''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
    """

    if message.channel.id == bot_stuff_id: # in bot stuff
        pass

    elif message.channel.id == signup_id:

        if args[0] == "!signup" and args[1]: # !signup <gamertag>
            await user_request_signup(message, args)

        elif not author_perms.administrator:
            await message.delete()


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


def get_season_6_stats(user_id,):
    """
    """

    gc = Support.get_g_client()
    workbook = gc.open_by_key(spreadsheets.season_6.key)
    worksheets = workbook.worksheets()
    driver_stats_ws = [ws for ws in worksheets if ws.id == spreadsheets.season_6.driver_stats][0]

    r = driver_stats_ws.get(f"A4:J{driver_stats_ws.row_count}")

    row_i, row, col_j = Support.find_value_in_range(r, user_id, get=True)

    if col_j >= 0:
        return SimpleNamespace(**{
            "id" : user_id,
            "gt" : row[1],
            "starts" : row[2],
            "finishes" : row[3],
            "dnss" : row[4],
            "reserves" : row[5],
            "best_5" : row[6], # Average of overall positions of best 5 races # Finish Position Overall / Number of Drivers
            "quali" : row[7],
            "pts" : row[8],
            "avg_dif" : row[9], # avg dif of best 5 to quali to pts
        })

    else:
        return None
# end get_season_6_stats


async def user_request_signup(message, args):
    """
    """

    await message.channel.trigger_typing()

    embed = await simple_bot_response(message.channel, send=False)
    embed.title = f"**{re.sub(r'[<>]', '', ' '.join(args[1:]))} - Signup Pending Approval**"

    # stats = get_season_6_stats(args[1])
    stats = get_season_6_stats(message.author.id)

    if stats:
        embed.set_footer(text=f"S6 GT: {stats.gt}")

        v = f"```Starts: {stats.starts}\n"
        v += f"Finishes: {stats.finishes}\n"
        v += f"DNSs: {stats.dnss}\n"
        v += f"Reserves: {stats.reserves}```\n"
        embed.add_field(name="**S6 Attendance**", value=v)

        v = f"```Best 5: Top {stats.best_5} {f'(D{round(float(stats.best_5[:-1]) / 100 * 7)+1})' if stats.best_5 else ''}\n"
        v += f"Quali: Top {stats.quali} {f'(D{round(float(stats.quali[:-1]) / 100 * 7)+1})' if stats.quali else ''}\n"
        v += f"Points: Top {stats.pts} {f'(D{round(float(stats.pts[:-1]) / 100 * 7)+1})' if stats.pts else ''}\n"
        v += f"Avg Dif: {stats.avg_dif}```\n"
        embed.add_field(name="**S6 Performance**", value=v)

    else:
        embed.description = "```S6 Stats Not Found```"

    msg = await message.channel.send(embed=embed)
    await msg.add_reaction(Support.emojis.tick_emoji)
    await msg.add_reaction(Support.emojis.x_emoji)
# end user_request_signup