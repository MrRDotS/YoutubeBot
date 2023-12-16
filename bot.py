import asyncio
from discord.ext import commands
import setup
from setup import *

@bot.command(aliases=['p', 'P'])
async def play(ctx: commands.Context, *query: str):
    await action.play(ctx, query)

@bot.command(aliases=['s', 'S'])
async def skip(ctx: commands.Context):
    await action.skip(ctx)

@bot.command(aliases=['q', 'Q'])
async def queue(ctx: commands.Context):
    await action.queue(ctx)

@bot.command(aliases=['r', 'R'])
async def remove(ctx: commands.Context, index: str):
    await action.remove(ctx, index)

@bot.command(aliases=['c', 'C'])
async def clear(ctx: commands.Context):
    await action.clear(ctx)

@bot.command(aliases=['j','J'])
async def jump(ctx: commands, index: str):
    await action.jump(ctx, index)

@bot.command(aliases=['h', 'H'])
async def help(ctx: commands):
    await action.help(ctx)

@bot.command(aliases=['l', 'L'])
async def leave(ctx : commands):
    await action.leave(ctx)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())

if __name__ == '__main__':
    setup
    main()
    
