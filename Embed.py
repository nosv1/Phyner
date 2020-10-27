import discord
import asyncio
import traceback
import re

import Logger

mo_id = 405944496665133058
phyner_id = 770416211300188190

async def main(client, message, args, author_perms):

  if len(args) == 2 or args[2] == "help" or args[2] == "?": # @Phyner <command> or @Phyner command help
    await Logger.botResponse(client, message, f"For help with embeds, click [__here__](https://github.com/nosv1/Phyner/wiki/User-Embeds) to visit the Phyner wiki page for **User Embeds**.")

  elif args[2] == "create":
    if author_perms.manage_messages:
      await createEmbed(message)
    else:
      await Logger.botResponse(client, message, f"{message.author.display_name}, you need the **Manage Messages** permission to create embeds with Phyner.")

# end main



async def createEmbed(message, embed): # passing embed incase it's edited
  attributes = [
    ".color",
    ".colour"
    ".title",
    ".title_logo",
    ".title_link"
    ".description",
    ".field#_title", # when checking for field stuff, replace number as #
    ".field#_text",
    ".footer",
    ".embed_thumbnail"
    ".embed_picture"
    ]

  embed = discord.Embed() if not embed else embed

  lines = message.content.split("\n")
  for line in lines:
    words = line.split(" ")
    first_word = words[0]
    first_word = re.sub(r"[0-9]", "#", first_word) # for .field#_ attributes

    if first_word in attributes:
      attribute = attributes.index(first_word)

      if attribute in [".color", ".colour"]:
        color = words[1].replace("#", "").strip()
        embed.color = int(f"0x{color}", 16)

      if attribute == ".title":
        embed.set_author(name=) # gotta find next attribute

# end createEmbed