"""
created by catzoo
created on: 11/9/2019
"""
__version__ = '0.1.0'

import os
import discord
from discord.ext import commands
import env_config

bot = commands.Bot(command_prefix='?')

# loading all the extensions
extension_list = os.listdir('cog')
for x in extension_list:
    x = x.replace('.py', '', 1)
    try:
        bot.load_extension(f'cog.{x}')
    except commands.NoEntryPointError:
        pass  # does not have a setup function

bot.load_extension('jishaku')


@bot.check
async def correct_guild_only(ctx):
    if ctx.guild:
        if ctx.guild.id == env_config.main_guild:
            return True
        else:
            name = bot.get_guild(env_config.main_guild)
            name = name.name
            await ctx.send(embed=discord.Embed(title='Sorry!',
                                               description='This bot can only handle one guild. '
                                                           'This is currently set to: '
                                                           f'{name}'))
    else:
        raise commands.NoPrivateMessage()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}\nVersion: {__version__}')


bot.run(env_config.token)
