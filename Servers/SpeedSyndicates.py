''' IMPORTS '''

import asyncio
import discord
import os
import random
import re
import pickle
import traceback
import validators
import scipy.optimize as opt

from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pytz import timezone
from types import SimpleNamespace

import Database
import Embeds
import Logger
from Logger import log
import Support
from Support import delete_last_field, messageOrMsg, simple_bot_response


''' CONSTANTS '''

# IDs
speed_syndicates_id = 731697166740881528
# speed_syndicates_id = 789181254120505386  # phyner_support
zarklow_id = 707006084019257424

# CHANNELS
time_trials_id = 844673061453561926
bot_log_id = 856204358772064258
# bot_log_id = 789182513633427507 # phyner_support private testing

# MESSAGES

# COLORS


# tt_spreadsheet
tt_spreadsheet = {
    "key": "1fFGIahQXg2b-hglE_mFaOYf46Kkw0FjErcjMSXIvMPY",
    "submissions": 1817619485,
    "ranges": {
        # submisisons
        "tt_timestamps": "B2:B",  # timestamp
        "tt_discord_ids": "C2:C",  # discord id
        "tt_discord_names": "D2:D",  # discord name"
        "tt_lap_times": "E2:E",  # lap times
        "tt_fps": "F2:F",  # fps
        "tt_round_numbers": "G2:G",  # round numbers

        # round sheet
        "round_positions": "A2:A",  # position
        "round_drivers": "B2:B",  # driver names
        "round_lap_times": "C2:C",  # lap times
        "round_intervals": "D2:D",  # intervals
    }
}
tt_spreadsheet_link = "https://docs.google.com/spreadsheets/d/1fFGIahQXg2b-hglE_mFaOYf46Kkw0FjErcjMSXIvMPY/edit#gid=0"



''' FUNCTIONS '''

async def main(
    client: discord.Client, message: discord.Message, args: list[str], author_perms
):

    args[0] = args[0].lower()

    if args[0] == "!test":
        pass

    if message.channel.id in [time_trials_id, bot_log_id] and args[0] == "!submit":
        await tt_submit(client, message, args)


async def tt_submit(client: discord.Client, message: discord.Message, args: list[str]):

    await message.channel.trigger_typing()    

    # # if it's Sunday after 6:00pm UK time and has not submitted before, too late
    # now = datetime.now(tz=timezone("Europe/London"))
    # late_hour = 18
    
    # is_late = now.weekday() == 6 and now.hour >= late_hour and now.minute >= 0
    # if is_late:  # only check to revert if it's late
    #     is_late = not (now.weekday() == 6 and now.hour >= 21)  # after race, submisisons open again

    # get the time from message
    lap_time = re.findall(
        r"[0-9]{1}:[0-5]{1}[0-9]{1}\.\d{3}", message.content
    )

    proof = [a for a in args if a and validators.url(re.sub(r"[<>]", "", a))]
    # check if there is a link in the message

    if not proof:  
        await simple_bot_response(
            message.channel,
            title="**Invalid proof!**",
            description="Please use a valid video link.\n\n`!submit <m:ss.000> <video_link>`",
            reply_message=message
        )
        return

    if not lap_time:
        await simple_bot_response(
            message.channel,
            title="**Invalid time format!**",
            description="Please use the following format: `!submit <m:ss.000> <video_link>`",
            reply_message=message
        )
        return

    lap_time = lap_time[0]
    driver_id = message.author.id

    g = Support.get_g_client()
    wb = g.open_by_key(tt_spreadsheet["key"])
    ws = wb.worksheets()
    submissions_ws = Support.get_worksheet(
        ws, tt_spreadsheet["submissions"]
    )

    round_number = int(submissions_ws.get("G1")[0][0][-2:])

    a1_ranges = [
        f"{tt_spreadsheet['ranges']['tt_timestamps']}{submissions_ws.row_count}", # timestamp
        f"{tt_spreadsheet['ranges']['tt_discord_ids']}{submissions_ws.row_count}",  # discord ids
        f"{tt_spreadsheet['ranges']['tt_discord_names']}{submissions_ws.row_count}",  # driver names
        f"{tt_spreadsheet['ranges']['tt_lap_times']}{submissions_ws.row_count}",  # lap times
        f"{tt_spreadsheet['ranges']['tt_fps']}{submissions_ws.row_count}",  # fps
        f"{tt_spreadsheet['ranges']['tt_round_numbers']}{submissions_ws.row_count}",  # round numbers
    ]
    
    ranges = submissions_ws.batch_get(
        a1_ranges,
        value_render_option="FORMULA"
    )

    # check for diff name with same discord id
    # if the names are different, change the existing names to the new name
    for i in range(len(ranges[0])):
        if ranges[0][i][0] == driver_id:
            if ranges[2][i][0] != message.author.display_name:
                ranges[2][i][0] = message.author.display_name

    # append the new submission
    ranges[0].append([datetime.now(tz=timezone("Europe/London")).strftime("%d/%m/%Y %H:%M")])  # timestamp
    ranges[1].append([str(driver_id)])  # discord ids
    ranges[2].append([message.author.display_name])  # driver names
    ranges[3].append([lap_time])  # lap times
    ranges[4].append([0])  # fps
    ranges[5].append([round_number])  # round numbers

    tt_round_numbers = ranges[5]

    # get past lap times in this round
    driver_submissions = []  # lap times in seconds
    driver_submission_history = f"**Submission history:**"
    for i, row in enumerate(ranges[1]):  # loop discord ids

        if str(row[0]) == str(driver_id) and str(tt_round_numbers[i][0]) == str(round_number):
            lap_time_str = ranges[3][i][0]
            lap_time_seconds = int(lap_time_str[0]) * 60 + float(lap_time_str[2:])

            if lap_time_seconds in driver_submissions:
                continue
            
            driver_submissions.append(lap_time_seconds)

            delta = 0
            if len(driver_submissions) > 0:
                delta = driver_submissions[-1] - driver_submissions[len(driver_submissions)-2]
            
            driver_submission_history += f"\n{Support.emojis.space_char * 2}**{len(driver_submissions)}.** {lap_time_str}" 

            if delta:
                driver_submission_history += f" ({delta:.3f}s)"

    # > 1 submisison
    if len(driver_submissions) > 1:
        if len(driver_submissions) > 1:
            driver_submission_history += f"\n**Total time found:** {driver_submissions[0] - driver_submissions[-1]:.3f}s"

    # update
    submissions_ws.batch_update(
        Support.ranges_to_dict(
            a1_ranges=a1_ranges,
            value_ranges=ranges
        ),
        value_input_option="USER_ENTERED"
    )

    # get the round sheet ranges
    round_sheet = [s for s in ws if s.title == f"Week {round_number}"][0]
    a1_ranges = [
        f"{tt_spreadsheet['ranges']['round_positions']}{round_sheet.row_count}", # positions
        f"{tt_spreadsheet['ranges']['round_drivers']}{round_sheet.row_count}", # driver names
        f"{tt_spreadsheet['ranges']['round_lap_times']}{round_sheet.row_count}",  # lap times
        f"{tt_spreadsheet['ranges']['round_intervals']}{round_sheet.row_count}",  # intervals
    ]
    
    ranges = round_sheet.batch_get(
        a1_ranges
        # value_render_option="FORMULA"
    )

    basic_lap_details: list[list[str]] = [
        ["**Position:**", ""],
        ["**Lap Time:**", ""],
        ["**To Leader:**", ""],
        ["**To Driver Ahead:**", ""]
    ]  # will join each column with " " and then join each row with "\n"

    for i, row in enumerate(ranges[1]):
        if row[0] == message.author.display_name:
            basic_lap_details[0][1] = f"{ranges[0][i][0]}"
            basic_lap_details[1][1] = f"{ranges[2][i][0]}"
            basic_lap_details[2][1] = f"{ranges[3][i][0]}"

            if i:  # if i > 0 then there is someone ahead
                driver_ahead_lap_time = ranges[2][i-1][0]
                driver_ahead_lap_time_seconds = int(driver_ahead_lap_time[0]) * 60 + float(driver_ahead_lap_time[2:])

                driver_lap_time_seconds = int(lap_time[0]) * 60 + float(lap_time[2:])
                delta = driver_lap_time_seconds - driver_ahead_lap_time_seconds

                basic_lap_details[3][1] = f"+{delta:.3f}"

            else:  # nobody ahead, remove the driver ahead line
                del basic_lap_details[3]

            break

    basic_lap_details = "\n".join([" ".join(row) for row in basic_lap_details])

    # lap time submitted message
    await simple_bot_response(
        message.channel,
        title=f"**Week {round_number} | {message.author.display_name}**",
        description=f"{basic_lap_details}\n\n{driver_submission_history}\n\n[**Spreadsheet**]({tt_spreadsheet_link.replace('gid=0', f'gid={round_sheet.id}')}) [**Proof**]({proof[0]})",
        reply_message=message
    )
# end tt_submit