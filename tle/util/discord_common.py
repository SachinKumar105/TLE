import firebase_admin
from firebase_admin import storage
import asyncio
import logging
import functools
import random
import subprocess

import discord
from discord.ext import commands

from tle.util import codeforces_api as cf
from tle.util import db

logger = logging.getLogger(__name__)

_CF_COLORS = (0xFFCA1F, 0x198BCC, 0xFF2020)
_SUCCESS_GREEN = 0x28A745
_ALERT_AMBER = 0xFFBF00


def embed_neutral(desc, color=discord.Embed.Empty):
    return discord.Embed(description=str(desc), color=color)


def embed_success(desc):
    return discord.Embed(description=str(desc), color=_SUCCESS_GREEN)


def embed_alert(desc):
    return discord.Embed(description=str(desc), color=_ALERT_AMBER)


def cf_color_embed(**kwargs):
    return discord.Embed(**kwargs, color=random.choice(_CF_COLORS))


def attach_image(embed, img_file):
    embed.set_image(url=f'attachment://{img_file.filename}')


def set_author_footer(embed, user):
    embed.set_footer(text=f'Requested by {user}', icon_url=user.avatar_url)


def send_error_if(*error_cls):
    """Decorator for `cog_command_error` methods. Decorated methods send the error in an alert embed
    when the error is an instance of one of the specified errors, otherwise the wrapped function is
    invoked.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(cog, ctx, error):
            if isinstance(error, error_cls):
                await ctx.send(embed=embed_alert(error))
                error.handled = True
            else:
                await func(cog, ctx, error)
        return wrapper
    return decorator


async def bot_error_handler(ctx, exception):
    if getattr(exception, 'handled', False):
        # Errors already handled in cogs should have .handled = True
        return

    if isinstance(exception, db.DatabaseDisabledError):
        await ctx.send(embed=embed_alert('Sorry, the database is not available. Some features are disabled.'))
    elif isinstance(exception, commands.NoPrivateMessage):
        await ctx.send(embed=embed_alert('Commands are disabled in private channels'))
    elif isinstance(exception, commands.DisabledCommand):
        await ctx.send(embed=embed_alert('Sorry, this command is temporarily disabled'))
    elif isinstance(exception, cf.CodeforcesApiError):
        await ctx.send(embed=embed_alert(exception))
    else:
        exc_info = type(exception), exception, exception.__traceback__
        logger.exception('Ignoring exception in command {}:'.format(ctx.command), exc_info=exc_info)

def uploadData():
    cred = firebase_admin.credentials.Certificate('key.json')
    firebase_admin.initialize_app(cred, {
      'databaseURL': 'https://smart-india-hackathon-d1f21.appspot.com/',
      'storageBucket': 'smart-india-hackathon-d1f21.appspot.com/',
    })

    blob = storage.bucket('smart-india-hackathon-d1f21.appspot.com').blob('data.zip') # intended name of file in Firebase Storage
    blob.upload_from_filename('data.zip') # path to file on local disk

async def presence(bot):
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name='your commands'))
    await asyncio.sleep(60)
    while True:
        target = random.choice([
            member for member in bot.get_all_members()
            if 'Purgatory' not in {role.name for role in member.roles}
        ])
        Activity_Type = random.randint(0, 2)
        if Activity_Type == 0:
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.listening, name="Kalasala"))
        elif Activity_Type == 1:
            await bot.change_presence(activity=discord.Game(
                name=f'{target.display_name} orz'))
        elif Activity_Type == 2:
            await bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching, name="Hariyali"))

        logger.info(f"Starting Backup...")
        bashCommand = "zip data.zip data/db/cache.db data/db/user.db"
        output, error = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE).communicate()
        
        logger.info(f"Uploading to cloud...")
        uploadData()

        bashCommand = "rm data.zip"
        output, error = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE).communicate()
        logger.info(f"Backup Complete")

        await asyncio.sleep(10 * 60)
