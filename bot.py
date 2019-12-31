"""
created by catzoo
created on: 11/9/2019
"""
__version__ = '1.2.0'

import os
from datetime import datetime
import discord
from discord.ext import commands
import env_config

bot = commands.Bot(command_prefix='pof?')
started = datetime.now()
ready = False  # make sure the code in on_ready only run once

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
    global ready
    if not ready:
        ready = True
        print(f'Logged in as {bot.user.name}\nVersion: {__version__}')


@bot.command()
async def info(ctx):
    date_string = ''
    time_up = datetime.now() - started
    time_up = time_up.total_seconds()
    # grabbing minutes from seconds
    minutes = int(time_up / 60)
    time_up -= minutes*60
    time_up = int(time_up)
    # grabbing hours from minutes
    hours = int(minutes / 60)
    minutes -= hours*60
    # grabbing days from hours
    days = int(hours / 24)
    hours -= days*24
    # adding it all to the string
    if time_up != 0:
        date_string = f' {time_up} seconds' + date_string

    if minutes != 0:
        date_string = f' {minutes} minutes' + date_string

    if hours != 0:
        date_string = f' {hours} hours' + date_string

    if days != 0:
        date_string = f' {days} days' + date_string

    embed = discord.Embed(color=discord.Color.blue())
    embed.set_thumbnail(url=ctx.me.avatar_url_as())
    embed.add_field(name='Created by:', value='catzoo', inline=False)
    embed.add_field(name='Created date:', value='11/9/2019', inline=False)
    embed.add_field(name='Version:', value=__version__, inline=False)
    embed.add_field(name='Been up for:', value=date_string)
    await ctx.send(embed=embed)

bot.run(env_config.token)
