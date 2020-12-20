''' IMPORTS '''

import asyncio
import discord
import traceback

import os
from dotenv import load_dotenv
load_dotenv()


import Database
import Logger
from Logger import log
import Support
from Support import simple_bot_response



''' CONSTANTS '''

aliases = ["", ]



''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
        @Phyner _command_
    """

# end main

def command_used(command, arg_2, success=False):
    """
        the idea is in controller, or command's main, you update its used += 1, if it succeeds, you update its success += 1
    """

    db = Database.connect_database()
    db.cursor.execute(f"""
        UPDATE CommandStats SET 
            attempts = attempts + {1 if not success else 0},
            successes = successes + {1 if success else 0}
        WHERE (
            command = '{command}' AND
            arg_2 = {Support.quote(arg_2) if arg_2 else 'NULL'}
        )
    ;""")
    if True or os.getenv("HOST") == "PI4":
        db.connection.commit()
    db.connection.close()
# end command_used