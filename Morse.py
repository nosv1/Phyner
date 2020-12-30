''' IMPORTS '''

import asyncio
import discord
import random
import traceback


import Database
import Logger
from Logger import log
import Help
import Support
from Support import simple_bot_response



''' CONSTANTS '''

aliases = ["", ]

morse_code = [ # A-Z + 1-0
    "• -", # A
    "- • • •", # B
    "- • - •", # C
    "- • •", # D
    "•", # E
    "• • - •", # F
    "- - •", # G
    "• • • •", # H
    "• •", # I
    "• - - -", # J
    "- • -", # K
    "• - • •", # L
    "- -", # M
    "- •", # N
    "- - -", # O
    "• - - •", # P
    "- - • -", # Q
    "• - •", # R
    "• • •", # S
    "-", # T
    "• • -", # U
    "• • • -", # V
    "• - -", # W
    "- • • -", # X
    "- • - -", # Y
    "- - • •", # Z
    "• - - - -", # 1
    "• • - - -", # 2
    "• • • - -", # 3
    "• • • • -", # 4
    "• • • • •", # 5
    "- • • • •", # 6
    "- - • • •", # 7
    "- - - • •", # 8
    "- - - - •", # 9
    "- - - - -", # 0
]



''' FUNCTIONS '''

async def main(client, message, args):
    """
        @Phyner morse
        @Phyner morse letter
    """

    if args[1] in Help.help_aliases:
        Support.previous_action_error(client, message)
        log("morse", "help")


    elif args[1] == "morse":
        await learn_morse(client, message)

    

# end main


async def learn_morse(client, message):
    """
        show letter, wait for response
    """


    def message_check(m):
        return (
            m.author.id == message.author.id and
            m.channel.id == message.channel.id
        )
    # end message_check

    embed = await Support.simple_bot_response(message.channel,
        title="Translate It",
        description="",
        send=False
    )


    msg = None
    while True:

        # prepare morse
        with open("word_list.txt") as wl:
            word = random.choice(wl.readlines())
            print(word)

        r_morse = "   ".join([morse_code[ord(c.upper()) - ord('A')] for c in word])

        translation = ""
        for word in r_morse.split(" " * 7): # word in phrase
            for letter in word.split(" " * 3): # letter in word
                translation += f"{chr(morse_code.index(letter) + ord('A'))} "
            translation += " " # punctuation goes here...
        translation = translation.strip()


        if not embed.description:
            embed.description = f"`{r_morse}`"


        # send it
        if msg:
            await msg.edit(embed=embed)
        else:
            msg = await message.channel.send(embed=embed)


        # wait
        try:
            mesge = await client.wait_for("message", check=message_check, timeout=60)
            await mesge.delete()

            user_translation = mesge.content

            if user_translation == translation:
                embed.description = ""

            else:
                embed.description += f"\n`{mesge.content}` is incorrect."

        except asyncio.TimeoutError:
            embed.title += "\nTimed Out"
            await msg.edit(embed=embed)
            break
    # end while

# end learn_morse