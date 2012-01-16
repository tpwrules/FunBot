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

config_name = "FunBot.ini" #name of the configuration file

print "[STATUS] Starting up..."

#import all the modules the bot needs
import socket
import pickle
import ConfigParser
import sys
import traceback
import time
import threading
import os
import copy
import hashlib

class Container: #a boring class intended for storing whatever we need
	pass
	
class KillYourselfException:
	pass
	
def passhash(value):
	return hashlib.sha1(value).hexdigest()

def log(x):
	global logfile
	ts = time.strftime("[%b %d, %Y %H:%M:%S]")
	print ts, x
	if logfile == None: return
	logfile.write(ts+" "+x+"\n")

class NetworkConnection:
	def __init__(self, s, net_name, sleeptime):
		self._s = s
		self._name = net_name
		self._lock = threading.Lock()
		self._thread = threading.Thread(target=self._handlequeue)
		self._queue = []
		self._st = sleeptime/100.0
		self._running = True
		self._thread.start()
	def quote(self, data):
		self._lock.acquire()
		self._queue.insert(0, data+"\r\n")
		self._lock.release()
	def privmsg(self, dest, msg):
		self.quote("PRIVMSG "+dest+" :"+msg)
	def notice(self, dest, msg):
		self.quote("NOTICE "+dest+" :"+msg)
	def _handlequeue(self):
		while self._running:
			time.sleep(self._st)
			self._lock.acquire()
			if len(self._queue) == 0:
				self._lock.release()
				continue
			self._s.send(self._queue.pop())
			self._lock.release()
		self._s.close()
			
class GameIrc:
	def __init__(self, net, gamename, dest, notice, prefix, host2nick, netname, tempplayers):
		self._net = net
		self._host2nick = host2nick
		self._gamename = gamename
		self._dest = dest
		self._notice = notice
		self._prefix = prefix
		self._netname = netname
		self._tempplayers = tempplayers
		self._tempdata = {}
	def quote(self, data):
		self._net.quote(data)
	def send(self, data):
		if self._notice:
			self._net.quote("NOTICE "+self._dest+" :"+data)
		else:
			self._net.quote("PRIVMSG "+self._dest+" :"+data)
	def notice(self, nick, data):
		self._net.quote("NOTICE "+nick+" :"+data)
	def getuserdata(self, hostname):
		if hostname in self._tempplayers:
			try:
				return self._tempdata[hostname]
			except:
				return None
		if hostname == "FunBot":
			try:
				return userdb[0]["FunBot"][1][self._gamename]
			except:
				return None
		try:
			return userdb[0][userdb[1][self._netname+hostname]][1][self._gamename]
		except:
			return None
	def setuserdata(self, hostname, data):
		if hostname in self._tempplayers:
			self._tempdata[hostname] = data
			return
		if hostname == "FunBot":
			userdb[0]["FunBot"][1][self._gamename] = data
			return
		userdb[0][userdb[1][self._netname+hostname]][1][self._gamename] = data
	def getprefix(self):
		return self._prefix
	def getnick(self, hostname):
		return self._host2nick[hostname]
			
def handle_exception():
	for x in traceback.format_exc().split("\n"):
		log("[TRACEBACK] "+x)

def handle_plugin_error(irc, chandata, channame, loggedin, host2nick):
	handle_exception()
	irc.privmsg(channame, "A plugin error has occurred! The game will have to be ended :(")
	cleanupgame(chandata, loggedin, channame, host2nick)
	
def connect(network):
	log("[STATUS] Parsing "+network)
	if not config_parser.has_section(network):
		log("[WARNING] No such network section, not connecting")
		return
	n = Container()
	n.prefix = global_config.prefix if not config_parser.has_option(network, "prefix") else config_parser.get(network, "prefix")
	if not config_parser.has_option(network, "nick"):
		log("[WARNING] No nick specified, not connecting")
		return
	n.nick = config_parser.get(network, "nick")
	if not config_parser.has_option(network, "server"):
		log("[WARNING] No server specified, not connecting")
		return
	n.serverpass = None if not config_parser.has_option(network, "pass") else config_parser.get(network, "pass")
	n.server = config_parser.get(network, "server")
	n.port = 6667 if not config_parser.has_option(network, "port") else config_parser.get(network, "port")
	if not config_parser.has_option(network, "channels"):
		n.channels = None
	else:
		n.channels = config_parser.get(network, "channels").split(",")
	msgwait = 50 if not config_parser.has_option(network, "msgwait") else config_parser.getint(network, "msgwait")
	n.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		n.s.connect((n.server, n.port))
	except:
		log("[WARNING] Could not create socket")
		handle_exception()
		return
	n.s.settimeout(1.0)
	n.conn = NetworkConnection(n.s, network, msgwait)
	log("[STATUS] Spawning network thread")
	n.running = True
	networks[network] = n
	n.thread = threading.Thread(target=network_handler, args=(n,))
	n.thread.start()
	return True
	
def cleanupgame(chandata, loggedin, channame, host2nick):
	chandata.currgame = None
	chandata.playing = 0
	chandata.startplayer = ""
	for x in chandata.playerlist:
		loggedin[x].chanlist.remove(channame)
	chandata.playerlist = []
	for x in chandata.tempplayers:
		del loggedin[x]
		del host2nick[x]
	chandata.tempplayers = []
	
def create_temp_user(chandata, loggedin, nick, hostname, host2nick):
	chandata.tempplayers.append(hostname)
	host2nick[hostname] = nick
	user = Container()
	user.username = nick
	user.chanlist = []
	loggedin[hostname] = user
			
def saveuserdb():
	global userdb
	log("[STATUS] Saving user database")
	pickle.dump(userdb, open(config_parser.get("config", "userfile"), "w"))
	
def dualcmdsend(stuff, text):
	if stuff[0]:
		stuff[3].notice(stuff[1], text)
	else:
		stuff[3].privmsg(stuff[1], stuff[2]+": "+text)
	
def handledualcmd(cmd, params, admin, user, stuff):
	if cmd == "help":
		if len(params) == 0:
			dualcmdsend(stuff, "Help displays help for built-in and game commands.")
			dualcmdsend(stuff, "Built-in commands: help, register, addhm, delhm, play, join, stop, stats")
			if admin:
				dualcmdsend(stuff, "Administrator commands: quote, reload, disconnect, connect")
			dualcmdsend(stuff, "Games loaded: "+", ".join(games.keys()))
			return
		if params[0] in games:
			try:
				x = params[1]
			except:
				x = None
			try:
				result = games[params[0]].show_help(x)
			except:
				dualcmdsend(stuff, "Help could not be retrieved!")
				return True
			if result == None:
				dualcmdsend(stuff, "That game does not have help for that command.")
				return True
			for x in result.split("\n"):
				dualcmdsend(stuff, x)
			return True
		if params[0] == "register":
			dualcmdsend(stuff, "Syntax: register <user> <pass>")
			dualcmdsend(stuff, "This command registers the user and pass specified and automatically adds the hostmask the command is issued from to the account. Note: Can only be issued via PM.")
		elif params[0] == "addhm":
			dualcmdsend(stuff, "Syntax: addhm <user> <pass>")
			dualcmdsend(stuff, "This command adds the hostmask the command is issued from to user's account. Note: Can only be issued via PM.")
		elif params[0] == "delhm":
			dualcmdsend(stuff, "Syntax: delhm <user> <pass>")
			dualcmdsend(stuff, "This command deletes the hostmask the command is issued from user's account. Note: Can only be issued via PM.")
		elif params[0] == "help":
			dualcmdsend(stuff, "Syntax: help <command|game> [command]")
			dualcmdsend(stuff, "This command shows the help for what's issued. If a built-in command is issued, shows help for that. If a game name is issued, shows help for that game. If a game name and a command are issued, shows help for that command in game.")
		elif params[0] == "start":
			dualcmdsend(stuff, "Syntax: start <game>")
			dualcmdsend(stuff, "Starts the joining process for game. Only logged in users may start a game.")
		elif params[0] == "join":
			dualcmdsend(stuff, "Syntax: join")
			dualcmdsend(stuff, "Joins the current game. Only logged in users may join.")
		elif params[0] == "play":
			dualcmdsend(stuff, "Syntax: play")
			dualcmdsend(stuff, "Starts play for the current game. The user that started the game must issue this command.")
		elif params[0] == "stop":
			dualcmdsend(stuff, "Syntax: stop")
			dualcmdsend(stuff, "Stops the current game. The user that started this game must issue this command.")
		elif params[0] == "stats":
			dualcmdsend(stuff, "Syntax: stats <game> [user]")
			dualcmdsend(stuff, "Shows stats for game. If user is specified, shows stats for that user, otherwise, shows stats for the user that issued the command. Must specify user if the person who issued the command is not logged in.")			
		elif admin:
			if params[0] == "quote":
				dualcmdsend(stuff, "Syntax: quote <data>")
				dualcmdsend(stuff, "Sends data to server.")
			elif params[0] == "reload":
				dualcmdsend(stuff, "Syntax: reload <game>")
				dualcmdsend(stuff, "Reloads the specified game. This command can only be issued via PM.")
			elif params[0] == "disconnect":
				dualcmdsend(stuff, "Syntax: [t]disconnect <network> [quitmsg]")
				dualcmdsend(stuff, "Disconnects from network and sends quitmsg. If the command is prefixed with t, it does a 'temporary' disconnect and does not record the disconnect in the config file.")
			elif params[0] == "connect":
				dualcmdsend(stuff, "Syntax: [t]connect <network>")
				dualcmdsend(stuff, "Connects to network. If the command is prefixed with t, performs a 'temporary' connect and does not record the change in teh config file.")
	elif cmd == "stats":
		try:
			game = params[0]
		except:
			dualcmdsend(stuff, "What game do you want stats for?")
			return True
		try:
			user_ = params[1]
		except:
			if user == "":
				dualcmdsend(stuff, "You must specify a user!")
				return True
			user_ = user
		try:
			userdata = userdb[0][user_][1][game]
		except:
			dualcmdsend(stuff, "No stats for that game and user!")
			return True
		try:
			result = games[game].show_stats(userdata)
		except:
			dualcmdsend(stuff, "Stats could not be retrieved!")
			return True
		for x in result.split("\n"):
			dualcmdsend(stuff, x)
	elif admin:
		if cmd == "quote":
			stuff[3].quote(" ".join(params))
		elif cmd == "disconnect" or cmd == "tdisconnect":
			if len(params) < 1:
				dualcmdsend(stuff, "You must specify a network to disconnect from")
				return True
			if params[0] not in networks:
				dualcmdsend(stuff, "I'm not connected to that network")
				return True
			global_config.networks.remove(params[0])
			if cmd == "disconnect":
				t = config_parser.get("config", "networks").split(",")
				try:
					t.remove(params[0])
				except:
					pass
				config_parser.set("config", "networks", ",".join(t))
				config_parser.write(open(config_name, "w"))
			networks[params[0]].running = False
			networks[params[0]].conn._s.send("QUIT :"+" ".join(params[1:])+"\r\n")
			try:
				networks[params[0]].thread.join(5.0)
				if networks[params[0]].thread.isAlive():
					dualcmdsend(stuff, "The network thread did not die in time")
					del networks[params[0]]
					return True
			except:
				del networks[params[0]]
				raise KillYourselfException
			del networks[params[0]]
		elif cmd == "connect" or cmd == "tconnect":
			if len(params) < 1:
				dualcmdsend(stuff, "You must specify a network to connect to")
				return True
			if params[0] in networks:
				dualcmdsend(stuff, "I'm already connected to that network")
				return True
			if not config_parser.has_section(params[0]):
				dualcmdsend(stuff, "That network doesn't exist in my config file")
				return True
			global_config.networks.append(params[0])
			if cmd == "connect":
				t = config_parser.get("config", "networks").split(",")
				if params[0] not in t:
					t.append(params[0])
				config_parser.set("config", "networks", ",".join(t))
				config_parser.write(open(config_name, "w"))
			dualcmdsend(stuff, "Beginning connection process...")
			connect(params[0])
		else:
			return False
	else:
		return False
	return True
	
def network_handler(net):
	channels = {}
	name2chan = {}
	chan2name = {}
	funbotuserinfo = Container()
	funbotuserinfo.username = "FunBot"
	funbotuserinfo.chanlist = []
	usersloggedin = {"FunBot":funbotuserinfo}
	host2nick = {"FunBot":net.nick}
	s = net.s
	irc = net.conn
	state = 0
	if net.serverpass != None:
		irc.quote("PASS "+net.serverpass)
	irc.quote("NICK "+net.nick)
	irc.quote("USER "+net.nick+" something nothing :FunBot 2.0")
	old = ""
	try:
		while net.running:
			try:
				data = old+s.recv(1024)
			except socket.timeout:
				continue
			data = data.replace("\n", "").split("\r")
			old = data[-1]
			for line in data[:-1]:
				if not net.running:
					break
				log("[STATUS] "+line)
				parts = line.split(" ")
				if parts[0] == "PING":
					irc.quote("PONG "+parts[1])
					continue
				if state == 1:
					if parts[0] == servername:
						if parts[1] == "366":
							log("[STATUS] Successfully joined "+parts[3])
							chancfg = Container()
							chancfg.currgame = None
							chancfg.prefix = net.prefix if not config_parser.has_option(chan2name[parts[3]], "prefix") else config_parser.get(chan2name[parts[3]], "prefix")
							chancfg.allowedgames = False if not config_parser.has_option(chan2name[parts[3]], "games") else config_parser.get(chan2name[parts[3]], "games").split(",")
							chancfg.playerlist = []
							chancfg.startplayer = ""
							chancfg.playing = 0
							chancfg.tempplayers = []
							channels[parts[3]] = chancfg
						elif parts[1] == "005":
							for x in parts[3:]:
								if x[:8] == "NETWORK=":
									netname = x[8:]
						continue
					nickend = parts[0].find("!")
					nick = parts[0][1:nickend]
					hostname = parts[0][nickend:]
					if netname+hostname in userdb[1]:
						if hostname not in usersloggedin:
							userinfo = Container()
							userinfo.username = userdb[1][netname+hostname]
							userinfo.chanlist = []
							usersloggedin[hostname] = userinfo
							host2nick[hostname] = nick
							irc.notice(nick, "Hello there! You have been automatically logged in.")
					loggedin = hostname in usersloggedin
					user = ""
					admin = False
					if loggedin:
						user = usersloggedin[hostname].username
						admin = user in global_config.admins
					if parts[1] == "PRIVMSG" and parts[2] == net.nick:
						log("[STATUS] Received PM from "+nick)
						cmd = parts[3][1:].lower()
						if cmd == "register":
							try:
								username = parts[4]
								password = passhash(parts[5])
							except:
								irc.notice(nick, "Error! Not enough parameters! Syntax: register <user> <pass>")
								continue
							if hostname in chan.tempplayers:
								irc.notice(nick, "Error! You cannot register while playing a game!")
								continue
							if username in userdb[0]:
								irc.notice(nick, "Error! A user with this name already exists!")
								continue
							if netname+hostname in userdb[1]:
								irc.notice(nick, "Error! This hostname is already being used with another account! Please register with another hostname")
								continue
							userdblock.acquire()
							userdb[0][username] = [password, {}]
							userdb[1][netname+hostname] = username
							saveuserdb()
							userdblock.release()
							userinfo = Container()
							userinfo.username = username
							userinfo.chanlist = []
							usersloggedin[hostname] = userinfo
							host2nick[hostname] = nick
							irc.notice(nick, "You have been successfully registered and logged in!")
						elif cmd == "addhm":
							try:
								username = parts[4]
								password = passhash(parts[5])
							except:
								irc.notice(nick, "Error! Not enough parameters! Syntax: addhm <user> <pass>")
								continue
							if netname+hostname in userdb[1]:
								irc.notice(nick, "Error! This hostname is already being used with another account!")
								continue
							userdblock.acquire()
							if username not in userdb[0]:
								irc.notice(nick, "Error! Incorrect username or password!")
								userdblock.release()
								continue
							if userdb[0][username][0] != password:
								irc.notice(nick, "Error! Incorrect username or password!")
								userdblock.release()
								continue
							userdb[1][netname+hostname] = username
							saveuserdb()
							userdblock.release()
							irc.notice(nick, "Hostname successfully added!")
						elif cmd == "delhm":
							try:
								username = parts[4]
								password = passhash(parts[5])
							except:
								irc.notice(nick, "Error! Not enough parameters! Syntax: delhm <user> <pass>")
								continue
							if len(usersloggedin[hostname].chanlist) != 0:
								irc.notice(nick, "Because deleting the current hostmask will automatically log you out, you need to finish your games!")
								continue
							userdblock.acquire()
							if username not in userdb[0]:
								irc.notice(nick, "Error! Incorrect username or password!")
								userdblock.release()
								continue
							if userdb[0][username][0] != password:
								irc.notice(nick, "Error! Incorrect username or password!")
								userdblock.release()
								continue
							del userdb[1][netname+hostname]
							saveuserdb()
							userdblock.release()
							del usersloggedin[hostname]
							irc.notice(nick, "Hostname successfully deleted! You have been logged out as well")
						else:
							if handledualcmd(cmd, parts[4:], admin, user, (True, nick, nick, irc)):
								continue
							if not admin:
								continue
							if cmd == "reload":
								try:
									module = games[parts[4]]
								except:
									irc.notice(nick, "No such game or game not specified!")
									continue
								try:
									reload(module)
								except:
									irc.notice(nick, "Game could not be reloaded!")
									handle_exception()
									continue
								irc.notice(nick, "Game successfully reloaded!")
					elif parts[1] == "PRIVMSG" and parts[3][:2] == ":"+channels[parts[2]].prefix:
						cmd = parts[3][2:].lower()
						chan = channels[parts[2]]
						if handledualcmd(cmd, parts[4:], admin, user, (False, parts[2], nick, irc)):
							continue
						if cmd == "start":
							if not loggedin:
								create_temp_user(chan, usersloggedin, nick, hostname, host2nick)
								irc.notice(nick, "A temporary account has been created for you. Information will not be saved.")
							if chan.playing != 0:
								irc.notice(nick, "A game has already been started!")
								continue
							try:
								game = parts[4]
							except:
								irc.notice(nick, "What do you want to play?")
								continue
							if game not in games:
								irc.notice(nick, "That game doesn't exist!")
								continue
							if chan.allowedgames != False:
								if game not in chan.allowedgames:
									irc.notice(nick, "You can't play that game in this channel!")
									continue
							gameirc = GameIrc(irc, game, parts[2], False, chan.prefix, host2nick, netname, chan.tempplayers)
							try:
								options = parts[5:]
							except:
								options = []
							try:
								chan.currgame = games[game].start(gameirc, options)
							except:
								handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
								continue
							chan.startplayer = hostname
							chan.playerlist.append(hostname)
							usersloggedin[hostname].chanlist.append(parts[2])
							try:
								chan.currgame.join(hostname)
							except:
								handle_plugin_error(irc, chan, parts[2], usersloggedin, hostwnick)
								continue
							chan.playing = 1
							irc.privmsg(parts[2], "Game is opening! Type "+chan.prefix+"join to join!")
						elif cmd == "join":
							if not loggedin:
								create_temp_user(chan, usersloggedin, nick, hostname, host2nick)
								irc.notice(nick, "A temporary account has been created for you. Information will not be saved.")
							if chan.playing == 0:
								irc.notice(nick, "Start a game first!")
								continue
							if chan.playing == 2:
								irc.notice(nick, "A game is already being played!")
								continue
							if hostname in chan.playerlist:
								irc.notice(nick, "You have already joined!")
								continue
							chan.playerlist.append(hostname)
							usersloggedin[hostname].chanlist.append(parts[2])
							try:
								chan.currgame.join(hostname)
							except:
								handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
								continue
							irc.privmsg(parts[2], nick+" has joined the game!")
						elif cmd == "play":
							if chan.playing == 0:
								irc.notice(nick, "Start a game first!")
								continue
							if chan.playing == 2:
								irc.notice(nick, "The game is already being played!")
								continue
							if chan.startplayer != hostname:
								irc.notice(nick, "You didn't start this game!")
								continue
							try:
								result = chan.currgame.canstart()
							except:
								handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
								continue
							if result == 0:
								pass
							elif result == 1:
								chan.playerlist.append("FunBot")
								usersloggedin["FunBot"].chanlist.append(parts[2])
								try:
									chan.currgame.join("FunBot")
								except:
									handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
									continue
								irc.privmsg(parts[2], host2nick["FunBot"]+" has joined the game!")
							else:
								try:
									irc.notice(nick, result)
								except:
									handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
								continue
							irc.privmsg(parts[2], "Players: "+", ".join([host2nick[hn] for hn in chan.playerlist]))
							irc.privmsg(parts[2], "The game has been started!")
							chan.playing = 2
							try:
								result = chan.currgame.start()
							except:
								handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
								continue
						elif cmd == "stop":
							if chan.playing == 0:
								irc.notice(nick, "There is no game to stop!")
								continue
							if chan.startplayer != hostname and admin == False:
								irc.notice(nick, "You didn't start this game!")
								continue
							try:
								chan.currgame.stop()
							except:
								handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
								continue
							cleanupgame(chan, usersloggedin, parts[2], host2nick)
							irc.privmsg(parts[2], "The game has been stopped!")
						elif chan.playing != 0:
							if not loggedin:
								create_temp_user(chan, usersloggedin, nick, hostname, host2nick)
								irc.notice(nick, "A temporary account has been created for you. Information will not be saved.")
							try:
								result = chan.currgame.handlecmd(cmd.lower(), parts[4:], hostname in chan.playerlist, hostname, host2nick[hostname])
							except:
								handle_plugin_error(irc, chan, parts[2], usersloggedin, host2nick)
								continue
							if result == True:
								irc.privmsg(parts[2], "The game has finished!")
								cleanupgame(chan, usersloggedin, parts[2], host2nick)
								saveuserdb()
				elif state == 0:
					if parts[1] == "001":
						state = 1
						servername = parts[0]
						for x in net.channels:
							log("[STATUS] Joining "+x)
							if not config_parser.has_section(x):
								log("[WARNING] No such section, not joining")
								continue
							try:
								chan = config_parser.get(x, "channel")
								kw = "" if not config_parser.has_option(x, "keyword") else " "+config_parser.get(x, "keyword")
							except:
								log("[WARNING] Improper section format, not joining")
								continue
							name2chan[x] = chan
							chan2name[chan] = x
							irc.quote("JOIN "+chan+kw)
	except KillYourselfException:
		log("[STATUS] Killing myself")
	except:
		handle_exception()
	log("[STATUS] Network thread "+irc._name+" shutting down")
	irc._running = False
	
networks = {}

print "[STATUS] Reading config file..."
global_config = Container()

#open the config file
try:
	config_parser = ConfigParser.ConfigParser() #create a new parser
	config_parser.readfp(open(config_name)) #and load the config file
except:
	print "[ERROR] Config file could not be loaded!"
	raise
	sys.exit(1) #quit if something went wrong
	
if not config_parser.has_section("config"): #fail if there isn't proper config data
	print "[ERROR] No config section!"
	raise
	sys.exit(1)

#now start parsing the config file
try:
	global_config.networks = config_parser.get("config", "networks").split(",")
	global_config.admins = config_parser.get("config", "admins").split(",")
	global_config.games = config_parser.get("config", "games").split(",")
	global_config.prefix = config_parser.get("config", "prefix")
except:
	print "[ERROR] Invalid config section!"
	raise
	sys.exit(1)
	
if not config_parser.has_option("config", "logfile"):
	print "[WARNING] Log file param not found!"
	logfile = None
else:
	try:
		logfile = open(config_parser.get("config", "logfile"), "a")
	except:
		print "[WARNING] Log file could not be opened!"
		logfile = None
		
if not config_parser.has_option("config", "userfile"):
	log("[ERROR] No userfile specified!")
	sys.exit(1)
		
log("[STATUS] Loading user database...")
try:
	userdb = pickle.load(open(config_parser.get("config", "userfile")))
except:
	log("[WARNING] User database could not be loaded, creating a new one")
	userdb = [{"FunBot":[None,{}]}, {"FunBot":"FunBot"}]
	try:
		pickle.dump(userdb, open(config_parser.get("config", "userfile"), "w"))
		saveuserdb()
	except:
		log("[ERROR] New user database could not be created!")
		sys.exit(1)
		
userdblock = threading.Lock()

global_config.userfile = config_parser.get("config", "userfile")

games = {}

log("[STATUS] Loading game modules...")

gamelist = [] if not config_parser.has_option("config", "games") else config_parser.get("config", "games").split(",")

for game in gamelist:
	log("[STATUS] Loading "+game)
	try:
		__import__("games."+game)
	except:
		log("[WARNING] Could not load game")
		handle_exception()
		continue
	m = sys.modules["games."+game]
	try:
		games[m.__gamename__] = m
	except:
		log("[WARNING] Game has no __gamename__ attribute, not loading")
	
log("[STATUS] FunBot successfully started up")

for network in global_config.networks:
	if connect(network) != True:
		pass
	
try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	log("[STATUS] Quitting")
	userdblock.acquire()
	saveuserdb()
	userdblock.release()
	l = logfile
	logfile = None
	l.close()
	os._exit(1)