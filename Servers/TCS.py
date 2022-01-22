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
# import scipy.optimize as opt


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
rival_selection_log_id = 929154488143581245
rivalry_log_id = 929154488143581245

# SPREADSHEET
spreadsheet = {
    "key": "1ecoU0lL2gROfneyF6WEXMJsM11xxj8CZ9VgMNdoiOPU",
    "leaderboards": 2120696652,
    "time_trial_submissions": 1968167541,
    "home": 1367712203,
    "leaderboards": 2120696652,
    "ranges": {
        # time trial submisisons
        "round_numbers": "F4:F",  # round numbers
        "gamertag_conversion": "H4:J",  # discord_id, gamertag, avail
        "rivals": "K4:K",  # rival_gamertag

        # leaderboards
        "avg_tt_pace_vs_field": "B4:D",  # pos, gamertag, pace v field
        "time_trial": "B6:G",  # pos, race?, gamertag, lap time, delta, pace v field
        "starting_order": "K6:O",  # pos, lby, gamertag, lap time, start time

        # round sheet
        "time_trial_times": "D7:E", # gamertag, lap_time
    }
}
spreadsheet_link = "https://docs.google.com/spreadsheets/d/1ecoU0lL2gROfneyF6WEXMJsM11xxj8CZ9VgMNdoiOPU/edit#gid=1367712203"

# MESSAGES
rival_selection_msg_id = 927758552955748404


''' FUNCTIONS '''

async def main(client, message, args, author_perms):

    args[0] = args[0].lower()
    in_bot_stuff = message.channel.id == bot_stuff_id
    in_tt_submit = message.channel.id == tt_submit_id

    if args[0] == "!test" and in_bot_stuff:
        # await pvf_to_lap_time(message, args)

        pass

    elif args[0] == "!pvf":
        # await pvf_to_lap_time(message, args)
        pass

    elif args[0] == "!tt" and (in_bot_stuff or in_tt_submit):
        await tt_submit(client, message, args)

    elif args[0] == "!update" and in_bot_stuff:

        g = Support.get_g_client()
        wb = g.open_by_key(spreadsheet["key"])
        ws = wb.worksheets()

        round_sheet = [sheet for sheet in ws if sheet.title == args[1]][0]
        
        time_trial_title = round_sheet.get("B5")[0][0]
        starting_order_title = round_sheet.get("K5")[0][0]
            
        await update_discord_tables(
            client,
            round_sheet.get(
                f"{spreadsheet['ranges']['time_trial']}{round_sheet.row_count}"
            ),
            "time_trial",
            time_trial_title,
            purge=True
        )
        await update_discord_tables(
            client,
            round_sheet.get(
                f"{spreadsheet['ranges']['starting_order']}{round_sheet.row_count}"
            ),
            "starting_order",
            starting_order_title
        )

    elif args[0] == "!staggered":
        await generate_staggered_start(message, args)
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



async def update_discord_tables(client: discord.Client, leaderboard: list, table_type: str, title: str, purge: bool = False):
    """
        leaderboard is [[row], ...]
    """

    if table_type == "time_trial":
        leaderboard[0][3] = leaderboard[0][3].replace("Lap Time", "Lap")
        leaderboard[0][5] = leaderboard[0][5].replace("Pace v Field", "PvF")

    else:
        leaderboard[0][4] = leaderboard[0][4].replace("Start Time", "Start")

    col_widths = Support.get_col_widths(leaderboard)

    channel = await client.fetch_channel(leaderboard_id)
    msg = None


    tt_headers = []
    starting_order_headers = []

    if table_type == "time_trial":
        tt_headers = [
            f"`{('[' + leaderboard[0][0] + ']').center(col_widths[0], ' ')}`", # pos
            f"`{('[' + leaderboard[0][2] + ']').ljust(col_widths[2], ' ')}`", # driver
            f"`{('[' + leaderboard[0][3] + ']').center(col_widths[3], ' ')}`", # lap time
            f"`{('[' + leaderboard[0][5] + ']').center(col_widths[5], ' ')}`", # pvf
        ]

    else:
        starting_order_headers = [
            f"`{('[' + leaderboard[0][0] + ']').center(col_widths[0], ' ')}`", # pos
            f"`{('[' + leaderboard[0][2] + ']').ljust(col_widths[2], ' ')}`", # driver
            f"`{('[' + leaderboard[0][4] + ']').center(col_widths[4], ' ')}`", # start time
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

            if not row or row[0] == "":
                exited = True
                break

            if table_type == "time_trial":

                line = [
                    f"{row[0]}".center(col_widths[0], " "),
                    f"{row[2]}".ljust(col_widths[2], " "),
                    f"{row[3]}".center(col_widths[3], " "),
                    f"{row[5]}".center(col_widths[5], " "),
                ]

            else:
                line = [
                    f"{row[0]}".center(col_widths[0], " "),
                    f"{row[2]}".ljust(col_widths[2], " "),
                    f"{row[4]}".center(col_widths[4], " "),
                ]

            table.append(line)

            table[-1] = " ".join([f"`{c}`" for c in table[-1]])

        if table:

            embed = await simple_bot_response(
                channel,
                description="\n".join(table),
                send=False
            )

            if i == 0:
                embed.title = title

            await channel.send(embed=embed)

        if exited:
            break

        table = []
# end update_discord_tables


async def update_rivalry_log(client: discord.Client, rivarly_log: discord.TextChannel, driver_user: discord.User, lap_time: str):

    g = Support.get_g_client()
    wb = g.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()
    time_trial_submissions_ws = Support.get_worksheet(
        ws, spreadsheet["time_trial_submissions"]
    )
    rivals = time_trial_submissions_ws.get(
        f"{spreadsheet['ranges']['rivals']}{time_trial_submissions_ws.row_count}"
    )
    gamertag_conversion = time_trial_submissions_ws.get(
        f"{spreadsheet['ranges']['gamertag_conversion']}{time_trial_submissions_ws.row_count}"
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
            time_trial_submissions_ws = Support.get_worksheet(
                ws, spreadsheet["time_trial_submissions"]
            )

            round_number = int(time_trial_submissions_ws.get("F3")[0][0][-2:])

            a1_ranges = [
                f"C4:C{time_trial_submissions_ws.row_count}",  # discord ids
                f"E4:E{time_trial_submissions_ws.row_count}",  # lap times
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

            round_numbers = time_trial_submissions_ws.get(
                f"{spreadsheet['ranges']['round_numbers']}{time_trial_submissions_ws.row_count}"
            )

            driver_submissions = []  # lap times in seconds
            driver_submission_history = f"**Round {round_number} | Submission history:**"
            for i, row in enumerate(ranges[0]):

                if row[0] == str(driver_id) and round_numbers[i][0] == str(round_number):
                    lap_time_str = ranges[1][i][0]
                    lap_time_seconds = int(lap_time_str[0]) * 60 + float(lap_time_str[2:])
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
                description=f"{driver_submission_history}\n\n[**Spreadsheet**]({spreadsheet_link}) <#{leaderboard_id}>",
                reply_message=message
            )

            
            round_sheet = [sheet for sheet in ws if sheet.title == f"R{round_number}"][0]
            
            time_trial_title = round_sheet.get("B5")[0][0]
            starting_order_title = round_sheet.get("K5")[0][0]
            
            await update_discord_tables(
                client,
                round_sheet.get(
                    f"{spreadsheet['ranges']['time_trial']}{round_sheet.row_count}"
                ),
                "time_trial",
                time_trial_title,
                purge=True
            )
            await update_discord_tables(
                client,
                round_sheet.get(
                    f"{spreadsheet['ranges']['starting_order']}{round_sheet.row_count}"
                ),
                "starting_order",
                starting_order_title
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

    lap_count = int(args[1])

    g = Support.get_g_client()
    wb = g.open_by_key(spreadsheet["key"])
    ws = wb.worksheets()
    time_trial_submissions_ws = Support.get_worksheet(
        ws, spreadsheet["time_trial_submissions"]
    )
    round_number = int(time_trial_submissions_ws.get("F3")[0][0][-2:])
    round_sheet = [sheet for sheet in ws if sheet.title == f"R{round_number}"][0]

    gamertag_conversion = time_trial_submissions_ws.get(f"{spreadsheet['ranges']['gamertag_conversion']}{time_trial_submissions_ws.row_count}")

    mentions = [m.id for m in message.mentions]
    gamertags = []
    for i, row in enumerate(gamertag_conversion):
        if int(row[0]) in mentions:
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

    try:
        target_pvf = float(target_pvf)

    except ValueError:
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
    time_trial_submissions_ws = Support.get_worksheet(
        ws, spreadsheet["time_trial_submissions"]
    )
    round_number = int(time_trial_submissions_ws.get("F3")[0][0][-2:])
    round_sheet = [sheet for sheet in ws if sheet.title == f"R{round_number}"][0]

    gamertag_conversion = time_trial_submissions_ws.get(f"{spreadsheet['ranges']['gamertag_conversion']}{time_trial_submissions_ws.row_count}")

    driver_gamertag = [row[1] for row in gamertag_conversion if row[0] == str(driver_id)]
    driver_gamertag = driver_gamertag[0] if driver_gamertag else None

    time_trial_times = round_sheet.get(f"{spreadsheet['ranges']['time_trial_times']}{round_sheet.row_count}")  # gamertag, lap_time

    # get all lap times except for driver lap time
    # when we calculate the target time, it needs to think it's a new driver
    lap_times = [row[1] for row in time_trial_times if row[0] != driver_gamertag]
    for i, lap_time in enumerate(lap_times):
        lap_times[i] = int(lap_times[i][0]) * 60 + float(lap_times[i][2:])

    avg_percent_diffs = get_avg_percent_diffs(lap_times)
    de_normalized_target_pvf = (
        target_pvf * 
        (avg_percent_diffs[0] - avg_percent_diffs[-1]) + 
        avg_percent_diffs[-1]  # [0] is max and [-1] is min
    )
    
    target_time = opt.brentq(lambda xi: f(xi, lap_times, len(lap_times), de_normalized_target_pvf), lap_times[0]-100, lap_times[-1]+100)

    # convert seconds to m:ss.000
    target_time = f"{int(target_time // 60)}:{target_time % 60:.3f}"
    
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
    time_trial_submissions_ws = Support.get_worksheet(
        ws, spreadsheet["time_trial_submissions"]
    )

    # loop avg tt pvf until no pos value given text below table on spreadsheet
    avg_tt_pace_vs_field = leaderboards_ws.get(f"{spreadsheet['ranges']['avg_tt_pace_vs_field']}{leaderboards_ws.row_count}")
    gamertag_conversion = time_trial_submissions_ws.get(f"{spreadsheet['ranges']['gamertag_conversion']}{time_trial_submissions_ws.row_count}")
    
    user_gamertag = [row[1] for row in gamertag_conversion if row[0] and int(row[0]) == user.id]
    user_gamertag = user_gamertag[0] if user_gamertag else None

    if not user_gamertag:
        await simple_bot_response(
            channel,
            title="**No gamertag found!**",
            description="You have not participated in a TT yet. You can select a rival next round."
        )
        return

    possible_rivals = []  # pos, driver, pace
    user_pace = None
    for i, row in enumerate(avg_tt_pace_vs_field):

        if row[1] != user_gamertag:
            racing = [
                r[2] for r in gamertag_conversion if r[1] == row[1]
            ][0]
            row.append(racing == "TRUE")
            possible_rivals.append(row)

        else:
            if i == 0:
                possible_rivals.append(avg_tt_pace_vs_field[i+1])
            user_pace = row[2]
            break

    description = "Beating your rival in the TT will give you a start-time deduction in this round's race - based on how many positions ahead your rival is; then, if you beat them in the race, you will get a fancy role for how many times you do so.\n\n"

    description += "Selecting a rival will ping them to let them know they've been chosen. If your rival does not plan to race, you will have the opportunity to pick a new rival.\n\n"

    description += f"**Select the position of the driver you would like to choose as your rival for the current round.**\n"


    embed_meta = "embed_meta/type=rivals/"

    for i, rival in enumerate(possible_rivals[-9:]):
        embed_meta += f"{Support.emojis.number_emojis[i+1]}={rival[1].replace(' ', '%20')}-{rival[2]}/"

        rival_line = f"{rival[1]} - {rival[2]}"

        if not rival[3]:
            rival_line = f"~~{rival_line}~~ (not racing)"

        description += f"{Support.emojis.space_char * 2}**{i+1}.** {rival_line}\n"
    
    description += f"{Support.emojis.space_char * 2}**{len(possible_rivals)+1}.** {user_gamertag} - {user_pace}\n\n"
    embed_meta += f"selector={user_gamertag.replace(' ', '%20')}-{user_pace}/"

    description += f"*The number to the right of the driver's name is their *Average TT Pace vs Field*; this number ranges from 1 to 0 and tries to evaluate how fast a driver typically is against a field."

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

        time_trial_submissions_ws = Support.get_worksheet(
            ws, spreadsheet["time_trial_submissions"]
        )

        gamertag_conversion = time_trial_submissions_ws.get(
            f"{spreadsheet['ranges']['gamertag_conversion']}{time_trial_submissions_ws.row_count}"
        )
        rivals = time_trial_submissions_ws.get(
            f"{spreadsheet['ranges']['rivals']}{time_trial_submissions_ws.row_count}"
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

        time_trial_submissions_ws.update(
            f"{spreadsheet['ranges']['rivals']}{time_trial_submissions_ws.row_count}",
            rivals
        )

        await msg.channel.delete()


    elif payload.emoji.name == Support.emojis.x_emoji:  # rival canceled

        await msg.clear_reactions()
        await prepare_rival_selection_channel(msg.channel, user, msg)
# end handle_rival_selection
