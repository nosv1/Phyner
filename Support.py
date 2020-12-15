''' IMPORTS '''
import discord
from types import SimpleNamespace
from bs4 import BeautifulSoup as bsoup
import requests
import re
import os
import sys

from dotenv import load_dotenv
load_dotenv()

import Logger


''' CONSTANTS '''

host = os.getenv("HOST")

## IDs ##
ids = SimpleNamespace(**{
    # user ids
    'mo_id' : 405944496665133058,
    'phyner_id' : 770416211300188190,

    # guild ids
    'mobot_support' : 467239192007671818,
})


## COLORS ##
colors = SimpleNamespace(**{
    'phyner_grey' : 0x9a9c9f,
})


## CHARACTERS / EMOJIS ##
emojis = SimpleNamespace(**{
    'space_char' : "⠀",
    'bullet' : "•",
    'x_emoji' : "❌",
    'tick_emoji' : "✅",
    'ok_emoji' : "🆗",
    'i_emoji' : "🛈",
    'number_emojis' : ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"],
    'exclamation_emoji' : "❗",
})



''' SUPPORT FUNCTIONS '''

async def clear_reactions(msg):
    try:
        await msg.clear_reactions()
    except discord.errors.Forbidden:
        pass
# end clear_reactions

def is_DMChannel(channel):
    return channel.type == discord.ChannelType.private
# end is_dm


def get_member_perms(channel, member):
    """
        Gets the permissions for a given member for a given channel. If the member is Mo, all permissions are returned as True.
    """

    author_perms = dict(channel.permissions_for(member))
    is_mo = member.id == ids.mo_id
    if is_mo:
        for permission  in author_perms:
            author_perms[permission] = True
    author_perms = SimpleNamespace(**author_perms) # converts dict back to class
    return author_perms
# end get_member_perms


def get_phyner_from_channel(channel):
    if channel.type != discord.ChannelType.private:
        return [member for member in channel.members if member.id == ids.phyner_id][0]
    else:
        return channel.me
# end get_phyner_member_from_channel


async def simple_bot_response(channel, title=discord.Embed().Empty, description=discord.Embed().Empty, footer=discord.Embed().Empty, send=True, reply_message=False, delete_after=None):
    """
        Bot sends message as basic embed
        reply_message is defaulted to False, but expects a discord.Message if declared in call
    """
    # TODO pass in embed_dict as starting point, no overwriting
    is_dm = is_DMChannel(channel)
    phyner = get_phyner_from_channel(channel)

    embed = discord.Embed()
    embed.colour = colors.phyner_grey if is_dm else phyner.roles[-1].color

    embed.title = title
    embed.description = description

    if footer:
        embed.set_footer(text=footer)


    if send:
        if type(reply_message) == discord.message.Message:
            msg = await reply_message.reply(embed=embed, delete_after=delete_after)
            
        else:
            msg = await channel.send(embed=embed, delete_after=delete_after)
                
        return msg

    else:
        return embed
# end botResponse


def search_github(query):
    """
        search github wiki
        return list of results [{link, title, p}]
    """
    while " " in query:
        query = query.replace(" ", "+")

    html = str(bsoup(requests.get(f"https://github.com/nosv1/Phyner/search?q={query}&type=wikis").text, "html.parser"))
    results = html.split("class=\"f4 text-normal\"")
    results = results[1:] if len(results) > 1 else []
    for i, result in enumerate(results):
        results[i] = {
            'link' : "https://github.com" + result.split("href=\"")[1].split("\"")[0],
            'title' : result.split("title=\"")[1].split("\"")[0],
            'p' : "\n".join(re.sub(r"(<|(</))(em>)", "**", result.split('<p')[1].split("\">")[1].split("</p>")[0].strip()).split(emojis.space_char))
        }
    return results
# end search


async def restart(client, message, restart_interval, restart=True):
    """
        close or restart pi4 host
    """

    if host == "PI4":
        if restart: # only PI4 has ability to restart
            Logger.log(f"Connection", f"{host} Restarting see you on the other side...")


        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, 
                name=f"{'restart' if restart else 'hut down'} soon!"
            )
        )

        await simple_bot_response(
            message.channel, 
            description=f"**{'Restarting' if restart else 'Shutting down'} in {restart_interval} seconds.**"
        )

    if not restart:
        Logger.log("Connection", f"{host} Shutting Down")

    return 1 if restart else 0
# end restart  