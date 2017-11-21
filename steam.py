import json
import urllib
import jinja2
import os
import urllib2
from urllib import urlencode
from io import open
from urllib import urlopen
from key import secretkey

debug = False  # prints URLs with game data. WARNING: YOUR API KEY WILL BE VISIBLE IN THE OUTPUT
apiKey = secretkey  # place in file "key.py" with variable name secretkey. Get a key at https://steamcommunity.com/dev!
steamID = "76561198011479838"  # I've included the ID for my own account for you to test things out with!
# Here's some info on how to find your steamID if you don't know it, btw:
# https://steamcommunity.com/sharedfiles/filedetails/?id=209000244
jinjaData = {'username': '', 'self': [], 'friends': [], 'finalString': ''}
gameTotals = {'SUMTOTAL': 0}
timeTotal = 0


def dataSafeGet(url):
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        if hasattr(e, "code"):
            if e.code == 500:
                print("Error: Account not found.")
            elif e.code == 403:
                print("Error: Invalid API Key")
            else:
                print("Unknown Error! D:")
                print("Error code: ", e.code)
        elif hasattr(e, 'reason'):
            print("Failed to reach server.")
            print("Reason: ", e.reason)
        return None
    data = response.read().decode("utf-8")
    return json.loads(data)

def gamePrinter(steamID, name ="this user"):
    url = "http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key=" + apiKey + "&steamid=" + steamID + "&format=json"
    userdata = dataSafeGet(url)
    if debug:
        print(url)
    if userdata != None:
        print("In the last two weeks " + name + " has played:")
        if len(userdata['response']) == 0:
            print("User data private! :<")
        elif userdata['response']['total_count'] == 0:
            print("Nothing!")
        else:
            for game in userdata['response']['games']:
                minutes = game['playtime_2weeks'] % 60
                hours = int((game['playtime_2weeks'] - minutes) / 60)
                if game.get('name', None) != None:
                    title = game['name']
                else:
                    #Some titles, like PUBG Test Server, do not provide a title in the API for some reason.
                    title = "PRODUCT ID DOES NOT LIST TITLE"
                totaler(title, game['playtime_2weeks'])
                print(playtimePrinter(title, hours, minutes))
        print("")

def playtimePrinter(title, hours, minutes):
    string = ""
    string += title + " for "
    if hours != 0:
        string += "%s hours and " % hours
    if minutes != 1:
        string += "%s minutes!" % minutes
    else:
        string += "%s minute!" % minutes
    return string

def totaler(title, time):
    if gameTotals.get(title, None) == None:
        gameTotals[title] = 0
    gameTotals[title] += time
    gameTotals['SUMTOTAL'] += time

def getFriends(steamID):
    url = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key=" + apiKey + "&steamid=" + steamID + "&relationship=friend"
    return dataSafeGet(url)

def getUserInfo(steamID):
    url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=" + apiKey + "&steamids=" + steamID
    data = dataSafeGet(url)
    return data["response"]["players"][0]

def printFriendRecentGames(steamID):
    frienddata = getFriends(steamID)
    for friend in frienddata["friendslist"]["friends"]:
        userdata = getUserInfo(friend["steamid"])
        gamePrinter(userdata["steamid"], userdata["personaname"])

def printRecentGames(steamID):
    userdata = getUserInfo(steamID)
    jinjaData['username'] = userdata['personaname']
    gamePrinter(userdata["steamid"], userdata["personaname"])

def totalPrint():
    totalTime = gameTotals.pop('SUMTOTAL')
    minutes = totalTime % 60
    hours = int((totalTime - minutes) / 60)
    import operator
    sortedGames = sorted(gameTotals.items(), key=operator.itemgetter(1), reverse=True)
    print 'The top ten games by playtime were:'
    for game in sortedGames[0:10]:
        tempMinutes = game[1] % 60
        tempHours = (game[1] - tempMinutes) / 60
        print '%s: %s hours and %s minute(s)' % (game[0], tempHours, tempMinutes)
    print '\n'
    finalA = 'You and your friends played games for a total of %s hours and %s minute(s)!' % (hours, minutes)
    finalB = 'That\'s enough time to read \"War & Peace\" over %s times!' % (hours/33)
    print finalA, finalB
    jinjaData['finalString'] = finalA + '\n' + finalB

def jinjaWrite(data):
    JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                           extensions=['jinja2.ext.autoescape'], autoescape=True)
    template = JINJA_ENVIRONMENT.get_template('jinjaTemplate.html')

    f = open('page.html', 'w', encoding='UTF-8')
    f.write(template.render(data))
    f.close()


printRecentGames(steamID)
printFriendRecentGames(steamID)
totalPrint()
jinjaWrite(jinjaData)