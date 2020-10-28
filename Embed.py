import discord
import asyncio
import traceback
import re

import Logger

mo_id = 405944496665133058
phyner_id = 770416211300188190

space_char = "⠀"

async def main(client, message, args, author_perms):

  if len(args) == 2 or args[2] == "help" or args[2] == "?": # @Phyner <command> or @Phyner command help
    await Logger.botResponse(message, f"For help with embeds, click [__here__](https://github.com/nosv1/Phyner/wiki/User-Embeds) to visit the Phyner wiki page for **User Embeds**.")

  elif args[2] == "create":
    if author_perms.manage_messages:
      await createEmbed(message, None)
    else:
      await Logger.botResponse(message, f"{message.author.display_name}, you need the **Manage Messages** permission to create embeds with Phyner.")

# end main



async def createEmbed(message, embed): # passing embed incase it's from editEmbed()
  attributes = {
    ".color" : None,
    ".colour" : None,
    ".title" : None,
    ".title_icon" : None,
    ".title_url" : None,
    ".description" : None,
    ".field#_title" : None, # when checking for field stuff, replace number as #
    ".field#_text" : None, # will be adding actual field# keys upon detection
    ".footer" : None,
    ".embed_thumbnail" : None,
    ".embed_picture" : None
  }


  embed = discord.Embed() if not embed else embed

  lines = message.content.split("\n")
  end_attribute = len(lines) - 1 # last line of current attribute
  for i in range(len(lines)-1, -1, -1):
    line = lines[i] + " "

    # preparing for the stripping that discord does, and adding spacechar where it's needed, here and when attribute is first word, basically if line is blank, add a spacechar to make sure discord doesn't get rid of the line
    words = line.split(" ")
    words += f"{space_char}" if line.strip() == "" else ""
    lines[i] = " ".join(words)

    first_word = words[0]
    first_word = re.sub(r"[0-9]", "#", first_word) # for .field#_ attributes

    if first_word in attributes:
      # more spacechar stuff if first word is attribute
      words += space_char if " ".join(words[1:]).strip() == "" else ""
      lines[i] = " ".join(words)

      if first_word in [".field#_title", ".field#_text"]:
        first_word = words[0] # get the field number back

      lines[i] = " ".join(words[1:]) # everything after first word in current line
      attr_content = "\n".join(lines[i:end_attribute+1])
      attributes[first_word] = attr_content
      end_attribute = i - 1
  # attributes should be fully detected and ready for embed assembly by now, except for field stuff, still need to check actual number of fields and correclty populate


  ## set embed attributes ##

  for attr in attributes:
    if not attributes[attr]: # attribute is none, then skip attr
      continue

    if attr in [".color", ".colour"]: # color
      try:
        color = attributes[attr].replace("#", "").strip() # #ffffff -> ffffff
      except AttributeError: # when attribute is None
        continue

      if len(color) != 6:
        await Logger.botResponse(message, "The color attribute doesn't have 6 characters. The color for a Phyner embed should be expressed as a HEX number, e.g. #FFFFFF or FFFFFF")
        return
      embed.color = int(f"0x{color}", 16)


    elif attr == ".title_url": # author
      embed = embed.to_dict()

      if attributes[".title"] or attributes[".title_icon"] or attributes[".title_url"]:
        embed["author"] = {}
      embed["author"]["name"] = attributes[".title"] if attributes[".title"] else space_char

      if attributes[".title_icon"]:
        embed["author"]["icon_url"] = re.sub(r"[<>]", "", attributes[".title_icon"])

      if attributes[".title_url"]:
        embed["author"]["url"] = re.sub(r"[<>]", "", attributes[".title_url"])

      embed = discord.Embed().from_dict(embed)

    
    elif attr == ".description": # description
      embed.description = attributes[attr]

    
    elif attr == ".footer": # footer
      embed.set_footer(text=attributes[attr])

  try:
    await message.channel.send(embed=embed)

  except discord.errors.HTTPException as e: # likely not a well formed URL
    await Logger.botResponse(message, str(e))

# end createEmbed