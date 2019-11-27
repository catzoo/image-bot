import discord
from discord.ext import commands
import asqlite
import env_config
from checks import Checks


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.checks = None
        self.ready = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.ready:  # so on_ready only runs once
            self.checks = await Checks.create()
            self.ready = True

    @commands.group()
    @commands.check(Checks.developer_check)
    async def role(self, ctx):
        if ctx.invoked_subcommand is None:
            raise commands.CommandNotFound()

    @role.command(name='add')
    @commands.check(Checks.developer_check)
    async def role_add(self, ctx, level: int, *, role: discord.Role):
        if not await self.checks.get_role(role.id):
            await self.checks.add_role(role.id, level)
            await ctx.send(embed=discord.Embed(description=f'Role {role.name} added successfully'
                                                           f'\nLevel is set to {level}',
                                               color=discord.Color.blue()))
        else:
            await ctx.send(embed=discord.Embed(description='That role has already been added',
                                               color=discord.Color.red()))

    @role.command(name='remove')
    @commands.check(Checks.developer_check)
    async def role_remove(self, ctx, *, role: discord.Role):
        if await self.checks.get_role(role.id):
            await self.checks.remove_role(role.id)
            await ctx.send(embed=discord.Embed(description=f'Removed the role successfully',
                                               color=discord.Color.blue()))
        else:
            await ctx.send(embed=discord.Embed(description='I cannot find that role',
                                               color=discord.Color.red()))

    @role.command(name='list')
    @commands.check(Checks.developer_check)
    async def role_list(self, ctx):
        roles = await self.checks.get_all_roles()
        string = ''  # Error string, will get set to the description
        levels = {1: '', 2: '', 3: ''}  # going to get separated by fields later

        if roles:
            for x in roles:
                # ID - Level
                role = ctx.guild.get_role(x[0])
                if role:
                    levels[x[1]] += f'    - {role.name}\n'
                else:
                    await self.checks.remove_role(x[0])
        else:
            string = 'List is empty'

        embed = discord.Embed(title='Roles', description=string, color=discord.Color.blue())
        for x in levels:
            if levels[x] != '':
                embed.add_field(name=f'Level {x}', value=levels[x], inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
