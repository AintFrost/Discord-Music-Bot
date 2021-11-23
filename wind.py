import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


from random import choice

client = commands.Bot(command_prefix= '.')

status = ['Banging!','Eating!','Sleeping!']

@client.event
async def on_ready():
    change_status.start()
    print('Bot is Ready.')

@client.command(name='ping',help='This command returns the Latency.')
async def ping(ctx):
  await ctx.send(f'**Pong!** Latency:{round(client.latency*1000)}ms')

@client.command(name='hello',help='Returns Random Welcome messages.')
async def hello(ctx):
  responses = ['Ohayo','Konbawa','FokOF']
  await ctx.send(choice(responses))

@client.command(name='play',help='This command plays Song.')
async def play(ctx,url):
  if not ctx.message.author.voice:
    await ctx.send('You are not connected to a Voice channel')
    return
  else:
    channel = ctx.message.author.voice.channel
  
  await channel.connect()

  server = ctx.message.guild
  voice_channel = server.voice_client

  async with ctx.typing():
      player = await YTDLSource.from_url(url,loop=client.loop)
      voice_channel.play(player,after=lambda e:print('Player Error : %s'%e) if e else None)
  await ctx.send(f'**Now playing:**{player.title}')  


@client.command(name='stop',help='This command stops the current queue.')
async def stop(ctx):
  responses = ['Ohayo','Konbawa','FokOF']
  await ctx.send(choice(responses))

@client.command(name='disconnect',help='This makes the bot leave the voice chat.')
async def disconnect(ctx):
  voice_client = ctx.message.guild.voice_client
  await voice_client.disconnect()

@tasks.loop(seconds=20)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))


client.run('YOUR_BOTS_TOKEN_HERE')
