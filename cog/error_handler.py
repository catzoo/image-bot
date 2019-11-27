"""
Command Error Handler
Created by: catzoo
Doesn't include all of the discord exceptions / errors.
But we don't really need all of the exceptions since we don't
raise all of them.
"""

import discord
from discord.ext import commands
import env_config
import traceback


class BotErrors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        message = ''
        if isinstance(error, commands.NoPrivateMessage):
            message = f'{ctx.command.name} cannot be used in DMs'

        elif isinstance(error, commands.DisabledCommand):
            message = f'{ctx.command.name} has been disabled'

        elif isinstance(error, commands.MissingPermissions):
            message = f'You are Missing Permissions for {ctx.command.name}'

        elif isinstance(error, commands.BotMissingPermissions):
            message = f'I am Missing Permissions for {ctx.command.name}'

        elif isinstance(error, commands.CheckFailure):
            """
            passing it since its used for Checks 
            """
            pass

        elif isinstance(error, commands.CommandOnCooldown):
            message = f'This command is on a cooldown. Try again in {int(error.retry_after)} seconds'

        elif isinstance(error, commands.MissingRequiredArgument):
            message = str(error)
            await ctx.send_help(ctx.command)

        elif isinstance(error, commands.UserInputError):
            message = str(error)

        else:
            # if I missed an exception, or its something else we'll just print it out or send the debug users the errors
            tb = ''.join(traceback.TracebackException.from_exception(error).format())
            message = f"Sorry, a unexpected error occurred."
            to_console = False
            for user_id in env_config.debug_id:
                user = self.bot.get_user(user_id)
                try:
                    await user.send(f'[Error Handler] [{ctx.author} used {ctx.command.name}]: {error}\n```py\n{tb}```')
                except discord.HTTPException:
                    await user.send(f'[Error Handler] [{ctx.author} used {ctx.command.name}]:\
                    {error}\n```Error too large, check server logs```')
                    to_console = True

            if to_console:
                print(tb)

        if message != '':
            message = message.replace('@', '@\u200b')
            await ctx.send(embed = discord.Embed(description=message, color=discord.Color.red()))


def setup(bot):
    bot.add_cog(BotErrors(bot))