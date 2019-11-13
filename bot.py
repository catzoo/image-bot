"""
created by catzoo
created on: 11/9/2019
"""
__version__ = '0.1.0'

import os
# import discord
from discord.ext import commands
import env_config

bot = commands.Bot(command_prefix='?')

# loading all the extensions
if __name__ == '__main__':
    extension_list = os.listdir('cog')
    for x in extension_list:
        if x != '__pycache__':
            x = x.replace('.py', '', 1)
            bot.load_extension(f'cog.{x}')
    bot.load_extension('jishaku')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}\nVersion: {__version__}')

bot.run(env_config.token)
