# bot.py
import asyncio
import os
# remove this later

from discord import Intents, FFmpegPCMAudio, AudioSource
from discord.ext import commands
from dotenv import load_dotenv

from collections import deque
import yt_dlp
import redis
from redis_server import startServer


currentDir = os.getcwd()
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',
    }],
    'limit-rate': '1m',
    'default_search': 'ytsearch',
    'outtmpl': f'{currentDir}/MusicFiles/%(title)s.%(ext)s'.strip()
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

redis_host = 'localhost' 
redis_port = 6379 # default port 

redis_mgr = redis.Redis(host=redis_host, port=redis_port)

class Actions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.started = False
        self.audio_queue = deque()
        self.queue_lock = asyncio.Lock()

    ''' This is just being used for testing, will be deleted later
       All commands called will be verified if user is in the same channel
       using the is in call method'''
    @commands.command()
    async def join(self, ctx: commands.Context):
        # Checks if a voice connection already exists, if so move to another channel
        check = await self.is_inCall(ctx)
        if check:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                bot_name = bot.user.name
                return await ctx.send(f'{bot_name} is being used in {channel}')
            await channel.connect()

    @commands.command()
    async def play(self, ctx: commands.Context, *query: str):
        # Handle either youtube link or query
        if len(query) > 1:
            query = " ".join(query)
            info_dict = ytdl.extract_info(query, download=False)
            query = info_dict['entries'][0]['webpage_url']
        else:
            query = query[0]

        if await self.is_inCall(ctx):
            async with ctx.typing():
                try:
                    audio_info = ytdl.extract_info(url=query, download=False)
                    audioTitle = audio_info['title']

                    #checks if file exists in cache or disk before downloading 
                    '''audio_file = self.retrieve_file(audioTitle)
                    if audio_file == None:
                        ytdl.extract_info(url=query, download=True)
                    '''

                    if not ctx.voice_client.is_playing():
                        ctx.voice_client.play(FFmpegPCMAudio(audio_info['url'],**ffmpeg_options), after=lambda e: asyncio.create_task(self.play_next(ctx)))
                        await ctx.send(f"Now playing {audioTitle}")
                    else:
                        self.audio_queue.append(audio_info)
                        await ctx.send(f'{audioTitle} queued')
                except:
                    await ctx.send("Invalid Source")

    async def play_next(self, ctx: commands.Context):
        # check if there is anything to play
        if self.audio_queue:
            audio_source = FFmpegPCMAudio(
                (self.audio_queue[0]['url']), **ffmpeg_options)
            await ctx.send(f"{self.audio_queue[0]['title']} queued")
            self.audio_queue.popleft()
            ctx.voice_client.play(audio_source, after=lambda e: self.play_next(ctx))

    '''
    def retrieve_file(self, audioTitle : str):
        if redis_mgr.exists(audioTitle):
          return redis_mgr.get(audioTitle)
        path = os.path.join(currentDir, "MusicFiles", audioTitle.strip()) + ".mp3"
        print(path) 
        if os.path.exists(path):
            self.cache_file(audioTitle)
            return path
    '''
    '''
    def cache_file(self, audioTitle : str):
        print(f'{currentDir}/MusicFiles/{audioTitle}.mp3')
        with open (f'{currentDir}/MusicFiles/{audioTitle}.mp3', 'rb') as file: 
            audio_file = file.read()
        redis_mgr.set(audioTitle, audio_file)
        return audio_file
    '''
        

    @commands.command()
    async def skip(self, ctx: commands.Context):
        check = await self.is_inCall(ctx)
        if check and self.audio_queue:
            ctx.voice_client.stop()
            async with self.queue_lock:
                await self.play_next(ctx)
            await ctx.send('Song has been skipped!')
        elif check and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        elif not ctx.voice_client.is_playing():
            await ctx.send(f'{ctx.author.name}, boss there is nothing queued to be skipped')

    @commands.command()
    async def queue(self, ctx: commands.Context):
        if await self.is_inCall(ctx):
            songQueue = "Queue\n --------- \n" + \
                '\n'.join([f"{index}: {song['title']}" for index,
                          song in enumerate(self.audio_queue, start=1)])
            await ctx.send(songQueue)

    @commands.command()
    async def remove(self, ctx: commands.Context, index):
        if await self.is_inCall(ctx) and index.isnumeric():
            async with self.queue_lock:
                del self.audio_queue[int(index) - 1]

    '''
       If more than 1 bot is called to channel lol 
    '''
    @commands.command()
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


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = Intents.default()
# need this for commands extension to function
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    #startServer()
    async with bot:
        await bot.add_cog(Actions(bot))
        await bot.start(TOKEN)

asyncio.run(main())
