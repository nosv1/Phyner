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

async def simple_bot_response(channel, title=discord.Embed().Empty, description=discord.Embed().Empty, footer=discord.Embed().Empty, send=True, reply=False):
    """
        Bot sends message as basic embed
        reply is defaulted to False, but expects a discord.Message if declared in call
    """

    is_dm = is_DMChannel(channel)
    phyner = get_phyner_from_channel(channel)

    embed = discord.Embed()
    embed.colour = colors.phyner_red if is_dm else phyner.roles[-1].color

    embed.title = title
    embed.description = description

    if footer:
        embed.set_footer(text=footer)


    if send:
        if type(reply) == discord.message.Message:
            msg = await reply.reply(embed=embed)
            
        else:
            msg = await channel.send(embed=embed)

            if reply: # cuz im silly sometimes
                for i in range(5):
                    Logger.log("MO", "You've set reply=True instead of reply=message somewhere...")
                
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
        close or restart pi4 host
    """

    if host == "PI4":
        if restart:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Phyner restart."))
            Logger.log(f"Connection", f"{host} Restarting see you on the other side...")

            await client.close()

            pid = os.getpid()
            os.system(f'bash restart.sh {pid}')

        else:
            await close(client)

    else:
        await close(client)
# end restart

async def close(client):
    """
        client.close() + sys.exit()
    """
    
    await client.close()
    sys.exit()
# end close   