import discord
import youtube_dl
import asyncio
import random
import os
import requests
import json

from discord.ext import commands
from riotwatcher import LolWatcher
from PIL import Image, ImageFont, ImageDraw

# Initialisation du bot
with open('token.json', 'r') as f:
    data = json.load(f)

help_command = commands.DefaultHelpCommand(no_category='Commands')
intents = discord.Intents().all()
bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents, help_command=help_command)

# Envoie un message en console quand le bot est prêt
@bot.event
async def on_ready():
    print("BEN READY !")
    await bot.change_presence(activity=discord.Game('Type !help'))

# Les variables qui suivent et la classe YTDLSource ont été récurpéré sur Internet, il permettent de télécharger
# l'audio d'une vidéo
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
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
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename


@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f":exclamation: {ctx.message.author.name} is not connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()
    await ctx.send(":magic_wand: Ben appeared in the voice channel", delete_after=2)


@bot.command(name='leave', help='Tells the bot to leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await ctx.send(":sob: Ben left the voice channel", delete_after=2)
        await voice_client.disconnect()
    else:
        await ctx.send(":exclamation: The bot is not connected to a voice channel. Type **!join**.")


@bot.command(name='play', help='Play a song')
async def play(ctx, url):
    server = ctx.message.guild
    voice_channel = server.voice_client
    try:
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        await ctx.send(f":musical_note: Ben is playing **{filename}**")
    except:
        await ctx.send(":exclamation: The bot is not connected to a voice channel. Type **!join**.")


@bot.command(name='pause', help='Pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await ctx.send(":pause_button: Music paused", delete_after=1)
        await voice_client.pause()
    else:
        await ctx.send(":exclamation: The bot is not playing anything at the moment.")


@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await ctx.send(":play_pause: Music resumed", delete_after=1)
        await voice_client.resume()
    else:
        await ctx.send(":exclamation: The bot was not playing anything before this. Type **!play [song]**")


@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await ctx.send(":mute: Music stopped", delete_after=1)
        await voice_client.stop()
    else:
        await ctx.send(":exclamation: The bot is not playing anything at the moment.")


class TicTacToe:
    def __init__(self, p1, p2):
        self.p1 = [":trident:", p1]
        self.p2 = [":fleur_de_lis:", p2]
        self.none = ":black_large_square:"
        self.board = [[self.none]*3, [self.none]*3, [self.none]*3]

    def play(self, player, case):
        case = case.split(',')
        column = int(case[0])-1
        line = int(case[1])-1
        pos = [0,1,2]
        if (column in pos) and (line in pos) and self.board[line][column] == self.none:
            self.board[line][column] = player[0]
            return True
        else:
            return False

    async def print_board(self, ctx):
        b = self.board
        await ctx.send(f"{b[0][0]} {b[0][1]} {b[0][2]}\n"
                       f"{b[1][0]} {b[1][1]} {b[1][2]}\n"
                       f"{b[2][0]} {b[2][1]} {b[2][2]}\n")

    def test_end(self, player):
        for line in self.board:
            if line.count(player[0]) == 3:
                return player
        for col in range(3):
            column = [self.board[i][col] for i in range(3)]
            if column.count(player[0]) == 3:
                return player
        diag1 = [self.board[i][i] for i in range(3)]
        if diag1.count(player[0]) == 3:
            return player
        diag2 = [self.board[i][2 - i] for i in range(3)]
        if diag2.count(player[0]) == 3:
            return player
        n = sum([line.count(':black_large_square:') for line in self.board])
        if n == 0:
            return True
        return False


@bot.command(name='ttt', help="Start a game of Tic-Tac-Toe. Take a mentioned user in arg")
async def ttt(ctx, user: discord.User):
    p2 = bot.get_user(user.id)
    TTT = TicTacToe(ctx.message.author, p2)
    player = TTT.p1
    end = False
    await TTT.print_board(ctx)

    while end == False:
        await ctx.send(f"{player[0]} **{player[1].name}**'s turn. **Type (column, line)**")

        def check(msg):
            return msg.author == player[1] and msg.channel == ctx.channel and len(msg.content) == 3
        msg = await bot.wait_for("message", check=check)
        if TTT.play(player, msg.content):
            await TTT.print_board(ctx)
            end = TTT.test_end(player)
            if not end:
                if player == TTT.p1:
                    player = TTT.p2
                else:
                    player = TTT.p1
        else:
            await ctx.send(":warning: Invalid argument", delete_after=2)
    if end == True:
        await ctx.send("égalité")
    await ctx.send(f"{player[0]} **{end[1].mention}** won !")


lol_watcher = LolWatcher(data["token_lol"])
version = lol_watcher.data_dragon.versions_for_region("euw1")
champions_version = version['n']['champion']


# Utiliser l'API de Riot Games pour donner les statistiques du joueur mentionné
@bot.command(name='rank', help='Give the lol statistics of the mentioned player (!rank DamStruk)')
async def rank(ctx, name: str):
    player = lol_watcher.summoner.by_name("euw1", name)
    prs = lol_watcher.league.by_summoner("euw1", player['id'])
    rankTypes = {"RANKED_FLEX_SR": ':dagger: Flexible : ', 'RANKED_SOLO_5x5': ':crossed_swords: Solo/Duo : '}
    embed = discord.Embed(
        title=f"{player['name']}'s ranks : ",
        color=discord.Color.red())
    embed.set_author(name=f"Requested by {ctx.author}",
                     url="https://developer.riotgames.com/",
                     icon_url="https://pbs.twimg.com/media/D4StaQrW4AINArW.png")
    embed.set_thumbnail(url=f"https://ddragon.leagueoflegends.com/cdn/{version['n']['profileicon']}/img/profileicon/"
                            f"{player['profileIconId']}.png")
    if not prs:
        embed.add_field(name="Aucun classement", value="Pas d'informations disponibles")
    for i in range(len(prs)):
        wins = prs[i]['wins']
        loses = prs[i]['losses']
        wr = round((wins / (wins + loses) * 100), 1)
        embed.add_field(name=rankTypes[prs[i]['queueType']], value=f"{prs[i]['tier']} {prs[i]['rank']} "
                                                                   f"*{prs[i]['leaguePoints']} LP* | `W:{wins} "
                                                                   f"L:{loses}` | `WR:{wr}%`", inline=False)
    user = await bot.fetch_user(313767268578361345)
    embed.set_footer(text=f"Developed by {user.name}#{user.discriminator}", icon_url=user.avatar_url)
    await ctx.send(embed=embed)


@bot.command(name="analyse", help="Photo montage | Refers to the anime Pyscho-pass (!analyse @DamStruk)")
async def analyse(ctx, member: discord.Member):
    await ctx.channel.send(":brain: Calculating the crime coefficient of " + member.name + " ...", delete_after=3)
    asset = member.avatar_url_as(format="png", size=1024)
    coefficient(asset, member.name, member.id)
    embed = discord.Embed(color=discord.Color.blue())
    embed.set_author(name=f"Requested by {ctx.author}",
                     icon_url="https://static.wikia.nocookie.net/psychopass/images/7/72/Sibyl_System.png/revision/latest?cb=20141029202159")
    file = discord.File(member.name + ".png", filename="image.png")
    embed.set_image(url="attachment://image.png")
    user = await bot.fetch_user(313767268578361345)
    embed.set_footer(text=f"Developed by {user.name}#{user.discriminator}", icon_url=user.avatar_url)
    await ctx.send(file=file, embed=embed)
    os.remove(member.name + ".png")


maxWidth = 1024
maxHeight = 1024


# Utilise la library PIL pour faire un montage photo
def coefficient(url: str, name: str, user_id: int):
    random.seed(user_id)
    cc_int = random.randint(0, 320)
    cc_float = random.randint(0, 9)
    if cc_int < 100:
        layer = Image.open("layers/blue_layer.png")
        target_text = "Not Target"
    elif 100 <= cc_int < 299:
        target_text = "Execution"
        layer = Image.open("layers/yellow_layer.png")
    else:
        layer = Image.open("layers/red_layer.png")
        target_text = "Execution"

    pp = Image.open(requests.get(url, stream=True).raw)

    width, height = pp.size
    ratio = min(maxWidth / width, maxHeight / height)
    size = (int(pp.size[0] * ratio), int(pp.size[1] * ratio))
    pp = pp.resize(size)

    cc_text = str(cc_int) + "." + str(cc_float)
    cc_font = ImageFont.truetype("ArialCEBoldItalic.ttf", 80)
    target_font = ImageFont.truetype("ArialCEBoldItalic.ttf", 43)

    pp.paste(layer, (0, 0), layer)

    draw = ImageDraw.Draw(pp)
    draw.text((752, 254), cc_text, (255, 255, 255), font=cc_font)
    draw.text((752, 371), target_text, (255, 255, 255), font=target_font)
    pp.save(name + ".png")


bot.run(data['token_discord'])
