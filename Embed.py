''' IMPORTS '''

import discord
import asyncio
import traceback
import re
import validators

import Logger
import Support
from Support import emojis



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


''' FUNCTIONS '''

async def main(client, message, args, author_perms):

    if args[2] in [" ", "help", "?"]: # @Phyner <command> or @Phyner command help
        await send_embed_help(message.channel)


    elif args[2] == "create":

        if author_perms.manage_messages:
            await create_user_embed(client, message)

        else:
            await send_permissions_needed(message.channel, message.author)


    elif args[2] == "edit":
        
        if author_perms.manage_messages:
            await edit_user_embed(client, message, args)

        else:
            await send_permissions_needed(message.channel, message.author)

    return
# end main

def get_embed_from_content(client, content, roles, embed=discord.Embed()):
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

    content = content.replace("\\s", emojis.space_char)
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

    errors = []

    for i, attr in enumerate(attrs): # get attr values
        next_attr = attrs[i+1] if i < len(attrs) - 1 else None
        if attr == next_attr:
            continue

        value = content[
            content.index(attr) + len(attr) : content.index(next_attr) - 1 if next_attr else len(content)
        ]

        attr = attr.strip()
        value = value if ".empty" not in value else discord.Embed().Empty

        if attr in ['.content']:
            msg_content = value if value else emojis.space_char

        elif attr in [".color", ".colour"]:
            try:
                role_color = [r.color for r in roles if str(r.id) == value] # get role color
                color = abs(int(value.replace("#", ""), 16) + 1) if not role_color and value else role_color
                color = role_color[0].value if role_color else (color if color else value)

                if not value or color <= 16777216: # really it's supposed to be < 16777215, but fixing that below
                    embed.color = abs(color + (1 if color == 0 else -2)) if color else value

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

            field_name = fields[field_index]['name']
            field_value = fields[field_index]['value']

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
            fields[field_index]['name'] = field['name'] if field['name'] else emojis.space_char
            fields[field_index]['value'] = field['value'] if field['value'] else emojis.space_char
            embed['fields'].append(field)

    embed = discord.Embed().from_dict(embed)

    Logger.log('embed', embed.to_dict())
    return embed, msg_content, errors
# end get_attributes_from_content

async def create_user_embed(client, message):
    embed, content, errors = get_embed_from_content(client, message.content, message.guild.roles)
    msg = await message.channel.send(content=content, embed=embed)

    if True or Support.show_moving_editing_phyner_messages(message.author.id): # TODO ... this ability?

        title = "Moving and Editing Phyner Messages"

        description = f"`{msg.id}` is the Message ID of the [message]({msg.jump_url}) above.\n\n"

        description += f"**Edit Embed:**\n`@Phyner#2797 embed edit {msg.id}\n[edit embed attributes]`\n*send a new message, or edit your existing [embed create message]({message.jump_url})*\n\n"

        description += f"**Copy Message:**\n`@Phyner#2797 copy {msg.id} [some_msg_id] ... <#destination>`\n\n" # TODO @Phyner copy

        description += f"**Replace Message:**\n`@Phyner#2797 replace <some_phyner_msg_id> {msg.id}`\n\n" # TODO @Phyner replace

        description += f"{emojis.x_emoji} to never show this message again (also deletes this message)" # TODO ... this ability?

        msg = await Support.simple_bot_response(
            message.channel,
            title=title,
            description=description, 
            footer=help_footer,
            reply=message
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
            # Support.show_moving_editing_phyner_messages(message.author.id, show=False) # TODO ... this ability?
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
    msg = None
    msg_id = args[3]

    try: # try to find msg in current channel first
        msg = await message.channel.fetch_message(msg_id)

    except discord.errors.NotFound:
        await message.channel.trigger_typing()

        for channel in message.guild.channels:
            try:
                msg = await channel.fetch_message(msg_id)

            except AttributeError: # channel is not text channel
                pass
            except discord.errors.NotFound: # msg not found
                pass

    except discord.errors.HTTPException: # not a valid msg_id
        pass

    if msg and msg.author.id == Support.ids.phyner_id: # msg found and phyner is author
        embed = msg.embeds[0] if msg.embeds else None
        embed, content, errors = get_embed_from_content(
            client,
            message.content, 
            message.guild.roles, 
            embed=embed if embed else discord.Embed()
        )
        await msg.edit(content=content, embed=embed)
        
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
                reply=message
            )
            Logger.log('embed', "could not edit another author's message")

        else: # msg not found, by deduction
            description = f"The message_id, `{msg_id}`, could not be found in any of the channels {client.user.mention} is in.\n\n"

            description += f"`@Phyner#2797 ids` to learn how to get message_ids.\n"
            # TODO @Phyner ids
            msg = await Support.simple_bot_response(message.channel,
                title="Could Not Find Message",
                description=description,
                footer=help_footer,
                reply=message
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
            await msg.remove_reaction(emojis.ok_emoji, client.user)
        
# end edit_user_embed



async def send_embed_help(channel): # TODO proper help message

    description = f"For help with embeds, click [__here__](https://github.com/nosv1/Phyner/wiki/Custom-Embed-Messages) to visit the Phyner wiki page for **User Embeds**."

    await Support.simple_bot_response(channel,
        title = "Custom Embed Messages",
        description=description
    )
    Logger.log("EMBED", "Help")
# end send_embed_help

async def send_permissions_needed(channel, member):
    await Support.simple_bot_response(channel,
        title="Permissions Needed",
        description=f"{member.mention}, you need the `Manage Messages` permission to create/edit embeds with {Support.get_phyner_from_channel(channel).mention}.",
        footer=help_footer
    )
    await Logger.log("EMBED", "Member Permissons Needed")
# end send_permissions_needed

async def send_embed_attr_errors(message, msg_id, errors):
    title = "Embed Errors"
    description = ""
    for error in errors:
        description += f"{error[0]}\n{error[1]}\n\n"

    await Support.simple_bot_response(message.channel, title, description, reply=message)
# end send_embed_attr_errors