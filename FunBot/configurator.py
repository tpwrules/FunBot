import ConfigParser
import pickle
import os
import glob
import sys
import hashlib

def get_param(param, default=""):
	v = raw_input(param+" ["+default+"]: ")
	if v == "":
		return default
	return v

if not (os.path.exists("FunBot.py") and os.path.exists("games")):
	print "Please run me from the directory with the FunBot.py file and games directory."
	exit()
	
print "Welcome to the FunBot configurator. I will guide you through steps to generate a FunBot.ini configuration file and user database."
print "Prompts will be displayed like this: parameter [defaultvalue]:.\nIf you do not enter anything and press enter, the default value will be used."
print "Scanning games directory..."

if not os.path.exists("games/__init__.py"):
	print "The games directory doesn't appear to have an __init__.py file."
	exit()
	
found_games = []

for file in glob.iglob("games/[a-zA-Z0-9]*.py"):
	try:
		__import__("games."+file[6:-3])
	except:
		continue
	m = sys.modules["games."+file[6:-3]]
	try:
		gamename = m.__gamename__
	except:
		continue
	try:
		help = m.show_help(None)
	except:
		help = None
	print "Found", gamename, "["+file[6:]+"]"
	if help != None:
		print "Help:", help
	print
	found_games.append((file[6:], gamename))
	
cfg = ConfigParser.ConfigParser()
cfg.add_section("config")

print "OK, let's start!"
print
userfilename = get_param("User database file name", "users.pickle")
cfg.set("config", "userfile", userfilename)
if get_param("Specify a log file? (Y/N)", "Y").upper() == "Y":
	cfg.set("config", "logfile", get_param("Log file name", "FunBot.log"))
global_prefix = get_param("Global prefix", "!")
cfg.set("config", "prefix", global_prefix)
print
print "Which games would you like to add to your FunBot?"
add_games = []
for game in found_games:
	if get_param("Add "+game[1]+" ["+game[0]+"]? (Y/N)", "Y").upper() == "Y":
		add_games.append(game)
		
cfg.set("config", "games", ",".join([game[0][:-3] for game in add_games]))
print
print "Now, we need to add networks. If you don't specify any network name or server, I will stop asking you for networks."

while True:
	net_name = get_param("Network section name")
	if net_name == "":
		break
	net_server = get_param("Network server")
	if net_server == "":
		break
	port = get_param("Port", "6667")
	password = get_param("Connection password", "")
	nick = get_param("Nick", "FunBot")
	network_prefix = get_param("Network prefix", global_prefix)
	if network_prefix == global_prefix:
		network_prefix = ""
	msgwait = get_param("Message delay", "50")
	print
	print "Let's add channels to your network. Again, if you don't specify any channel name or channel, I will stop asking you for channels."
	channels = []
	while True:
		channel_name = get_param("Channel section name")
		if channel_name == "":
			break
		channel = get_param("Channel")
		if channel == "":
			break
		key = get_param("Channel keyword")
		chan_prefix = get_param("Channel prefix", global_prefix if network_prefix == "" else network_prefix)
		if chan_prefix == global_prefix if network_prefix == "" else network_prefix:
			chan_prefix = ""
		channels.append((channel_name, channel, key, chan_prefix))
		print
	print "We're done with", net_name, "now!"
	print
	for channel in channels:
		cfg.add_section(channel[0])
		cfg.set(channel[0], "channel", channel[1])
		if channel[2] != "":
			cfg.set(channel[0], "key", channel[2])
		if channel[3] != "":
			cfg.set(channel[0], "prefix", channel[3])
	cfg.add_section(net_name)
	cfg.set(net_name, "server", net_server)
	if port != "6667":
		cfg.set(net_name, "port", port)
	if password != "":
		cfg.set(net_name, "pass", password)
	cfg.set(net_name, "nick", nick)
	if network_prefix != "":
		cfg.set(net_name, "prefix", network_prefix)
	cfg.set(net_name, "channels", ",".join([channel[0] for channel in channels]))
	if msgwait != "50":
		cfg.set(net_name, "msgwait", msgwait)

print
print "Now, I need an admin username and password."
while True:
	username = get_param("Admin username")
	if username != "":
		break
	print "No, really, I need a username."
while True:
	password = get_param("Admin password")
	if password != "":
		break
	print "Seriously, I need a password for the admin account."
	
cfg.set("config", "admins", username)

print
print "Saving configuration file..."
while True:
	try:
		f = open("FunBot.ini", "w")
	except:
		print "FunBot.ini could not be opened."
		v = get_param("Try again? (Y/N)", "Y").upper()
		if v == "Y":
			continue
		print "OK then. Here's what the configuration file should look like:"
		cfg.write(stdout)
		break
	cfg.write(f)
	f.close()
	break

print "Creating the user database..."
d = [{"FunBot":[None,{}], username:[hashlib.sha1(password).hexdigest(),{}]}, {"FunBot":"FunBot"}]
pickle.dump(d, open(userfilename, "w"))

print
print "We're all done! You can now run FunBot. NOTE: Once FunBot starts up, you will need to add your hostmask to the admin account."