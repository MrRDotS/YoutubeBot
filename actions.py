import asyncio

from discord import FFmpegPCMAudio
from discord.ext import commands
from collections import deque
from youtube_setup import ytdl, ffmpeg_options


class Actions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audio_queue = deque()
        self.queue_lock = asyncio.Lock()

    ''' This is just being used for testing, will be deleted later
       All commands called will be verified if user is in the same channel
       using the is in call method'''
    # @commands.command()
    async def join(self, ctx: commands.Context):
        # Checks if a voice connection already exists, if so move to another channel
        check = await self.is_inCall(ctx)
        if check:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                bot_name = self.bot.user.name
                return await ctx.send(f'{bot_name} is being used in {channel}')
            await channel.connect()

    async def play(self, ctx: commands.Context, query: str) -> None:
        # Handle either youtube link or query
        if len(query) > 1:
            query = " ".join(query)
            # When its not given a link, it returns all possible links when this query is searched on yt
            info_dict = ytdl.extract_info(query, download=False)
            query = info_dict['entries'][0]['webpage_url']
        else:
            query = query[0]

        if await self.is_inCall(ctx):
            async with ctx.typing():
                try:
                    youtube_info = ytdl.extract_info(
                        url=query, download=False)

                    if not ctx.voice_client.is_playing():
                        ctx.voice_client.play(FFmpegPCMAudio(
                            youtube_info['url'], **ffmpeg_options), after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                        await ctx.send(f"Now playing {youtube_info['title']}")
                    else:
                        self.audio_queue.append(youtube_info)
                        await ctx.send(f"{youtube_info['title']} queued")
                except:
                    await ctx.send("Invalid Source")

    async def play_next(self, ctx: commands.Context) -> None:
        # check if there is anything to play
        if self.audio_queue:
            audio_source = FFmpegPCMAudio(
                (self.audio_queue[0]['url']), **ffmpeg_options)
            await ctx.send(f"Now playing {self.audio_queue[0]['title']}")
            self.audio_queue.popleft()
            ctx.voice_client.play(
                audio_source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))

    async def skip(self, ctx: commands.Context):
        check = await self.is_inCall(ctx)
        if check and self.audio_queue:
            ctx.voice_client.stop()
            await ctx.send('Song has been skipped!')
        elif check and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('Song has been skipped!')
        elif not ctx.voice_client.is_playing():
            await ctx.send(f'{ctx.author.name}, boss there is nothing queued to be skipped')

    async def queue(self, ctx: commands.Context):
        if await self.is_inCall(ctx):
            songQueue = "Queue\n --------- \n" + \
                '\n'.join([f"{index}: {song['title']}" for index,
                          song in enumerate(self.audio_queue, start=1)])
            await ctx.send(songQueue)

    async def remove(self, ctx: commands.Context, index):
        if await self.is_inCall(ctx) and index.isnumeric() and int(index) <= len(self.audio_queue):
            async with self.queue_lock:
                song = self.audio_queue[int(index) - 1]['title']
                del self.audio_queue[int(index) - 1]
                await ctx.send(f'{song} has been removed from queue!')

    async def jump(self, ctx: commands.Context, index):
        if await self.is_inCall(ctx) and index.isnumeric() and 1 < int(index) <= len(self.audio_queue):
            async with self.queue_lock:
                song = self.audio_queue[int(index) - 1]
                del self.audio_queue[int(index) - 1]
                self.audio_queue.appendleft(song)
        elif index == '1':
            await ctx.send("Brother it's already at the top of the queue")
        else: 
            await ctx.send("Enter a number that's in the queue dude")

    async def help(self, ctx: commands.context):
        await ctx.send('''Commands\n ---------------------
        Every command uses "!" as a prefix
        !play '<link> or name' you can pass in a youtube link or just type the song name. Sometimes video plays so whatever 
        song you search add "lyrics" at the end if you're not passing in the yt link
        !queue returns the all the songs queued up
        !skip skip the song playing currently
        !remove <number in queue> Just input the number on the queue list you wanna remove
        !jump <number in queue> If you want to move something to the top of the queue
        If bot breaks just pm me and I'll take a look when I can, this is still in testing phase
        You can use the first letter of every command if you're lazy to type i.e : !p...''')

    '''
       If more than 1 bot is called to channel lol, I'll make this into a command later
    '''
    async def leave(self, ctx: commands.Context):
        if await self.is_inCall(ctx):
            await ctx.voice_client.disconnect()

    '''
    Checks if user who uses command is in the same call the bot is active in 
    '''
    async def is_inCall(self, ctx: commands.Context):
        # is not in a call yet
        if not ctx.voice_client and ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.send('Joining..!')
            return True
        # Check if user calling the bot is in the same channel as the bot
        if (ctx.voice_client and ctx.author.voice) and ctx.voice_client.channel == ctx.author.voice.channel:
            return True
        # Check if bot active and user is the in the same channel
        elif (ctx.voice_client and ctx.author.voice) and ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.send(f'{ctx.author.name}, brother this bot is active in another channel')
        # bot is called and caller isn't even in a channel
        else:
            await ctx.send(f'{ctx.author.name}, you must join the channel to use commands')
