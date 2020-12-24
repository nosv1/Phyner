''' IMPORTS '''

import asyncio
import discord

import os
from dotenv import load_dotenv
load_dotenv()


from Stats import command_used
import Support
from Support import simple_bot_response



''' FUNCTIONS '''

## TETS ##

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