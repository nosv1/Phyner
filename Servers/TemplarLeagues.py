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

                elif ( # series report verificaiton + tick_emoji button
                    "/id=templar_leagues_series_report_verification/" in embed.author.url and 
                    payload.emoji.name == Support.emojis.tick_emoji
                ):
                    await verify_series_report(client, message)

    return remove_reaction
# end on_reaction_add




async def prepare_series_report_channel(channel, user):

    series_report_embed = Embeds.get_saved_embeds(link=series_report_embed_link)[0].embed
    # series_report_embed = Embeds.get_saved_embeds(link="https://discord.com/channels/789181254120505386/789182513633427507/791648883343884328")[0].embed
    msg = await channel.send(content=user.mention, embed=series_report_embed)
    await msg.add_reaction(Support.emojis.ok_emoji)

    log("templar leagues", "submit series report")
# end series_report


async def series_report(client, message, user):
    """
        match id
        result team a
        result team b
        proof
    """

    def message_check(mesge):
        return mesge.author.id == user.id
    # end message_check


    # copy some attrs from existing series report embed

    series_report_embed = message.embeds[0].to_dict()
    embed = discord.Embed()
    embed = embed.to_dict()
    embed["author"] = series_report_embed["author"] # copy author 
    if any(c in series_report_embed for c in ["color", "colour"]): # copy color
        embed["color"] = series_report_embed["color" if "color" in series_report_embed else "colour"]
    embed = discord.Embed().from_dict(embed)

    # prepare description
    embed.description = "**Match ID:** \n\n" # lines[0]
    embed.description += "**Home Team:** \n" # lines[2]
    embed.description += "**Away Team:** \n\n" # lines[3]
    embed.description += f"**Proof:** \n{Support.emojis.space_char}" # lines[5]


    # set up fields    
    '''embed.add_field(name="**Match ID**", value=Support.emojis.space_char, inline=False)
    embed.add_field(name="**Home Team Wins**", value=Support.emojis.space_char, inline=True)
    embed.add_field(name="**Away Team Wins**", value=Support.emojis.space_char, inline=True)
    embed.add_field(name="**Proof**", value=Support.emojis.space_char, inline=False)'''
    embed.add_field(name="**Instruction**", value=Support.emojis.space_char, inline=False)
    instruction_field_name = "**Instruction**"

    def restart(reason):
        embed.add_field(name=f"**{reason.upper()}**", value=f"To restart, go to [this message]({message.jump_url}), then click the {Support.emojis.ok_emoji}", inline=False)
    # end restart


    ## series report process
    gc = Support.get_g_client()
    workbook = gc.open_by_key(spreadsheets.season_6_league_database.key)
    worksheets = workbook.worksheets()

    msg = None
    try:
        
        ''' GET MATCH ID '''

        fixtures_template_sheet = [ws for ws in worksheets if ws.id == spreadsheets.season_6_league_database.fixtures_template][0]

        match_id = None
        row = [] # match id row, 5 columns wide 
        while not match_id:

            # prepare to wait
            value = f"Input the **Match ID** of the match you are submitting."
            Support.update_field_value(embed, instruction_field_name, value)
            if msg:
                await msg.edit(embed=embed) 

            else:
                msg = await message.channel.send(embed=embed)

            # wait
            mesge = await client.wait_for("message", check=message_check, timeout=60)

            # tease user
            embed.set_footer(text="Verifying input...")
            await msg.edit(embed=embed)

            # verify format
            match_id = re.findall(r"(\d{4})", mesge.content)
            match_id = match_id[0] if match_id else None

            if match_id: # correct format
                fixtures_template_range = fixtures_template_sheet.range(f'B3:F{fixtures_template_sheet.row_count}')
                i = Support.find_value_in_range(fixtures_template_range, mesge.content)

                if i >= 0: # found
                    row = [c.value for c in fixtures_template_range[i:i+5]] 

                else: # not found
                    embed.set_footer(text="Match ID Not Found")
                    match_id = None

            else: # incorrect format
                embed.set_footer(text="Incorrect Match ID Format - should be 0000 format")

            await mesge.delete()

        # end while

        home_team = row[2]
        away_team = row[4]

        lines = embed.description.split("\n")
        lines[0] += f"`{match_id}`"
        lines[2] = f"**{home_team}:** "
        lines[3] = f"**{away_team}:** "

        embed = embed.to_dict()
        embed["description"] = "\n".join(lines)
        del embed["footer"]
        embed = discord.Embed().from_dict(embed)


        ''' GET HOME TEAM WINS '''
        ''' GET AWAY TEAM WINS '''

        home_team_wins = -1
        away_team_wins = -1
        while home_team_wins < 0 or away_team_wins < 0:

            # prepare to wait
            value = f"Input the number of wins for **{home_team if home_team_wins < 0 else away_team}**."
            embed = Support.update_field_value(embed, instruction_field_name, value)
            await msg.edit(embed=embed)

            # wait
            mesge = await client.wait_for("message", check=message_check, timeout=60)

            await mesge.delete()

            # tease user
            embed.set_footer(text="Verifying input...")
            # await msg.edit(embed=embed)

            # verify format
            wins = re.findall(r"(\d{1})", mesge.content)
            wins = int(wins[0]) if wins else -1

            if wins == -1:
                embed.set_footer(text="Invalid Input")

            away_team_wins = wins if home_team_wins >= 0 else away_team_wins # set away if home set 
            home_team_wins = wins if home_team_wins < 0 else home_team_wins # set home if not set

            # await mesge.delete()

            lines = embed.description.split("\n")
            lines[3] = f"**{away_team}:** " + (f"`{away_team_wins}`" if away_team_wins >= 0 else "")
            lines[2] = f"**{home_team}:** " + (f"`{home_team_wins}`" if home_team_wins >= 0 else "")

            embed = embed.to_dict()
            embed["description"] = "\n".join(lines)
            if wins >= 0: # valid input
                del embed["footer"]
            embed = discord.Embed().from_dict(embed)

        # end while


        def reaction_check(reaction, r_user):
            return (
                reaction.message == msg and 
                r_user.id == user.id and
                str(reaction.emoji) in [Support.emojis.tick_emoji]
            )
        # end reaction_check


        ''' GET PROOF '''

        stop = False
        phyner_tick_added = False
        ballchasing_links = []
        other_links = []
        while not stop:

            # prepare to wait
            value = f"Attach all forms of proof you have (links or screenshots). All that is needed, though, is one https://ballchasing.com/group/... link. When you have sent all of your proof, click the {Support.emojis.tick_emoji} to continue - you have 5 minutes before the submission times out."
            embed = Support.update_field_value(embed, instruction_field_name, value)

            await msg.edit(embed=embed)

            if not phyner_tick_added:
                await msg.add_reaction(Support.emojis.tick_emoji)
                phyner_tick_added = True

            # wait
            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=300)

            # tease user
            embed.set_footer(text="Verifying input...")
            # await msg.edit(embed=embed)

            # verify input
            history = await message.channel.history(after=msg, oldest_first=False).flatten()
            for mesge in history:
                if mesge.author.id == user.id: # get inputted links
                    ballchasing_links += re.findall(r"(https:\/\/ballchasing.com\/group\/\S+[^>])", mesge.content) #  ballchasing links
                    other_links += [link for link in re.findall(r"(http\S+[^>])", mesge.content) if validators.url(link)] # other links

                if mesge.attachments: # detect attachments
                    mesge.attachments.reverse()
                    for attachment in mesge.attachments:
                        other_links.append(await Support.save_image_to_random_storage(client, attachment)) # save to a discord channel to keep a valid link

                if ballchasing_links or len(other_links) >= away_team_wins + home_team_wins: # stop condtion
                    stop = True

            if not stop: # not satisfied
                embed.set_footer(text="No ballchasing link provided. Must have at least one link per game otherwise. ")

            await Support.remove_reactions(msg, user, Support.emojis.tick_emoji)

        # add proof to embed
        lines = embed.description.split("\n")
        lines[5] = "**Proof:** " + " ".join([f"[{'link' if 'ballchasing' not in link else 'ballchasing'}]({link})" for link in other_links])

        embed = embed.to_dict()
        embed["description"] = "\n".join(lines)
        del embed["footer"]
        embed = discord.Embed().from_dict(embed)

        # end while


        ''' CONFIRM '''

        # prepare to wait 
        value = f"If the information below looks right, click the {Support.emojis.tick_emoji} to submit this match. If there is an error, go to [this message]({message.jump_url}) and click the {Support.emojis.ok_emoji} to restart."
        embed = Support.update_field_value(embed, instruction_field_name, value)
        await msg.edit(embed=embed)

        # wait
        reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=60)

        # tease user
        embed.set_footer(text="Submitting...")
        # await msg.edit(embed=embed)

        # send to staff leagues log
        value = f"Please check that the proof matches the result, and verify the score by clicking the {Support.emojis.tick_emoji}!"
        embed = Support.update_field_value(embed, instruction_field_name, value)

        embed = embed.to_dict()
        embed["author"]["url"] = "https://google.com/id=templar_leagues_series_report_verification/"
        del embed["footer"]
        embed = discord.Embed().from_dict(embed)

        staff_guild = client.get_guild(staff_templar_leagues_id) # get staff guild
        league_results_log = staff_guild.get_channel(staff_league_results_log_id) # get league results channel
        msg = await league_results_log.send(content=f"<@&{staff_moderator_id}> <@&{staff_support_id}>", embed=embed) # send to league results
        await msg.add_reaction(Support.emojis.tick_emoji)

        # delete submission channel
        await message.channel.delete()

        log("templar leagues series report", "submitted")

    except asyncio.TimeoutError:
        restart("Timed Out")
        
        try:
            await msg.edit(embed=embed)

        except discord.errors.NotFound:
            pass

    except:
        await Support.previous_action_error(client, message)
# end series_report

async def verify_series_report(client, message):
    embed = message.embeds[0]

    # tease user
    embed.set_footer(text="Verifying...")
    await message.edit(embed=embed)

    # clean up embed
    embed = embed.to_dict()
    del embed["footer"]
    embed["description"] = embed["description"][:-1] # get rid of space char
    embed = Support.delete_last_field(embed)

    # send embed staff_stats and main_approved
    staff_guild = client.get_guild(staff_templar_leagues_id)
    main_guild = client.get_guild(templar_leagues_id)

    staff_stats = staff_guild.get_channel(staff_stats_log_id)
    main_approved_results = main_guild.get_channel(approved_results_id)

    await staff_stats.send(content=f"<@&{staff_stats_id}>", embed=embed)
    await main_approved_results.send(embed=embed)

    await message.edit(embed=embed) # edit the verified message now

    log("templar leagues series report", "verified")

# end verify_series_repor