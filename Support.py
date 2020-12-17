''' IMPORTS '''

import discord
from types import SimpleNamespace
from bs4 import BeautifulSoup as bsoup
import requests
import re
import sys
import traceback
import json

import os
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
    'mobot_support_id' : 467239192007671818,
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

## COMMON ALIASES ##
add_aliases = ["add", "+"]
remove_aliases = ["remove", "-"]



''' SUPPORT FUNCTIONS '''

def load_embed_from_Embeds(guild_id, channel_id, message_id):

    embed = None
    embed_file_name = f"{hex(guild_id)}-{hex(channel_id)}-{hex(message_id)}"
    with open(f"Embeds/{'testing/' if os.getenv('HOST') == 'PC' else ''}{embed_file_name}.json", "r") as embed_file:
        embed = discord.Embed().from_dict(json.load(embed_file))

    return embed
# end load_embed_from_Embeds


def messageOrMsg(msg):  
    """
        figure out if bot msg or user message, once again got tired of typing this :D
        returns embed, message, msg
    """

    embed = msg.embeds[0] if msg and msg.embeds else discord.Embed()
    message = None if msg and msg.author.id in [ids.phyner_id] else msg  # is user message
    msg = None if message else msg  # is bot msg

    return embed, message, msg
# end messageOrMsg

def get_phyner_from_channel(channel):
    if channel.type != discord.ChannelType.private:
        return [member for member in channel.members if member.id == ids.phyner_id][0]
    else:
        return channel.me
# end get_phyner_member_from_channel


def get_id_from_str(str):
    """
        returns list
    """
    return re.findall(r"(\d{17,})", str)
# end get_id_from_str


def get_args_from_content(content):
    content = re.sub(r"[“”]", '"', content)
    content = re.sub(r"[\n\t\r]", ' ', content)
    content += " "
    while "  " in content:
        content = content.replace("  ", " ")
    args = content.split(" ")

    return args, content
# end get_args_from_content


## embed stuff ##

def confirm_input_last_field(embed):
    embed = embed.to_dict()
    field_footer = embed["fields"][-1]["value"]
    embed["fields"][-1]["value"] = "**Confirming Input...**"
    embed = discord.Embed().from_dict(embed)
    return field_footer, embed
# end confirm_input_last_field

def revert_confirm_input_last_field(field_footer, embed):
    embed = embed.to_dict()
    embed["fields"][-1]["value"] = field_footer
    embed = discord.Embed().from_dict(embed)
    return embed
# end revert_confirm_input_last_field

def revert_confirm_input_last_field_exclamation(field_footer, embed):
    lines = field_footer.split("\n")
    lines[-2] = f"**{lines[-2]} {emojis.exclamation_emoji}**"

    embed = embed.to_dict()
    embed["fields"][-1]["value"] = "\n".join(lines)
    embed = discord.Embed().from_dict(embed)
    return embed
# end revert_confirm_input_last_field

def delete_last_field(embed):
    embed = embed.to_dict() if type(embed) != dict else embed
    del embed["fields"][-1]
    return discord.Embed().from_dict(embed)
# end delete_last_field

def switch_last_two_fields(embed):
    embed = embed.to_dict() if type(embed) != dict else embed
    t_field = embed["fields"][-2]
    del embed["fields"][-2]
    embed["fields"].append(t_field)
    return discord.Embed().from_dict(embed)
# end switch_last_two_fields


def quote(s):
    return f"'{s}'"
# end quote


## clearing reactions ##

async def clear_reactions(msg):
    try:
        await msg.clear_reactions()
    except discord.errors.Forbidden:
        pass
# end clear_reactions

async def remove_reactions(msg, user, reactions):
    for reaction in reactions:
        try:
            await msg.remove_reaction(reaction, user)
        except:
            pass
# end remove_reactions


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


async def simple_bot_response(channel, author=discord.Embed().Empty, author_icon_url=discord.Embed().Empty, title=discord.Embed().Empty, thumbnail_url=discord.Embed().Empty, description=discord.Embed().Empty, footer=discord.Embed().Empty, send=True, reply_message=False, delete_after=None):
    """
        Bot sends message as basic embed
        reply_message is defaulted to False, but expects a discord.Message if declared in call
    """
    # TODO pass in embed_dict as starting point, no overwriting
    is_dm = is_DMChannel(channel)
    phyner = get_phyner_from_channel(channel)

    embed = discord.Embed()
    embed.colour = colors.phyner_grey if is_dm else phyner.roles[-1].color

    if author or author_icon_url:
        embed.set_author(
            name=author if author else emojis.space_char,
            icon_url=author_icon_url
        )


    embed.title = title
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
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
                name=f"{'Restarting' if restart else 'Temporarily shutting down'} soon!"
            )
        )

        msg = await simple_bot_response(
            message.channel, 
            description=f"**{'Restarting' if restart else 'Shutting down'} in {restart_interval} seconds.**"
        )

    return (1 if restart else 0), msg
# end restart  