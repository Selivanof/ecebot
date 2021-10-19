#IMPORTS
import asyncio
import discord
from nextcord.ext import commands
import nextcord
import os
import requests
from datetime import datetime, timezone
import pytz
import psycopg2
import unicodedata
import random

#Colors to be used by the "now" command
year_colors_now = [0x305ec9,0x39c49b,0x66c24a,0xc8d64d,0xd19136]
year_colors_upcoming = [0x183066,0x206b55,0x366628,0x818a33,0x78531f]

#
#DATETIME STUFF
#

#Setting up the timezone
tz = pytz.timezone('Europe/Athens')

#For english-greek conversion of day names
day_names = {
    "Monday": "Δευτέρα",
    "Tuesday": "Τρίτη",
    "Wednesday": "Τετάρτη",
    "Thursday": "Πέμπτη",
    "Friday": "Παρασκευή"
}

#
#DISCORD STUFF
#

intents = nextcord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='meli ', intents=intents,help_command=None) #COMMANDS PREFIX HERE

#
#HELPER FUNCTIONS
#

#Getting the role of a member
def get_role(name):
  return nextcord.utils.find(lambda r: r.name == name, bot.guild.roles)

#Remove any accents and decapitilize greek strings
def greek_normal(s):
  text = unicodedata.normalize("NFC", "".join(
    ch
    for ch in unicodedata.normalize("NFD", s)
    if ch not in ["\u0301"])
  )
  return text.lower()



#
#PASTEBIN API STUFF
#

login_data = {
    'api_dev_key': os.getenv('PSTB_TOKEN'),
    'api_user_name': os.getenv('PSTB_USER'),
    'api_user_password': os.getenv('PSTB_PASS')
    }

data = {
      'api_option': 'paste',
      'api_dev_key':os.getenv('PSTB_TOKEN'),
      'api_paste_code':' - ',
      'api_paste_name':' - ',
      'api_paste_expire_date': '2W',
      'api_user_key': None,
      'api_paste_format': 'python'
      }
 
#Logging in to pastebin API
login = requests.post("https://pastebin.com/api/api_login.php", data=login_data)
print("Pastebin login status: ", login.status_code if login.status_code != 200 else "OK/200")
print("Pastebin user token: ", login.text)
data['api_user_key'] = login.text

#Function for uploading pastes to pastebin
def uploadPaste(title,body,duration):
  if not title:
    title = 'No title'
  if not body:
    body = 'No text'
  if not duration:
    duration = '1D'

  data['api_paste_name'] = title
  data['api_paste_code'] = body
  data['api_paste_expire_date'] = duration
  
  newpaste = requests.post("https://pastebin.com/api/api_post.php", data=data)
  print("Paste title:", data['api_paste_name'])
  print("Paste send: ", newpaste.status_code if newpaste.status_code != 200 else "OK/200")
  print("Paste URL: ", newpaste.text)
  return newpaste.text



#BOT READY
@bot.event
async def on_ready():
  activity = nextcord.Game(name="meli help", type=3) #BOT ACTIVITY STATUS HERE
  await bot.change_presence(status=nextcord.Status.online, activity=activity)
  print("Bot ready!") 


#
#UTILITY COMMANDS
#

#Updating every member's role to next year (e.g. members with the year1 role get the year2 role) - only for admins
@bot.command(name='update',pass_context=True)
@commands.has_permissions(administrator=True)
async def updateRoles(ctx):
  if os.getenv('ALLOW_UPDATE') == '1': #An enviroment variable can disable this command so that it is not used by mistake
    print('Updating roles...')
    
    log_title = "Roles Update | " + datetime.today().strftime('%d-%m-%Y')
    update_log="Updating roles \n\n"

    await ctx.send("Starting roles update...")
    guild = ctx.message.guild
    for member in guild.members:

          #ROLE NAMES BY DESCENDING ORDER
          roles = [ nextcord.utils.get(guild.roles,name="5ο ΕΤΟΣ"), 
                    nextcord.utils.get(guild.roles,name="4ο ΕΤΟΣ"),
                    nextcord.utils.get(guild.roles,name="3ο ΕΤΟΣ"),
                    nextcord.utils.get(guild.roles,name="2ο ΕΤΟΣ"),
                    nextcord.utils.get(guild.roles,name="1ο ΕΤΟΣ")]

          if role :=next((role for role in roles if role in member.roles),False):
              
              index = roles.index(role)
              if 1 <= index <= 4: #If the role is year 1-4 | Year 5 students don't need to get their year role increased
                #Add user's name to log
                update_log += "\n" + "User: " + member.name
                #Change roles
                await member.add_roles(roles[index-1])
                await member.remove_roles(roles[index])
                #Add changes to log
                update_log += "\n" + "Old role: " + roles[index].name
                update_log += "\n" + "New role: " + roles[index-1].name
                await asyncio.sleep(1) #Optional sleep to not exceed request limit
                update_log+="\n------------------"
    
    #Upload to pastebin after completion
    paste_url = uploadPaste(log_title,update_log,"1D")
    print('Roles Updated')
    await ctx.send("Roles Updated\nLog at:" + paste_url)
  else:
    await ctx.send("You don't have permission to execute this command")


#Returns a professor's contact info - requires a professors table in the database
@bot.command(name='info')
async def info(ctx, name=None):
  
  #Connect to the database
  con = psycopg2.connect(dbname=os.getenv('DB_NAME'),user=os.getenv('DB_USER'),password=os.getenv('DB_PASS'), host=os.getenv('DB_HOST'))
  cur = con.cursor() 

  #If the user gave a string as a name
  if isinstance(name, str):
    simple_name = greek_normal(name)
    command = "SELECT * FROM professors WHERE simple_last_name = '"+ simple_name + "';"
    cur.execute(command)
    fetched_data = cur.fetchall()

    con.close()

    if fetched_data: 
      prof_data = list(fetched_data[0])

      hex_str = "0x" + ("%06x" % random.randint(0, 0xFFFFFF))
      main_color_hex = int(hex_str, 16) + 0x200

      embed=nextcord.Embed(title=prof_data[2] + ' ' +prof_data[3], description="Τομέας "+prof_data[1], color=main_color_hex)
      embed.add_field(name="Email: ", value=prof_data[4], inline=False)
      embed.add_field(name="Γραφείο: ", value=prof_data[5], inline=False)
      embed.add_field(name="Τηλέφωνο: ", value= prof_data[6], inline=False)
      embed.add_field(name="Ιστοσελίδα: ", value=prof_data[7], inline=False)

      if prof_data[8]:
        embed.set_image(url=prof_data[8])
        
      await ctx.send(embed=embed) 
    else:
      #Name not found in database
      await ctx.send("Δεν βρέθηκε καθηγητής με αυτό το όνομα")
  elif name is None:
    #No name included
    await ctx.send('Χρησιμοποιήστε το command έτσι: (meli info <όνομα καθηγητή στα ελληνικά>)') 
  else:
    #If the user gave a non-string name
    await ctx.send("Μετά το info βάλτε το όνομα του καθηγητή") 


#Sends the current and upcoming lessons
@bot.command(name='now')
async def info(ctx, year=None):
  
  #Tracking the number of current lessons
  currentLessons = 0;
  #Getting datetime info
  now = datetime.now(tz)

  current_day = day_names[now.strftime("%A")] #Current day
  current_time = now.strftime("%H:%M") #Current time
  #current_time = '17:31' #For testing outside schedule hours
  
  #Connecting to database
  con = psycopg2.connect(dbname=os.getenv('DB_NAME'),user=os.getenv('DB_USER'),password=os.getenv('DB_PASS'), host=os.getenv('DB_HOST'))
  cur = con.cursor() 

  years = ['1','2','3','4','5']

  if isinstance(year, str):
    if '1'<=year<='5':
      years = [year]
    else:#User did not enter valid year
      await ctx.send("Χρησιμοποιείστε το command έτσι: (meli info <προαιρετικός αριθμός έτους 1-5>)")
      return

  for year in years:

    #Get the table name for the year
    table_name = 'schedule_year' + year

    #Getting current lesson from the database
    command = "SELECT * FROM {} WHERE day = '{}' and start_time < '{}' and end_time > '{}'; ".format(table_name,current_day,current_time,current_time)
    cur.execute(command)
    fetched_data = cur.fetchall()
    

    year_clarification = "" if len(years)==1 else (year +'ο Έτος: ')
    
    for lesson_today in fetched_data: #Send results
      embed=nextcord.Embed(title=year_clarification+lesson_today[0] + " ({} - {})".format(lesson_today[3], lesson_today[4]) , description="Αίθουσα: {}".format(lesson_today[1]),color=year_colors_now[int(year)-1])
      currentLessons += 1
      await ctx.send(embed=embed)

    #If no lessons were found at all
    if (len(fetched_data) == 0) and (currentLessons==0) and (year==years[len(years)-1]):
      await ctx.send('Δεν διεξάγεται κανένα μάθημα αυτήν την στιγμή')
    
    #If the user requested data for a specific year, also check for upcoming lessons
    if len(years)==1:
      await ctx.send("**Προσεχώς**")
      #Getting upcoming lesson from the database
      command = "SELECT * FROM {} WHERE day = '{}' AND start_time > '{}' ORDER BY start_time LIMIT 1".format(table_name,current_day,current_time)
      cur.execute(command)
      fetched_data = cur.fetchall()

      if len(fetched_data) == 0: #No upcoming lessons
        await ctx.send('Δεν υπάρχουν άλλα μαθήματα για σήμερα')

      for lesson_today in fetched_data: #Send results
        embed=nextcord.Embed(title=lesson_today[0] + " ({} - {})".format(lesson_today[3], lesson_today[4]) , description="Αίθουσα: {}".format(lesson_today[1]),color=year_colors_upcoming[int(year)-1])
        await ctx.send(embed=embed)

#
#FUN COMMANDS
#

#Sends a "Αυτα μ'αέσουν" GIF
@bot.command(name='pog')
async def autaMaresoun(ctx):
  await ctx.message.delete()
  embed=nextcord.Embed(title="Αυτά μ'αρέσουν", description="", color=0xffffff)
  embed.set_image(url='https://c.tenor.com/EgALw2bXi2oAAAAC/mamalakis-auta-maresoun.gif')
  await ctx.send(embed=embed) 

#Sends a picture of a steak
@bot.command(name='mprizolitses')
async def autaMaresoun(ctx):
  embed=nextcord.Embed(title="Μπριζολίτσες", description="με μέλι και μουστάρδα", color=0xcca42b)
  embed.set_image(url='https://www.syntagesmekefi.gr/wp-content/uploads/2015/03/brizola.jpg')
  await ctx.send(embed=embed) 

#Sends a song from Sofia Vempo
#Todo: add multiple songs in the database and choose one randomly
@bot.command(name='sdok')
async def autaMaresoun(ctx):
  await ctx.send('https://www.youtube.com/watch?v=l8JzuSXs0GU&t=14s') 

#
#BASIC COMMANDS
#

#Lists all the functions that a member without admin privileges can access
@bot.command(name="help", description="Shows available commands")
async def help(ctx):
    embed=nextcord.Embed(title="Διαθέσιμα commands:", description="", color=0xffffff)

    #Utility commands
    embed.add_field(name="info", value="πληροφορίες καθηγητών", inline=False) #Command info
    embed.add_field(name="now", value="πληροφορίες τρεχόντων και προσεχών μαθημάτων ", inline=False) #Command now
    
    #Fun commands
    embed.add_field(name="pog", value="Αυτά μ'αρέσουν", inline=False) #Command pog
    embed.add_field(name="mprizolitses", value="με μέλι και μουστάρδα", inline=False) #Command mprizolitses
    embed.add_field(name="sdok", value="της ελλάδος παιδιά", inline=False) #Command info

    await ctx.send(embed=embed) 

#Sent when there is an error
@bot.event
async def on_command_error(ctx, error):
    print(error) #Print error to the console
    await ctx.send("Ουώχ, υπήρξε κάποιο πρόβλημα. Οι admins θα το κοιτάξουν σύντομα!")

#Starting the bot
bot.run(os.getenv('DISC_TOKEN'))