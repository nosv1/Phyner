''' IMPORTS '''

import asyncio
from datetime import datetime
import discord
# from matplotlib import pyplot as plt
# import matplotlib as mpl
# import numpy as np
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
cotm_id = 527156310366486529

# CHANNELS
bot_stuff_id = 527168346404159488
cotm_streams_id = 527161746473877504
quali_submit = 705787893364555785
s7_leaderboard_id = 796786622191763487
signup_id = 796401927411728414
start_orders_id = 622484589465829376
vote_id = 608472349712580608
voting_log_id = 530284914071961619
division_updates_id = 527319768911314944

div_channels = [
    527225908613087279,
    527225928712060938,
    527225947997601814,
    527225959745585161,
    527226003722862613,
    527226023146684427,
    527226036232912927,
    702658342669254676,
    800926709205434378, # waiting list
]

# ROLES
children_id = 529112570448183296
fetuses_id = 796357522536661033
peeker_id = 534230087244185601

# MESSAGES
consistency_test_leaderboard = [
    800211294271569952, # d1
    800211319214440468, # d2
    800211328403898399, # d3
    800211342191362068, # d4
    800211342921302056, # d5
    800211363023814696, # d6
    800211384582537247, # d7
    800211386701447209, # d8
    800211406070874143, # wl
]

time_trial_leaderboard = [
    800212112596008967,
    800212113247305788,
    800212113787191298,
    800212114605473802,
    800212115226361886,
    800212134713229312,
    800212135258357770,
    800212135812399104,
    800212136449015878,
]

start_order_msgs = [
    805657555682590751,
    805657556386578452,
    805657556671397909,
    805657557548138566,
    805657558199042099,
    805657577227681853,
    805657577929048135,
    805657578700668929,
    805657578868441179    
]

vote_msg_id = 807766191015067700
streams_msg_id = 819078511302017035

# EMOJIs
emojis = SimpleNamespace(**{
    "invalid_emoji" : "<:invalid:797893546295296011>",
    "youtube_emoji" : "<:Youtube:622139522502754304>",
    "twitch_emoji" : "<:Twitch:622139375282683914>",
    "mixer_emoji" : "<:Mixer:622139665306353675>",
})

division_emojis = [
  702654860801081474,
  702654861006602299,
  702654861065322526,
  702655539112443997,
  702654861086294086,
  702655538831425547,
  702654859983454318,
  702654860478251128,
  808444919701569647 # waiting list
]


drivers_per_div = 14
num_divs = 8


# SPREADSHEETS
spreadsheets = SimpleNamespace(**{
    "season_7" : SimpleNamespace(**{
        "key" : "1BIFN9DlU50pWOZqQrz4C44Dk-neDCteZMimTSblrR5U",
        "driver_history" : 744645833,
        "my_sheet" : 762852343,
        "quali_submisisons" : 530052553,
        "quali" : 128540696,
        "roster" : 1284096187,
        "signups" : 253796822,
        "start_orders" : 1636306417,
        "voting" : 242811195,
    }),

    "season_6" : SimpleNamespace(**{
        "key" : "1WgGMgiUF4NVZyFCo-8DW2gnY3kwhXB8l02ov0Cp4pRQ",
        "roster" : 1284096187,
        "driver_history" : 744645833,
        "driver_stats" : 1734830265,
    }),

    "driver_history" : SimpleNamespace(**{
        "key" : "1lbsKkpWdzBBc8i7zdstRmZyzY-SvafifuDlIlbwvLoQ", 
        "s6_stats" : 1668927625,
    }),
})

# EMBEDS
signup_conditions_link = "https://discord.com/channels/527156310366486529/527168346404159488/810052959836438529"

aliases = ["", ]



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
    """

    args[0] = args[0].lower()

    # TODO remember to move the commands from == bot_stuff_id: to proper if blocks

    if message.channel.id == bot_stuff_id: # in bot stuff

        if args[0] == "!updatedivs":
            await message.add_reaction(Support.emojis._9b9c9f_emoji)

            await update_divisions(message.guild)

            await Support.remove_reactions(message, Support.get_phyner_from_channel(message.channel), Support.emojis._9b9c9f_emoji)
            await Support.process_complete_reaction(message, remove=True)


        elif args[0] == "!updatequali":
            # get the sheet

            g = Support.get_g_client()
            wb = g.open_by_key(spreadsheets.season_7.key)
            ws = wb.worksheets()
            quali_submissions_ws = Support.get_worksheet(ws, spreadsheets.season_7.quali_submisisons)
            quali_ws = Support.get_worksheet(ws, spreadsheets.season_7.quali)
            await update_discord_leaderboard(client, quali_ws.get(f"J3:O{quali_ws.row_count}"), time_trial_leaderboard)
            await update_discord_leaderboard(client, quali_ws.get(f"B3:H{quali_ws.row_count}"), consistency_test_leaderboard)
            
        pass


    elif message.channel.id == signup_id: # signup

        if args[0] == "!signup": # !signup <gamertag>
            # await simple_bot_response(message.channel, description="```testing on PC```")
            await request_signup(client, message, args)
            return

        elif not author_perms.administrator: # deleting messages that aren't from staff

            await simple_bot_response(message.channel,
                description="**Only `!signup <gamertag>` messages can be sent in this channel.**",
                delete_after=10
            )
            await message.delete()


    elif message.channel.id == quali_submit and (datetime.utcnow() < datetime(2021, 4, 4, 22, 59, 59) or message.author.id == Support.ids.mo_id): # quali submit
        
        if args[0] in ["!ct", "!tt"]: # !ct <race_time> <video.com> <screenshot.com>
            await submit_time(client, message, args)
            
        pass

    
    # end channel specific commands
    
    if args[0] == "!license": # view license
        await display_license(message, args)


    elif args[0] == "!stream": # link stream
        await link_stream(message, args)


    elif args[0] in ["!compare", "!stats", "!history"]: # compare drivers' stats
        await compare_stats(client, message, args)


# end main


async def on_reaction_add(client, message, user, payload):

    remove_reaction = False
    embed = message.embeds[0] if message.embeds else None

    if embed:

        if embed.author:

            if embed.author.url:
                pass


        if embed.title:

            if (
                str(payload.emoji.id) in emojis.invalid_emoji and 
                re.findall(r"(((Time Trial)|(Consistency Test)) Submitted)", embed.title) and
                Support.get_member_perms(message.channel, user).administrator
            ): # invalid emojii clicked on submission
                await invalidate_time(client, message)


            elif (
                str(payload.emoji.name) in [e for e in Support.emojis.number_emojis[0:max_votes+1]] + [Support.emojis.counter_clockwise_arrows_emoji, Support.emojis.x_emoji, Support.emojis.tick_emoji]  and
                "Voting" in embed.title
            ): # number emoji or tick or x or refresch clicked on voting embed
                await handle_voting_reaction(message, payload, user)


            elif (
                "Signup Pending Approval" in embed.title and
                payload.emoji.name in [Support.emojis.tick_emoji, Support.emojis.x_emoji]
            ): # tick or x clicked on signup embed
                await handle_signup_reaction(message, user)
                return


            elif (
                "Streams" in embed.title and 
                payload.emoji.name == Support.emojis.counter_clockwise_arrows_emoji
            ): # refresh clicked on streams embed
                await update_streamers(message)
                remove_reaction = True

            
            elif "Reserves" in embed.title:
                remove_reaction = await handle_reserve_reaction(message, payload, user)


        if message.id in start_order_msgs:

            if payload.emoji.name == Support.emojis.counter_clockwise_arrows_emoji:
                await update_start_order(message, get_start_orders()[start_order_msgs.index(message.id)])

                remove_reaction = True


    return remove_reaction
# end on_reaction_add


async def on_reaction_remove(client, message, user, payload):
    '''
    '''

    embed = message.embeds[0] if message.embeds else None

    if embed:

        if embed.author:

            if embed.author.url:
                pass


        if embed.title:

            if "Reserves" in embed.title:
                if payload.emoji.name != Support.emojis.counter_clockwise_arrows_emoji:
                    await handle_reserve_reaction(message, payload, user, remove=True)
# end on_reaction_remove




## SIGNUP ##

async def request_signup(client, message, args):
    """
    """
    await message.channel.trigger_typing()


    msg = None
    def reaction_check(r, u):
        return (
            u.id == message.author.id and
            r.message.id == msg.id and
            str(r.emoji) == Support.emojis.tick_emoji
        )
    # end reaction_check


    await message.channel.trigger_typing()
    now = timezone("UTC").localize(datetime.utcnow()).astimezone(timezone("Europe/London"))

    if not args[1]: # no gamertag
        await simple_bot_response(message.channel,
            description="**Include your gamertag when using the command.**\n\n`!signup <gamertag>`",
            reply_message=message
        )
        return


    embed = Embeds.get_saved_embeds(link=signup_conditions_link)[0].embed # signup condition embed
    msg = await message.channel.send(embed=embed)

    await asyncio.sleep(5) # this matches the saved embed footer

    embed.set_footer(text="(120 seconds)")
    await msg.edit(embed=embed)
    await msg.add_reaction(Support.emojis.tick_emoji)


    try:
        reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120.0)
        await Support.clear_reactions(msg)

    except asyncio.TimeoutError:
        embed.set_footer(text=f"TIMED OUT - resend '{message.content}'")
        await msg.edit(embed=embed)
        await Support.clear_reactions(msg)
        return


    # user has accepted the terms
    await message.channel.trigger_typing()


    # get gt
    gt = re.sub(r'[<>]', '', ' '.join(args[1:])).strip()
    await message.author.edit(nick=gt)

    try:

        gc = Support.get_g_client()
        wb = gc.open_by_key(spreadsheets.season_7.key)
        ws = wb.worksheets()
        signups_ws = Support.get_worksheet(ws, spreadsheets.season_7.signups)
        signups = signups_ws.get(f"A1:C{signups_ws.row_count}")


        # update
        signups.append([str(now), str(message.author.id), gt])
        signups_ws.update(f"A1:C{signups_ws.row_count}", signups, value_input_option="USER_ENTERED")


        # stats = get_season_6_stats(args[1])
        stats = get_season_6_stats(message.author.id, gc)
    
    except: # just in case there is an error with getting the stats
        await Logger.log_error(client, traceback.format_exc())
        signups = []
        stats = 0


    embed = await simple_bot_response(message.channel, send=False)
    embed.title = f"**#{len(signups)-1} - {gt} - Signup Pending Approval**"

    if stats:
        embed.set_footer(text=f"S6 GT: {stats.gt} | ID: {message.author.id}")

        v = f"```Starts: {stats.starts}\n"
        v += f"Finishes: {stats.finishes}\n"
        v += f"DNSs: {stats.dnss}\n"
        v += f"Reserves: {stats.reserves}```\n"
        embed.add_field(name="**S6 Attendance**", value=v)

        v = f"```Best 5: Top {stats.best_5} {f'(D{int(float(stats.best_5[:-1]) / 100 * 8)+1})' if stats.best_5 else ''}\n"
        v += f"Quali: Top {stats.quali} {f'(D{int(float(stats.quali[:-1]) / 100 * 8)+1})' if stats.quali else ''}\n"
        v += f"Points: Top {stats.pts} {f'(D{int(float(stats.pts[:-1]) / 100 * 8)+1})' if stats.pts else ''}\n"
        v += f"Avg Dif: {stats.avg_dif}```\n"
        embed.add_field(name="**S6 Performance**", value=v)


    else:
        embed.description = f"```S6 Stats Not Found{' (error)' if stats == 0 else ''}```"
        embed.set_footer(text=f"ID: {message.author.id}")


    await msg.edit(embed=embed)
    await msg.add_reaction(Support.emojis.tick_emoji)
    await msg.add_reaction(Support.emojis.x_emoji)

    log("cotm", embed.to_dict())
# end request_signup


async def handle_signup_reaction(msg, user):
    """
    """
    
    threshold = 2 # at least 2 staff members hits tick, accepts signup (account for phyner reaction)


    embed = msg.embeds[0].to_dict()


    reactions = msg.reactions
    for reaction in reactions:
        count = 0

        async for user in reaction.users():

            if user.id == Support.ids.phyner_id: # is phyner
                continue

            if Support.get_member_perms(msg.channel, user).administrator: # is staff
                count += 1

                if str(reaction.emoji) == Support.emojis.tick_emoji:

                    if count != threshold:
                        continue

                    else:
                        embed["title"] = embed["title"].replace("Signup Pending Approval", "Signup Accepted")
                        embed["color"] = Support.colors.bright_green

                        member = msg.guild.get_member(int(embed["footer"]["text"].split("ID:")[1].strip()))

                        fetuses_role = [r for r in msg.guild.roles if r.id == fetuses_id][0]

                        await member.add_roles(fetuses_role)
                        log("cotm", "signup accepted")

                        break


                elif str(reaction.emoji) == Support.emojis.x_emoji:

                    if count == threshold:
                        embed["title"] = embed["title"].replace("Signup Pending Approval", "Signup Rejected")
                        embed["color"] = Support.colors.red
                        log("cotm", "signup rejected")

                        break


    await msg.edit(embed=discord.Embed().from_dict(embed))

# end handle_signup_reaction


async def unsignup_user(): # TODO !unsignup @user
    """
        !unsignup @user
    """
    pass
# end unsignup_user


async def link_stream(message, args):
    """
    """

    wb = Support.get_g_client().open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()
    
    roster_ws = Support.get_worksheet(ws, spreadsheets.season_7.roster)
    roster = roster_ws.range(f"D4:G{roster_ws.row_count}")
    i, _, __ = Support.find_value_in_range(roster, message.author.id)

    if i < 0:
        await simple_bot_response(message.channel,
            description=f"**You cannot link your stream channel if you have not signed up to the event.**\n\n<#{signup_id}>\n`!signup <gamertag>`",
            reply_message=message
        )
        return
        
    args[-2] = re.sub(r"[<>]", "", args[-2])
    if validators.url(args[-2]):

        roster[i+3].value = args[-2] # update stream link

        for i, c in enumerate(roster):

            if c.col in [4, 6]: # discord id col or div col
                roster[i].value = ""

            

        roster_ws.update_cells(roster, value_input_option="USER_ENTERED")

        await simple_bot_response(message.channel,
            title="**Stream Linked**",
            description=f"<#{cotm_streams_id}> is automatically updated based on the races streamers are in."
        )

        await update_streamers(await message.guild.get_channel(cotm_streams_id).fetch_message(streams_msg_id))

    else:
        await simple_bot_response(message.channel,
            description=f"**`{args[-2]}` is not a valid link.**\n\n`!stream https://twitch.tv/moshots`\nlink can also be your YouTube channel's link",
            reply_message=message
        )
        return
# end link_stream



## STREAM ##

def get_streamers():
    '''
    '''

    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()
    roster_ws = Support.get_worksheet(ws, spreadsheets.season_7.roster)

    
    a1_ranges = [
        f"C4:D{roster_ws.row_count}", # gt, discord_id
        f"G4:G{roster_ws.row_count}" # link
    ]

    ranges = roster_ws.batch_get(a1_ranges)
    
    streamers = [] # [[gt, discord_id, link], ...]

    for i, link in enumerate(ranges[1]): # loop through links

        if link: # is streamer
            streamers.append([ranges[0][i][0], ranges[0][i][1], link[0]])


    log("COTM", f"Received Streamers: {streamers}")
    return streamers
# end get_streamers


async def update_streamers(streams_msg):
    '''
    '''

    await streams_msg.add_reaction(Support.emojis._9b9c9f_emoji)

    streamers = get_streamers() # [[gt, discord_id, div, link], ...]


    embed = streams_msg.embeds[0].to_dict()

    multi_streams = []

    for i, field in enumerate(embed["fields"]):

        embed["fields"][i]["value"] = [] # sotring in list for now, will join to \n string later

        multi_streams.append([])


    for streamer in streamers:

        emoji = ""

        if "twitch" in streamer[-1].lower():
            emoji = emojis.twitch_emoji

        elif "youtube" in streamer[-1].lower():
            emoji = emojis.youtube_emoji

        elif "mixer" in streamer[-1].lower():
            emoji = emojis.mixer_emoji

        if streamer[-1]:

            member = streams_msg.guild.get_member(int(streamer[1]))

            member_divs = []

            try:

                for role in member.roles:

                    if "Division" in role.name:

                        div = int(role.name[-1])

                        if div not in member_divs: # in case some how has two of same div role :shrug:
                            
                            member_divs.append(div)


                for div in member_divs:

                    embed["fields"][div-1]["value"].append(f"{Support.emojis.space_char}[{member.display_name}]({streamer[-1]})") # [name](link)

                    if emoji == emojis.twitch_emoji:

                        multi_streams[div-1].append(streamer[-1].split(".tv/")[1].split("/")[0]) # https://twitch.tv/moshots -> moshots
            
            except AttributeError: # member is none (not in server)
                continue


    for i, field in enumerate(embed["fields"]):

        if field["value"]: # streamers in div

            embed["fields"][i]["value"] = "\n".join(field["value"])


            if multi_streams[i]: # ttv profiles avail

                multi_stream = "https://multistre.am/" + "/".join(multi_streams[i])

                embed["fields"][i]["value"] += f"\n[multi-stream]({multi_stream})\n{Support.emojis.space_char}"


        else: # no streamers

            embed["fields"][i]["value"] = Support.emojis.space_char

    
    await streams_msg.edit(embed=discord.Embed().from_dict(embed))

    await Support.remove_reactions(streams_msg, streams_msg.author, Support.emojis._9b9c9f_emoji)


    log("COTM", "Streams Message Updated")

# end update_streamers



## LICENSE ##

def get_license(gt, wb=Support.get_g_client().open_by_key(spreadsheets.season_7.key), ws=None, driver_history_ws=None):
    """
        gt should be exact
    """

    if not driver_history_ws:
        driver_history_ws = Support.get_worksheet(ws if ws else wb.worksheets(), spreadsheets.season_7.driver_history)    

    driver_history = driver_history_ws.get("C4:P")

    i, row, j = Support.find_value_in_range(driver_history, gt, get=True)

    if row:
        return SimpleNamespace(**{
            "gt" : row[0],
            "starts" : row[1],
            "finishes" : row[2],
            "dnss" : row[3],
            "reserves" : row[4],
            "penalty_time" : row[5],
            "penalty_points" : row[6],
            "best_4" : row[7], # Average of overall positions of best 5 races # Finish Position Overall / Number of Drivers
            "division" : row[8],
            "points" : row[10], # avg dif of best 5 to quali to pts
            "points_as_reserve" : row[13]
        })

    else:
        return None
# end get_license


async def display_license(message, args):
    """
    """

    await message.channel.trigger_typing()

    user = message.mentions[0] if message.mentions else message.author
    gt = get_gt(user.id)

    license = get_license(gt)

    if not license:
        await simple_bot_response(message.channel,
            description=f"**{user.mention} has not signed up for Season 7.**",
            reply_message=message
        )
        return

    embed = discord.Embed(color=Support.colors.phyner_grey)

    embed.title = f"**{gt}'s COTM License**"
    embed.set_thumbnail(url=user.avatar_url)


    value = "```"
    value += f"Starts: {license.starts}\n"
    value += f"Finishes: {license.finishes}\n"
    value += f"DNSs: {license.dnss}\n"
    value += f"Reserves: {license.reserves}\n"
    value += "```"

    embed.add_field(name="**Attendance**", value=value)


    value = "```"
    value += f"Division: {license.division}\n"
    value += f"Points: {license.points}\n"
    value += f"Pts as Rsv: {license.points_as_reserve}\n\n"

    value += f"Penalty Sec: {license.penalty_time}\n"
    value += f"Penalty Pts: {license.penalty_points}\n"
    value += "```"

    embed.add_field(name="**Performance**", value=value)

    await message.channel.send(embed=embed)
# end display_license



## COMPARE STATS ##

async def compare_stats(client, message, args):
    '''
        !compare/history/stats @driver ...
        !... @division
    '''

    log("COTM", f"Compare Stats {message.author.id}, '{message.content}'\n")

    await message.channel.trigger_typing()


    # get list of members 

    members = message.mentions # starter list of members to compare

    for role in message.role_mentions: # only div roles

        if re.findall(r"(^Division \d$)", role.name): # if div role

            members += role.members

    members = list(set(members)) # remove duplicates


    # get the s7 history
    
    g = Support.get_g_client()
    wb = g.open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()

    signups_ws = Support.get_worksheet(ws, spreadsheets.season_7.signups)
    driver_history_ws = Support.get_worksheet(ws, spreadsheets.season_7.driver_history)

    signups = signups_ws.get("B2:C")
    gts = [get_gt(m.id, wb=wb, ws=ws, signups_ws=signups_ws, signups=signups) for m in members] # may contain Nones where driver has not signed up


    div_points_table = driver_history_ws.get("C3:P") # Drivers, Starts, Finishes, DNSs, RSVS, PS, PP, O Perf, C Div, L Div, C Pts, L Pts, PPR, Pts as Rsv
    rounds_table = driver_history_ws.get("Z3:DQ") # Div, SPOS, FPOS, Overall, Reserve, Best Lap, Total Time, PS, PP, CLSF, PTS, _

    driver_stats = {}

    for i, gt in enumerate(gts):

        if gt:

            row_i, row, col_j = Support.find_value_in_range(div_points_table, gt, get=True)
            
            if row: # driver has history

                driver_stats[gt] = {
                    'member' : members[i],
                    'rounds' : [rounds_table[row_i][j : j + 12] for j in range(0, len(rounds_table[row_i]), 12)], # split row into rounds
                    'stats' : div_points_table[row_i],

                    # per round stats
                    'divisions' : [],
                    'start_positions' : [],
                    'finish_positions' : [],
                    'reserves' : [],
                    'points' : [],
                    'color' : hex(random.randint(0, int(0xffffff))).replace("0x", "#").ljust(7, "0"), # divide range of colors by num gts + 2, use middle hexs as line colors
                }




    fig, div_ax = plt.subplots()
    s_pos_ax = f_pos_ax = div_ax.twinx()

    for driver in driver_stats:

        for i, round in enumerate(driver_stats[driver]["rounds"]):

            if round[-2] and len(round) > 2: # has points and round completed

                driver_stats[driver]["divisions"].append(int(round[0]))
                driver_stats[driver]["start_positions"].append(int(round[1]))
                driver_stats[driver]["finish_positions"].append(int(round[2]))
                driver_stats[driver]["reserves"].append(round[4])
                driver_stats[driver]["points"].append(int(round[10]))

            else:

                driver_stats[driver]["divisions"].append(0)
                driver_stats[driver]["start_positions"].append(0)
                driver_stats[driver]["finish_positions"].append(0)
                driver_stats[driver]["reserves"].append('')
                driver_stats[driver]["points"].append(0)
                
    max_div = 0
    max_rounds = 0
    num_rounds = 8

    for driver in driver_stats:

        m = max([int(d) for d in driver_stats[driver]['divisions'] if d])
        max_div = m if m > max_div else max_div

        while len(driver_stats[driver]["finish_positions"]) < num_rounds:
            driver_stats[driver]["finish_positions"].append(0)

        r = max([num_rounds-i for i, r in enumerate(driver_stats[driver]["finish_positions"][::-1]) if r])
        max_rounds = r if r > max_rounds else max_rounds


    for driver in driver_stats:

        div_ax.plot(driver_stats[driver]['divisions'][:max_rounds], color=driver_stats[driver]["color"])
        s_pos_ax.plot(driver_stats[driver]['start_positions'][:max_rounds], linestyle="dotted", color=driver_stats[driver]["color"])
        f_pos_ax.plot(driver_stats[driver]['finish_positions'][:max_rounds], linestyle="dashed", color=driver_stats[driver]["color"])


    log("COTM", f"Stats to Compare {driver_stats}")


    f_pos_ax.legend(("Start Pos.", "Finish Pos."), loc="upper left", bbox_to_anchor=(1.1, 1))
    div_ax.legend(tuple([gt for gt in driver_stats]), loc="upper left", bbox_to_anchor=(1.1, .85))

    div_ax.tick_params(axis='y')
    f_pos_ax.tick_params(axis='y')


    div_ax.set_xticks(range(0, max_rounds))
    div_ax.set_xticklabels(range(1, max_rounds + 1))
    div_ax.set_xlabel("Round")


    y_ticks = range(0, max_div+1)
    div_ax.set_yticks(y_ticks)
    div_ax.set_yticklabels(y_ticks)

    div_ax.set_ylabel("Division")
    f_pos_ax.set_ylabel(f"Start/Finish Position", rotation=270, labelpad=10)


    plt.savefig("COTM_graph.png", facecolor=fig.get_facecolor(), transparent=True, bbox_inches="tight")
    plt.close()

    with open("COTM_graph.png", "rb") as graph:
        attachment_url = await Support.save_image_to_random_storage(client, file=discord.File(graph))
    os.remove("COTM_graph.png")


    embed = await simple_bot_response(message.channel, title="**__Season 7 Stats__**", send=False)

    for driver in driver_stats:

        value = ""
        value += f"Starts: {driver_stats[driver]['stats'][1]}\n"
        value += f"Finishes: {driver_stats[driver]['stats'][2]}\n"
        value += f"DNSs: {driver_stats[driver]['stats'][3]}\n"
        value += f"Rsvs: {driver_stats[driver]['stats'][4]} {', '.join([f'R{i+1}' for i, _ in enumerate(driver_stats[driver]['reserves']) if _])}\n"
        value += f"Div: {driver_stats[driver]['stats'][-6]}\n"
        value += f"Points: {driver_stats[driver]['stats'][-4]}\n"

        embed.add_field(
            name=f"**{driver}**",
            value=f"```{value}```{Support.emojis.space_char}"
        )

    embed.set_image(url=attachment_url)


    await message.channel.send(embed=embed)


    



# end compare_stats




## VOTING ##

max_votes = 5

async def prepare_vote_channel(channel, source_embed):
    """
    """

    options = source_embed.to_dict()["fields"][0]["value"].split(Support.emojis.bullet)[1:5]
    options = [f'{Support.emojis.number_emojis[0]} {o.split(chr(10))[0].strip()}' for o in options] # [:0: Option #\n, ...]


    vote_type = re.sub(r"[*_]", "", source_embed.title) # removing **__ from title
    vote_type = "car" if "Car" in vote_type else "track"


    embed = await simple_bot_response(channel, send=False)

    embed.title = "__**Voting**__"
    embed.add_field(name="**Options**", value="\n".join(options))

    embed.description = "To receive eligibility to vote, please post your screenshot of the playlist results below. You will be pinged when you may continue."


    msg = await channel.send(embed=embed)
    await msg.add_reaction(Support.emojis.counter_clockwise_arrows_emoji)


    if vote_type == "car":
        await reset_vote(msg)

    log("cotm vote", "vote channel prepared")
# end prepare_vote_channel


async def reset_vote(msg):
    """
    """
    
    await Support.clear_reactions(msg)


    embed = msg.embeds[0]


    embed.description = f"You have 5 votes to spend. You can spend all 5 on one option, or 3 on one and 2 on another, etc., but you must use all 5 votes.\n{Support.emojis.space_char}\n"

    embed.description += "To cast a vote for the current option, shown by the :arrow_left:, click one of the number buttons below. Once all 5 votes are spent, a :white_check_mark: will appear, and you will need to click it to submit your votes.\n\n"

    embed.description += f"To restart, click the :x:.\n{Support.emojis.space_char}"


    embed = embed.to_dict()

    options = []
    for o in embed["fields"][0]["value"].split("\n"):

        option = re.findall(r"(\[.*\]\(.*\))", o)[0]
        options.append(f"{Support.emojis.number_emojis[0]} {option}")

    options[0] += f" {Support.emojis.arrow_left_emoji}"
        

    del embed["fields"]
    embed = discord.Embed.from_dict(embed)
    embed.add_field(name="**Options**", value="\n".join(options))


    await msg.edit(embed=embed)
    [await msg.add_reaction(Support.emojis.number_emojis[i]) for i in range(0, max_votes+1)]
    await msg.add_reaction(Support.emojis.x_emoji)

    log("cotm vote", "vote reset")

# end reset_vote


async def handle_voting_reaction(msg, payload, user):
    """
    """

    log("cotm vote", f"{user} {payload.emoji.name}")

    user_perms = Support.get_member_perms(msg.channel, user)
    if (
        (
            payload.emoji.name == Support.emojis.counter_clockwise_arrows_emoji and user_perms.administrator
        ) or
        payload.emoji.name == Support.emojis.x_emoji
    ):
        await reset_vote(msg)
        return


    embed = msg.embeds[0].to_dict()


    options = embed["fields"][0]["value"].split("\n") # [:number: [option](link) :arrow:, ...]

    for i, o in enumerate(options): # get current counts
        o = o.split(" ")

        is_current_option = Support.emojis.arrow_left_emoji == o[-1]
        
        count = Support.emojis.number_emojis.index(o[0])

        try:
            count += Support.emojis.number_emojis.index(payload.emoji.name) if is_current_option else 0
            
        except ValueError: # non number clicked
            pass

        options[i] = [count, o[1:len(o) if not is_current_option else -1], is_current_option]

    # [[count, [option], is_current_option], ...] where option is a list of words from a .split(" ")


    votes_left = max_votes - sum(o[0] for o in options)


    if votes_left < 0: # somehow used more than allotted votes
        await reset_vote(msg)
        return


    elif votes_left == 0 and payload.emoji.name == Support.emojis.tick_emoji: # submit votes
        await msg.channel.trigger_typing()

        g = Support.get_g_client()
        wb = g.open_by_key(spreadsheets.season_7.key)
        ws = wb.worksheets()
        voting_ws = Support.get_worksheet(ws, spreadsheets.season_7.voting)

        r = voting_ws.get("C9:G", value_render_option="FORMULA")

        row_index, row, col_index = Support.find_value_in_range(r, user.display_name, get=True)

        if row: # duplicate vote
            await msg.channel.send(f"<@{Support.ids.mo_id}>, this guy tried to vote > 1 time.")
            return

        r.append([user.display_name] + [o[0] for o in options])

        voting_ws.update("C9:G", r, value_input_option="USER_ENTERED")

        await simple_bot_response(msg.channel,
            description="**Thank you for voting. :)**"
        )

        await asyncio.sleep(3)

        voting_log = msg.guild.get_channel(voting_log_id)
        embed = await simple_bot_response(voting_log,
            title="**__Vote Submitted__**",
            send=False
        )

        counts = "\n".join([f"{' '.join(o[1])} - **{o[0]}**" for o in options])
        embed.add_field(
            name=f"**{user.display_name}**", 
            value=f"{counts}\n{Support.emojis.space_char}"
        )


        totals = [0, 0, 0, 0]
        for vote in r[1:]:
            for i, v in enumerate(vote[1:]):
                totals[i] += int(v)

        totals = "\n".join([f"{' '.join(options[i][1])} - **{v}**" for i, v in enumerate(totals)])
        embed.add_field(
            name="**Totals**", 
            value=f"{totals}\n{Support.emojis.space_char}"
        )


        embed.add_field(
            name="**Total Votes**",
            value="".join([Support.emojis.number_emojis[int(c)] for c in str(len(r)-1)]),
            inline=False
        )


        await voting_log.send(embed=embed)


        vote = msg.guild.get_channel(vote_id)
        vote_msg = await vote.fetch_message(vote_msg_id)
        vote_embed = vote_msg.embeds[0].to_dict()
        vote_embed["fields"][-1] = embed.to_dict()["fields"][-1]

        await vote_msg.edit(embed=discord.Embed.from_dict(vote_embed))

        await msg.channel.delete()

        log("cotm vote", "vote submitted")
        return
        
    reactions_to_remove = []

    for reaction in msg.reactions: # remove vote buttons that exceed votes left

        try:

            if Support.emojis.number_emojis.index(str(reaction)) > votes_left or votes_left == 0:
                reactions_to_remove.append(reaction)

        except ValueError: # reaction was not a number emoji
            pass


    del embed["fields"]

    embed = discord.Embed.from_dict(embed)
    embed.add_field(name="**Options**", value="")
    embed = embed.to_dict()

    for i, o in enumerate(options):

        o = f"{Support.emojis.number_emojis[o[0]]} {' '.join(o[1])}" # :count: option
        o += f" {Support.emojis.arrow_left_emoji}" if options[i - 1][2] else '' # += :arrow_left_emoji:
        
        embed["fields"][0]["value"] += f"{o}\n"


    await msg.edit(embed=discord.Embed.from_dict(embed))

    await msg.remove_reaction(payload.emoji, user)
    await Support.remove_reactions(msg, msg.author, reactions_to_remove)

    if votes_left == 0:
        await msg.add_reaction(Support.emojis.tick_emoji)


    log("cotm vote", f"votes left: {votes_left}")

# end handle_voting_reaction



## QUALIFYING ##

async def invalid_time(message, time):
    """
    """

    await simple_bot_response(message.channel,
        description=f"**`{time}` is not a valid submission time.**\n```mm:ss.000 >> 1:23.456```",
        reply_message=message
    )
# end invalid_time


async def update_discord_leaderboard(client, leaderboard, message_ids):
    """
        leaderboard is [[row], ...]
    """

    col_widths = [0] * len(leaderboard[0] + [""])
    for i, row in enumerate(leaderboard):
        for j, value in enumerate(row):
            
            value = f"[{value}]" if i == 0 else value

            try:
                if len(value) > col_widths[j]:
                    col_widths[j] = len(value)

            except IndexError: # when leader, div, interval times are blank
                pass


    channel = await client.fetch_channel(s7_leaderboard_id)
    msg = None


    header = [
        f"`{('[' + leaderboard[0][0] + ']').center(col_widths[0], ' ')}`",
        f"`{('[' + leaderboard[0][1] + ']').center(col_widths[1], ' ')}`",
        f"`{('[' + leaderboard[0][2] + ']').center(col_widths[2], ' ')}`",
        f"`{('[' + leaderboard[0][3] + ']').center(col_widths[3], ' ')}`",
        # f"`{('[' + leaderboard[0][4] + ']').rjust(col_widths[4], ' ')}`", leader column toooo wide for discord
    ]

    if "Div" in leaderboard[0][1]:
        del header[1]

    header = [" ".join(header)]



    for m, m_id in enumerate(message_ids):
        table = [] + header

        for i, row in enumerate(leaderboard[1:][m*14:m*14+14]):

            line = [
                f"{row[0]}".center(col_widths[0], " "),
                f"{row[1]}".center(col_widths[1], " "),
                f"{row[2]}".ljust(col_widths[2], " "),
                f"{row[3]}".center(col_widths[3], " "),
            ]
            # ] + ([f"{row[4]}".rjust(col_widths[4], " ")] if col_widths[-1] != 0 else [])
            table.append(line) # in case it's a TT and not a CT update

            if "Div" in leaderboard[0][1]:
                del table[-1][1]

            table[-1] = " ".join([f"`{c}`" for c in table[-1]])
            
        msg = await channel.fetch_message(m_id)
        msg.embeds[0].description = "\n".join(table)
        await msg.edit(embed=msg.embeds[0])
        log("cotm leaderboard", f"updated {m}")
# end update_discord_leaderboard


async def no_proof(message, quali_type):
    """
        quali type should be ct or tt
    """
 
    description = "There was not enough proof found in your message."

    if quali_type == "ct":
        description += f"```!ct <race-time> <last-lap-video.com> <screenshot.com>```"

    elif quali_type == "tt":
        description += f"```!tt <lap-time> <screenshot.com>```"

    await simple_bot_response(message.channel,
        title="Not Enough Proof!",
        description=description,
        reply_message=message
    )
# end no_proof


async def submit_time(client, message, args):
    """
        !ct <race_time> <screenshot.com> <video.com>
        !tt <lap_time> <screenshot.com> [video.com]
    """
    await message.channel.trigger_typing()

    now = timezone("UTC").localize(datetime.utcnow()).astimezone(timezone("Europe/London"))


    ct = args[0] == "!ct"
    tt = args[0] == "!tt"


    args += ["", ""]
    

    # get race time
    race_time = re.findall(r"2[0-4]:[0-5]\d[.]\d{3}", args[1]) if ct else None
    lap_time = re.findall(r"2:[0-1]\d[.]\d{3}", args[1]) if tt else None

    time = None
    if (ct and not race_time) or (tt and not lap_time):
        await invalid_time(message, args[1])
        return

    else:
        time = race_time[0] if ct else lap_time[0]


    # get proof
    proof = [re.sub(r"[<>]", "", a) for a in args[2:4] if validators.url(re.sub(r"[<>]", "", a))]

    if message.attachments:
        for a in message.attachments:
            proof.append(a.url)

    if not proof or (ct and len(proof) < 2):
        await no_proof(message, args[0][1:])
        return
        
    proof += ["", "", ""]


    # get gt
    gt = re.sub(rf"^\[D[1-{num_divs}]\]\s{{1}}", "", message.author.display_name)


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
                str(time), # time
                (f'=HYPERLINK("{proof[0]}", "ss?")' if proof[0] else ""), # proof video
                (f'=HYPERLINK("{proof[1]}", "video?")' if proof[1] else ""), # proof ss
                (f'=HYPERLINK("{proof[2]}", "mystery?")' if proof[2] else "") # proof attch
            ])


            # update
            quali_submissions_ws.batch_update(Support.ranges_to_dict(a1_ranges=a1_ranges, value_ranges=ranges), value_input_option="USER_ENTERED")


            # get time details from quali sheet
            leaderboard = quali_ws.get(f"B3:H{quali_ws.row_count}" if ct else f"J3:O{quali_ws.row_count}")
            
            _i, row, _j = Support.find_value_in_range(leaderboard, gt, get=True)
            row += ["", "", ""] # in case time is leader

            div = row[1]
            pts = row[1]


            # prepare
            footer = f"Submission " # Submission 0.0.0.0 • %d %b %I:%M%p %Z 
            
            submission_counts = [
                str(len([i for i in range(len(ranges[0])) if str(ranges[0][i][1]) == str(message.author.id) and ranges[1][i][0] in args[0]])), # user specific
                str(len([i for i in range(len(ranges[0])) if str(ranges[0][i][1]) == str(message.author.id)])), # user
                str(len([i for i in range(len(ranges[0])) if ranges[1][i][0] in args[0]])), # total specific
                str(len(ranges[0])-1) # total
            ]
            footer += ".".join(submission_counts)

            footer += f" {Support.emojis.bullet} "

            formatted_timestamp = now.strftime(Support.smart_day_time_format("{S} %B %I:%M%p %Z", now))
            footer += formatted_timestamp.replace("AM ", "am ").replace("PM ", "pm ").replace(" 0", " ")

                
            # send it
            embed = await simple_bot_response(message.channel,
                title=f"**{gt} - {'Consistency Test' if ct else 'Time Trial'} Submitted**",
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

            value += f"Position: {Support.num_suffix(int(row[0]))}"

            if ct:
                value += f" / {Support.num_suffix(int(row[0]) % 14)}"

            value += "```"

            value += f"[spreadsheet](https://docs.google.com/spreadsheets/d/1BIFN9DlU50pWOZqQrz4C44Dk-neDCteZMimTSblrR5U/edit#gid=128540696&range={'D' if ct else 'L'}{int(row[0])+2}) {Support.emojis.bullet} {', '.join(f'[proof{i+1}]({p})' for i, p in enumerate(proof) if p)}"

            embed.add_field(name="**Details**", value=value)


            # gaps
            value = f"```To Leader: {row[4]}\n"

            if ct:
                value += f"To Div Leader: {row[5]}\n"

            value += f"To Driver Ahead: {row[5 if tt else 6]}```"
            value += f"<#{s7_leaderboard_id}>"
            embed.add_field(name="**Gaps**", value=value)


            if not msg:
                msg = await message.channel.send(embed=embed)
            else:
                await msg.edit(embed=embed)

            await msg.add_reaction(emojis.invalid_emoji)


            if ct:
                await update_divisions(message.guild, Support.get_worksheet(ws, spreadsheets.season_7.roster))

                children_role = message.guild.get_role(children_id)
                fetuses_role = message.guild.get_role(fetuses_id)
                peeker_role = message.guild.get_role(peeker_id)

                if children_role not in message.author.roles:
                    await message.author.add_roles(children_role)
                    await message.author.remove_roles(peeker_role)
                    await message.author.remove_roles(fetuses_role)
                    


            await update_discord_leaderboard(client, leaderboard, consistency_test_leaderboard if ct else time_trial_leaderboard)

            log("cotm", embed.to_dict())
            break


        except Support.gspread.exceptions.APIError:

            attempts = [60, 180, 300]

            log("cotm", f"ct quali submission failed, trying again in {attempts[attempt_count]} seconds")

            try:
                embed = await simple_bot_response(message.channel,
                    description=f"**There were technical difficulties whilst submitting - trying again in {attempts[attempt_count]} seconds.**",
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


async def invalidate_time(client, message):
    """
    """

    embed = message.embeds[0]
    embed.title = embed.title.replace("Submitted", "Invalidated")
    embed.color = 1
    embed.set_thumbnail(url=[e for e in message.guild.emojis if str(e.id) in emojis.invalid_emoji][0].url)


    await message.edit(embed=embed)
    await Support.clear_reactions(message)


    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()
    quali_submissions_ws = Support.get_worksheet(ws, spreadsheets.season_7.quali_submisisons)
    quali_ws = Support.get_worksheet(ws, spreadsheets.season_7.quali)


    quali_submissions = quali_submissions_ws.get("I1:I", value_render_option="FORMULA")


    submission_index = int(embed.footer.text.split(".")[-1].split(" ")[0])
    quali_submissions[submission_index][0] = "TRUE"


    quali_submissions_ws.update("I1:I", quali_submissions, value_input_option="USER_ENTERED")

    
    # get time details from quali sheet
    ct = "Consistency Test" in embed.title
    tt = "Time Trial" in embed.title
    gt = embed.title.split("-")[0].strip()
    leaderboard = quali_ws.get(f"B3:H{quali_ws.row_count}" if ct else f"J3:O{quali_ws.row_count}")

    await update_discord_leaderboard(client, leaderboard, consistency_test_leaderboard if ct else time_trial_leaderboard)

    log("cotm", embed.to_dict())
# end invalidate_time



## RESERVES ##

class R_Driver:

    def __init__(self, r_driver=None, type=None, div=None, date=None):
        '''
        '''

        self.r_driver = r_driver
        self.type = type # 0 is reservee, 1 is reserve
        self.div = div
        self.date = date
    # end __init__


    def __eq__(self, other):
        return (
            self.r_driver == other.r_driver and 
            self.div == other.div and 
            self.type == other.type and
            self.date == other.date
        )
    # end __eq__



    def to_string(self):
        return f"{self.r_driver}, {self.type}, {self.div}, {self.date}"
    # end to_string
# end Driver


async def remove_r_driver(user, type, div):
    '''
    '''

    db = Database.connect_database('COTM')

    db.cursor.execute(f"""
        DELETE FROM reserves
        WHERE
            `r_driver` = '{user.id}' AND
            `type` = '{type}' AND
            `div` = '{div}'
    """)

    db.connection.commit()
    db.connection.close()

    for role in user.roles:
        if role.name == f"Reserve Division {div}":
            await user.remove_roles(role)
    # end remove_r_driver


def insert_r_driver(driver_id, type, div):
    '''
    '''

    db = Database.connect_database('COTM')

    db.cursor.execute(f"""
        INSERT INTO reserves (
            `r_driver`, `type`, `div`, `date`
        ) VALUES (
            '{driver_id}', 
            '{type}',
            '{div}',
            '{(datetime.utcnow() - datetime(2021, 3, 26)).total_seconds()}'
        )
    """)

    db.connection.commit()
    db.connection.close()
# end insert_r_driver


def get_r_driver_from_entry(r):
    '''
    '''

    return R_Driver(
        r_driver=int(r[0]),
        type=int(r[1]), # 0 is reservee, 1 is reserve
        div=int(r[2]),
        date=float(r[3])
    )
# end get_driver_from_entry


def get_r_drivers():
    '''
    '''

    db = Database.connect_database(db_name="COTM")
    db.cursor.execute(f"""
        SELECT `r_driver`, `type`, `div`, `date` FROM reserves
    """) # type, 0 is reservee, 1 is reserve
    db.connection.close()

    r_drivers = db.cursor.fetchall()

    if r_drivers:
        r_drivers.sort(key=lambda x:float(x[3]))  # sorted based on click order, first to last

    return [get_r_driver_from_entry(r) for r in r_drivers]
# end get_r_drivers


async def handle_reserve_reaction(message, payload, user, remove=False):
    '''
    '''

    remove_reaction = False
    skip_start_order_update = False

    
    await message.add_reaction(Support.emojis._9b9c9f_emoji)


    if payload.emoji.name == Support.emojis.wave_emoji: # need reserve
        remove_reaction = await handle_need_reserve(message, user, remove=remove)


    elif payload.emoji.id in division_emojis: # reserve available
        remove_reaction = await handle_reserve_available(message, user, division_emojis.index(payload.emoji.id) + 1, remove=remove)


    elif payload.emoji.name == Support.emojis.counter_clockwise_arrows_emoji and user.id == Support.ids.mo_id: # refresh
        r_drivers = get_r_drivers()
        await update_reserves(message, generate_div_combos(r_drivers), r_drivers)
        remove_reaction = True


    elif payload.emoji.name == Support.emojis.x_emoji and user.id == Support.ids.mo_id: # clear

        if not remove:
            await clear_reserves(message)

        else:
            skip_start_order_update = True

        remove_reaction = True


    else: # not wave or div number
        skip_start_order_update = True
        remove_reaction = True


    await Support.remove_reactions(message, Support.get_phyner_from_channel(message.channel), Support.emojis._9b9c9f_emoji)


    # update start orders

    if not skip_start_order_update:

        start_orders_channel = message.guild.get_channel(start_orders_id)

        start_orders = get_start_orders()

        for i, start_order in enumerate(start_order_msgs):

            start_order_msg = await start_orders_channel.fetch_message(start_order)

            await update_start_order(start_order_msg, start_orders[i])


    return remove_reaction
# end reserve_reaciton


def generate_div_combos(r_drivers):
    '''
    '''

    # assign by first come first served first, then randomize

    divs = [[[], []] for d in range(num_divs)] # will be [[[d1_reservees, ...], [d1_reserves, ...]], ...]

    for r_driver in r_drivers:

        if r_driver.type: # is reserve
            divs[r_driver.div-1][1].append(r_driver)

        else:
            divs[r_driver.div-1][0].append(r_driver)

    div_combos = [list(zip(*div)) for div in divs] # [[(d1_reservee, d1_reserve), ...], ...]


    # randomize

    for i, div_combo in enumerate(div_combos):

        reservees = []
        reserves = []

        for combo in div_combo:
            reservees.append(combo[0])
            reserves.append(combo[1])

        random.shuffle(reserves)

        div_combos[i] = list(zip(*[reservees, reserves]))

    return div_combos # [[(d1_reservee, d1_reserve), ...], ...]
# end generate_combos


async def handle_need_reserve(message, user, remove=False):
    '''
    '''

    try:
        div = int(user.display_name.split("[D")[1].split("]")[0])

        old_r_drivers = get_r_drivers()

        if remove:
            await remove_r_driver(user, 0, div)

        else:
            insert_r_driver(user.id, 0, div)

        div_combos = generate_div_combos(get_r_drivers()) # [[(d1_reservee, d1_reserve), ...], ...]
        
        await update_reserves(message, div_combos, old_r_drivers)

    except IndexError: # Div couldn't be recognized
        return True # remove reaction
# end handle_need_reserve


async def handle_reserve_available(message, user, div, remove=False):
    '''
    '''

    def div_check(div, r_driver_div):
        '''
        '''

        if r_driver_div == "WL": # check spreadsheet for elgible reserve divs

            gc = Support.get_g_client()
            wb = gc.open_by_key(spreadsheets.season_7.key)
            ws = wb.worksheets()
            quali_ws = Support.get_worksheet(ws, spreadsheets.season_7.quali)

            ct_driver_divs = quali_ws.get("C4:D")
            row_i, row, col_i = Support.find_value_in_range(ct_driver_divs, get_gt(user.id, wb, ws), get=True)

            if row: # driver has completed CT
                r_driver_div = int(row[0]) if row[0] != "WL" else num_divs + 1
                return div in [r_driver_div - 1, r_driver_div, r_driver_div + 1] # div below, div, div above

        else:
            return div in [r_driver_div - 1, r_driver_div + 1] # div below, div above
    # end div_check


    embed = message.embeds[0].to_dict()

    try:
        r_driver_div = int(user.display_name.split("[D")[1].split("]")[0])

    except IndexError:
        r_driver_div = "WL" if "[WL]" in user.display_name else None


    if not r_driver_div: # not in a div/WL...
        return True

    if not div_check(div, r_driver_div): # not in an elgiible div compared to the div clicked
        return True


    old_r_drivers = get_r_drivers()


    if remove:
        await remove_r_driver(user, 1, div)

    else:
        insert_r_driver(user.id, 1, div)


    div_combos = generate_div_combos(get_r_drivers()) # [[(d1_reservee, d1_reserve), ...], ...]
    

    await update_reserves(message, div_combos, old_r_drivers)
# end handle_reserve_available


async def update_reserves(message, div_combos, old_r_drivers):
    '''
        div_combos = [[(d1_reservee, d1_reserve), ...], ...]
    '''


    has_reserve = [] # [reservee_id, ...]
    is_reserving = [[] for i in div_combos] # [[d1_reserve_id, ...], ...]


    # add roles

    for i, div_combo in enumerate(div_combos): # add reserve roles

        for combo in div_combo:

            reservee = message.guild.get_member(combo[0].r_driver)
            reserve = message.guild.get_member(combo[1].r_driver)

            log('COTM', f"{reserve.display_name} is reserving for {reservee.display_name} in {combo[0].div}")

            
            has_reserve.append(reservee.id) # storing for later when adding tick emojis next to name
            is_reserving[combo[1].div-1].append(reserve.id) # storing for later when checking to remove reserve roles


            reserve_role_name = f"Reserve Division {combo[1].div}"
            if reserve_role_name not in [r.name for r in reserve.roles]: # add role and send to channel
                
                await reserve.add_roles([r for r in message.guild.roles if r.name == reserve_role_name][0])


                for c in [div_channels[combo[1].div-1], division_updates_id]: # div and div updates channel

                    c = message.guild.get_channel(c)

                    await simple_bot_response(c,
                        content=reserve.mention,
                        description=f"**{reserve.display_name} is reserving for <:D{combo[1].div}:{division_emojis[combo[1].div-1]}>.**",
                    )

                log('cotm', 'message sent to div' + str(combo[1].div))


    old_div_combos = generate_div_combos(old_r_drivers)

    div_reservees = [[] for i in range(num_divs)]
    div_reserves = [[] for i in range(num_divs)]

    
    for old_r_driver in old_r_drivers: # get lists of reservees and reserves

        if old_r_driver.type == 0: # is reservee
            div_reservees[old_r_driver.div-1].append(old_r_driver)

        else: # is reserve
            div_reserves[old_r_driver.div-1].append(old_r_driver)

    
    # check if any reserves are no longer reserving

    for div_reserve in div_reserves: # looping all reserves avail

        for reserve in div_reserve: # looping reserves per div

            for i, old_div_combo in enumerate(old_div_combos):

                for combo in old_div_combo: # combos in div

                    if combo[1] == reserve: # was reserve in this div

                        still_reserve = False
                        
                        for combo in div_combos[i]: # looping new div combos

                            if combo[1] == reserve: # still reserving in div
                                still_reserve = True
                                break

                        if not still_reserve:

                            for c in [div_channels[combo[1].div-1], division_updates_id]: # div and div updates channel

                                c = message.guild.get_channel(c)

                                reserve_div_role = [r for r in message.guild.roles if r.name == f"Reserve Division {reserve.div}"][0]
                                
                                member = message.guild.get_member(reserve.r_driver)
                                await member.remove_roles(reserve_div_role)

                                await simple_bot_response(c,
                                    content=member.mention,
                                    description=f"**{member.display_name} is no longer reserving for <:D{combo[1].div}:{division_emojis[combo[1].div-1]}>.**",
                                )

                            log('cotm', 'message sent to div' + str(combo[1].div))

    
    # update spreadsheet

    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()

    my_sheet_ws = Support.get_worksheet(ws, spreadsheets.season_7.my_sheet)
    signups_ws = Support.get_worksheet(ws, spreadsheets.season_7.signups)
    reserves = my_sheet_ws.get(f"Q2:R")

    for i, r in enumerate(reserves):
        reserves[i] = ["" for c in r]


    count = 0 # index of reserves list

    for div_combo in div_combos: # loop new reserve combos

        for combo in div_combo: # loop combos in div

            if not reserves: # ss reserves was previously blank
                reserves.append(["", ""])

            elif reserves[-1][-1] != "": # more reserves than before
                reserves.append(["", ""])

            reserves[count][0] = get_gt(combo[0].r_driver, wb, ws, signups_ws)
            reserves[count][1] = get_gt(combo[1].r_driver, wb, ws, signups_ws)

            count += 1

    my_sheet_ws.update("Q2:R", reserves)


    # update reserve embed

    embed = message.embeds[0].to_dict()
    
    fields = [[] for i in range((len(embed["fields"])-2))] # empty the felds
    
    for r_driver in get_r_drivers(): # add drivers to fields

        if r_driver.type == 0: # needs reserve

            reservee = message.guild.get_member(r_driver.r_driver)

            fields[0].append(f"{reservee.display_name}{(' ' + Support.emojis.tick_emoji) if r_driver.r_driver in has_reserve else ''}") # [D#] Driver tick_emoji if has reserve

        else: # available to reserve

            reserve = message.guild.get_member(r_driver.r_driver)
            
            is_reserve = r_driver.r_driver in is_reserving[r_driver.div-1]            

            fields[r_driver.div].append(f"{reserve.display_name}{(' ' + Support.emojis.tick_emoji) if is_reserve else ''}") # [D#] Driver tick_emoji if reserving

    
    for i, f in enumerate(fields):
        embed["fields"][i]["value"] = "\n".join(f + [Support.emojis.space_char])


    await message.edit(embed=discord.Embed().from_dict(embed))
# end update_reserves


async def clear_reserves(message):
    '''
    '''

    r_drivers = get_r_drivers()


    # clear database

    db = Database.connect_database('COTM')
    db.cursor.execute(f"""
        DELETE FROM reserves
        WHERE id > 0
    """)
    db.connection.commit()
    db.connection.close()


    # clear reserve roles

    for r_driver in r_drivers: 

        if r_driver.type == 1: # potiential reserve

            member = message.guild.get_member(r_driver.r_driver)
            [await member.remove_roles(r) for r in member.roles if 'Reserve Division' in r.name]


    # clear spreadsheet

    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()

    my_sheet_ws = Support.get_worksheet(ws, spreadsheets.season_7.my_sheet)
    reserves = my_sheet_ws.range(f"Q2:R{my_sheet_ws.row_count}")

    for i in range(len(reserves)):
        reserves[i].value = ""

    my_sheet_ws.update_cells(reserves, value_input_option="USER_ENTERED")


    # clear embed

    embed = message.embeds[0].to_dict()
    
    for i in range(len(embed["fields"])-2):
        embed["fields"][i]["value"] = Support.emojis.space_char

    await message.edit(embed=discord.Embed().from_dict(embed))


    # clear reactions

    await message.clear_reactions()

    await message.add_reaction(Support.emojis.wave_emoji)

    for i in range(num_divs):
        await message.add_reaction([e for e in message.guild.emojis if e.id == division_emojis[i]][0])
# end clear_reserves



## START ORDERS ##

def get_start_orders():
    '''
    '''

    gc = Support.get_g_client()
    wb = gc.open_by_key(spreadsheets.season_7.key)
    ws = wb.worksheets()
    start_orders_ws = Support.get_worksheet(ws, spreadsheets.season_7.start_orders)

    
    a1_ranges = [
        f"B3:F31",
        f"H3:L31",
        f"N3:R31",
        f"T3:X31",
        f"Z3:AD31",
        f"AF3:AJ31",
        f"AL3:AP31",
        f"AR3:AV31",
        f"AX3:BB31",
    ]

    ranges = start_orders_ws.batch_get(a1_ranges) # D1-WL

    log("COTM", f"Received Start Orders: {ranges}")

    return ranges
# end get_start_orders


async def update_start_order(start_order_msg, start_order_range):
    '''
        start_order_range = [[pos, div, driver, reserve, ppr], ...]
    '''

    await start_order_msg.add_reaction(Support.emojis._9b9c9f_emoji)

    embed = start_order_msg.embeds[0]

    col_widths = [3, 0, 0] # pos, driver, reserve

    for driver in start_order_range:
        if len(driver[2]) > col_widths[1]:
            col_widths[1] = len(driver[2]) # driver name

        if len(driver[3]) > col_widths[2]:
            col_widths[2] = len(driver[3]) # reserve name
    

    start_order = []

    for driver in start_order_range:
        start_order.append(f"`{driver[0].rjust(col_widths[0], ' ')}` `{driver[2].ljust(col_widths[1])}` `{driver[3].ljust(col_widths[2])}`")


    embed.description = "\n".join(start_order)

    await start_order_msg.edit(embed=embed)

    await Support.remove_reactions(start_order_msg, start_order_msg.author, Support.emojis._9b9c9f_emoji)


    div = start_order_msgs.index(start_order_msg.id) + 1
    log("COTM", f"Updated Start Order {div}")
# end update_start_order




## SUPPORT ##

async def update_divisions(guild, roster_ws=None):
    '''
    '''

    log('cotm', 'Updating Divisions')

    if not roster_ws:
        wb = Support.get_g_client().open_by_key(spreadsheets.season_7.key)
        ws = wb.worksheets()
        
        roster_ws = Support.get_worksheet(ws, spreadsheets.season_7.roster)

    roster = roster_ws.get(f"C4:G{roster_ws.row_count}")

    
    div_channels = [c for c in guild.channels if re.findall(rf"(division-[1-{num_divs}])|(waiting-list)", c.name)]
    div_channels.sort(key=lambda x:x.name)
    div_roles = [r for r in guild.roles if re.findall(rf"(^Division [1-{num_divs}]$)|(^Waiting List$)", r.name)]

    for row in roster:
        
        member = [m for m in guild.members if row[1] == str(m.id)]

        if member: # member in server

            member = member[0]

            gt = row[0]
            div = row[3] if len(row) >= 4 else None

            member_div_role = [r for r in member.roles if r in div_roles]
            incorrect_role = None

            role_added = False

            if div:
                incorrect_role = (
                    member_div_role and (
                        (
                            member_div_role[0].name == "Waiting List" and 
                            div not in ['WL', 'CT']
                        ) or (
                            member_div_role[0].name != 'Waiting List' and
                            member_div_role[0].name[-1] != div
                        )
                    )
                )

            
                if (not member_div_role or incorrect_role): # needs role

                    div_role = [r for r in div_roles if r.name[-1] == div or (r.name == "Waiting List" and div in ["WL", "CT"])][0]

                    await member.add_roles(div_role)

                    if div != "CT":
                        await member.edit(nick=f"[{'D' + div if div != 'WL' else 'WL'}] {gt}")

                    else:
                        await member.edit(nick=gt)

                    role_added = True

                    div_name = f"D{div}" if div not in ['WL', 'CT'] else div
                    div = int(re.sub(r"(WL)|(CT)", str(len(division_emojis)), div))

                    await simple_bot_response(div_channels[div-1],
                        content=member.mention,
                        description=f"**{gt} was added to <:{div_name}:{division_emojis[div-1]}>.**",
                    )


                    log("cotm", f"{member.display_name} added to {div}")


            if incorrect_role or (member_div_role and not div): # has wrong role or has role and shouldn't

                await member.remove_roles(member_div_role[0])

                if not role_added: # gt was not udpated already
                    await member.edit(nick=gt)


                div_name = None
                if 'Division' in member_div_role[0].name:
                    div = int(member_div_role[0].name[-1])
                    div_name = f'D{div}'

                else:
                    div = len(division_emojis)
                    div_name = 'WL'
                
                await simple_bot_response(div_channels[div-1],
                    content=member.mention,
                    description=f"**{gt} was removed from <:{div_name}:{division_emojis[div-1]}>.**",
                )


                log("cotm", f"{member.display_name} removed from {div}")

    log("cotm", "Divisions Updated")
# end update_divisions


def get_gt(discord_id, wb=Support.get_g_client().open_by_key(spreadsheets.season_7.key), ws=None, signups_ws=None, signups=None):
    """
    """

    if not signups_ws:
        signups_ws = Support.get_worksheet(ws if ws else wb.worksheets(), spreadsheets.season_7.signups)

    if not signups:
        signups = signups_ws.get("B2:C")

    i, row, j = Support.find_value_in_range(signups, discord_id, get=True)

    if row:
        return row[1]
# end get_gt


def get_season_6_stats(user_id, gc=None):
    """
    """

    if not gc:
        gc = Support.get_g_client()

    wb = gc.open_by_key(spreadsheets.driver_history.key)
    worksheets = wb.worksheets()
    driver_stats_ws = [ws for ws in worksheets if ws.id == spreadsheets.driver_history.s6_stats][0]

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
            "avg_dif" : row[9] if len(row) >= 10 else '-', # avg dif of best 5 to quali to pts
        })

    else:
        return None
# end get_season_6_stats