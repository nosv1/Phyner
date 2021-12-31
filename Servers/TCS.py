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
tt_submit = 925206419458900088
bot_stuff = 925188627154210839

# SPREADSHEET
spreadsheet = {
    "key" : "1ecoU0lL2gROfneyF6WEXMJsM11xxj8CZ9VgMNdoiOPU",
    "leaderboards" : 2120696652,
    "time_trial_submissions" : 1968167541,
}


''' FUNCTIONS '''

async def main(client, message, args, author_perms):

    args[0] = args[0].lower()

    if args[0] == "!tt":
        await tt_submit(message)

# end main


async def tt_submit(message):

    await message.channel.trigger_typing()

    # get the time from message
    lap_time = re.findall(
        r"[0-5]{1}:[0-9]{2}.\d{3}", message.content
    )

    if lap_time:

        lap_time = lap_time[0]
        driver_id = message.author.id

        g = Support.get_g_client()
        wb = g.open_by_key(spreadsheet["key"])
        ws = wb.worksheets()
        time_trial_submissions_ws = Support.get_worksheet(
            ws, spreadsheet["time_trial_submissions"]
        )

        a1_ranges = [
            f"C4:C{time_trial_submissions_ws.row_count}",  # discord ids
            f"E4:E{time_trial_submissions_ws.row_count}"  # lap times
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
            description="**Your lap time has been submitted!**",
            reply_message=message
        )

    else: # invalid time format

        await simple_bot_response(
            message.channel,
            description="**Invalid time format. Please use the following format: `!tt [m:ss.000]`**",
            reply_message=message
        )

        return
