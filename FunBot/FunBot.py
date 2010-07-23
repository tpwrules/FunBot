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

class Container: #a boring class intended for storing whatever we need
	pass

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
		self._running = True
		self._queue = []
		self._st = sleeptime/100.0
		self._thread.start()
	def quote(self, data):
		self._lock.acquire()
		self._queue.insert(0, data+"\r\n")
		self._lock.release()
	def _handlequeue(self):
		while self._running:
			time.sleep(self._st)
			self._lock.acquire()
			if len(self._queue) == 0:
				self._lock.release()
				continue
			self._s.send(self._queue.pop())
			self._lock.release()
	
def network_handler(net):
	s = net.s
	irc = net.conn
	state = 0
	if net.serverpass != None:
		irc.quote("PASS "+net.serverpass)
	irc.quote("NICK "+net.nick)
	irc.quote("USER "+net.nick+" something nothing :FunBot 2.0")
	old = ""
	try:
		while True:
			data = old+s.recv(1024)
			data = data.replace("\n", "").split("\r")
			old = data[-1]
			for line in data[:-1]:
				log("[STATUS] "+line)
				parts = line.split(" ")
				if parts[0] == "PING":
					irc.quote("PONG "+parts[1])
	except:
		pass
	
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
	userdb = {"FunBot":[None,{}]}
	try:
		pickle.dump({"FunBot":[None,{}]}, open(config_parser.get("config", "userfile"), "w"))
	except:
		log("[ERROR] New user database could not be created!")
		sys.exit(1)

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
		continue
	m = sys.modules["games."+game]
	try:
		games[m.__gamename__] = m
	except:
		log("[WARNING] Game has no __gamename__ attribute, not loading")
	
log("[STATUS] FunBot successfully started up")

for network in global_config.networks:
	log("[STATUS] Parsing "+network)
	if not config_parser.has_section(network):
		log("[WARNING] No such network section, not connecting")
		continue
	networks[network] = Container()
	n = networks[network]
	n.prefix = global_config.prefix if not config_parser.has_option(network, "prefix") else config_parser.get(network, "prefix")
	if not config_parser.has_option(network, "nick"):
		log("[WARNING] No nick specified, not connecting")
		continue
	n.nick = config_parser.get(network, "nick")
	if not config_parser.has_option(network, "server"):
		log("[WARNING] No server specified, not connecting")
		continue
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
		continue
	n.conn = NetworkConnection(n.s, network, msgwait)
	log("[STATUS] Spawning network thread")
	n.thread = threading.Thread(target=network_handler, args=(n,))
	n.thread.start()
	
try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	log("[STATUS] Quitting")
	os._exit(1)