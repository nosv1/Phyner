''' IMPORTS '''

import discord

import os
from dotenv import load_dotenv
load_dotenv()


import Support
from Support import simple_bot_response



''' FUNCTIONS '''

## TETS ##

async def test(message, args):

    # await new_slash_cmd()
    # await gspread_testing()
    await templar_test(message)

    await message.channel.send('test done', delete_after=3)
# end test


async def templar_test(message):
    from Servers import TemplarLeagues

    channel = message.guild.get_channel(648401621977399298)
    await TemplarLeagues.prepare_series_report_channel(channel, message.author)
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