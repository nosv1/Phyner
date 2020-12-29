''' IMPORTS '''

import asyncio
import copy
from datetime import datetime
import discord
import gspread
import re
import traceback

from gspread.utils import rowcol_to_a1
from mysql.connector.errorcode import ER_MASTER_HAS_PURGED_REQUIRED_GTIDS


import Database
import Guilds
import Logger
from Logger import log
import Help
import Support
from Support import create_aliases, edit_aliases
from Support import simple_bot_response



''' CONSTANTS '''

table_length = 1500
table_aliases = ["table", "tables"]

table_styles = ["multi_markdown", "single_markdown", "plain"]



''' CLASSES '''

class Table:
    def __init__(self, guild_id=None, channel_id=None, msg_ids=[], range=None, workbook_key=None, worksheet_id=None, cells=[], left_aligned=["all"], right_aligned=['none'], centered=['none'], headers=['none'], no_markdown_cols=['none'], no_markdown_rows=['none'], table_style=table_styles[0], for_embed=False, update_interval=0, buffer_messages=0):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.msg_ids = msg_ids # max 9 messages per table, given max primary key length wont allow for 210 chars
        self.old_msg_ids = copy.copy(self.msg_ids)

        self.guild = None
        self.channel = None
        self.messages = []


        self.range = a1_to_numeric(range) if range else None
        self.workbook_key = workbook_key
        self.worksheet_id = worksheet_id

        self.workbook = None
        self.worksheet = None
        self.worksheets = []


        self.cells = cells # this is from the gspread.range
        self.cell_values = []
        if cells:
            self.get_cell_values()

        self.tables = []


        # style options
        self.left_aligned = [a1_to_numeric(r) for r in left_aligned]
        self.right_aligned = [a1_to_numeric(r) for r in right_aligned]
        self.centered = [a1_to_numeric(r) for r in centered]
        self.headers = [a1_to_numeric(r) for r in headers]


        self.no_markdown_cols = [a1_to_numeric(r) for r in no_markdown_cols] # these are overwritten by multi_markdown style
        self.no_markdown_rows = [a1_to_numeric(r) for r in no_markdown_rows] # these also need to be corrected for offset, B:C should be 0 and 1 not 2 and 3


        self.table_style = table_style # see table styles constant
        self.for_embed = for_embed # if embed, then embed.description else content

        self.update_interval = update_interval # default to 0, no auto updating, free 1 per day, manual 1 per hour, manual from command
        self.buffer_messages = buffer_messages
    # end __init__


    def open_workbook(self):
        gc = Support.get_g_client()
        self.workbook = gc.open_by_key(self.workbook_key)
    # end open_workbook


    def get_worksheet(self):
        if not self.workbook:
            self.open_workbook()

        self.worksheets = self.workbook.worksheets() if not self.worksheets else self.worksheets
        self.worksheet = [ws for ws in self.worksheets if str(ws.id) == self.worksheet_id]
        self.worksheet = self.worksheet[0] if self.worksheet else None
    # end get_worksheet


    def get_cells(self):
        if not self.worksheet:
            self.get_worksheet()

        first_row = self.range[0][1]
        first_col = self.range[0][0]
        last_row = self.range[1][1] if self.range[1][1] != "_" else self.worksheet.row_count
        last_col = self.range[1][0] if self.range[1][0] != "_" else self.worksheet.col_count

        self.cells = self.worksheet.range(first_row, first_col, last_row, last_col)
        self.get_cell_values()
    # end get_table


    def get_cell_values(self):
        self.cell_values = []

        row = [self.cells[0]]
        for cell in self.cells[1:]:

            if cell.row != row[-1].row:
                self.cell_values.append([c.value for c in row])
                row = [cell]

            else:
                row.append(cell)

        self.cell_values.append([c.value for c in row])
    # end get_cell_values


    def get_table_displays(self):
        """
            styles: multi_markdown, single_markdown, plain
            if single line markdown, ability to not markdown specific columns
            ability to not markdown specific rows
        """

        is_multi_markdown = self.table_style == "multi_markdown" # everything surroudned by ```
        is_single_markdown = self.table_style == "single_markdown" # individual rows surroudned by `
        is_plain = self.table_style == "plain"

        numeric_range = self.range
        col_offset = numeric_range[0][0]
        row_offset = numeric_range[0][1] 


        ## GET MAX WIDTHS ##

        if not self.cells:
            self.get_cells()

        col_max_widths = [0] * len(self.cell_values[0])
        for i, row in enumerate(self.cell_values):

            for j, value in enumerate(row):

                if row_col_in_range(i + row_offset, j + col_offset, self.headers) and is_single_markdown:
                    value = f"[{value}]"

                col_max_widths[j] = len(value) if len(value) > col_max_widths[j] else col_max_widths[j]

        print(col_max_widths)


        ## CREATE TABLES ##

        tables = [""]
        tables[-1] += "```" if is_multi_markdown else ""

        for i, row in enumerate(self.cell_values): # loop rows
            
            line = []
            for j, value in enumerate(row): # loop cols in row
                v = ""
                if row_col_in_range(i + row_offset, j + col_offset, self.left_aligned): # left align
                    v = value.ljust(col_max_widths[j], " ")

                if row_col_in_range(i + row_offset, j + col_offset, self.right_aligned): # right align
                    v = value.rjust(col_max_widths[j], " ")

                if row_col_in_range(i + row_offset, j + col_offset, self.centered): # center
                    v = value.center(col_max_widths[j], " ")

                if row_col_in_range(i + row_offset, j + col_offset, self.headers): # center

                    if is_single_markdown or is_multi_markdown:
                        value = f"[{value}]"

                    elif is_plain:
                        value = f"**{value}**"
                    
                    v = value.center(col_max_widths[j], " ")

                if (
                    is_single_markdown and 
                    not row_col_in_range(i + row_offset, j + col_offset, self.no_markdown_cols)
                ): # wrap in ``, once wrapped later, it will reverse the effect
                    v = f"`{v}`"

                line.append(v)


            line = f"{'|' if is_multi_markdown else ' '}".join(line)


            if (
                is_single_markdown and
                row_col_in_range(i + row_offset, j + col_offset, self.no_markdown_rows)
            ): # remove ` if no markdown row
                line = line.replace("`", "")

            
            line = f"{line}\n"
                
            
            if len(tables[-1] + line) < table_length: # yes, new table = new message
                tables[-1] += line

            else:
                tables[-1] += "```\n" if is_multi_markdown else ""
                tables.append("```" if is_multi_markdown else "")
                tables[-1] += line

        tables[-1] += "```\n" if is_multi_markdown else ""

        # wrapping in zero width to be able to identify tables in messages later
        print('yes')
        self.tables = [f"{Support.emojis.zero_width*2}{table[:-1]}{Support.emojis.zero_width*2}" for table in tables]
        print(Support.emojis.zero_width*2 in self.tables[-1])
    # end get_table_displays


    async def send_table(self, client):
        guild = client.get_guild(self.guild_id)
        destination = guild.get_channel(self.channel_id)

        # check if table exists in channel based off existing message id
        prev_message = None
        if self.msg_ids:
            try:
                prev_message = await destination.fetch_message(self.msg_ids[0])

            except discord.errors.NotFound:
                pass


        if not self.tables:
            self.get_table_displays()

        send_new = True
        if prev_message: # possible existing messages to accomodate an edit
            
            if len(self.tables) <= len(self.msg_ids): # if enough possible messages to accomodate
                print('yes')
                send_new = False

                mesges = []
                self.messages = []

                # first, checking for validitiy in all the message ids, are they suitable to place tables in
                for mesge_id in self.msg_ids:

                    mesge = await destination.fetch_message(mesge_id)
                    embed = mesge.embeds[0] if mesge.embeds else None
                    content = mesge.content # is "" if blank

                    if embed:
                        if embed.description:
                            split = embed.description.split(Support.emojis.zero_width*2) 
                            if len(split) == 3: # has table inside
                                mesges.append(mesge)

                        else: # if no description, we can add one :D
                            mesges.append(mesge)

                    elif content:
                        split = content.split(Support.emojis.zero_width*2)
                        if len(split) == 3:
                            mesges.append(mesge)


                if len(self.tables) <= len(mesges): # enough valid messages to accomodate
                
                    for i, table in enumerate(self.tables): # udpate messages for needed tables, later clearing not used messages
                        mesge = mesges[i]
                        
                        embed = mesge.embeds[0] if mesge.embeds else None
                        content = mesge.content

                        split = []
                        if embed:
                            if embed.description:
                                split = embed.description.split(Support.emojis.zero_width*2)

                            else: # there may not be a description in embed, doesn't stop me tho!
                                split = ["", "", ""]

                        else:
                            split = content.split(Support.emojis.zero_width*2)

                        split[1] = table # already has zero_width chars in it

                        if embed:
                            embed.description = "".join(split)

                        else:
                            content = "".join(split)


                        await mesge.edit(content=content, embed=embed)
                        self.messages.append(mesge)


                    for mesge in mesges[len(self.tables):]: # clear not updated messages
                        
                        embed = mesge.embeds[0] if mesge.embeds else None
                        content = mesge.content

                        if embed:
                            if embed.description:
                                split = embed.description.split(Support.emojis.zero_width*2)
                                if len(split) == 3: # had table in it
                                    split[1] = ""
                                    embed.description = "".join(split)

                        else:
                            split = content.split(Support.emojis.zero_width*2)
                            if len(split) == 3:
                                split[1] = ""
                                content = "".join(split)

                        await mesge.edit(content=content, embed=embed)


        print('send, new')
        if send_new: # SEND IT
            new_ids = []
            self.messages = []
            for table in self.tables:
                if self.for_embed:
                    msg = await simple_bot_response(destination, description=table)

                else:
                    msg = await destination.send(table)

                new_ids.append(msg.id)
                self.messages.append(msg)

            self.old_msg_ids = self.msg_ids
            self.msg_ids = new_ids


        await self.messages[-1].add_reaction(Support.emojis.counter_clockwise_arrows_emoji)
        self.update_table(get_tables(guild_id=self.guild_id))
    # end send_table


    def update_table(self, tables):
        """
        """

        db = Database.connect_database()

        existing = False
        for table in tables:

            print(self.old_msg_ids, table.msg_ids)
            if self.old_msg_ids == table.msg_ids:
                print('yes')
                existing = True

                sql = f"""
                    UPDATE Tables SET 
                        `guild_id` = '{self.guild_id}',
                        `channel_id` = '{self.channel_id}',
                        `message_ids` = '{",".join([str(m_id) for m_id in self.msg_ids])}',
                        `range` = '{numeric_to_a1(self.range)}',
                        `workbook_key` = '{self.workbook_key}',
                        `worksheet_id` = '{self.worksheet_id}',
                        `left_aligned` = '{','.join([numeric_to_a1(r) for r in self.left_aligned])}',
                        `right_aligned` = '{','.join([numeric_to_a1(r) for r in self.right_aligned])}',
                        `centered` = '{','.join([numeric_to_a1(r) for r in self.centered])}',
                        `headers` = '{','.join([numeric_to_a1(r) for r in self.headers])}',
                        `no_markdown_cols` = '{','.join([numeric_to_a1(r) for r in self.no_markdown_cols])}',
                        `no_markdown_rows` = '{','.join([numeric_to_a1(r) for r in self.no_markdown_rows])}',
                        `style` = '{self.table_style}',
                        `embed` = '{1 if self.for_embed else 0}',
                        `update_interval` = '{self.update_interval}'
                    WHERE 
                        `message_ids` = '{",".join([str(m_id) for m_id in self.old_msg_ids])}'
                ;"""
                break

        if not existing:
            sql = f"""
                INSERT INTO Tables (

                    `guild_id`,
                    `channel_id`,
                    `message_ids`,
                    `range`,
                    `workbook_key`,
                    `worksheet_id`,
                    `left_aligned`,
                    `right_aligned`,
                    `centered`,
                    `headers`,
                    `no_markdown_cols`,
                    `no_markdown_rows`,
                    `style`,
                    `embed`,
                    `update_interval`

                ) VALUES (

                    '{self.guild_id}',
                    '{self.channel_id}',
                    '{",".join([str(m_id) for m_id in self.msg_ids])}',
                    '{numeric_to_a1(self.range)}',
                    '{self.workbook_key}',
                    '{self.worksheet_id}',
                    '{','.join([numeric_to_a1(r) for r in self.left_aligned])}',
                    '{','.join([numeric_to_a1(r) for r in self.right_aligned])}',
                    '{','.join([numeric_to_a1(r) for r in self.centered])}',
                    '{','.join([numeric_to_a1(r) for r in self.headers])}',
                    '{','.join([numeric_to_a1(r) for r in self.no_markdown_cols])}',
                    '{','.join([numeric_to_a1(r) for r in self.no_markdown_rows])}',
                    '{self.table_style}',
                    '{1 if self.for_embed else 0}',
                    '{self.update_interval}'
                )
            ;"""

        db.cursor.execute(sql)
        db.connection.commit()
        db.connection.close()
    # end edit_table


    def to_string(self):
        return f"spreadsheet: {self.workbook_key}, worksheet: {self.worksheet}, message_ids: {self.msg_ids}"
    # end to_string
# end Table



''' FUNCTIONS '''

async def main(client, message, args, author_perms):
    """
        @Phyner table create <spreadsheet_link> <tab_name> <range> <#channel>
    """


    if args[1] in Help.help_aliases:
        await Support.previous_action_error(client, message)
        log("tables", "help message") # TODO tables error


    elif args[1] in create_aliases and not message.edited_at:
        await get_table_from_user_input(client, message, author_perms)


    elif args[1] in edit_aliases:
        await edit_table(client, message, get_table(args[2], message.guild.id))
# end main


async def get_table_from_user_input(client, message, author_perms):
    """
    """
    msg = None

    if not author_perms.manage_messages: # MISSING PERMS BRO
        Support.previous_action_error(client, message)
        log("tables", "missing perms") # TODO tables error
        return
        

    def message_edit_check(before, after):
        return after.id == message.id
    # end message_edit_check


    def reaction_check(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in [Support.emojis.tick_emoji]
        )
    # end reaction_check


    args, content = Support.get_args_from_content(message.content)

    phyner = Support.get_phyner_from_channel(message.channel)
    guild_prefix = Guilds.get_guild_prefix(message.guild.id)


    # syntax examples
    syntax_example_template = f"`{guild_prefix} table {args[2]} <spreadsheet_url> <tab_name> <range> <#channel>`"
    syntax_example_real = f"`{guild_prefix} table {args[2]} <https://docs.google.com/spreadsheets/d/1Hg2eyyfbSSACMMIBx1FBvNRschQFsxmgPS-oqCFeRJ8/edit#gid=0> Standings A1:B10` #standings"


    missing_arg_embed = await simple_bot_response(message.channel,
        title="**Missing Argument**",
        description="",
        footer=f"{guild_prefix} table help",
        send=False
    )


    table = Table(
        guild_id=message.guild.id if message.guild else message.author.id,
        left_aligned=["all"]
    )
    table.guild = message.guild if message.guild else message.author


    ''' get key '''
    while not table.workbook_key:

        args, content = Support.get_args_from_content(message.content)

        # https://docs.google.com/spreadsheets/d/1Hg2eyyfbSSACMMIBx1FBvNRschQFsxmgPS-oqCFeRJ8/edit#gid=0
        # 1Hg2eyyfbSSACMMIBx1FBvNRschQFsxmgPS-oqCFeRJ8
        key = re.findall(r"(?:\/d\/)(\S+)(?:\/)", args[3])

        if key:
            table.workbook_key = key[0]

        else:

            missing_arg_embed.description = "There was not a spreadsheet linked in your message.\n\n"

            missing_arg_embed.description += "**Syntax:**\n"
            missing_arg_embed.description += f'{syntax_example_template.replace("spreadsheet_url", "SPREADSHEET_URL")}\n\n'

            missing_arg_embed.description += f"{syntax_example_real}\n\n"

            missing_arg_embed.description += f"**Edit your [message above]({message.jump_url}) to continue.**"


            # prompt user
            if msg:
                await msg.edit(embed=missing_arg_embed)

            else:
                msg = await message.reply(embed=missing_arg_embed)
            await message.add_reaction(Support.emojis.x_emoji)


            # wait
            try:
                before, after = await client.wait_for("message_edit", check=message_edit_check, timeout=300)
                await Support.remove_reactions(message, client.user, [Support.emojis.x_emoji])
                message = after

            except asyncio.TimeoutError:
                missing_arg_embed.title += "\nTimed Out"
                await msg.edit(embed=missing_arg_embed)
                return

    # end while


    ''' got workbook key, but now check for perms '''
    while not table.workbook:

        try:
            table.open_workbook()

        except gspread.exceptions.APIError as gspread_error:

            if gspread_error['status'] == "PERMISSION_DENIED":

                description = f"{phyner.mention} does not have access to the linked spreadsheet.\n\n"

                description += f"Share the spreadsheet with the email below (hold to copy), then click the {Support.emojis.tick_emoji} to continue.\n"
                description += f"*You don't need to give {phyner.mention} editor access, but it does need view permission. You can also ignore the email regarding `Mail Delivery Error`, as it is expected when sharing with a service account.*"

                embed = simple_bot_response(message.channel,
                    title="**No Access to Spreadsheet**",
                    description=description,
                    send=False
                )


                # prompt
                if msg:
                    await msg.edit(embed=embed)
                else:
                    msg = await message.channel.send(embed=embed)

                email_msg = await message.channel.send(Support.ids.phyner_service_account)

                await msg.add_reaction(Support.emojis.tick_emoji)


                # wait
                try:
                    await client.wait_for("reaction_add", check=reaction_check, timeout=300)
                    await email_msg.delete()
                    await Support.clear_reactions(msg)

                except asyncio.TimeoutError:
                    missing_arg_embed.title += "\nTimed Out"
                    await msg.edit(embed=missing_arg_embed)
                    return
    # end while 


    ''' GET TAB'''
    table.worksheets = table.workbook.worksheets()
    while not table.worksheet:

        args, content = Support.get_args_from_content(message.content)

        if args[4]: # possible tab name
            for worksheet in table.worksheets:
                a, c = Support.get_args_from_content(worksheet.title)
                a = " ".join(a).strip().lower()

                for i in range(len(args), 4, -1): # loop backwards through args, getting new tab name each time with less args
                    tab_name_args = args[4:i]
                    tab_name = " ".join(tab_name_args)

                    if a == tab_name.lower():
                        table.worksheet = worksheet
                        table.worksheet_id = worksheet.id
                        break
                
                if table.worksheet:
                    break


        if not table.worksheet:

            missing_arg_embed.description = f"There were no matching tab names in your message.\n\n"

            missing_arg_embed.description += "**Syntax:**\n"
            missing_arg_embed.description += f'{syntax_example_template.replace("tab_name", "TAB_NAME")}\n\n'

            missing_arg_embed.description += f"{syntax_example_real}\n\n"

            missing_arg_embed.description += f"**Edit your [message above]({message.jump_url}) to continue.**"


            # prompt user
            if msg:
                await msg.edit(embed=missing_arg_embed)
            else:
                msg = await message.channel.send(embed=missing_arg_embed)
            await message.add_reaction(Support.emojis.x_emoji)


            # wait
            try:
                before, after = await client.wait_for("message_edit", check=message_edit_check, timeout=300)
                await Support.remove_reactions(message, client.user, [Support.emojis.x_emoji])
                message = after

            except asyncio.TimeoutError:
                missing_arg_embed.title += "\nTimed Out"
                await msg.edit(embed=missing_arg_embed)
                return

    # end while


    ''' GET RANGE '''
    while not table.range:

        args, content = Support.get_args_from_content(message.content)
        args = [a.lower() for a in args]

        # range should be the arg after the last word of the tab name
        a1_user_range = args[args.index(table.worksheet.title.lower().split(" ")[-1]) + 1]


        if a1_user_range: # not ''
            try:
                table.range = a1_to_numeric(a1_user_range)
                table.get_cells()
            
            except gspread.exceptions.APIError: # likely invalid argument
                table.range = None
                table.cells = []


        if not table.range:

            missing_arg_embed.description = f"There was not a valid range in your message.\n\n"

            missing_arg_embed.description += "**Syntax:**\n"
            missing_arg_embed.description += f'{syntax_example_template.replace("range", "RANGE")}\n\n'

            missing_arg_embed.description += f"{syntax_example_real}\n\n"

            missing_arg_embed.description += f"**Edit your [message above]({message.jump_url}) to continue.**"


            # prompt user
            if msg:
                await msg.edit(embed=missing_arg_embed)
            else:
                msg = await message.channel.send(embed=missing_arg_embed)
            await message.add_reaction(Support.emojis.x_emoji)


            # wait
            try:
                before, after = await client.wait_for("message_edit", check=message_edit_check, timeout=300)
                await Support.remove_reactions(message, client.user, [Support.emojis.x_emoji])
                message = after

            except asyncio.TimeoutError:
                missing_arg_embed.title += "\nTimed Out"
                await msg.edit(embed=missing_arg_embed)
                return

    # end while


    ''' GET CHANNEL '''
    while not table.channel_id:

        if message.channel_mentions:
            table.channel = message.channel_mentions[-1]
            table.channel_id = table.channel.id


        if not table.channel:

            missing_arg_embed.description = f"There was not a destination channel in your message.\n\n"

            missing_arg_embed.description += "**Syntax:**\n"
            missing_arg_embed.description += f'{syntax_example_template.replace("channel", "CHANNEL")}\n\n'

            missing_arg_embed.description += f"{syntax_example_real}\n\n"

            missing_arg_embed.description += f"**Edit your [message above]({message.jump_url}) to continue.**"


            # prompt user
            if msg:
                await msg.edit(embed=missing_arg_embed)
            else:
                msg = await message.channel.send(embed=missing_arg_embed)
            await message.add_reaction(Support.emojis.x_emoji)


            # wait
            try:
                before, after = await client.wait_for("message_edit", check=message_edit_check, timeout=300)
                await Support.remove_reactions(message, client.user, [Support.emojis.x_emoji])
                message = after

            except asyncio.TimeoutError:
                missing_arg_embed.title += "\nTimed Out"
                await msg.edit(embed=missing_arg_embed)
                return

    # end while

    await edit_table(client, message, [table])
# end get_table_from_user_input


async def edit_table(client, message, table):
    """
    """
    await message.channel.trigger_typing()

    if table:
        table = table[0]
        if not table.workbook:
            table.open_workbook()
            table.get_worksheet()
            table.get_cells()

    else:
        await Support.previous_action_error(client, message)
        log("edit table", "table does not exist") # TODO edit table error
        return


    msg = None
    reactions = []
    for c in "abcdefghijkl":
        reactions.append(Support.emojis.letter_emojis[c])

    def reaction_check(reaction, r_user):
        return (
            r_user.id == message.author.id and
            reaction.message.id == msg.id and
            str(reaction.emoji) in [Support.emojis.floppy_disk_emoji] + reactions
        )
    # end reaction_check

    def message_check(mesge):
        return (
            mesge.author.id == message.author.id and
            mesge.channel.id == message.channel.id
        )
    # end message_check


    async def build_embed():
        embed = await simple_bot_response(message.channel,
            title="**Table Editing**",
            description="",
            send=False
        )


        embed.description += f"**Workbook**: `{table.workbook.title}`\n"
        embed.description += f":regional_indicator_a: **Worksheet:** `{table.worksheet.title}`\n"
        embed.description += f":regional_indicator_b: **Range:** `{numeric_to_a1(table.range)}`\n"
        
        embed.description += f":regional_indicator_c: **Message IDs:** {' '.join([f'[{m.id}]({m.jump_url})' for m in table.messages])}\n\n" # insert diff msg ids to edit existing messages with tabels?

        embed.description += f":regional_indicator_d: **Headers:** `{' '.join([numeric_to_a1(r) for r in table.headers])}`\n"
        embed.description += f":regional_indicator_e: **Left Aligned:** `{' '.join([numeric_to_a1(r) for r in table.left_aligned])}`\n"
        embed.description += f":regional_indicator_f: **Right Aligned:** `{' '.join([numeric_to_a1(r) for r in table.right_aligned])}`\n"
        embed.description += f":regional_indicator_g: **Centered:** `{' '.join([numeric_to_a1(r) for r in table.centered])}`\n\n"

        embed.description += f":regional_indicator_h: **No Markdown Columns:** `{' '.join([numeric_to_a1(r) for r in table.no_markdown_cols])}`\n"
        embed.description += f":regional_indicator_i: **No Markdown Rows:** `{' '.join([numeric_to_a1(r) for r in table.no_markdown_rows])}`\n\n"

        embed.description += ":regional_indicator_j: **Table Style:** multi_markdown/single_markdown/plain\n".replace(table.table_style, f"`{table.table_style}`")
        embed.description += f":regional_indicator_k: **For Embed?:** {'`Yes`/No' if table.for_embed else 'Yes/`No`'}\n"
        embed.description += f":regional_indicator_l: **Update Interval:** `{f'{table.update_interval} seconds' if table.update_interval else 'Manual'}`\n"
        # embed.description += f":regional_indicator_m: **Buffer Messages:** `{table.buffer_messages}`\n" # TODO BUFFER MESSAGES

        return embed
    # end build_embed


    async def refresh_table(): # get new displays, send new tables, update msg ids        
        table.get_cells()
        table.get_table_displays()
        await table.send_table(client)

        embed = await build_embed()

        # edit embed with new msg ids
        embed.set_footer(
            text=f"{Support.emojis.floppy_disk_emoji} Save/Update | Saved {datetime.utcnow().strftime('%H:%M UTC')}"
        )
        await msg.edit(embed=embed)
        return embed
    # end refresh_table


    # build starter embed from existing table
    embed = await build_embed()
    embed.set_footer(text="Updating...")
    msg = await message.channel.send(embed=embed)


    # send/update table
    embed = await refresh_table()

    await msg.add_reaction(Support.emojis.floppy_disk_emoji)
    [await msg.add_reaction(r) for r in reactions]


    mesge = None
    reaction = None
    r_user = None

    timeout=False # used for timeout warning
    while True:
        
        done, pending = await asyncio.wait([
            client.wait_for('reaction_add', check=reaction_check),
            client.wait_for('message', check=message_check),
            ],
            timeout=480 if not timeout else 120,
            return_when=asyncio.FIRST_COMPLETED # default, can also have asyncio.FIRST_COMPLETED
        )


        if done: # something finished
            timeout = False

            for task in done:
                if type(task.result()) == discord.message.Message:
                    mesge = task.result()

                else:
                    reaction, r_user = task.result()

            print(reaction, r_user, mesge)

            if reaction: # reaction clicked
                await msg.add_reaction(Support.emojis._9b9c9f_emoji)

                if str(reaction.emoji) == Support.emojis.floppy_disk_emoji:
                    embed = await refresh_table()


                elif reactions.index(str(reaction.emoji)) == 9: # table style
                    table.table_style = table_styles[
                        table_styles.index(table.table_style) - (len(table_styles) - 1)
                    ] # toggle through array, 0 becomes 1, 1 becomes 2...

                elif reactions.index(str(reaction.emoji)) == 10: # for embed?
                    table.for_embed = abs(table.for_embed - 1)


                elif str(reaction.emoji) in reactions and mesge: # letter emoji clicked and mesge sent
                    a, c = Support.get_args_from_content(mesge.content)
                    mesge_content = " ".join(a).strip()
                    print('adding reaction')

                    if reactions.index(str(reaction.emoji)) == 0: # worksheet

                        for ws in table.worksheets:
                            a, c = Support.get_args_from_content(ws.title)
                            ws_title = " ".join(a).strip()

                            if mesge_content.lower() == ws_title.lower() or mesge_content == str(ws.id):
                                table.worksheet = ws
                                table.worksheet_id = ws.id
                                break

                    elif reactions.index(str(reaction.emoji)) == 1: # range

                        try:
                            t_table = copy.copy(table)
                            t_table.range = a1_to_numeric(mesge_content)
                            t_table.get_cells()
                            table = copy.copy(t_table)
                        except gspread.exceptions.APIError:
                            pass

                    elif reactions.index(str(reaction.emoji)) == 2: # TODO message ids
                        pass


                    elif reactions.index(str(reaction.emoji)) == 3: # Headers
                        table.headers = [a1_to_numeric(r) for r in mesge_content.split(" ")]

                    elif reactions.index(str(reaction.emoji)) == 4: # left_aligned
                        table.left_aligned = [a1_to_numeric(r) for r in mesge_content.split(" ")]

                    elif reactions.index(str(reaction.emoji)) == 5: # right_aligned
                        table.right_aligned = [a1_to_numeric(r) for r in mesge_content.split(" ")]

                    elif reactions.index(str(reaction.emoji)) == 6: # centered
                        table.centered = [a1_to_numeric(r) for r in mesge_content.split(" ")]


                    elif reactions.index(str(reaction.emoji)) == 7: # no_markdown_cols
                        table.no_markdown_cols = [a1_to_numeric(r) for r in mesge_content.split(" ")]

                    elif reactions.index(str(reaction.emoji)) == 8: # no_markdown_rows
                        table.no_markdown_rows = [a1_to_numeric(r) for r in mesge_content.split(" ")]

                    print('deleting')
                    await mesge.delete()


                footer = embed.to_dict()['footer']['text']
                print('building')
                embed = await build_embed()
                embed.set_footer(text=footer)
                print('editing')
                await msg.edit(embed=embed)


                print('removing')
                await Support.remove_reactions(msg, msg.author, Support.emojis._9b9c9f_emoji)
                await Support.remove_reactions(msg, r_user, str(reaction.emoji))
                reaction = None


            for future in pending:
                future.cancel()
                    

        elif timeout:
            embed.title += "\nTimed Out"
            await msg.edit(embed=embed)
            await Support.clear_reactions(msg)
            break

        else:
            timeout = True
            await simple_bot_response(message.channel,
                description="**Table Editing time out in 2 minutes. Remember to save your changes**",
                reply_message=message,
                delete_after=120
            )
# end edit_table


def row_col_in_range(row, col, numeric_ranges):
    """
        numeric_range is A1:B10 >> [[1, 1], [2, 10]]
    """

    in_ranges = []
    for numeric_range in numeric_ranges:
        if numeric_range == "all":
            return True

        if numeric_range == "none":
            return False

        in_ranges.append(
            row >= numeric_range[0][1] and
            (numeric_range[1][1] == "_" or row <= numeric_range[1][1]) and
            col >= numeric_range[0][0] and
            (numeric_range[1][0] == "_" or col <= numeric_range[1][0])
        )

    return any(in_ranges)
# end row_col_in_range


def a1_to_numeric(a1_range):
    """
        A1:B10 >> [[1, 1], [2, 10]]
        A:B >> [[1, 1], [2, _]]
        A:1 >> [[1, 1], [1, 1]]
        A: >> [[1, 1], [_, _]]
        _ is to end
    """


    if a1_range in ["all", "none"]:
        return a1_range


    range = [[0, 0], [0, 0]]
    a1_cells = f"{a1_range.upper()}:".split(":")[:2] # A1 >> A1: >> [A1, ''], A1:A10 >> A1:A10: >> [A1, A10]


    for i, cell in enumerate(a1_cells): 


        ## GET COLS ##

        col = re.findall(r"([A-Z]+)", cell)

        if col: # letters in cell
            for j, letter in enumerate(col[0][::-1]): # reverse letters so 26 ^ j works out easier
                range[i][0] += (ord(letter) - ord("A") + 1) * (26 ** j) # C - A + 1 = 3 * the digit, i.e. 3 * (26 ** 1) if 2nd digit

        elif i == 0: # if first cell, col = A, or 1
            range[i][0] = 1

        else: # if second cell, col = first cell's col
            range[i][0] = "_"


        ## GET ROWS ## 

        row = re.findall(r"(\d+)", cell)

        if row: # row given
            range[i][1] = int(row[0])

        elif i == 0: # if first cell row = 1
            range[i][1] = 1

        else: # if second cell, row = _
            range[i][1] = "_"


    if range[1][0] != "_" and range[1][0] < range[0][0]: # switcherro if right col is bigger than left and not 0
        t = range[0][0]
        range[0][0] = range[1][0]
        range[1][0] = t

    if range[1][1] != "_" and range[1][1] < range[0][1]: # same as above but for rows
       t = range[0][1]
       range[0][1] = range[1][1]
       range[1][1] = t

    return range
# end a1_to_numeric


def numeric_to_a1(numeric_range):
    """
        [[1, 1], [2, 10]] >> A1:B10
        [[1, 1], [2, 0]] >> A1:B_
    """

    if numeric_range in ["all", "none"]:
        return numeric_range

    a1_range = ""
    for cell in numeric_range:
    
        ## GET COL ##

        col = cell[0]
        col_letters = ""
        while True:
            if col == "_" or col < 26: # single letter column
                if col != "_":
                    col_letters += chr(col + ord("A") - 1)
                else:
                    col_letters += "_"
                break

            # 53 >> BA
            r = col % 26 # 53 % 26 = 1, or A
            col_letters += chr(r + ord("A") - 1) # the remainder is the letter
            col = (col // 26) # 53 // 26 = 2, so last letter is A

        # end while

        a1_range += f"{col_letters[::-1]}{cell[1]}:" # reverse col and append the row


    return a1_range[:-1] # rids the extra :
# end numeric_to_a1


def get_table_from_entry(entry):
    return Table (
        guild_id=int(entry[0]),
        channel_id=(int(entry[1]) if entry[1] else None),
        msg_ids=([int(m_id) for m_id in entry[2].split(",")] if entry[2] else []),

        range=entry[3],
        workbook_key=entry[4],
        worksheet_id=entry[5],

        left_aligned=entry[6].split(","),
        right_aligned=entry[7].split(","),
        centered=entry[8].split(","),
        headers=entry[9].split(","),

        no_markdown_cols=entry[10].split(","),
        no_markdown_rows=entry[11].split(","),

        table_style=entry[12],
        for_embed=int(entry[13]),
        update_interval=int(entry[14]),
        buffer_messages=int(entry[15])
    )
# end get_table_from_entry


def get_table(message_id, guild_id):
    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT * FROM Tables
        WHERE 
            message_ids LIKE '%{message_id}%' AND
            guild_id LIKE '{guild_id}'
    ;""")
    db.connection.close()
    return [get_table_from_entry(entry) for entry in db.cursor.fetchall()]
# end get_table


def get_tables(guild_id="%%"):
    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT * FROM Tables
        WHERE guild_id LIKE '{guild_id}'
    ;""")
    db.connection.close()
    return [get_table_from_entry(entry) for entry in db.cursor.fetchall()]
# end Tables