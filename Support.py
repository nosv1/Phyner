''' IMPORTS '''
import discord
from types import SimpleNamespace
from bs4 import BeautifulSoup as bsoup
import requests
import re
import subprocess
import os
import sys

from dotenv import load_dotenv
load_dotenv()

import Logger


''' CONSTANTS '''

host = os.getenv("HOST")

## IDs ##
ids = SimpleNamespace(**{
    'mo_id' : 405944496665133058,
    'phyner_id' : 770416211300188190,
})


## COLORS ##
colors = SimpleNamespace(**{
    'phyner_red' : 0x980B0D,
})


## CHARACTERS / EMOJIS ##
emojis = SimpleNamespace(**{
    'space_char' : "⠀",
    'x_emoji' : "❌",
    'ok_emoji' : "🆗",
    'i_emoji' : "🛈",
})



''' SUPPORT FUNCTIONS '''

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
    return [member for member in channel.members if member.id == ids.phyner_id][0]
# end get_phyner_member_from_channel

async def simple_bot_response(channel, title=discord.Embed().Empty, description=discord.Embed().Empty, footer=discord.Embed().Empty, send=True, reply=False):
    """
    Bot sends message as basic embed
    reply is defaulted to False, but expects a discord.Message if declared in call
    """

    in_dm = False
    try:
        phyner = get_phyner_from_channel(channel)
    except AttributeError:
        in_dm = True

    embed = discord.Embed()
    embed.colour = colors.phyner_red if in_dm else phyner.roles[-1].color

    embed.title = title
    embed.description = description

    if footer:
        embed.set_footer(text=footer)


    if send:
        if reply:
            msg = await reply.reply(embed=embed)
        else:
            msg = await channel.send(embed=embed)
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

async def restart(client, restart=True):
    """
        ability to restart PI4 host
    """

    if host == "PI4":
        if restart:
            Logger.log(f"{host} Connection", "Restarting see you on the other side...")
            subprocess.call("restart.sh")

    await client.close()
    sys.exit()

# end restart