"""
created by catzoo
created on 11/9/2019
"""
import os
import discord
from discord.ext import commands
import env_config
import sqlite3

__cog_name__ = 'image'


class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_location = f'{env_config.data_folder}/image.db'

        # setting up the database (if its not already made)
        if not os.path.exists(self.database_location):
            conn = sqlite3.connect(self.database_location)
            c = conn.cursor()
            c.execute("CREATE TABLE users (user_id integer, points integer)")
            c.execute("CREATE TABLE images (img_id integer, url text)")
            conn.close()

    # todo: add command to add image
    # todo: add command to remove image
    # todo: add loop to randomly place image in channel
    # todo: add a way to ignore channels (need to figure out config)

def setup(bot):
    bot.add_cog(Image(bot))
