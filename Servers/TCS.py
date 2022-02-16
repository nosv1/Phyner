''' IMPORTS '''

import asyncio
from datetime import datetime
import discord
import os
import random
import re
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
tcs_id = 925184986699685919
drivers_role_id = 925189004893253673

# CHANNELS
tt_submit_id = 925206419458900088
bot_stuff_id = 925188627154210839
tt_n_starting_order_id = 927333542726348861
rival_selection_log_id = 929154488143581245
rivalry_log_id = 929154488143581245
leaderboards_id = 935016463968903259

# SPREADSHEET
spreadsheet = {
    "key": "1ecoU0lL2gROfneyF6WEXMJsM11xxj8CZ9VgMNdoiOPU",
    "leaderboards": 2120696652,
    "submissions": 1968167541,
    "home": 1367712203,
    "leaderboards": 2120696652,
    "ranges": {
        # submisisons
        "tt_discord_ids": "C4:C",  # discord id
        "tt_lap_times": "E4:E",  # lap times
        "tt_round_numbers": "F4:F",  # round numbers
        "ll_discord_ids": "I4:I",  # discord id
        "ll_laps": "K4:K", # lap counts
        "ll_round_numbers": "L4:L",  # round numbers
        "gamertag_conversion": "N4:P",  # discord_id, gamertag, avail
        "rivals": "Q4:Q",  # rival_gamertag

        # leaderboards
        "avg_tt_pace_vs_field": "B2:D",  # pos, gamertag, pace v field
        "avg_race_pace_vs_field": "F2:H",  # pos, gamertag, pace v field
        "avg_overall_pace_vs_field": "J2:L",  # pos, gamertag, pace v field

        # round sheet
        "time_trial": "B5:I",  # pos, race?, gamertag, lap time, delta, pace v field
        "time_trial_times": "D7:E", # gamertag, lap_time
        "starting_order": "K5:Q",  # pos, lby, gamertag, lap time, start time

        # tables
        "drivers_of_the_week": "H2:I",  # gamertag, count
        "time_trial_counts": "K2:P",  # wins gamertag, count, podiums gamertag, count, particpation gamertag, count
        "race_counts": "R2:W",  # wins gamertag, count, podiums gamertag, count, particpation gamertag, count
        "rivals_beat": "Y2:AD",  # tt gamertag, count, race gamertag, count, swept gamertag, count
    }
}
spreadsheet_link = "https://docs.google.com/spreadsheets/d/1ecoU0lL2gROfneyF6WEXMJsM11xxj8CZ9VgMNdoiOPU/edit#gid=1367712203"

# MESSAGES
rival_selection_msg_id = 927758552955748404

# COLORS
metallic_seaweed = '#177e89'
ming = '#106575'
cg_red = '#db3a34'
mango_tango = '#ed8146'
max_yellow_red = '#ffc857'
jet = '#323031'


''' FUNCTIONS '''

async def main(client, message, args, author_perms):

    args[0] = args[0].lower()
    in_bot_stuff = message.channel.id == bot_stuff_id
    in_tt_submit = message.channel.id == tt_submit_id

    if args[0] == "!test" and in_bot_stuff:
        pass

    elif args[0] == "!pvf":
        await pvf_to_lap_time(message, args)

    elif args[0] == "!logit":
        await log_laps(message, args)

    elif args[0] == "!tt" and (in_bot_stuff or in_tt_submit):
        await tt_submit(client, message, args)

    elif args[0] == "!update" and in_bot_stuff:
        
        g = Support.get_g_client()
        wb = g.open_by_key(spreadsheet["key"])
        ws = wb.worksheets()

        sheet = None
        table_types = []

        # leaderboards
        if args[1] == "leaderboards":
            leaderboard_sheet = [sheet for sheet in ws if sheet.title == "Leaderboards"][0]
            sheet = leaderboard_sheet
            table_types = [
                "avg_tt_pace_vs_field", 
                "avg_race_pace_vs_field", 
                "avg_overall_pace_vs_field"
            ]

        # counts
        elif args[1] == "counts":
            random_tables_sheet = [sheet for sheet in ws if sheet.title == "Random Tables"][0]
            sheet = random_tables_sheet
            table_types = [
                "drivers_of_the_week", 
                "time_trial_counts", 
                "race_counts", 
                "rivals_beat"
            ]

        # round sheet
        else:
            round_sheet = [sheet for sheet in ws if sheet.title == args[1]][0]
            sheet = round_sheet
            table_types = [
                "time_trial", 
                "starting_order"
            ]
        
        for i, table_type in enumerate(table_types):
            
            await update_discord_tables(
                client,
                sheet.get(
                    f"{spreadsheet['ranges'][table_type]}{sheet.row_count}"
                ),
                table_type,
                purge = i==0 and args[1] != "leaderboards"
            )

    elif args[0] == "!staggered":
        await generate_staggered_start(message, args)

    elif args[0] == "!resetnicks":
        await reset_nicknames(message)
# end main


async def on_reaction_add(client, message, user, payload):

    remove_reaction = False
    embed = message.embeds[0] if message.embeds else None

    if embed:

        if embed.description:
            
            embed_meta = embed.description.split("embed_meta/")

            if len(embed_meta) > 1:
                embed_meta = embed_meta[1][:-1]  # gets rid of the ) at the end
                embed_type = embed_meta.split("type=")[1].split("/")[0]

                if embed_type == "rivals":
                    await handle_rival_selection(message, user, payload, embed_meta)



    return remove_reaction
# end on_reaction_add



async def update_discord_tables_old(client: discord.Client, leaderboard: list, table_type: str, title: str, purge: bool = False):
    # """
    #     leaderboard is [[row], ...]
    # """

    # if table_type == "time_trial":
    #     leaderboard[0][3] = leaderboard[0][3].replace("Lap Time", "Lap")
    #     leaderboard[0][5] = leaderboard[0][5].replace("Pace v Field", "PvF")

    # else:
    #     leaderboard[0][4] = leaderboard[0][4].replace("Start Time", "Start")

    # col_widths = Support.get_col_widths(leaderboard)

    # channel = await client.fetch_channel(tt_n_starting_order_id)
    # msg = None


    # tt_headers = []
    # starting_order_headers = []

    # if table_type == "time_trial":
    #     tt_headers = [
    #         f"`{('[' + leaderboard[0][0] + ']').center(col_widths[0], ' ')}`", # pos
    #         f"`{('[' + leaderboard[0][2] + ']').ljust(col_widths[2], ' ')}`", # driver
    #         f"`{('[' + leaderboard[0][3] + ']').center(col_widths[3], ' ')}`", # lap time
    #         f"`{('[' + leaderboard[0][5] + ']').center(col_widths[5], ' ')}`", # pvf
    #     ]

    # else:
    #     starting_order_headers = [
    #         f"`{('[' + leaderboard[0][0] + ']').center(col_widths[0], ' ')}`", # pos
    #         f"`{('[' + leaderboard[0][2] + ']').ljust(col_widths[2], ' ')}`", # driver
    #         f"`{('[' + leaderboard[0][4] + ']').center(col_widths[4], ' ')}`", # start time
    #     ]

    # header = [" ".join(
    #     tt_headers if table_type == "time_trial" else starting_order_headers
    # )]

    # if purge:
    #     await channel.purge()

    # table = header
    # for i in range(len(leaderboard) // 25 + 1):

    #     exited = False
    #     for j, row in enumerate(leaderboard[1:][i*25:i*25+25]):

    #         if not row or row[0] == "":
    #             exited = True
    #             break

    #         if table_type == "time_trial":

    #             line = [
    #                 f"{row[0]}".center(col_widths[0], " "),
    #                 f"{row[2]}".ljust(col_widths[2], " "),
    #                 f"{row[3]}".center(col_widths[3], " "),
    #                 f"{row[5]}".center(col_widths[5], " "),
    #             ]

    #         else:
    #             line = [
    #                 f"{row[0]}".center(col_widths[0], " "),
    #                 f"{row[2]}".ljust(col_widths[2], " "),
    #                 f"{row[4]}".center(col_widths[4], " "),
    #             ]

    #         table.append(line)

    #         table[-1] = " ".join([f"`{c}`" for c in table[-1]])

    #     if table:

    #         embed = await simple_bot_response(
    #             channel,
    #             description="\n".join(table),
    #             send=False
    #         )

    #         if i == 0:
    #             embed.title = title

    #         await channel.send(embed=embed)

    #     if exited:
    #         break

    #     table = []
    return
# end update_discord_tables_old

async def update_discord_tables(
    client: discord.Client, leaderboard: list[list[str]], table_type: str, purge: bool = False
):

    for row in leaderboard:
        if not row or not row[-1] or not row[0]:
            leaderboard = leaderboard[:leaderboard.index(row)]
            break

    if len(leaderboard[1]) < len(leaderboard[2]):
        leaderboard[1].append('')

    header_heights = [24, 20]
    if table_type == "time_trial":
        # pos, race?, driver, lap time, delta, pvf, rival, rival beat?
        column_widths = [40, 40, 140, 80, 50, 75, 140, 40]
        column_alignments = ["center", "center", "left", "center", "center", "center", "center", "center"]

    elif table_type == "starting_order":
        # pos, lby, driver, lap time, start time, rival, rival beat?
        column_widths = [40, 40, 140, 80, 80, 140, 40]
        column_alignments = ["center", "center", "left", "center", "center", "center", "center"]

    elif table_type in [
        "avg_tt_pace_vs_field", 
        "avg_race_pace_vs_field", 
        "avg_overall_pace_vs_field"
    ]:
        column_widths = [40, 140, 90]
        column_alignments = ["center", "left", "center"]

    elif table_type == "drivers_of_the_week":
        # gt, count
        column_widths = [140, 40]
        column_alignments = ["center", "center"]

    elif table_type in [
        "time_trial_counts", 
        "race_counts"
    ]:
        # wins gt, count, podiums gt, count, participation gt, count
        column_widths = [140, 40, 140, 40, 140, 40]
        column_alignments = ["center", "center", "center", "center", "center", "center"]

    elif table_type == "rivals_beat":
        # tt gt, count, race gt, count, swept gt, count
        column_widths = [140, 40, 140, 40, 140, 40]
        column_alignments = ["center", "center", "center", "center", "center", "center"]

    body_rows = len(leaderboard) - len(header_heights)
    bg_margin = 10

    # load image
    checkbox = Image.open('Images/Checkbox.png').resize((16, 16))
    empty_checkbox = Image.open('Images/Empty Checkbox.png').resize((16, 16))

    out = Image.new(
        "RGB", (
            sum(column_widths) + bg_margin * 2, 
            20 * body_rows + sum(header_heights) + bg_margin * 2
        ), jet
    )

    draw = ImageDraw.Draw(out)

    # rectangles
    draw.rectangle((8, 8, out.size[0]-8, out.size[1]-8), fill=mango_tango)  # 2px outline
    
    draw.rectangle(  # header 1
        (
            bg_margin, bg_margin, 
            out.size[0]-bg_margin, bg_margin + header_heights[0]
        ), fill=cg_red
    )  

    draw.rectangle(  # header 2
        (
            bg_margin, bg_margin + header_heights[0], 
            out.size[0]-bg_margin, bg_margin + sum(header_heights[0:2])
        ), fill=ming
    )

    draw.rectangle(  # body
        (
            bg_margin, bg_margin + sum(header_heights), 
            out.size[0]-bg_margin, out.size[1]-bg_margin
        ), fill=metallic_seaweed
    )

    # borders
    draw.line(  # header 1 bottom border
        (
            bg_margin, bg_margin + header_heights[0], 
            out.size[0]-bg_margin, bg_margin + header_heights[0]
        ), fill="black", width=1
    )
    draw.line(  # header 2 bottom border
        (
            bg_margin, bg_margin + sum(header_heights[0:2]), 
            out.size[0]-bg_margin, bg_margin + sum(header_heights[0:2])
        ), fill="black", width=1
    )

    for i in range(1, body_rows): # body bottom borders
        offset_y = bg_margin + sum(header_heights) + 20*i
        draw.line((bg_margin, offset_y, out.size[0]-bg_margin, offset_y), fill=ming, width=1)

    # text
    roboto_bold = "Fonts/Roboto-Bold.ttf"
    roboto_medium = "Fonts/Roboto-Medium.ttf"
    pt_to_px = 4/3
    px_font_sizes = {
        12: 12*pt_to_px,
        14: 14*pt_to_px
    }
    header_1_font = ImageFont.truetype(roboto_bold, 14)
    header_2_font = ImageFont.truetype(roboto_bold, 12)
    body_font = ImageFont.truetype(roboto_medium, 12)

    draw.text(  # header 1
        (
            bg_margin + (out.size[0]-bg_margin*2)//2 - header_1_font.getsize(text=leaderboard[0][0])[0]//2,
            bg_margin + header_heights[0]//2 - header_1_font.getsize(text=leaderboard[0][0])[1]//2
        ), leaderboard[0][0], fill=max_yellow_red, font=header_1_font
    )

    # header 2
    for i, text in enumerate(leaderboard[1]):
        offset_x = bg_margin + sum(column_widths[:i])
        offset_y = bg_margin + sum(header_heights[0:1]) + (header_heights[1] // 2 - px_font_sizes[12] // 2) + 1  # no idea why it's + 1, but it works

        # mergeable columns
        mergeable = False
        column_width = column_widths[i]
        if i < len(column_widths) - 1:
            if not leaderboard[1][i+1]:
                column_width += column_widths[i+1]
                mergeable = True

        previous_column_merged = False
        if i > 0:
            if leaderboard[1][i-1] != '' and not leaderboard[1][i]:
                previous_column_merged = True

        if not previous_column_merged:

            if column_alignments[i] == "center":
                draw.text(
                    (
                        offset_x + (column_width - header_2_font.getsize(text=text)[0])//2,
                        offset_y
                    ), text, fill=max_yellow_red, font=header_2_font
                )

            else:
                draw.text(
                    (
                        offset_x,
                        offset_y
                    ), text, fill=max_yellow_red, font=header_2_font
                )

    # body
    for i, row in enumerate(leaderboard[2:]):

        for j, text in enumerate(row):

            offset_x = bg_margin + sum(column_widths[:j]) 
            offset_y = bg_margin + sum(header_heights[0:2]) + 20*i + 3

            if text in ['TRUE', 'FALSE']:
                out.paste(
                    checkbox if text == 'TRUE' else empty_checkbox,
                    (
                        offset_x + (column_widths[j] - checkbox.size[0])//2,
                        offset_y + (header_heights[1] - checkbox.size[1])//2 - 2
                    )
                )

            else:

                if column_alignments[j] == "center":
                    draw.text(
                        (
                            offset_x + (column_widths[j] - body_font.getsize(text=text)[0])//2,
                            offset_y
                        ), text, fill=max_yellow_red, font=body_font
                    )

                else:
                    draw.text(
                        (
                            offset_x,
                            offset_y
                        ), text, fill=max_yellow_red, font=body_font
                    )

    out.save(f"Images/{table_type}.png")
    
    if table_type in [
        "time_trial", 
        "starting_order"
    ]:
        channel = await client.fetch_channel(tt_n_starting_order_id)
        
    elif table_type in [
        # leaderboards
        "avg_tt_pace_vs_field", 
        "avg_race_pace_vs_field", 
        "avg_overall_pace_vs_field",

        # counts
        "drivers_of_the_week", 
        "time_trial_counts", 
        "race_counts", 
        "rivals_beat"
    ]:
        channel = await client.fetch_channel(leaderboards_id)

    if purge:
        await channel.purge()

    image = discord.File(f"Images/{table_type}.png")
    await channel.send(file=image)
# end update_discord_tables

async def update_rivalry_log(client: discord.Client, rivarly_log: discord.TextChannel, driver_user: discord.User, lap_time: str):

    g = Support.get_g_client()
    wb = g.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()
    submissions_ws = Support.get_worksheet(
        ws, spreadsheet["submissions"]
    )
    rivals = submissions_ws.get(
        f"{spreadsheet['ranges']['rivals']}{submissions_ws.row_count}"
    )
    gamertag_conversion = submissions_ws.get(
        f"{spreadsheet['ranges']['gamertag_conversion']}{submissions_ws.row_count}"
    )

    # get driver gamertag by looping through the gamertag conversion
    driver_gamertag = None
    for row in gamertag_conversion:
        if row[0] == str(driver_user.id):
            driver_gamertag = row[1]
            break

    # get the rival user ids for pings by looping through the rivals
    selector_users = []

    for i, row in enumerate(rivals):

        if row and row[0] == driver_gamertag:  # found someone who has the driver as their rival

            selector_id = gamertag_conversion[i][0] # so if Deux Veloce picked Mo v0, this is Veloce's ID
            selector_users.append(await client.fetch_user(int(selector_id)))

    if selector_users:
        msg_str = f"{', '.join([s.mention for s in selector_users])}, your rival, {driver_gamertag}, just set a {lap_time}!"
        await rivarly_log.send(msg_str)
# end update_rival_log


async def tt_submit(client: discord.Client, message: discord.Message, args: list[str]):

    await message.channel.trigger_typing()

    # get the time from message
    lap_time = re.findall(
        r"[0-5]{1}:[0-9]{2}\.\d{3}", args[1]
    )

    proof = validators.url(re.sub(r"[<>]", "", args[2]))

    if proof or True:

        if lap_time:

            lap_time = lap_time[0]
            driver_id = message.author.id

            g = Support.get_g_client()
            wb = g.open_by_key(spreadsheet["key"])
            ws = wb.worksheets()
            submissions_ws = Support.get_worksheet(
                ws, spreadsheet["submissions"]
            )

            round_number = int(submissions_ws.get("F3")[0][0][-2:])

            a1_ranges = [
                f"{spreadsheet['ranges']['tt_discord_ids']}{submissions_ws.row_count}",  # discord ids
                f"{spreadsheet['ranges']['tt_lap_times']}{submissions_ws.row_count}",  # lap times
            ]
            
            ranges = submissions_ws.batch_get(
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
            submissions_ws.batch_update(
                Support.ranges_to_dict(
                    a1_ranges=a1_ranges,
                    value_ranges=ranges
                ),
                value_input_option="USER_ENTERED"
            )

            tt_round_numbers = submissions_ws.get(
                f"{spreadsheet['ranges']['tt_round_numbers']}{submissions_ws.row_count}"
            )

            # get past lap times in this round
            driver_submissions = []  # lap times in seconds
            driver_submission_history = f"**Round {round_number} | Submission history:**"
            for i, row in enumerate(ranges[0]):

                if row[0] == str(driver_id) and tt_round_numbers[i][0] == str(round_number):
                    lap_time_str = ranges[1][i][0]
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

            if len(driver_submissions) > 1:
                driver_submission_history += f"\n**Total time found:** {driver_submissions[0] - driver_submissions[-1]:.3f}s"

            await simple_bot_response(
                message.channel,
                title=f"**Your lap time has been submitted!**",
                description=f"{driver_submission_history}\n\n[**Spreadsheet**]({spreadsheet_link}) <#{tt_n_starting_order_id}>",
                reply_message=message
            )
            
            # alert for brand new driver
            if [str(driver_id)] not in ranges[0]:
                mo_user = discord.utils.find(
                    lambda u: u.id == Support.ids.mo_id, message.guild.members
                )
                await message.channel.send(
                    f"{mo_user.mention}, {message.author.display_name} is a brand new submitter! Update the spreadsheet.\n\n"
                )

            # update the discord tables
            round_sheet = [sheet for sheet in ws if sheet.title == f"R{round_number}"][0]
            
            await update_discord_tables(
                client,
                round_sheet.get(
                    f"{spreadsheet['ranges']['time_trial']}{round_sheet.row_count}"
                ),
                "time_trial",
                purge=True
            )
            await update_discord_tables(
                client,
                round_sheet.get(
                    f"{spreadsheet['ranges']['starting_order']}{round_sheet.row_count}"
                ),
                "starting_order"
            )

            await update_rivalry_log(
                client,
                message.guild.get_channel(rivalry_log_id),
                message.author,
                lap_time
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
# end tt_submit


async def generate_staggered_start(message: discord.Message, args: list[str]):
    
    await message.channel.trigger_typing()

    try:
        lap_count = int(args[1])
    except:  # bad input
        await simple_bot_response(
            message.channel,
            title="**Invalid input!**",
            description="Please use the following format: `!staggered_start <lap_count> <@Driver> <@Driver> ...`",
            reply_message=message
        )
        return

    g = Support.get_g_client()
    wb = g.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()
    submissions_ws = Support.get_worksheet(
        ws, spreadsheet["submissions"]
    )
    round_number = int(submissions_ws.get("F3")[0][0][-2:])
    round_sheet = [sheet for sheet in ws if sheet.title == f"R{round_number}"][0]

    gamertag_conversion = submissions_ws.get(f"{spreadsheet['ranges']['gamertag_conversion']}{submissions_ws.row_count}")

    mentions = [m.id for m in message.mentions]
    gamertags = []
    for i, row in enumerate(gamertag_conversion):
        if row[0] and int(row[0]) in mentions:
            gamertags.append(row[1])

    driver_lap_times = round_sheet.get(
        f"D7:E{round_sheet.row_count}"
    )

    # convert lap times to seconds
    for i, row in enumerate(driver_lap_times):
        driver_lap_times[i][1] = int(driver_lap_times[i][1][0]) * 60 + float(driver_lap_times[i][1][2:])

    # remove drivers not in gamertags
    i = len(driver_lap_times) - 1
    while i >= 0:
        if driver_lap_times[i][0] not in gamertags:
            driver_lap_times.pop(i)
        i -= 1
    
    # sort driver lap times based on lap time
    driver_lap_times.sort(key=lambda x: x[1], reverse=True)

    # get deltas between laptimes
    deltas = [0]
    for i, row in enumerate(driver_lap_times):
        if i > 0:
            deltas.append((driver_lap_times[0][1] - driver_lap_times[i][1]) * lap_count)

    start_times = []
    offset = 15  # seconds
    for i, delta in enumerate(deltas):
        if i == 0:
            start_times.append(offset)
        else:
            start_times.append(start_times[i-1] + delta)

    description = f"**Lap Count:** {lap_count}\n"
    for i, start_time in enumerate(start_times):
        description += f"{Support.emojis.space_char * 2}**{i+1}.** {driver_lap_times[i][0]} +{start_time:.3f}s\n"

    await simple_bot_response(
        message.channel,
        title="**Staggered start times generated!**",
        description=description,
    )
# end generate_staggered_start


async def pvf_to_lap_time(message: discord.Message, args: list[str]):

    def get_avg_percent_diffs(times: list[float]) -> list[float]:
        diffs = []

        for time in times:
            if time:

                sum = 0
                for field_time in times:

                    if field_time:
                        sum += (field_time - time) / ((time + field_time) / 2)

                diffs.append(sum / len(times))

        return diffs
    # end get_avg_percent_diffs

    def f(Td: float, times: list[float], num_drivers: int, target_pvf: float) -> float:
        """
        create the equation for opt.brentq()

        0 = (Tfn1 - Td) / (1/2 * (Tfn1 + Td)) + ... - (PvF * num_drivers)
        
        Tfn are the field times Tfn1, Tfn2, ...

        Parameters
        ----------
        Td: driver time
        times: list of driver times
        num_drivers: current number of drivers
        target_pvf: denormalized verion
        """

        time_terms = []

        for time in times:
            time_terms.append(
                f"({time} - Td) / (1/2 * ({time} + Td))"
            )

        eq = f"{' + '.join(time_terms)} - ({target_pvf} * {num_drivers})"

        return eval(eq)
    # end f

    await message.channel.trigger_typing()

    driver = message.mentions[0] if message.mentions else message.author
    driver_id = driver.id
    target_pvf = args[1]

    bad_pvf = False
    try:
        target_pvf = float(target_pvf)
        
        if target_pvf < 0 or target_pvf > 1:
            bad_pvf = True

    except ValueError:
        bad_pvf = True
    
    if bad_pvf:
        await simple_bot_response(
            message.channel,
            title="**Invalid PvF!**",
            description="`target_pvf` should be in the range [0, 1] \n\n`!pvf <target_pvf> [@Driver]`\n`!pvf 0.75 @Mo`",
            reply_message=message
        )
        return

    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()
    submissions_ws = Support.get_worksheet(
        ws, spreadsheet["submissions"]
    )
    round_number = int(submissions_ws.get("F3")[0][0][-2:])
    round_sheet = [sheet for sheet in ws if sheet.title == f"R{round_number}"][0]

    gamertag_conversion = submissions_ws.get(f"{spreadsheet['ranges']['gamertag_conversion']}{submissions_ws.row_count}")

    driver_gamertag = [row[1] for row in gamertag_conversion if row[0] == str(driver_id)]
    driver_gamertag = driver_gamertag[0] if driver_gamertag else None

    time_trial_times = round_sheet.get(f"{spreadsheet['ranges']['time_trial_times']}{round_sheet.row_count}")  # gamertag, lap_time

    # get all lap times except for driver lap time
    # when we calculate the target time, it needs to think it's a new driver
    lap_times = [row[1] for row in time_trial_times if row[0] != driver_gamertag]

    if not lap_times:
        await simple_bot_response(
            message.channel,
            title="**Not enough lap times submitted!**",
            description=f"Not enough lap times submitted for Round {round_number} - missing {2 - len(lap_times)}. Please, try again later.",
            reply_message=message
        )
        return

    for i, lap_time in enumerate(lap_times):
        lap_times[i] = int(lap_times[i][0]) * 60 + float(lap_times[i][2:])

    avg_percent_diffs = get_avg_percent_diffs(lap_times)
    de_normalized_target_pvf = (
        target_pvf * 
        (avg_percent_diffs[0] - avg_percent_diffs[-1]) + 
        avg_percent_diffs[-1]  # [0] is max and [-1] is min
    )
    
    target_time = opt.brentq(
        lambda xi: f(xi, lap_times, len(lap_times), de_normalized_target_pvf), 
        lap_times[0]-100, 
        lap_times[-1]+100
    )

    # convert seconds to m:ss.000
    target_time = f"{int(target_time // 60)}:{str(int(target_time % 60)).zfill(2)}.{str(int((target_time % 1) * 1000)).zfill(3)}"
    
    await simple_bot_response(
        message.channel,
        description=f"**{driver.mention} needs to set a `{target_time}` for a `{target_pvf}` PvF.**",
        reply_message=message
    )
# end pvf_to_lap_time


async def prepare_rival_selection_channel(channel: discord.TextChannel, user: discord.User, msg: discord.Message = None):

    g = Support.get_g_client()
    wb = g.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()

    leaderboards_ws = Support.get_worksheet(
        ws, spreadsheet["leaderboards"]
    )
    submissions_ws = Support.get_worksheet(
        ws, spreadsheet["submissions"]
    )

    # loop avg tt pvf until no pos value given text below table on spreadsheet
    avg_overall_pace_vs_field = leaderboards_ws.get(
        f"{spreadsheet['ranges']['avg_overall_pace_vs_field']}{leaderboards_ws.row_count}"
    )
    gamertag_conversion = submissions_ws.get(
        f"{spreadsheet['ranges']['gamertag_conversion']}{submissions_ws.row_count}"
    )
    
    user_gamertag = [row[1] for row in gamertag_conversion if row[0] and int(row[0]) == user.id]
    user_gamertag = user_gamertag[0] if user_gamertag else None

    if not user_gamertag:
        await simple_bot_response(
            channel,
            title="**No gamertag found!**",
            description="You have not participated in a TT or finished a race yet. You can select a rival once you've done both in the same round."
        )
        return

    possible_rivals = []  # pos, driver, pace
    user_pace = None
    for i, row in enumerate(avg_overall_pace_vs_field[2:]):

        if row[1] != user_gamertag:
            racing = [
                r[2] for r in gamertag_conversion if r[1] == row[1]
            ][0]
            row.append(racing == "TRUE")
            possible_rivals.append(row)

        else:
            if i == 0:
                possible_rivals.append(avg_overall_pace_vs_field[i+1])
            user_pace = row[2]
            break

    description = "Beating your rival in the TT will give you a start-time deduction in this round's race - based on how many positions ahead your rival is; then, if you also beat them in the race, you will get an honourable mention and a role.\n\n"

    description += "Selecting a rival will ping them to let them know they've been chosen. If your rival does not plan to race, you will have the opportunity to pick a new rival - assuming your rival notifies staff before Thursday.\n\n"

    description += f"**Select the position of the driver you would like to choose as your rival for the current round.**\n"


    embed_meta = "embed_meta/type=rivals/"

    # setting the possible rivals
    for i, rival in enumerate(possible_rivals[-9:]):
        embed_meta += f"{Support.emojis.number_emojis[i+1]}={rival[1].replace(' ', '%20')}-{rival[2]}/"

        # rival - pvf
        rival_line = f"{rival[1]} - {rival[2]}"

        # rival not racing
        if not rival[3]:
            rival_line = f"~~{rival_line}~~ (not racing)"

        # #. rival - pvf
        description += f"{Support.emojis.space_char * 2}**{i+1}.** {rival_line}\n"
    
    # driver line
    description += f"{Support.emojis.space_char * 2}**{len(possible_rivals)+1}.** {user_gamertag} - {user_pace}\n\n"
    embed_meta += f"selector={user_gamertag.replace(' ', '%20')}-{user_pace}/"

    description += f"*The number to the right of the driver's name is their *Average Overall Pace vs Field*; this number ranges from 1 to 0 and tries to evaluate how fast a driver typically is against a field."

    description += f"[{Support.emojis.zero_width}]({embed_meta})"

    embed = await simple_bot_response(
        channel,
        title="**Choose a rival!**",
        description=description,
        send=False
    )
    if msg:
        await msg.edit(embed=embed)
    else:
        msg = await channel.send(embed=embed)

    for i, rival in enumerate(possible_rivals[-9:]):

        if rival[3]:
            await msg.add_reaction(Support.emojis.number_emojis[i+1])

    return
# end prepare_rival_selection_channel


async def handle_rival_selection(
    msg: discord.Message, user: discord.User, payload: discord.RawReactionActionEvent, embed_meta: str
): 

    if payload.emoji.name in embed_meta:  # number emoji clicked

        rival_gamertag, rival_pace = embed_meta.split(payload.emoji.name + "=")[1].split("/")[0].split("-")

        embed = msg.embeds[0]
        embed.add_field(
            name = Support.emojis.zero_width,
            value = f"**Are you sure you want to choose `{rival_gamertag.replace('%20', ' ')}` as your rival?**",
        )

        embed_meta += f"selection={rival_gamertag}-{rival_pace}/"
        # replace old embed_meta with new one
        embed.description = embed.description.replace(embed.description.split("embed_meta/")[1], embed_meta) + ")"

        await msg.edit(embed=embed)

        await msg.clear_reactions()
        await msg.add_reaction(Support.emojis.ballot_checkmark_emoji)
        await msg.add_reaction(Support.emojis.x_emoji)


    elif payload.emoji.name == Support.emojis.ballot_checkmark_emoji:  # rival confirmed

        rival_gamertag, rival_pace = embed_meta.split("selection=")[1].split("/")[0].replace('%20', ' ').split("-")
        selector, selector_pace = embed_meta.split("selector=")[1].split("/")[0].replace("%20", " ").split("-")

        g = Support.get_g_client()
        wb = g.open_by_key(spreadsheet["key"])
        ws = wb.worksheets()

        submissions_ws = Support.get_worksheet(
            ws, spreadsheet["submissions"]
        )

        gamertag_conversion = submissions_ws.get(
            f"{spreadsheet['ranges']['gamertag_conversion']}{submissions_ws.row_count}"
        )
        rivals = submissions_ws.get(
            f"{spreadsheet['ranges']['rivals']}{submissions_ws.row_count}"
        )
        
        discord_id = [int(row[0]) for row in gamertag_conversion if row[1] == rival_gamertag][0]
        rival_user = discord.utils.find(lambda u: u.id == discord_id, msg.guild.members)
        mo_user = discord.utils.find(lambda u: u.id == Support.ids.mo_id, msg.guild.members)

        rival_selection_log = msg.guild.get_channel(rival_selection_log_id)
        await rival_selection_log.send(
            f"{rival_user.mention} ({rival_pace}), {user.mention} ({selector_pace}) has selected you as their rival. Please, let {mo_user.mention} know if you do not plan to race on Sunday."
        )

        await msg.channel.send("Thank you for selecting a rival. Good luck :thumbsup:")

        for i in range(len(gamertag_conversion) - len(rivals)):
            rivals += [['']]

        for i, row in enumerate(gamertag_conversion):
            
            if row[1] == selector:

                if not rivals[i]:
                    rivals[i] = [rival_gamertag]

                rivals[i][0] = rival_gamertag

        submissions_ws.update(
            f"{spreadsheet['ranges']['rivals']}{submissions_ws.row_count}",
            rivals
        )

        await msg.channel.delete()


    elif payload.emoji.name == Support.emojis.x_emoji:  # rival canceled

        await msg.clear_reactions()
        await prepare_rival_selection_channel(msg.channel, user, msg)
# end handle_rival_selection


async def log_laps(message, args):
    """
        get number of laps from args and log it to spreadsheet
    """

    await message.channel.trigger_typing()

    lap_count = re.findall(r"[-]{0,1}\d+", args[1])
    if lap_count:
        lap_count = int(lap_count[0])

        if not lap_count or (lap_count < -50 or lap_count > 50):
            await simple_bot_response(
                message.channel,
                title="**Error!**",
                reply_message=message
            )
            return

    else:
        await simple_bot_response(
            message.channel,
            title="**Invalid number of laps!**",
            description="Please, provide a number of laps to log.\n\n`!logit 10`",
        )
        return

    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()
    submissions_ws = Support.get_worksheet(
        ws, spreadsheet["submissions"]
    )

    round_number = int(submissions_ws.get("F3")[0][0][-2:])

    ll_round_numbers = submissions_ws.get(
        f"{spreadsheet['ranges']['ll_round_numbers']}{submissions_ws.row_count}"
    )

    a1_ranges = [
        f"{spreadsheet['ranges']['ll_discord_ids']}{submissions_ws.row_count}",
        f"{spreadsheet['ranges']['ll_laps']}{submissions_ws.row_count}",
    ]

    ranges = submissions_ws.batch_get(
        a1_ranges,
        value_render_option="FORMULA"
    )

    total_laps = lap_count
    for i, row in enumerate(ranges[0]):
        if (
            row[0] == str(message.author.id) and 
            ll_round_numbers[i][0] == str(round_number)
        ):
            total_laps += int(ranges[1][i][0])

    ranges[0].append([
        str(message.author.id),
    ])

    ranges[1].append([
        str(lap_count),
    ])

    submissions_ws.batch_update(
        Support.ranges_to_dict(
            a1_ranges=a1_ranges,
            value_ranges=ranges
        ),
        value_input_option="USER_ENTERED"
    )

    await simple_bot_response(
        message.channel,
        title=f"**{'Logged' if lap_count > 0 else 'Deducted'} {lap_count} laps!**",
        description=f"You have logged a total of {total_laps} laps during Round {round_number}.",
        reply_message=message
    )
# end log_laps


async def reset_nicknames(message):

    msg = await message.channel.send("Resetting nicknames...")

    g = Support.get_g_client()
    wb = g.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()
    submissions_ws = Support.get_worksheet(
        ws, spreadsheet["submissions"]
    )
    gamertag_conversion = submissions_ws.get(
        f"{spreadsheet['ranges']['gamertag_conversion']}{submissions_ws.row_count}"
    )

    for i, row in enumerate(gamertag_conversion):

        if row[0]:

            # reset nickname if has driver role
            discord_id = int(row[0])
            user = discord.utils.find(
                lambda u: u.id == discord_id, message.guild.members
            )
            if user:
                if discord.utils.find(
                    lambda r: r.id == drivers_role_id, user.roles
                ):
                    try:
                        await user.edit(nick=row[1])
                    except discord.errors.Forbidden:
                        pass

        # if half way done, send message
        if i and i % (len(gamertag_conversion) / 2) == 0:
            await msg.edit(content=f"Resetting nicknames... {i}/{len(gamertag_conversion)}")

    await msg.delete()
    await Support.process_complete_reaction(message, remove=False)

# end reset_nicknames