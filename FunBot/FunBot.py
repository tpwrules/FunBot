#Copyright (c) 2010 Thomas Watson

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

print "Starting up..."

import socket
import pickle
import ConfigParser
import sys
import copy
import traceback
import time
import threading
import os

#GAME IMPORTS
from games import saynumber
from games import roulette
from games import gofish
from games import uno

#PLUGIN DICTIONARY
gamemodules = {uno.__gamename__:uno, saynumber.__gamename__:saynumber, roulette.__gamename__:roulette, gofish.__gamename__:gofish}

class Irc:
	def __init__(self, s, users, config, nicklist):
		self._s = s
		self._users = users
		self._nicklist = nicklist
		self._config = config
		self._queue = []
		self._lock = threading.Lock()
		self._running = True
		self._thread = threading.Thread(target=self._queuehandler)
		self._thread.start()
	def quote(self, data):
		self._lock.acquire()
		self._queue.insert(0, data+"\r\n")
		self._lock.release()
	def privmsg(self, dest, msg):
		self.quote("PRIVMSG "+dest+" :"+msg)
	def notice(self, dest, msg):
		self.quote("NOTICE "+dest+" :"+msg)
	def saveuserdb(self):
		pickle.dump(self._users, open(config.userfile, "w"))
	def getuserdata(self, name, user):
		try:
			data = copy.copy(self._users[user][1][name])
		except:
			data = None
		return data
	def setuserdata(self, name, user, data):
		try:
			self._users[user][1][name] = copy.copy(data)
		except:
			pass
	def getnick(self, user):
		return self._nicklist[user]
	def _queuehandler(self):
		while self._running:
			time.sleep(0.4)
			self._lock.acquire()
			if len(self._queue) == 0:
				self._lock.release()
				continue
			self._s.send(self._queue.pop())
			self._lock.release()
	def __del__(self):
		self._running = False
		
class GameIrc:
	def __init__(self, irc, dest, gamename):
		self._irc = irc
		self._gamename = gamename
		self._dest = dest
	def send(self, data):
		self._irc.privmsg(self._dest, data)
	def notice(self, person, data):
		self._irc.notice(person, data)
	def quote(self, data):
		self._irc.quote(data)
	def getuserdata(self, user):
		return self._irc.getuserdata(self._gamename, user)
	def setuserdata(self, user, data):
		self._irc.setuserdata(self._gamename, user, data)
	def getnick(self, user):
		return self._irc.getnick(user)
		

class Container:
	pass

config = Container()
old = ""
loggedin = {}
nicklist = {}
state = 0
channels = {}
chanlookup = {}

print "Reading config file..."
cfgfile = ConfigParser.RawConfigParser()
cfgfile.readfp(open("FunBot.ini"))
config.godusers = cfgfile.get("config", "godusers").split(",")
config.server = cfgfile.get("config", "server")
config.port = cfgfile.getint("config", "port")
config.userfile = cfgfile.get("config", "userfile")
config.nick = cfgfile.get("config", "nick")
config.prefix = cfgfile.get("config", "prefix")
try:
	config.password = cfgfile.get("config", "pass")
except:
	config.password = None
cfgchanlist = cfgfile.get("config", "channels").split(",")

print "Reading user file..."
try:
	users = pickle.load(open(config.userfile))
except:
	print "Error loading user file! Creating a new one..."
	pickle.dump({}, open(config.userfile, "w"))
	users = {}

print "Connecting to server..."
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((config.server, config.port))

irc = Irc(s, users, config, nicklist)

if config.password != None:
	irc.quote("PASS "+config.password)

irc.quote("NICK "+config.nick)
irc.quote("USER "+config.nick+" something nothing :FunBot!")

def handledualcmd(frompm, cmddata, nick, hostname, channel=""):
	if frompm == True:
		cmd = cmddata[0][1:].lower()
	else:
		cmd = cmddata[0][2:].lower()
	cmddata = cmddata[1:]
	if cmd == "help":
		try:
			gamename = cmddata[0]
		except:
			irc.notice(nick, "Error! Not enough parameters! Syntax: help <gamename>")
			return True
		if gamename not in gamemodules:
			irc.notice(nick, "Error! No such game!")
			return True
		for x in gamemodules[gamename].__helptext__.split("\n"):
			irc.notice(nick, x)
	elif cmd == "stats":
		try:
			gamename = cmddata[0]
		except:
			irc.notice(nick, "Error! Not enough parameters! Syntax: stats <gamename> [user]")
			return True
		if gamename not in gamemodules:
			irc.notice(nick, "Error! No such game!")
			return True
		try:
			person = cmddata[1]
		except:
			if hostname not in loggedin:
				irc.notice(nick, "Error! You must specify a user because you are not logged in!")
				return True
			person = loggedin[hostname][0]
		try:
			x = users[person]
		except:
			irc.notice(nick, "Error! No such user!")
			return True
		if frompm == True:
			gameirc = GameIrc(irc, nick, gamename)
		else:
			gameirc = GameIrc(irc, channel, gamename)
		try:
			gamemodules[gamename].disp_stats(gameirc, users[person][1][gamename])
		except:
			irc.notice(nick, "Error! No stats exist for this game and person!")
	elif cmd == "list":
		irc.notice(nick, "Games: " + ", ".join(gamemodules.keys()))
	else:
		return False
	return True
	
def handle_plugin_error(chan):
	irc.privmsg(chan, "Internal plugin error! Game will have to be ended :(")
	channels[chan][5] = 0
	channels[chan][2] = None
	for x in channels[chan][6]:
		loggedin[x][1].remove(chan)
	print "[PLUGIN ERROR TRACEBACK]"
	traceback.print_exc(file=sys.stdout)
	print "[END PLUGIN TRACEBACK]\nSending to tpw_rules"
	irc.privmsg("tpw_rules", "Your bot had an exception! Do something!")
	for x in traceback.format_exc().split("\n"):
		irc.privmsg("tpw_rules", x)
		time.sleep(1)
	
try:
	while True:
		cmds = old+s.recv(1024)
		cmds = cmds.replace("\n", "").split("\r")
		old = cmds[-1]
		for line in cmds[:-1]:
			print line
			parts = line.split(" ")
			if parts[0] == "PING":
				irc.quote("PONG "+parts[1])
				continue
			if state == 1: #main loop
				if parts[0] == servername:
					if parts[1] == "366":
						print "Successfully joined", parts[3]
						try:
							gamelist = cfgfile.get(chanlookup[parts[3]], "games").split(",")
						except:
							gamelist = []
						try:
							prefix = cfgfile.get(chanlookup[parts[3]], "prefix")
						except:
							prefix = config.prefix
						channels[parts[3]] = [gamelist, "", None, [], "", 0, [], prefix] 
					continue
				nickend = parts[0].find("!")
				nick = parts[0][1:nickend]
				hostname = parts[0][nickend:]
				if parts[1] == "PRIVMSG" and parts[2] == config.nick:
					cmd = parts[3][1:].lower()
					if cmd == "register":
						try:
							username = parts[4]
							password = parts[5]
						except:
							irc.notice(nick, "Error! Not enough parameters! Syntax: register <user> <pass>")
							continue
						if username in users:
							irc.notice(nick, "Error! This user already exists!")
							continue
						users[username] = [password, {}]
						irc.saveuserdb()
						irc.notice(nick, "User created successfully!")
					elif cmd == "login":
						try:
							username = parts[4]
							password = parts[5]
						except:
							irc.notice(nick, "Error! Not enough parameters! Syntax: login <user> <pass>")
							continue
						if username not in users:
							irc.notice(nick, "Error! User does not exist!")
							continue
						if users[username][0] != password:
							irc.notice(nick, "Error! Invalid password!")
							continue
						if hostname not in loggedin and username not in nicklist:
							loggedin[hostname] = [username, []]
							nicklist[username] = nick
							irc.notice(nick, "Successfully logged in!")
						else:
							irc.notice(nick, "You're already logged in!")
					elif cmd == "logout":
						if hostname not in loggedin:
							irc.notice(nick, "You're not logged in!")
							continue
						if len(loggedin[hostname][1]) != 0:
							irc.notice(nick, "Finish your games first!")
							continue
						del nicklist[loggedin[hostname][0]]
						del loggedin[hostname]
						irc.notice(nick, "Logged out successfully!")
					else:
						if handledualcmd(True, parts[3:], nick, hostname):
							continue
						try:
							if loggedin[hostname][0] not in config.godusers:
								continue
						except:
							continue
						if cmd == "quote":
							irc.quote(" ".join(parts[4:]))
						elif cmd == "reload":
							try:
								module = gamemodules[parts[4]]
							except:
								irc.notice(nick, "No such game!")
								continue
							try:
								reload(module)
							except:
								irc.privmsg(nick, "Reload error!")
								for x in traceback.format_exc().split("\n"):
									irc.privmsg(nick, x)
									time.sleep(1)
								print traceback.format_exc()
								continue
							irc.notice(nick, "Plugin reloaded successfully!")
				elif parts[1] == "PRIVMSG" and parts[3][:2] == ":"+channels[parts[2]][7]:
					chan = parts[2]
					if handledualcmd(False, parts[3:], nick, hostname, chan):
						continue
					if hostname not in loggedin:
						irc.notice(nick, "Error! You need to be logged in!")
						continue
					cmd = parts[3][2:].lower()
					if cmd == "play":
						if channels[chan][5] != 0:
							irc.notice(nick, "Error! A game has already been started!")
							continue
						try:
							gamename = parts[4]
						except:
							irc.notice(nick, "Error! Not enough parameters! Syntax: play <gamename> [options]")
							continue
						if gamename not in gamemodules:
							irc.notice(nick, "Error! No such game!")
							continue
						channelstuff = channels[chan]
						if len(channelstuff[0]) != 0:
							if gamename not in channelstuff[0]:
								irc.notice(nick, "Error! That game cannot be played in this channel!")
								continue
						channelstuff[1] = gamename
						try:
							channelstuff[2] = gamemodules[gamename].start(GameIrc(irc, chan, gamename), parts[5:])
						except:
							try:
								channelstuff[2] = gamemodules[gamename].start(GameIrc(irc, chan, gamename), [])
							except:
								handle_plugin_error(chan)
								continue
						channelstuff[3] = [loggedin[hostname][0]]
						channelstuff[6] = [hostname]
						loggedin[hostname][1].append(chan)
						channelstuff[4] = loggedin[hostname][0]
						channelstuff[5] = 1
						try:
							channels[chan][2].join(loggedin[hostname][0])
						except:
							handle_plugin_error(chan)
							continue
						irc.privmsg(chan, "Game "+gamename+" opening! Type !join to join!")
					elif cmd == "stop":
						if channels[chan][5] == 0:
							irc.notice(nick, "Error! Game is already stopped!")
							continue
						if loggedin[hostname][0] != channels[chan][4]:
							irc.notice(nick, "Error! You didn't start this game!")
							continue
						channels[chan][5] = 0
						try:
							channels[chan][2].stop()
						except:
							handle_plugin_error(chan)
							continue
						channels[chan][2] = None
						for x in channels[chan][6]:
							loggedin[x][1].remove(chan)
						irc.privmsg(chan, "Game has been stopped!")
					elif cmd == "start":
						if channels[chan][5] != 1:
							irc.notice(nick, "Error! Game has already been started or no game is running!")
							continue
						if loggedin[hostname][0] != channels[chan][4]:
							irc.notice(nick, "Error! You didn't start this game!")
							continue
						players = gamemodules[channels[chan][1]].__players__
						if players != -1:
							if len(channels[chan][3]) < players:
								irc.notice(nick, "Error! You need at least "+str(players)+" players! You currently have "+str(len(channels[chan][3])))
								continue
						irc.privmsg(chan, "Players: " + ", ".join(channels[chan][3]))
						irc.privmsg(chan, "Game has started!")
						try:
							channels[chan][2].start()
						except:
							handle_plugin_error(chan)
							continue
						channels[chan][5] = 2
					elif cmd == "join":
						if channels[chan][5] != 1:
							irc.notice(nick, "Error! Game has already been started or no game is running!")
							continue
						if loggedin[hostname][0] in channels[chan][3]:
							irc.notice(nick, "Error! You have already joined the game!")
							continue
						try:
							channels[chan][2].join(loggedin[hostname][0])
						except:
							handle_plugin_error(chan)
							continue
						channels[chan][3].append(loggedin[hostname][0])
						channels[chan][6].append(hostname)
						loggedin[hostname][1].append(chan)
						irc.privmsg(chan, loggedin[hostname][0] + " has joined the game!")
					elif channels[chan][5] == 2:
						try:
							result = channels[chan][2].handlecmd(parts[3][2:], parts[4:], loggedin[hostname][0], nick)
						except:
							handle_plugin_error(chan)
							continue
						if result:
							irc.privmsg(chan, "The game has ended!")
							channels[chan][5] = 0
							for x in channels[chan][6]:
								loggedin[x][1].remove(chan)
							channels[chan][2] = None
							irc.saveuserdb()
				elif parts[1] == "NICK":
					try:
						nicklist[loggedin[hostname]] = parts[2][1:]
					except:
						continue
				elif parts[0] == "ERROR":
					sys.exit(1)
			elif state == 0: #connecting to server
				if parts[1] == "001":
					state = 1
					servername = parts[0]
					for x in cfgchanlist:
						channel = cfgfile.get(x, "channel")
						try:
							keyword = " "+cfgfile.get(x, "key")
						except:
							keyword = ""
						chanlookup[channel] = x
						print "Joining", channel
						irc.quote("JOIN "+channel+keyword)
except KeyboardInterrupt:
	print "Exiting..."
	irc.quote("QUIT :No, not CTRL+C!")
	irc.saveuserdb()
	os._exit(0)
except Exception, e:
	irc.privmsg("tpw_rules", "Your bot had an exception! Do something!")
	for x in traceback.format_exc().split("\n"):
		irc.privmsg("tpw_rules", x)
		time.sleep(1)
	irc.quote("QUIT :Internal error! Go complain to tpw_rules! Bot should restart shortly")
	pickle.dump(users, open(config.userfile+".err", "w"))
	raise
	os._exit(1)