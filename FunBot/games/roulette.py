__gamename__ = "roulette"
__helptext__ = "Spin! You'll need two players or more!"
__players__ = 2

import random

class Saynumber:
	def __init__(self, irc, options):
		self.irc = irc
		self.userlist = []
		self.userdata = []
		self.biggestnumber = 0
		self.curruser = 0
	def join(self, user):
		self.userlist.append(user)
		userdata = self.irc.getuserdata(user)
		if userdata == None:
			userdata = [0, 0]
		self.userdata.append(userdata)
	def start(self):
		self.doturn()
	def stop(self):
		pass
	def doturn(self):
		self.irc.send(self.irc.getnick(self.userlist[self.curruser]) + ", !spin the revolver!")
	def handlecmd(self, cmd, args, user, nick):
		if cmd == "spin":
			if user != self.userlist[self.curruser]:
				self.irc.notice(nick, "It's not your turn!")
				return
			rand = random.randint(1,6)
			if rand == 1:
				self.irc.quote("KICK " + self.irc._dest + " " + nick + " :BANG!");
				self.userlist.remove(user)
				self.userdata.remove(self.userdata[self.curruser])
			else:
				self.irc.send("*CLICK*")
				self.userdata[self.curruser][0] += 1
				for x in xrange(len(self.userlist)):
					self.irc.setuserdata(self.userlist[x], self.userdata[x])
				self.curruser += 1
			if self.curruser == len(self.userlist):
				self.curruser = 0
			if 1 == len(self.userlist):
				self.irc.send("The game has ended! The survivor was " + str(self.userlist[0]))
				self.userdata[0][1] += 1
				self.irc.setuserdata(self.userlist[0], self.userdata[0])
				return True
			self.doturn()
	
def start(irc, options):
	global x
	x = Saynumber(irc, options)
	return x
	
def disp_stats(irc, userdata):
	irc.send("Total rounds survived: "+str(userdata[0])+" Total games survived: "+str(userdata[1]))