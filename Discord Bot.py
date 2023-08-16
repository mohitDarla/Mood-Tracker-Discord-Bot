import discord #imported discord package from cmd
from discord.ext import commands, tasks #Retrieving commands and tasks module from discord.ext package 
#sqlite3 is the default for syncronous, aiosqlite is better for asyncronous
import aiosqlite #Using the discord package database SQL for async commands!
import datetime #importing the current date and time
import requests #fetching the JSON api format
import config

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all()) #command start with '!' & enabling all intents
#Main program can use the api keys
"""
Using an 'async def' is for asynchronous commands and programs
Using 'await' keyword is inside async func to call other async func or coroutines. Can switch tasks aswell 
'async with' sets up the connection to the computer and ensures that the async resource is properly managed, acquired, and released
Cursor is an object or a handle to interact with a database. Traverses and mainpulates data row by row
Allows you to navigate thru this result set/access data each row
Query is a request to the database to retrieve and use data. You can add, delete, insert, and update,etc
'with' keyword is used to handle resource allocation and clean up automatically. the 'as' keyword is used to assign a var to the resource
Use of paramter 'ctx' => discord.py and handles user commands within dicord bot  
     """
@bot.event #event handler
#Function that starts up the bot and immediately connects to the database
async def on_ready():  
    print('The bot is now ready for use~')
    #defined to handle database connections. connects to the database, whenever event is started
    #Use aiosqlite.connect("the database file") as database:
    async with aiosqlite.connect("mood_tracker.db") as database:
        #Creating a cursor to traverse the query
        async with database.cursor() as cursor:
            #Creating the table 'mood data' that the data can store user's mood
            #Table headers can be anything HOWEVER must be consistent throughout when using 'cursor.execute()'
            #Implementing "CREATE TABLE IF NOT EXISTS" ensures that the table will only be created once if there is no database
            await cursor.execute('CREATE TABLE IF NOT EXISTS mood_tracker (user INTEGER, mood TEXT, timeDate TEXT, lastReminder TEXT)')
            #Must use database.commit() everytime data is being changed or stored
        await database.commit()

    async with aiosqlite.connect("lastQuote.db") as database:
        #Creating a cursor to traverse the query
        async with database.cursor() as cursor:
            #Creating a table specifically for daily quotes and the time to be accessed
            await cursor.execute('CREATE TABLE IF NOT EXISTS lastQuote (quote TEXT, time TEXT)')
            bool = await cursor.fetchone()
            if bool:
                pass
            elif not bool:
                tempQuote = "I Love You"
                tempTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                await cursor.execute('INSERT INTO lastQuote (quote, time) VALUES (?, ?)',(tempQuote, tempTime))

        await database.commit()    
    #Close database at the end, but dont need because of 'async function' await database.close()
    remindMood.start()
    motivationalQuote.start()
            
@bot.command(name = 'dm') #defining the command explicitly
async def directMessage(ctx):
    
    userID = ctx.author.id
    
    async with aiosqlite.connect('mood_tracker.db') as database:
        async with database.cursor() as cursor:
            await cursor.execute("SELECT user FROM mood_tracker")
            allUsers = await cursor.fetchall()
            userList = []
            for i in allUsers:
                userList.append(i[0])
            if userID in userList:
                pass
            else:          
                message = 'A direct message from FeelingYou! \n' + 'Congratulations! You just created your own private dm with me. \n' + 'My goal is to assist you in tracking your mood and to put a smile on your beautiful face!'
                await ctx.author.send(message) #Sends a message to the author only
                await cursor.execute("INSERT INTO mood_tracker (user, timeDate, lastReminder) VALUES (?, ?, ?)",(userID, datetime.datetime.now(), datetime.datetime.now()))
                await database.commit()
    

@bot.command(name = 'track') # defining the mood command explicitly
#* is needed for the string to support multiple data types
async def trackMood(ctx, *moodType: str): #moodType: str is useful for conveying the parameter var type 
    moodPhrase = ' '.join(moodType) #creates a phrase from each string
    #isinstance function is when the specified object is of the same type and returns true
    #Checks if the command is invoked in the text or DM
    if isinstance(ctx.channel, discord.DMChannel):
        userID = ctx.author.id #Initializing user id var so that database can differentiate between each user
        currentDateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')  # Gets current timestamp
        #Establishes a connection to the database
        async with aiosqlite.connect("mood_tracker.db") as database:
            #Creates an asyncronous cursor within the database that is used to execute queries
            async with database.cursor() as cursor:
            #Updates the mood type values, user Id, mood type, and the current date and time to the database in the string format
                await cursor.execute('INSERT INTO mood_tracker (user, mood, timeDate, lastReminder) VALUES (?, ?, ?, ?)',(userID, moodPhrase, currentDateTime, currentDateTime))
                #Must use database.commit() everytime data is being changed or stored
            await database.commit()      
        phrase = ""      
        for i in range(len(moodPhrase)):
            phrase += moodPhrase[i]   
        await ctx.author.send("You've successfully updated your mood log of " + phrase +"! Type in !remove to remove your latest mood")
    else:
        await ctx.author.send('Please use this command in your private server with your bot')
        await ctx.message.delete() #deletes a message in the server

@bot.command(name = 'remove') #Explicitly defined command
#Function to remove the latest mood that was tracked
async def removeMood(ctx): #Paramter of ctx, which is the user string in the discord server or dm
    userID = ctx.author.id #Retrieves the id of the user in integer format
    #Checks whether in a server or DM
    if isinstance(ctx.channel, discord.DMChannel):
        #connects to the database
        async with aiosqlite.connect("mood_tracker.db") as database:
            async with database.cursor() as cursor:
                #Selects the SQL query to retrieve using the cursor object on a database, or you could also select a specfic query using the userID
                #await cursor.execute --> Initiates the execution of an SQL query using a cursor obj
                """
                SELECT mood, timeDate: This specifies that you want to retrieve the values from the mood and the timeDate column.
                FROM mood_tracker: This indicates that you're retrieving data from the mood_tracker table.
                WHERE user = ?: This is a condition that filters the rows. It's looking for rows where the value in the user column matches the value provided as the parameter. The ? is a placeholder for the value of userID.
                ORDER BY timeDate DESC: This clause specifies that the results should be ordered by the timeDate column in descending order. This means the latest (most recent) entries will be at the top.
                LIMIT 1: This restricts the result to only one row. Since you're ordering by timeDate in descending order, this will give you the latest entry for the specified user.
                (userID, his is a tuple containing the value of userID. The comma at the end is necessary to indicate that it's a tuple with a single element. The execute method will replace the ? placeholder with the actual value of userID.   
                """
                await cursor.execute('SELECT mood, timeDate FROM mood_tracker WHERE user = ? ORDER BY timeDate DESC', (userID,))
                deleteData = await cursor.fetchall() #Retrieves the result of the query using 'fetchone()' in the form of a tuple
                #Check if there is a query of the fetchone func
                if len(deleteData) > 1: #If there is a query
                    #The query is stored in a tuple.
                    #User Id is not part of the tuple
                    moodType = deleteData[0] #Mood type is in the tuple of the database in the first column
                    dateAndTime = deleteData[1] #Mood type is in the tuple of the database of the second column, because defined in the cursor.execute above
                    #Executes the deletion of the entire query from the database in this format
                    await cursor.execute('DELETE FROM mood_tracker WHERE user = ? AND mood = ? AND timeDate = ?', (userID, moodType, dateAndTime))
                    #Ensures changes are saved when made using .commit
                    await database.commit()
                    await ctx.author.send('You successfully deleted your mood entry of ' + moodType + ".")
                else:
                    await ctx.author.send('You have no existing moods logged')    
    else:
        await ctx.author.send('Please use this command in your private server with your bot')
        await ctx.message.delete()        
@bot.command(name = 'history')
async def trackHistory(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        #Connects to the SQLite server as a database
        async with aiosqlite.connect("mood_tracker.db") as database:
            #Utilizing the cursor to execute any possible queries within the database
            async with database.cursor() as cursor:
                #Retrieves the user id of the user within the DM
                userID = ctx.author.id
                #await keyword for the asynchronous command, cursor.execute to select the entire mood and timeDate column
                await cursor.execute('SELECT mood, timeDate FROM mood_tracker WHERE user = ? ORDER BY timeDate DESC', (userID,))
                #Fetches all queries from the databases and need await for the async coroutines and functions
                moodLog = await cursor.fetchall()
                #checks if there is a query within the database
                if moodLog:
                    #Loops through the entire database full of queries and prints them out to the user
                    for q in range(len(moodLog)- 1):
                        await ctx.author.send(moodLog[q])
                else:
                     await ctx.author.send('You have no existing moods logged')
    else:
        await ctx.author.send('Please use this command in your private server with your bot')
        await ctx.message.delete()  

@tasks.loop(seconds = 86400)
async def remindMood():
    async with aiosqlite.connect('mood_tracker.db') as database:
        async with database.cursor() as cursor:
            #'Uses a query to SELECT a DISTINCT user from the database
            #You can modify the SELECT clause to fit your description and in this case it gets the maximum time for each individual user
            await cursor.execute("SELECT user, MAX(lastReminder) FROM mood_tracker GROUP BY user")
            #Fetches the table of users based on the query call on the data retreival in the form of a tuple
            userTuple = await cursor.fetchall()
            for i in userTuple:
                distinctUsers = i[0]
                reminder = i[1]
                user =  bot.get_user(distinctUsers)
                """strptime is used for converting a string to a datetime object.
                strftime is used for converting a datetime object to a formatted string."""
                lastReminder =  datetime.datetime.strptime(reminder, '%Y-%m-%d %H:%M:%S.%f') 
                currentTime = datetime.datetime.now()#current time and date
                #Whenever two objects are subtracted, there is a time delta difference & 3600 seconds in an hour
                dIS = currentTime - lastReminder
                #Sends a message every 24+ hours to remind the user or if there is no updated time
                #Using boolean to limit any unecessary loops when the bot is started
                if (dIS.total_seconds() >= 86400.0 or dIS.days >= 1): 
                    await user.send('Reminder to log in your mood for the day~ It has been about ' + str(int(dIS.total_seconds() // 3600)) + ' hours since your last update.')
                    await cursor.execute("UPDATE mood_tracker SET lastReminder = ? WHERE user = ? AND timeDate = (SELECT MAX(timeDate) FROM mood_tracker WHERE user = ?)", (currentTime, distinctUsers, distinctUsers))
                    await database.commit() 
"""Using an API from ZenQuotes.io
->JSON is a text based format that uses key-value pairs to store data, where the key is a string and a value is text
->
->
"""
def fetchQuote():
    baseURL = 'https://zenquotes.io/api/random/'
    r = requests.get(baseURL)
    data = r.json()[0]['q']
    quote = data.split(" ")
    singular = ['man', 'men']
    plural = ['men', 'women']
    for i in range(len(quote)):
        if i in singular:
            quote[i] = 'person'
        elif i in plural:
            quote[i] = 'people'

    phrase = " ".join(quote)
    
    return phrase

@tasks.loop(seconds=21600)
async def motivationalQuote():
    currTime = datetime.datetime.now()
    quoteTupletime = ()
    async with aiosqlite.connect("lastQuote.db") as db1:
        async with db1.cursor() as c1:
            await c1.execute("SELECT quote, time FROM lastQuote ORDER BY time DESC LIMIT 1")
            quoteTupletime = await c1.fetchone()
    
    latestTime = datetime.datetime.strptime(quoteTupletime[1], '%Y-%m-%d %H:%M:%S.%f')
    dIS = currTime - latestTime
    
    if dIS.total_seconds() >= 21600.0 or dIS.days >= 1:
        phrase = fetchQuote()
    
        async with aiosqlite.connect("lastQuote.db") as db1:
            async with db1.cursor() as c1:
                await c1.execute('INSERT INTO lastQuote (quote, time) VALUES (?, ?)', (phrase, currTime))
                await db1.commit()
                
        async with aiosqlite.connect("mood_tracker.db") as db2:
            async with db2.cursor() as c2:
                await c2.execute("SELECT user FROM mood_tracker")
                userTuple = await c2.fetchall()
        
        user_ids = []
        for user in userTuple:
            if user[0] in user_ids:
                pass
            else:
                user_ids.append(user[0]) 
        
        for i in user_ids:
            user = bot.get_user(i)            
            await user.send("This is your daily dose of inspirational quotes! \n" + phrase)
            
            

bot.run(config.botToken)

