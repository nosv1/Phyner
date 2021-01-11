# TODO #bot-spam !stream <link> !yt <link>
# TODO invalidate lap time
# TODO accept/reject signup

''' IMPORTS '''

from datetime import datetime
import discord
import asyncio
from pytz import timezone
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

# IDs
cotm_id = 527156310366486529

# CHANNELS
bot_stuff_id = 527168346404159488
signup_id = 796401927411728414
s7_leaderboard_id = 796786622191763487
quali_submit = 705787893364555785

# ROLES
children_id = 529112570448183296

# MESSAGES
# series_report_message_id = 791041462719873074

# EMOJIs
emojis = SimpleNamespace(**{
    "invalid" : "<:invalid:797893546295296011>",
})

drivers_per_div = 14
num_divs = 8


# Spreadsheets
spreadsheets = SimpleNamespace(**{
    "season_7" : SimpleNamespace(**{
        "key" : "1BIFN9DlU50pWOZqQrz4C44Dk-neDCteZMimTSblrR5U",
        "quali_submisisons" : 530052553,
        "quali" : 128540696,
        "signups" : 253796822,
    }),

    "season_6" : SimpleNamespace(**{
        "key" : "1WgGMgiUF4NVZyFCo-8DW2gnY3kwhXB8l02ov0Cp4pRQ",
        "roster" : 1284096187,
        "driver_history" : 744645833,
        "driver_stats" : 1734830265,
    }),
})

# embeds
# series_report_embed_link = "https://discord.com/channels/437936224402014208/519260837727436810/791050164067893329"

aliases = ["", ]



''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
    """

    args[0] = args[0].lower()

    if message.channel.id == bot_stuff_id: # in bot stuff
        
        if args[0] in ["!ct", "!tt"]: # !ct <race_time> <video.com> <screenshot.com>
            await submit_time(message, args)

        if args[0] == "!signup": # !signup <gamertag>
            await request_signup(message, args)


    elif message.channel.id in signup_id: # signup
        
        if not author_perms.administrator:
            await simple_bot_response(message.channel,
                description="**Only `!signup <gamertag>` messages can be sent in this channel.**",
                delete_after=10
            )
            await message.delete()


    elif message.channel.id in quali_submit:
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


def get_season_6_stats(user_id, gc=None):
    """
    """

    if not gc:
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


## SIGNUP ##

async def request_signup(message, args):
    """
    """
    await message.channel.trigger_typing()
    now = timezone("UTC").localize(datetime.utcnow()).astimezone(timezone("Europe/London"))

    if not args[1]: # no gamertag
        await simple_bot_response(message.channel,
            description="**Include your gamertag when using the command.**\n\n`!signup <gamertag>`",
            reply_message=message
        )
        return


    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()
    signups_ws = Support.get_worksheet(ws, spreadsheets.season_7.signups)
    signups = signups_ws.get(f"A1:C{signups_ws.row_count}")


    # get gt
    gt = re.sub(r'[<>]', '', ' '.join(args[1:])).strip()
    await message.author.edit(nick=gt)


    # update
    signups.append([str(now), str(message.author.id), gt])
    signups_ws.update(f"A1:C{signups_ws.row_count}", signups, value_input_option="USER_ENTERED")


    embed = await simple_bot_response(message.channel, send=False)
    embed.title = f"**#{len(signups)-1} - {gt} - Signup Pending Approval**"

    # stats = get_season_6_stats(args[1])
    stats = get_season_6_stats(message.author.id, gc)

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

    log("cotm", embed.to_dict())
# end request_signup


async def unsignup_user(): # TODO !unsignup @user
    """
        !unsignup @user
    """
    pass
# end unsignup_user



## QUALIFYING ##

async def invalid_time(message, time):
    """
    """

    await simple_bot_response(message.channel,
        description=f"**`{time}` is not a valid time.**\n```mm:ss.000 >> 1:23.456```",
        reply_message=message
    )
# end invalid_time


async def no_proof(message, quali_type):
    """
        quali type should be ct or tt
    """
 
    description = "There was no proof found in your message."

    if quali_type == "ct":
        description += f"```!ct <race-time> <last-lap-video.com> <screenshot.com>```"

    elif quali_type == "tt":
        description += f"```!tt <lap-time> <screenshot.com>```"

    await simple_bot_response(message.channel,
        title="No Proof!",
        description=description,
        reply_message=message
    )
# end no_proof


async def submit_time(message, args):
    """
        !ct <race_time> <last-lap-video.com> <screenshot.com>
        !tt <lap_time> <screenshot.com> [video.com]
    """
    await message.channel.trigger_typing()

    now = timezone("UTC").localize(datetime.utcnow()).astimezone(timezone("Europe/London"))


    ct = args[0] == "!ct"
    tt = args[0] == "!tt"


    args += ["", ""]
    

    # get race time
    race_time = re.findall(r"[2-4][0-9]:[0-5]\d.\d{3}", args[1]) if ct else None
    lap_time = re.findall(r"[1-3]:[0-5]\d.\d{3}", args[1]) if tt else None

    time = None
    if ct and not race_time or tt and not lap_time:
        await invalid_time(message, args[1])
        return

    else:
        time = race_time[0] if ct else lap_time[0]


    # get proof
    proof = [re.sub(r"[<>]", "", a) for a in args[2:4] if validators.url(re.sub(r"[<>]", "", a))]

    if not message.attachments:

        if not any(proof): # no proof
            await no_proof(message, args[0][1:])
            return

    else:
        proof.append(message.attachments[0].url)
    proof += ["", "", ""]


    # get gt
    gt = re.sub(rf"^\[D[1-{num_divs}]\]\s{1}", "", message.author.display_name)


    msg = None
    attempt_count = 0
    while True:

        try:
            # get the sheet

            g = Support.get_g_client()
            wb = g.open_by_key(spreadsheets.season_7.key)
            ws = wb.worksheets()
            quali_submissions_ws = Support.get_worksheet(ws, spreadsheets.season_7.quali_submisisons)
            quali_ws = Support.get_worksheet(ws, spreadsheets.season_7.quali)

            
            a1_ranges = [
                f"A1:B{quali_submissions_ws.row_count}",
                f"D1:H{quali_submissions_ws.row_count}"
            ]

            ranges = quali_submissions_ws.batch_get(a1_ranges, value_render_option="FORMULA")


            # set the values
            
            ranges[0].append([
                str(now), # timestamp
                str(message.author.id) # discord id
            ])

            ranges[1].append([
                args[0][1:], # quali type
                str(time), # race time
                (f'=HYPERLINK("{proof[0]}", "video?")' if proof[0] else ""), # proof video
                (f'=HYPERLINK("{proof[1]}", "ss?")' if proof[1] else ""), # proof ss
                (f'=HYPERLINK("{proof[2]}", "mystery?")' if proof[2] else "") # proof attch
            ])


            # update
            quali_submissions_ws.batch_update(Support.ranges_to_dict(a1_ranges=a1_ranges, value_ranges=ranges), value_input_option="USER_ENTERED")


            # get time details from quali sheet
            leaderboard = quali_ws.get(f"B4:H{quali_ws.row_count}" if ct else f"J4:O{quali_ws.row_count}")
            
            _i, row, _j = Support.find_value_in_range(leaderboard, gt, get=True)
            row += ["", "", ""] # in case time is leader

            div = row[1]
            pts = row[1]


            # prepare
            footer = f"Submission " # Submission 0-0-0 • %d %b %I:%M%p %Z 
            footer += str(len([row[1] for row in ranges[0] if str(row[1]) == str(message.author.id)])) + "-"# count discord ids
            footer += str(len([row[0] for row in ranges[1] if row[0] in args[0]])) + "-"# total ct submissions
            footer += str(len(ranges[0]) - 1) # total submissions

            footer += f" {Support.emojis.bullet} "

            formatted_timestamp = now.strftime(Support.smart_day_time_format("{S} %b %I:%M%p %Z", now))
            footer += formatted_timestamp.replace("AM ", "am ").replace("PM ", "pm ").replace(" 0", " ")

                
            # send it
            embed = await simple_bot_response(message.channel,
                title=f"**{gt} - {'Consistency Test' if ct else 'Time-Trial'} Submitted**",
                footer=footer,
                send=False
            )

            if ct:
                div_role = [r for r in message.guild.roles if r.name == f"Division {div}"][0]
                embed.color = div_role.color


            # details
            value = f"```{'Race' if ct else 'Lap'} Time: {time}\n"

            if ct:
                value += f"Division: {div}\n"
            elif tt:
                value += f"Points: {pts}\n"

            value += f"Position: {row[0]}{Support.num_suffix(int(row[0]))}"

            if ct:
                value += f" / {row[0]}{Support.num_suffix(int(row[0]) % 14)}"

            value += "```"

            value += f"[spreadsheet](https://docs.google.com/spreadsheets/d/1BIFN9DlU50pWOZqQrz4C44Dk-neDCteZMimTSblrR5U/edit#gid=128540696&range={'D' if ct else 'L'}{int(row[0])+2}) {Support.emojis.bullet} {' '.join(f'[proof_{i+1}]({p})' for i, p in enumerate(proof) if p)}"

            embed.add_field(name="**Details**", value=value)


            # gaps
            value = f"```To Leader: {row[4]}\n"

            if ct:
                value += f"To Div Leader: {row[5]}\n"

            value += f"To Driver Ahead: {row[6]}```"
            value += f"<#{s7_leaderboard_id}>"
            embed.add_field(name="**Gaps**", value=value)


            if not msg:
                msg = await message.channel.send(embed=embed)
            else:
                await msg.edit(embed=embed)

            await msg.add_reaction(emojis.invalid)


            if ct:
                await update_division(message.guild.roles, div, message.author, gt)

                children_role = message.guild.get_role(children_id)
                if children_role not in message.author.roles:
                    await message.author.add_roles(children_role)

            log("cotm", embed.to_dict())
            break


        except Support.gspread.exceptions.APIError:

            attempts = [60, 180, 300]

            log("cotm", f"ct quali submission failed, trying again in {attempts[attempt_count]} seconds")

            try:
                embed = await simple_bot_response(message.channel,
                    description=f"**There were technical difficulties whilst submitting. Trying again in {attempts[attempt_count]} seconds.**",
                    send=False
                )

                if not msg:
                    msg = await message.reply(embed=embed)
                else:
                    await msg.edit(embed=embed)

                attempt_count += 1

                await asyncio.sleep(attempts[attempt_count])

            except IndexError:
                log("cotm", "ct quali submission failed")

                embed = await simple_bot_response(message.channel,
                    description=f"**Could not submit your time. Try again later.**"
                )
                await msg.edit(embed=embed)
    # end while 
# end submit_consitency_test



## SUPPORT ##
async def update_division(roles, div, user, gt):
    """
        add role
        edit name
        send message in div channel
    """

    for role in user.roles: # remove div roles
        if re.findall(r"^Division \d$", role.name):
            await user.remove_roles(role)


    div_role = discord.utils.find(lambda r: r.name == f"Division {div}", roles)
    await user.add_roles(div_role)
    await user.edit(nick=f"[D{div}] {gt}")

    # TODO send message in div channel

# end update_division