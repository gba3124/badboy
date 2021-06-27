import asyncio
import discord
from discord import channel
from discord.activity import Game
import youtube_dl
import random
import time
from discord.ext import commands
import threading

# Some variable
# 427063677368139776凱畯
# 603589482683301889阿仁
first_person_we_want_to_follow = 427063677368139776
second_person_we_want_to_follow = 603589482683301889


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   description='Relatively simple music bot example', intents=intents)

# Suppress noise about console usage from errors
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

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """進入語音聊天室"""

        list_id=ctx.message.author.id
        list_channel=ctx.guild.get_member(list_id).voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(list_channel)

        await list_channel.connect()


    @commands.command()
    async def play(self, ctx, *, query="88.mp3"):
        """播放本地檔案"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        time.sleep(5)
        #await ctx.send(f'Now playing: {query}')
        await ctx.voice_client.disconnect(force=1)

    @commands.command()
    async def yt(self, ctx, *, url):
        """下載YouTube影片來播放"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def stream(self, ctx, *, url):
        """不下載直接播放YouTube影片"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """調整音量"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """趕走機器人"""

        await ctx.voice_client.disconnect()



    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

class Text(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def add(self, ctx, left: int, right: int):
        """相加兩數"""
        await ctx.send(left + right)

    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self, ctx, *choices: str):
        """從多個輸入選項選一個機掰人"""
        await ctx.send(random.choice(choices))

    @commands.command()
    async def repeat(self, ctx, times: int, content='repeating...'):
        """重複你說的話N次"""
        for i in range(times):
            await ctx.send(content)

    @commands.command()
    async def joined(self, ctx, member: discord.Member):
        """成員加入公會的時間"""
        await ctx.send(f'機掰人 {member.name} 在 {member.joined_at} 加入了公會')

    @commands.group()
    async def cool(self, ctx):
        """Says if a user is cool.
        In reality this just checks if a subcommand is being invoked.
        """
        await ctx.send(f'Detecting about is {ctx.subcommand_passed} cool???')
        if ctx.invoked_subcommand is None:
            await ctx.send(f'No, {ctx.subcommand_passed} is not cool')


    @cool.command(name='bot')
    async def _bot(self, ctx):
        """Is the bot cool?"""
        await ctx.send('Yes, the bot is cool.')

    @commands.command()
    async def lastMessage(self, ctx, users_id: int):
        """查看某個人在這裡打出的最後一段話"""

        oldestMessage = None
        for channel in ctx.guild.text_channels:
            fetchMessage = await channel.history().find(lambda m: m.author.id == users_id)
            if fetchMessage is None:
                continue


            if oldestMessage is None:
                oldestMessage = fetchMessage
            else:
                if fetchMessage.created_at > oldestMessage.created_at:
                    oldestMessage = fetchMessage

        if (oldestMessage is not None):
            await ctx.send(f"Oldest message is {oldestMessage.content}")
        else:
            await ctx.send("No message found.")

    @commands.command()
    async def checkChannel(self, ctx, channel_id: int):
        """查看頻道目前有誰"""
        channel = bot.get_channel(channel_id) #gets the channel you want to get the list from

        members = channel.members #finds members connected to the channel

        memids = [] #(list)
        for member in members:
            memids.append(member.id)

        await ctx.send(f"目前有: {memids}")

    @commands.command()
    async def checkg(self, ctx, gulid_id: int):
        """查看公會目前有那些頻道"""

        await ctx.send(f"以玩家來掃描房間")
        guile = ctx.guild
        users =  guile._voice_states
        for user in users:
            await ctx.send(f"玩家ID: {user} 正在線上")
            await ctx.send(f"所在地: {users[user].channel.name}")

        member = guile.get_member(563962142445928458)

        await ctx.send(f"以房間來掃描玩家")
        voice_channels = guile.voice_channels
        for voice_channel in voice_channels:
            await ctx.send(f"頻道ID: {voice_channel.id}, 頻道名稱:{voice_channel.name}")
            for menber in voice_channel.voice_states:
                await ctx.send(f"抓到一個玩家，ID: {menber}")


        owner_id = guile.owner_id
        guile_name = guile.name

        await ctx.send(f"公會名稱: {guile_name}, 持有人id: {owner_id}")

    @commands.command()
    async def find(self, ctx,member_id = 438335376499802132 ):
        """偵查某ID的人所在頻道的ID"""
        guild= ctx.guild
        await ctx.send(f"群組名稱 {guild.name}")
        M = guild.get_member(member_id)
        channel_id = M.voice.channel.id
        channel_name = M.voice.channel.name
        await ctx.send(f"名子: {M.name}")
        await ctx.send(f"頻道ID: {channel_id},頻道名子 {channel_name}")
        '''
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("88.mp3"))
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        time.sleep(5)
        #await ctx.send(f'Now playing: {query}')
        await ctx.voice_client.disconnect(force=1)
        '''


class BadBoy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def find1(self, ctx, member_id = 438335376499802132 ):
        """使機器人偵查某ID的人並直接潛入他的頻道"""
        guild= ctx.guild
        await ctx.send(f"群組名稱 {guild.name}")
        M = guild.get_member(member_id)
        channel_id = M.voice.channel.id
        channel_name = M.voice.channel.name
        await ctx.send(f"名子: {M.name}")
        await ctx.send(f"頻道ID: {channel_id},頻道名子 {channel_name}")
        my_channel = bot.get_channel(channel_id)

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(my_channel)
            aa.play
        await my_channel.connect()

    @commands.command()
    async def change_person1(self, ctx, person = 427063677368139776 ):
        """更換可憐蟲1號"""
        global first_person_we_want_to_follow
        first_person_we_want_to_follow = person
        await ctx.send(f"可憐蟲1號:{ctx.guild.get_member(person).name}")


    @commands.command()
    async def change_person2(self, ctx, person = 603589482683301889 ):
        """更換可憐蟲2號"""
        global second_person_we_want_to_follow
        second_person_we_want_to_follow = person
        await ctx.send(f"可憐蟲2號:{ctx.guild.get_member(person).name}")


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.event
    async def on_ready():
        print(discord.__version__)
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        global first_person_we_want_to_follow
        global second_person_we_want_to_follow
        if member.id == first_person_we_want_to_follow or member.id == second_person_we_want_to_follow:

            if member.guild.voice_client is not None:
                return await member.guild.voice_client.move_to(after.channel)

            await after.channel.connect()

            ctx = member.guild
            music = self.bot.get_cog('Music')
            #await music.volume(ctx,volume = 100)
            if member.id == 427063677368139776:#凱駿
                await music.play(ctx, query='88.mp3')
            elif member.id == 603589482683301889:#彥仁
                await music.play(ctx, query='44.mp3')
            elif member.id == 407936301984120843:#杜
                await music.play(ctx, query='car.mp3')
            elif member.id == 439435085956251648:#國洲
                await music.play(ctx, query='DejaVu.mp3')
            elif member.id == 438335376499802132:#蕭
                await music.play(ctx, query='86.mp3')
            else:
                await music.play(ctx, query='fi.mp3')


    @commands.Cog.listener()
    async def on_message(self, message):
        badwords = ['彥仁', 'Allen', '凱畯', '凱駿', '水梨', '梨子']
        for i in badwords: # Go through the list of bad words;
            if i in message.content:
                #  await message.delete()
                if message.author.mention != '<@856511285663760435>':
                    if i in badwords[0:2]:
                        await message.channel.send(f"{message.author.mention} 別說{i}這種骯髒之詞!!")
                    if i in badwords[2:6]:
                        await message.channel.send(f"{message.author.mention} 別跟我提{i}這個機掰人!!")

                    bot.dispatch('profanity', message, i)
                    return # So that it doesn't try to delete the message again, which will cause an error.
                await bot.process_commands(message)

    @commands.Cog.listener()
    async def on_profanity(self, message, word):
        channel = bot.get_channel(856530569080471602) # for me it's bot.get_channel(817421787289485322)
        embed = discord.Embed(title="嚴重警告!",description=f"{message.author.name} 剛剛說了 ||{word}||", color=discord.Color.blurple()) # Let's make an embed!
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        if user.id == (427063677368139776):
            await channel.send(f"廢物梨子人正打算用文字圖謀不軌")



bot.add_cog(Music(bot))
bot.add_cog(Text(bot))
bot.add_cog(BadBoy(bot))
bot.add_cog(Events(bot))

bot.run('ODU2NTExMjg1NjYzNzYwNDM1.YNCGSw.Opv42te_1Ku115G89lKkXULDyzU')