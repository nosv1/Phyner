''' IMPORTS '''

import asyncio
from datetime import datetime
import discord
import os
import random
import re
from pytz import timezone
import traceback
from types import SimpleNamespace
import validators


import Database
import Embeds
import Logger
from Logger import log
import Support
from Support import delete_last_field, messageOrMsg, simple_bot_response


''' CONSTANTS '''

# IDs
tcs_id = 925184986699685919

# CHANNELS
tt_submit_id = 925206419458900088
bot_stuff_id = 925188627154210839
leaderboard_id = 927333542726348861

# SPREADSHEET
spreadsheet = {
    "key": "1ecoU0lL2gROfneyF6WEXMJsM11xxj8CZ9VgMNdoiOPU",
    "leaderboards": 2120696652,
    "time_trial_submissions": 1968167541,
    "home": 1367712203
}
spreadsheet_link = "https://docs.google.com/spreadsheets/d/1ecoU0lL2gROfneyF6WEXMJsM11xxj8CZ9VgMNdoiOPU/edit#gid=1367712203"


''' FUNCTIONS '''

async def main(client, message, args, author_perms):

    args[0] = args[0].lower()
    in_bot_stuff = message.channel.id == bot_stuff_id
    in_tt_submit = message.channel.id == tt_submit_id

    if args[0] == "!tt" and (in_bot_stuff or in_tt_submit):
        await tt_submit(client, message, args)

    elif args[0] == "!update" and in_bot_stuff:

        g = Support.get_g_client()
        wb = g.open_by_key(spreadsheet["key"])
        ws = wb.worksheets()
        round_sheet = [sheet for sheet in ws if sheet.title == args[1]][0]
        await update_discord_tables(
            client,
            round_sheet.get(
                f"B6:J{round_sheet.row_count}"
            ),
            "time_trial",
            purge=True
        )
        await update_discord_tables(
            client,
            round_sheet.get(
                f"L6:O{round_sheet.row_count}"
            ),
            "starting_order"
        )

# end main



async def update_discord_tables(client, leaderboard, table_type, purge=False):
    """
        leaderboard is [[row], ...]
    """

    col_widths = Support.get_col_widths(leaderboard)

    channel = await client.fetch_channel(leaderboard_id)
    msg = None


    tt_headers = [
        f"`{('[' + leaderboard[0][2] + ']').ljust(col_widths[2], ' ')}`", # driver
        f"`{('[' + leaderboard[0][3] + ']').center(col_widths[3], ' ')}`", # lap time
        f"`{('[' + leaderboard[0][-1] + ']').rjust(col_widths[-2], ' ')}`", # pts
    ]

    starting_order_headers = [
        f"`{('[' + leaderboard[0][0] + ']').center(col_widths[0], ' ')}`", # pos
        f"`{('[' + leaderboard[0][1] + ']').ljust(col_widths[1], ' ')}`", # driver
        f"`{('[' + leaderboard[0][3] + ']').center(col_widths[3], ' ')}`", # start time
    ]

    header = [" ".join(
        tt_headers if table_type == "time_trial" else starting_order_headers
    )]

    if purge:
        await channel.purge()

    table = header
    for i in range(len(leaderboard) // 25 + 1):

        exited = False
        for j, row in enumerate(leaderboard[1:][i*25:i*25+25]):

            if row[0] == "":
                exited = True
                break

            tt_line = [
                f"{row[2]}".ljust(col_widths[2], " "),
                f"{row[3]}".center(col_widths[3], " "),
                f"{row[-1]}".center(col_widths[-2], " "),
            ]

            starting_order_line = [
                f"{row[0]}".center(col_widths[0], " "),
                f"{row[1]}".ljust(col_widths[1], " "),
                f"{row[3]}".center(col_widths[3], " "),
            ]

            table.append(
                tt_line if table_type == "time_trial" else starting_order_line
            )

            table[-1] = " ".join([f"`{c}`" for c in table[-1]])

        if table:

            embed = await simple_bot_response(
                channel,
                description="\n".join(table),
                send=False
            )

            if i == 0:
                embed.title = f"**Time Trial**" if table_type == "time_trial" else f"**Starting Order**"

            await channel.send(embed=embed)

        if exited:
            break

        table = []
# end update_discord_tables


async def tt_submit(client, message, args):

    await message.channel.trigger_typing()

    # get the time from message
    lap_time = re.findall(
        r"[0-5]{1}:[0-9]{2}.\d{3}", args[1]
    )

    proof = validators.url(re.sub(r"[<>]", "", args[2]))

    if proof:

        if lap_time:

            lap_time = lap_time[0]
            driver_id = message.author.id

            g = Support.get_g_client()
            wb = g.open_by_key(spreadsheet["key"])
            ws = wb.worksheets()
            time_trial_submissions_ws = Support.get_worksheet(
                ws, spreadsheet["time_trial_submissions"]
            )
            home_ws = Support.get_worksheet(
                ws, spreadsheet["home"]
            )

            a1_ranges = [
                f"C4:C{time_trial_submissions_ws.row_count}",  # discord ids
                f"E4:E{time_trial_submissions_ws.row_count}",  # lap times
                f"B4:B{home_ws.row_count}" # rounds
            ]
            
            ranges = time_trial_submissions_ws.batch_get(
                a1_ranges,
                value_render_option="FORMULA"
            )

            # append the new submission

            ranges[0].append([
                str(driver_id)
            ])

            ranges[1].append([
                str(lap_time)
            ])

            # update
            time_trial_submissions_ws.batch_update(
                Support.ranges_to_dict(
                    a1_ranges=a1_ranges,
                    value_ranges=ranges
                ),
                value_input_option="USER_ENTERED"
            )

            await simple_bot_response(
                message.channel,
                title=f"**Your lap time has been submitted!**",
                description=f"[**Spreadsheet**]({spreadsheet_link}) <#{leaderboard_id}>",
                reply_message=message
            )

            
            round_sheet = [sheet for sheet in ws if sheet.title == f"R{ranges[2][-1][0]}"][0]
            
            await update_discord_tables(
                client,
                round_sheet.get(
                    f"B6:J{round_sheet.row_count}"
                ),
                "time_trial",
                purge=True
            )
            await update_discord_tables(
                client,
                round_sheet.get(
                    f"L6:O{round_sheet.row_count}"
                ),
                "starting_order"
            )

        else: # invalid time format

            await simple_bot_response(
                message.channel,
                title="**Invalid time format!**",
                description="Please use the following format: `!tt [m:ss.000] [screnshot_link]`",
                reply_message=message
            )

            return

        # end if lap_time

    else: # no proof

        await simple_bot_response(
            message.channel,
            title="**Invalid proof!**",
            description="Please use a valid screenshot link.\n\n`!tt [m:ss.000] [screnshot_link]`",
            reply_message=message
        )

        return

    # end if proof
