''' IMPORTS '''

import asyncio
import discord
import json
import pathlib
import re
import traceback

import validators

import os
from dotenv import load_dotenv
load_dotenv()


import General
import Guilds
import Help
import Logger
import Support
from Support import emojis, get_phyner_from_channel
import Tables



''' CONSTATNS '''

help_footer = f"@Phyner#2797 embed help"

embed_attrs = [
    '.content',
    '.color ', '.colour ',

    '.author ',
    '.author_url ',
    '.author_icon_url ',

    '.thumbnail_url ',
    '.title ',

    '.description ',

    '.field#_name ',
    '.field#_value ',
    '.field#_inline ', # .field#_inline true/True

    '.footer ', 
    '.footer_icon_url ',

    '.image_url ',
]

embed_aliases = ["embed", "embeds"]

embed_colors = {
    ".phyner_grey" : Support.colors.phyner_grey,
    ".phyner_gray" : Support.colors.phyner_grey,
    ".white" : 0xffffff,
    ".black" : 0x1, # 1 and not 0 cause fucks up if statments
    ".grey" : 0x808080,
    ".pink" : 0xffc0cb,
    ".red" : 0xff0000,
    ".orange" : 0xFFA500,
    ".yellow" : 0xFFFF00,
    ".green" : 0x008000,
    ".blue" : 0x0000ff,
    ".purple" : 0x800080,
    ".brown" : 0x964B00,
}


''' CLASS '''

class SavedEmbed:
    """
        embed should be discord.Embed()
    """
    def __init__(self, guild_id, channel_id, message_id, embed, name="", path=None):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.embed = embed # should be discord.Embed() by now
        self.name = name
        self.path = path
    # end __init__


    def save_embed(self):
        gcm = [str(self.guild_id), str(self.channel_id), str(self.message_id)]
        self.path = f"Embeds/{'testing/' if os.getenv('HOST') == 'PC' else ''}{'-'.join(gcm)}{'-' + self.name if self.name else ''}.json"

        saved_embeds = get_saved_embeds(guild_id=self.guild_id)
        for saved_embed in saved_embeds:
            existing_gcm = saved_embed.path.split("-")[:3] # :3 because there may be a - in embed name
            existing_gcm[0] = Support.get_id_from_str(existing_gcm[0])[0]
            existing_gcm[-1] = Support.get_id_from_str(existing_gcm[-1])[0]

            if gcm == existing_gcm: # if gcms match, delete old if new name given
                if not self.name: # new name not given
                    self.path = saved_embed.path # overwrite existing file

                else: # new name given, delete existing file, add new
                    os.remove(saved_embed.path)

        with open(self.path, "w+") as embeds:
            json.dump(self.embed.to_dict(), embeds, indent=4, sort_keys=True)

        return self
    # send save_embed
# end SavedEmbed



''' FUNCTIONS '''

async def main(client, message, args, author_perms):

    if args[2] in Help.help_aliases: # @Phyner <command> or @Phyner command help
        await send_embed_help(client, message)


    elif args[2] in General.say_aliases:

        if author_perms.manage_messages:
            await create_user_embed(client, message)

        else:
            await send_permissions_needed(message, message.author)


    elif args[2] == "edit":
        
        if author_perms.manage_messages:
            await edit_user_embed(client, message, args)

        else:
            await send_permissions_needed(message, message.author)


    elif args[2] == "send":
        if author_perms.manage_messages:
            await send_saved_embed_from_message(message, args[3:-1])

        else:
            await send_permissions_needed(message, message.author)


    elif args[2] == "save":
        if author_perms.manage_messages:
            await save_embed(client, message, args[3:-1])

        else:
            await send_permissions_needed(message, message.author)

    elif args[2] == "convert":
        await convert(client, message, args[3:])
    

    elif args[2] == "saved":
        embed = generate_saved_embeds_display(
            get_saved_embeds(guild_id=args[3] if args[3] else message.guild.id if message.guild else message.author.id), 
            message.guild if message.guild else message.author, 
            get_phyner_from_channel(message.channel)
        )
        await message.channel.send(embed=embed)

    return
# end main



## SAVED EMBEDS ##

def get_saved_embeds(guild_id="", channel_id="", message_id="", name="", link=""):
    """
        returns [embed] if link or ids and name provided otherwise [embed, ...]
    """

    embeds_folder = pathlib.Path(f"Embeds/{'testing/' if os.getenv('HOST') == 'PC' else ''}")
    embed_files = sorted(embeds_folder.iterdir(), key=os.path.getctime)

    embed_ids = link.split("/")[-3:] if link else [str(guild_id), str(channel_id), str(message_id)] # will be at least [''] # FIXME this assumes no / in name

    save_embeds = []
    for embed_file in embed_files:
        file_ids = re.findall(r"(\d{17,})", str(embed_file))[:3]

        if (
            not embed_ids[0] or # nothing provided
            file_ids == embed_ids or # exact match
            (not embed_ids[1] and embed_ids[0] == file_ids[0]) # if only guild given
        ):
            name = str(embed_file).split(file_ids[-1])[1][1:-5] # if name in file, remove '-' after message_id and .json at the end
            name = file_ids[-1] if not name else name # name is either name or str(message_id) now

            save_embeds.append(SavedEmbed(int(file_ids[0]), int(file_ids[1]), int(file_ids[2]), load_embed_from_Embeds(str(embed_file)), name, str(embed_file)))

    return save_embeds
# end get_saved_embeds


def generate_saved_embeds_display(saved_embeds, guild, phyner):
    """
        saved_embeds should be [SavedEmbed, ...] not [discord.Embed(), ...]
    """

    embed = discord.Embed(color=Support.colors.phyner_grey if type(guild) != discord.guild.Guild else phyner.roles[-1].color)
    embed.title = f"{guild.name}'s Saved Embeds"

    if saved_embeds:

        embed.description = "Click the link to go to the saved embed (assuming it still exists).\n\n"

        for saved_embed in saved_embeds:
            embed.description += f"[{saved_embed.name if saved_embed.name else saved_embed.message_id}](https://discord.com/channels/{saved_embed.guild_id}/{saved_embed.channel_id}/{saved_embed.message_id})\n"


        embed.description += f"\nSend a Saved Embed:\n"
        embed.description += f"`{Guilds.get_guild_prefix(guild.id)} embed send <embed_name> [#destination]`\n\n" # TODO embed send

        embed.description += f"Convert Saved Embed to `{Guilds.get_guild_prefix(guild.id)} embed create` message:\n" # TODO convert saved embed to `embed create` message
        embed.description += f"`{Guilds.get_guild_prefix(guild.id)} embed convert <embed_name>`"

    else:
        embed.description = f"No embeds have been saved in {guild.name}.\n\n"

        embed.description += f"Save an Embed:"
        embed.description += f"`{Guilds.get_guild_prefix(guild.id)} embed save <message_id> [embed_name]`"

    return embed
# end generate_saved_embeds_display


def load_embed_from_Embeds(path):
    """
        in path
        return embed
    """

    with open(path, "r") as embed_file:
        embed = discord.Embed().from_dict(json.load(embed_file))

    return embed
# end load_embed_from_Embeds


async def send_saved_embed_from_message(message, args):

    # TODO send saved embed help

    # get destination channel 
    channel = message.channel_mentions[-1] if message.channel_mentions else message.channel
    if message.channel_mentions:
        del args[-1]


    embed_name = "_".join(args)
    saved_embeds = get_saved_embeds(guild_id=message.guild.id)
    saved_embed = [s for s in saved_embeds if s.name == embed_name]

    if saved_embed:
        await channel.send(embed=saved_embed[0].embed)

    else:
        await channel.send(embed=generate_saved_embeds_display(saved_embeds, message.guild))
# end send_saved_embed



## FUNCTIONALITY ##

async def get_embed_from_content(client, message, roles=[], embed=discord.Embed()):
    """ 
    Creating a discord.Embed() from the content of a message, or simply from a string.
    returns embed and list of readable error messages

    content is a string
    roles is a list of guild.roles, used for getting role colors
    embed can be existing or blank

    ------
    content should look something like:
    `@Phyner#2797 embed edit {msg_id} {.attr} {attr_value}`

    `@Phyner#2797 embed edit {msg_id} 
    {.attr} {attr_value}`
    """

    content = message.content.replace("\\s", emojis.space_char).replace("\\b", emojis.bullet).replace("\\z", emojis.zero_width)
    msg_content = emojis.space_char
    attrs = []


    # find all the attrs in order of apperance

    for attr in embed_attrs: 
        try:
            i = content.index(attr)
            attrs.append([attr, i])
        except ValueError: # attr not in content
            if '.field' in attr:
                field_attrs = re.findall(r"(\.field[0-9]+_(name|value|inline) )", content)
                for field_attr in field_attrs:
                    field_attr = field_attr[0] # for some reason the findall returns [(.field1_name, name), ...]
                    i = content.index(field_attr)
                    attrs.append([field_attr, i])
            pass

    attrs.sort(key=lambda a:a[1]) # sort based on index (appearance)
    attrs = [a[0] for a in attrs] # remove index bit from attrs


    # prepare existing fields

    embed = embed.to_dict()
    fields = {} 
    if 'fields' in embed:
        for i, field in enumerate(embed['fields']):
            fields[i+1] = field # {name, value, inline}
    embed = discord.Embed().from_dict(embed)


    # get and assign attr values, fields after this loop

    errors = [] # [attribute, value]

    for i, attr in enumerate(attrs): # get attr values
        next_attr = attrs[i+1] if i < len(attrs) - 1 else None
        if attr == next_attr:
            continue
            
        ## SETUP VALUE ##

        value = content[
            content.index(attr) + len(attr) : content.index(next_attr) - 1 if next_attr else len(content)
        ]

        attr = attr.strip()
        value = value if ".empty" not in value else discord.Embed().Empty
        value = str(message.guild.icon_url) if ".guild_icon" in str(value) else value

        # get table
        if ".table_" in value:
            table_message_id = Support.get_id_from_str(value.split(".table_")[1])
            table_message_id = table_message_id[0] if table_message_id else None
            if table_message_id:

                table = Tables.get_table(table_message_id, message.guild.id if message.guild else message.author.id)
                if table:
                    table = table[0]
                    print(table_message_id)
                    print(table.to_string())

                    table.channel = client.get_channel(table.channel_id)
                    for i, m_id in enumerate(table.msg_ids):
                        if m_id != table_message_id: # given message id must match
                            continue

                        table.messages.append(await table.channel.fetch_message(m_id))
                        
                        if table.messages[i].embeds:
                            table_embed = table.messages[i].embeds[0]
                            if table_embed.description and Support.emojis.zero_width*2 in table_embed.description:
                                table.tables.append(table_embed.description.split(Support.emojis.zero_width*2)[1])

                        if table.messages[i].content:
                            if Support.emojis.zero_width*2 in table.messages[i].content:
                                table.tables.append(table.messages[i].content.split(Support.emojis.zero_width*2)[1])

                        print(table.tables)
                        if table.tables:
                            value = value.replace(f".table_{table_message_id}", f"{Support.emojis.zero_width*2}{table.tables[0].strip()}{Support.emojis.zero_width*2}")

                else:
                    errors.append([f"**Attribute:** `{attr}`", f"**Value:** `{value}` No matching table message ids"])

            else:
                errors.append([f"**Attribute:** `{attr}`", f"**Value:** `{value}` No table message id given. Ex. `.table_793447251506364436`"])


        if attr in ['.content']:
            msg_content = value if value else emojis.space_char

        elif attr in [".color", ".colour"]:
            try:
                role_color = [r.color for r in roles if str(r.id) == value] # get role color
                color = embed_colors[[c for c in embed_colors if c == value.strip()][0]] if any(c == value.strip() for c in embed_colors) else role_color
                color = abs(int(value.replace("#", ""), 16)) if not color and value else color # use given hex else role_color
                color = role_color[0].value if role_color else (color if color else value)

                color = (16777214 if color >= 16777215 else 1 if color <= 0 else color) if color else color

                if not value or color:
                    embed.color = color if color else value

                else:
                    errors.append([f"**Attribute:** `{attr}`", f"**Value:** `{value}` is not a role id or is too large of a hex value"])

            except: # likely not quality color
                errors.append([f"**Attribute:** `{attr}`", f"**Value:** `{value}` is not a role id or hex value"])
                Logger.log('error', traceback.format_exc())

        
        ### AUTHOR ###

        elif attr in [".author"]:
            embed = embed.to_dict()
            
            if value:
                embed['author'] = {} if 'author' not in embed else embed['author']
                embed['author']['name'] = value

            else:
                if 'author' in embed and 'name' in embed['author']:
                    del embed['author']['name']

            embed = discord.Embed().from_dict(embed)

        elif attr in [".author_url", ".author_icon_url"]:
            embed = embed.to_dict()
            embed['author'] = {} if 'author' not in embed else embed['author']
            
            url = re.sub(r"[<>]", "", value.strip()) if value else value
            url_icon_url = 'url' if attr == '.author_url' else 'icon_url'
            if value and validators.url(url):
                embed['author'][url_icon_url] = url

                if 'name' not in embed['author']:
                    embed['author']['name'] = emojis.space_char

            else: 
                if url_icon_url in embed['author']:
                    del embed['author'][url_icon_url]

                if value:
                    errors.append([f"**Attribute:** `{attr}`", f"**Value:** `{value}` is not a valid link"])


        ### THUMBNAIL AND IMAGE ###
            
        elif attr in [".thumbnail_url", ".image_url"]:
            embed = embed.to_dict()

            thumbnail_image = 'thumbnail' if attr == '.thumbnail_url' else 'image' if attr == '.image_url' else 'video'
            embed[thumbnail_image] = {} if thumbnail_image not in embed else embed[thumbnail_image]

            url = re.sub(r"[<>]", "", value.strip()) if value else value
            if value and validators.url(url):
                embed[thumbnail_image]['url'] = url

            else:
                if 'url' in embed[thumbnail_image]:
                    del embed[thumbnail_image]['url']
                if value:
                    errors.append([f"**Attribute:** `{attr}`", f"**Value:** `{value}` is not a valid link"])


        ### TITLE ###

        elif attr in [".title"]:
            embed.title = value


        ### DESCRIPTION ###

        elif attr in [".description"]:
            embed.description = value


        ### FIELDS ###

        elif '.field' in attr and any(w in attr for w in ['_name', '_value', 'inline']):
            field_index = re.findall(r"(\.field[0-9]+_)", attr)
            field_index = int(re.findall(r"[0-9]+", field_index[0])[0])

            if field_index not in fields:
                fields[field_index] = {
                    'name' : discord.Embed().Empty, 'value' : discord.Embed().Empty, 'inline' : False
                }

            if '_name' in attr:
                fields[field_index]['name'] = value

            elif '_value' in attr:
                fields[field_index]['value'] = value

            elif '_inline' in attr:
                fields[field_index]['inline'] = value.strip() in ['True', 'true', '1']


        ### FOOTER ###

        elif attr in [".footer"]:
            embed = embed.to_dict()

            if value:
                embed['footer'] = {} if 'footer' not in embed else embed['footer']

                embed['footer']['text'] = value

            else:
                if 'footer' in embed and 'text' in embed['footer']:
                    del embed['footer']['text']
        
        elif attr in [".footer_icon_url"]:
            embed = embed.to_dict()
            embed['footer'] = {} if 'footer' not in embed else embed['footer']
            
            url = re.sub(r"[<>]", "", value.strip()) if value else value
            if value and validators.url(url):
                embed['footer']['icon_url'] = url

                if 'text' not in embed['footer']:
                    embed['footer']['text'] = emojis.space_char

            else:
                errors.append([f"**Attribute:** `{attr}`", f"**Value:** `{value}` is not a valid link"])
                if not value and 'icon_url' in embed['footer']:
                    del embed['footer']['icon_url']

        embed = discord.Embed().from_dict(embed) if type(embed) == dict else embed

    ### ADDING FIELDS ###

    field_indexes = list(fields.keys())
    field_indexes.sort()

    embed = embed.to_dict()
    if 'fields' in embed:
        del embed['fields']
    embed['fields'] = []

    for i, field_index in enumerate(field_indexes):
        field = fields[field_index]
        if field['name'] or field['value']: # both not Embed.Empty

            fields[field_index]['name'] = field['name'] if field['name'] and field['name'].strip() else emojis.space_char
            fields[field_index]['value'] = field['value'] if field['value'] and field['value'].strip() else emojis.space_char
            embed['fields'].append(field)

    embed = discord.Embed().from_dict(embed)

    Logger.log('embed', embed.to_dict())
    return embed, msg_content, errors
# end get_attributes_from_content


async def create_user_embed(client, message):
    embed, content, errors = await get_embed_from_content(
        client, message, 
        roles=message.guild.roles if message.guild else [] # may be dm channel
    )

    msg = await message.channel.send(content=content, embed=embed)
    phyner = Support.get_phyner_from_channel(message.channel)

    title = "Moving and Editing Phyner Messages"

    description = f"`{msg.id}` is the Message ID of the [message above]({msg.jump_url}).\n\n"

    description += f"**Edit Embed:**\n`@{phyner} embed edit {msg.id}\n[edit embed attributes]`\n*send a new message, or edit your existing [embed create message]({message.jump_url})*\n\n"

    description += f"**Copy Message:**\n`@{phyner} copy {msg.id} [some_msg_id ...] [#msg_location] <#destination>`\n\n" 

    description += f"**Replace Message:**\n`@{phyner} replace <some_phyner_msg_id> {msg.id}`\n\n" 

    description += f"{emojis.x_emoji} to dismiss"

    msg = await Support.simple_bot_response( 
        message.channel,
        title=title,
        description=description, 
        footer=help_footer,
        reply_message=message
    )
    await msg.add_reaction(emojis.x_emoji)

    def check_x_emoji(payload):
        return (
            payload.emoji.name in [emojis.x_emoji] and
            payload.message_id == msg.id and
            payload.user_id == message.author.id
        )
    # end reaction_check

    try:
        await client.wait_for('raw_reaction_add', check=check_x_emoji, timeout=30.0)
        await msg.delete()
        
    except asyncio.TimeoutError:
        description = "\n".join(description.split("\n")[:-1])
        embed = msg.embeds[0]
        embed.description = description
        await msg.edit(embed=embed)
        await msg.remove_reaction(emojis.x_emoji, client.user)

    if errors:
        await send_embed_attr_errors(message, msg.id, errors)
    Logger.log('embed', f"errors: {errors}")
    Logger.log('embed', f'custom embed created')
# end create_user_embed


async def edit_user_embed(client, message, args):
    phyner = Support.get_phyner_from_channel(message.channel)

    # get msg source channel
    channel_id = Support.get_id_from_str(args[4])
    channel_id = int(channel_id[0]) if channel_id else message.channel.id
    channel = [c for c in message.guild.channels if c.id == channel_id]
    channel = channel[0] if channel else None
    
    # get msg
    msg = None
    msg_id = Support.get_id_from_str(args[3])
    msg_id = int(msg_id[0]) if msg_id else None
    try:
        msg = await channel.fetch_message(msg_id) if channel and msg_id else None    
    except discord.errors.NotFound:
        pass # error message below

    if msg and msg.author.id == Support.ids.phyner_id: # msg found and phyner is author
        embed = msg.embeds[0] if msg.embeds else None
        embed, content, errors = await get_embed_from_content(
            client,
            message, 
            roles=message.guild.roles, 
            embed=embed if embed else discord.Embed()
        )
        await msg.edit(content=content, embed=embed)
        await Support.process_complete_reaction(message)
        
        if errors:
            await send_embed_attr_errors(message, msg_id, errors)

        Logger.log('embed', f"errors: {errors}")
        Logger.log('embed', f'custom embed edited')

    else:

        if msg and msg.author.id != Support.ids.phyner_id: # msg found, phyner not author
            msg = await Support.simple_bot_response(message.channel,
                title="Could Not Edit Message",
                description=f"{client.user.mention} is not the author of the given message {msg.jump_url}",
                footer=help_footer,
                reply_message=message
            )
            Logger.log('embed', "could not edit another author's message")

        else: # msg not found, by deduction
            description = f"The message_id, `{msg_id}`, could not be found in {channel.mention}. If this channel is not where the message is located, edit your [message above]({message.jump_url}) to match the syntax below to specify where {phyner.mention} should look for the message.\n\n"

            description += f"`@{phyner} embed edit {msg_id} <#channel> [set_embed_attributes]`\n\n"
            description += f"`@{phyner} ids` to learn how to get message_ids.\n"
            
            msg = await Support.simple_bot_response(message.channel,
                title="Could Not Find Message",
                description=description,
                footer=help_footer,
                reply_message=message
            )
            Logger.log("embed", "could not find message")

        await msg.add_reaction(emojis.ok_emoji)

        def check_ok_emoji(payload):
            return (
                payload.emoji.name in [emojis.ok_emoji] and
                payload.message_id == msg.id and
                payload.user_id == message.author.id
            )
        # end reaction_check

        try:
            await client.wait_for('raw_reaction_add', check=check_ok_emoji, timeout=60)
            await msg.delete()

        except asyncio.TimeoutError:
            try:
                await msg.remove_reaction(emojis.ok_emoji, client.user)
            except:
                pass
# end edit_user_embed


async def save_embed(client, message, args):
    """
        ..p embed save <msg_id> [#channel] [embed_name]
    """

    # TODO embed save help

    if message.channel_mentions:
        channel = message.channel_mentions[0]
        del args[1]

    else:
        channel = message.channel


    mesge_id = Support.get_id_from_str(args[0])
    del args[0]
    if mesge_id:
        try:
            mesge = await channel.fetch_message(int(mesge_id[0]))

        except discord.errors.NotFound:
            await Support.previous_action_error(client, message)
            Logger.log("embed save", "mesge not found") # TODO embed save error
            return

        embed = mesge.embeds[0] if mesge.embeds else None # BUG error when saving in dms
        if embed:
            gcm = (mesge.guild.id if mesge.guild else message.author.id, mesge.channel.id, mesge.id) # guild channel message
            name = f"-{'_'.join(args)}" 
            embed = SavedEmbed(*gcm, embed, name=name[1:] if name != "-" else "")
            embed = embed.save_embed()

            await Support.process_complete_reaction(message)
            Logger.log("embed save", f"embed saved - {embed.path}")

        else:
            await Support.previous_action_error(client, message)
            Logger.log("embed save error", "embed does not exist at this location") # TODO embed save error
            return

    else:
        await Support.previous_action_error(client, message)
        Logger.log("embed save error", "no message id given") # TODO embed save error 
        return
# end save_embed


async def convert(client, message, args):
    """
        ..p embed convert <message_id> [#channel]
        ..p embed convert <embed_name>
        ..p embed convert <embed_name> [guild_id] # is mo
    """

    # TODO embed convert help

    embed_dict = None
    saved_embeds = get_saved_embeds(guild_id=str(message.guild.id) if not args[1] else args[1])
    for saved_embed in saved_embeds:
        if args[0] == saved_embed.name:
            embed_dict = saved_embed.embed.to_dict()

    if not embed_dict:
        channel = message.channel_mentions[0] if message.channel_mentions else message.channel
        msg_id = Support.get_id_from_str(args[0])
        msg_id = int(msg_id[0]) if msg_id else None

        if msg_id:
            try:
                msg = await channel.fetch_message(int(args[0]))

                if msg.embeds:
                    embed_dict = msg.embeds[0].to_dict()

                else:
                    Logger.log("convert error", "no embed on this msg")
                    return

            except discord.errors.NotFound:
                Logger.log("convert embed", "msg not found") # TODO convert embed error
                return

        else:
            Logger.log("convert embed", "no msg id given") # TODO convert embed error
            return

    # should have embed_dict by now
    create_messages = Support.convert_embed_dict_to_create_messages(embed_dict)

    for c in create_messages:
        await message.channel.send(c)
# end convert



## RESPONSES ##

async def send_embed_help(client, message):
    msg = await Help.send_help_embed(client, message, Help.help_links.embed_menu, default_footer=False)
    Logger.log("EMBED", "Help")
    embed = msg.embeds[0]
    
    emojis = [Support.emojis.pencil_emoji, Support.emojis.floppy_disk_emoji, Support.emojis.clipboard_emoji] 
    for r in emojis[:1]: # FIXME EMBED HELP REACTIONS
        await msg.add_reaction(r)

    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and
            r_user.id == message.author.id and
            str(reaction.emoji) in emojis
        )
    # end reaction_check

    try:
        while True:
            reaction, user = await client.wait_for("reaction_add", check=reaction_check, timeout=120)


            if str(reaction.emoji) == emojis[0]: # pencil
                embed = get_saved_embeds(link=Help.help_links.creating_and_editing_embeds["link"])[0].embed

            elif str(reaction.emoji) == emojis[1]: # floppy disk
                embed = get_saved_embeds(link=Help.help_links.creating_and_editing_embeds["link"])[0].embed

            elif str(reaction.emoji) == emojis[2]: # clipboard
                embed = get_saved_embeds(link=Help.help_links.creating_and_editing_embeds["link"])[0].embed


            if str(reaction.emoji) in emojis:
                await msg.edit(embed=embed)
                await Support.clear_reactions(msg)
                break

    except asyncio.TimeoutError:
        await Support.clear_reactions(msg)

# end send_embed_help


async def send_permissions_needed(message, member):
    await Support.simple_bot_response(message.channel,
        title="Permissions Needed",
        description=f"You need the `Manage Messages` permission to create/edit embeds with {Support.get_phyner_from_channel(message.channel).mention}.",
        footer=help_footer,
        reply_message=message
    )
    await Logger.log("EMBED", "Member Permissons Needed")
# end send_permissions_needed


async def send_embed_attr_errors(message, msg_id, errors):
    title = "Embed Errors"
    description = ""
    for error in errors:
        description += f"{error[0]}\n{error[1]}\n\n"

    await Support.simple_bot_response(message.channel, title=title, description=description, reply_message=message)
# end send_embed_attr_errors