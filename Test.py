''' IMPORTS '''

import asyncio
import discord
from PIL import ImageDraw, Image, ImageShow, ImageFont

import os
from dotenv import load_dotenv
load_dotenv()


from Stats import command_used
import Support
from Support import simple_bot_response



''' FUNCTIONS '''

## TETS ##
def test():

    time_trial_table = [
        ["Time Trial - Avg: 2:12.865"],
        ["Pos", "Race?", "Driver", "Lap Time", "Delta", "Pace v Field", "Rival"],
        ["1", "TRUE", "Rezorects", "2:09.765", "+0.000", "1.000", "", "FALSE"],
        ["2", "FALSE", "Parcelius", "2:09.990", "+0.225", "0.969", "", "TRUE"],
    ]
    column_alignments = ["center", "center", "left", "center", "center", "center", "center", "center"]

    metallic_seaweed = '#177e89'
    ming = '#106575'
    cg_red = '#db3a34'
    mango_tango = '#ed8146'
    max_yellow_red = '#ffc857'
    jet = '#323031'

    # create an image with a blue background of size 200x200  
    header_heights = [24, 20]
    column_widths = [40, 40, 150, 80, 50, 75, 140, 40]
    body_rows = len(time_trial_table) - len(header_heights)
    bg_margin = 10

    # load image
    checkbox = Image.open('Images/Checkbox.png').resize((16, 16))
    empty_checkbox = Image.open('Images/Empty Checkbox.png').resize((16, 16))

    out = Image.new(
        "RGB", (
            sum(column_widths) + bg_margin * 2, 
            20 * body_rows + sum(header_heights) + bg_margin * 2
        ), jet
    )

    draw = ImageDraw.Draw(out)

    # rectangles
    draw.rectangle((8, 8, out.size[0]-8, out.size[1]-8), fill=mango_tango)  # 2px outline

    
    draw.rectangle(  # header 1
        (
            bg_margin, bg_margin, 
            out.size[0]-bg_margin, bg_margin + header_heights[0]
        ), fill=cg_red
    )  

    draw.rectangle(  # header 2
        (
            bg_margin, bg_margin + header_heights[0], 
            out.size[0]-bg_margin, bg_margin + sum(header_heights[0:2])
        ), fill=ming
    )

    draw.rectangle(  # body
        (
            bg_margin, bg_margin + sum(header_heights), 
            out.size[0]-bg_margin, out.size[1]-bg_margin
        ), fill=metallic_seaweed
    )

    # borders
    draw.line(  # header 1 bottom border
        (
            bg_margin, bg_margin + header_heights[0], 
            out.size[0]-bg_margin, bg_margin + header_heights[0]
        ), fill="black", width=1
    )
    draw.line(  # header 2 bottom border
        (
            bg_margin, bg_margin + sum(header_heights[0:2]), 
            out.size[0]-bg_margin, bg_margin + sum(header_heights[0:2])
        ), fill="black", width=1
    )

    for i in range(1, body_rows): # body bottom borders
        offset_y = bg_margin + sum(header_heights) + 20*i
        draw.line((bg_margin, offset_y, out.size[0]-bg_margin, offset_y), fill=ming, width=1)

    # text
    roboto_bold = "Fonts/Roboto-Bold.ttf"
    roboto_medium = "Fonts/Roboto-Medium.ttf"
    pt_to_px = 4/3
    px_font_sizes = {
        12: 12*pt_to_px,
        14: 14*pt_to_px
    }
    header_1_font = ImageFont.truetype(roboto_bold, 14)
    header_2_font = ImageFont.truetype(roboto_bold, 12)
    body_font = ImageFont.truetype(roboto_medium, 12)

    draw.text(  # header 1
        (
            bg_margin + (out.size[0]-bg_margin*2)//2 - header_1_font.getsize(text=time_trial_table[0][0])[0]//2,
            bg_margin + header_heights[0]//2 - header_1_font.getsize(text=time_trial_table[0][0])[1]//2
        ), time_trial_table[0][0], fill=max_yellow_red, font=header_1_font
    )

    # header 2
    for i, text in enumerate(time_trial_table[1]):
        offset_x = bg_margin + sum(column_widths[:i])
        offset_y = bg_margin + sum(header_heights[0:1]) + (header_heights[1] // 2 - px_font_sizes[12] // 2) + 1  # no idea why it's + 1, but it works

        if column_alignments[i] == "center":
            draw.text(
                (
                    offset_x + (column_widths[i] - header_2_font.getsize(text=text)[0])//2,
                    offset_y
                ), text, fill=max_yellow_red, font=header_2_font
            )

        else:
            draw.text(
                (
                    offset_x,
                    offset_y
                ), text, fill=max_yellow_red, font=header_2_font
            )

    # body
    for i, row in enumerate(time_trial_table[2:]):

        for j, text in enumerate(row):

            offset_x = bg_margin + sum(column_widths[:j]) 
            offset_y = bg_margin + sum(header_heights[0:2]) + 20*i + 3

            if text in ['TRUE', 'FALSE']:
                out.paste(
                    checkbox if text == 'TRUE' else empty_checkbox,
                    (
                        offset_x + (column_widths[j] - checkbox.size[0])//2,
                        offset_y + (header_heights[1] - checkbox.size[1])//2 - 2
                    )
                )

            else:

                if column_alignments[j] == "center":
                    draw.text(
                        (
                            offset_x + (column_widths[j] - body_font.getsize(text=text)[0])//2,
                            offset_y
                        ), text, fill=max_yellow_red, font=body_font
                    )

                else:
                    draw.text(
                        (
                            offset_x,
                            offset_y
                        ), text, fill=max_yellow_red, font=body_font
                    )
# end test


async def test(client, message, args):

    '''
    import Tables
    tables = Tables.get_tables(guild_id=789181254120505386)
    table = tables[1]
    table.cells = table.get_cells()
    table.cell_values = table.get_cell_values()
    tables = table.get_table_displays()
    await simple_bot_response(message.channel,
        description = tables[0]
    )'''

    # await new_slash_cmd()
    # await gspread_testing()
    # await templar_test(message)


    ''' test setup '''
    msg = await message.channel.send("testing")
    for r in [Support.emojis.tick_emoji, Support.emojis.x_emoji] + Support.emojis.number_emojis[1:4]:
        await msg.add_reaction(r)


    ''' check 1 '''
    def reaction_check_1(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in [Support.emojis.tick_emoji, Support.emojis.x_emoji]
        )
    # end reaction_check_1


    ''' check 2 '''
    def reaction_check_2(reaction, r_user):
        return (
            reaction.message == msg and 
            r_user.id == message.author.id and
            str(reaction.emoji) in Support.emojis.number_emojis[1:4]
        )
    # end reaction_check_2


    ''' wait for multiple conditions '''
    done, pending = await asyncio.wait([
        client.wait_for('reaction_add', check=reaction_check_1),
        client.wait_for('reaction_add', check=reaction_check_2),
        ],
        timeout=30,
        return_when=asyncio.ALL_COMPLETED # default, can also have asyncio.FIRST_COMPLETED
    )

    print('done')
    for task in done:
        reaction, user = task.result()
        print(type(task), str(reaction.emoji), user)
        print()

    print('cancelling pending')
    for future in pending:
        print(type(future), future)
        future.cancel()

    await message.channel.send('test done', delete_after=3)
# end test


async def templar_test(message):
    from Servers import TemplarLeagues

    await TemplarLeagues.prepare_series_report_channel(message.channel, message.author)
# end templar_test


def gspread_testing():
    import gspread

    gc = gspread.service_account(filename="Secrets/phyner-a9859c6daae5.json")

    sh = gc.open("Random Testing")

    print(sh.sheet1.get("a3"))
# end gspread_testing

'''
## NEW SLASH CMD

async def new_slash_cmd():
    import requests

    # url = "https://discord.com/api/v8/applications/<my_application_id>/commands" # update once an hour
    # url = "https://discord.com/api/v8/applications/<my_application_id>/guilds/<guild_id>/commands" # update instantly, use for testing
    url = "https://discord.com/api/v8/applications/770416211300188190/guilds/467239192007671818/commands"


    json = {
        "name": "blep",
        "description": "Send a random adorable animal photo",
        "options": [
            {
                "name": "animal",
                "description": "The type of animal",
                "type": 3,
                "required": True,
                "choices": [
                    {
                        "name": "Dog",
                        "value": "animal_dog"
                    },
                    {
                        "name": "Cat",
                        "value": "animal_dog"
                    },
                    {
                        "name": "Penguin",
                        "value": "animal_penguin"
                    }
                ]
            },
            {
                "name": "only_smol",
                "description": "Whether to show only baby animals",
                "type": 5,
                "required": False
            }
        ]
    }

    headers = {
        "Authorization" : os.getenv("TOKEN")
    }

    r = requests.post(url, headers=headers, json=json)
# end new_slash_cmd
'''