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

        if not os.path.exists(self.database_location):
            # database file is not made, so we will assume the database isn't setup
            conn = sqlite3.connect(self.database_location)
            c = conn.cursor()
            c.execute("CREATE TABLE users (user_id integer NOT NULL, points integer)")
            c.execute("CREATE TABLE images (img_id integer NOT NULL PRIMARY KEY, url text)")
            conn.commit()
        else:
            conn = sqlite3.connect(self.database_location)

        self.connection = conn  # database connection

    # todo: add url check
    @commands.guild_only()
    @commands.command()
    async def add_image(self, ctx, url=None):
        if ctx.message.attachments:
            url = ctx.message.attachments[0].url
            print(url)
        if url:
            try:
                # testing to make sure its a correct URL
                # and also so the user can see if the embed can load the image
                # todo: maybe add a check if the embed can load the image (check the extension)
                embed = discord.Embed(title='Preview')
                embed.set_image(url=url)
                await ctx.send(embed=embed)
            except discord.HTTPException:
                await ctx.send(embed=discord.Embed(description='Bad URL',
                                                   color=discord.Color.red()))
            else:
                # adding the image
                c = self.connection.cursor()
                c.execute("INSERT INTO images (url) VALUES (?)", [url])
                self.connection.commit()
                img_id = c.lastrowid  # getting the id
                # sending the success message
                embed = discord.Embed()
                embed.description = 'Image added successfully'
                embed.colour = discord.Color.green()
                embed.set_footer(text=f'ID: {img_id}')
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(description='URL or attachment is required',
                                               color=discord.Color.red()))

    @commands.guild_only()
    @commands.command()
    async def remove_image(self, ctx, img_id : int):
        c = self.connection.cursor()
        c.execute("SELECT * FROM images WHERE img_id=?", [img_id])
        # make sure it exists
        if c.fetchone():
            c.execute("DELETE FROM images WHERE img_id=?", [img_id])
            self.connection.commit()
            await ctx.send(embed=discord.Embed(description=f"Successfully removed the image",
                                               color=discord.Color.green()))
        else:
            await ctx.send(embed=discord.Embed(description=f"I can't find that image",
                                               color=discord.Color.red()))

    # todo: add loop to randomly place image in channel
    # todo: add a way to ignore channels (need to figure out config)


def setup(bot):
    bot.add_cog(Image(bot))
