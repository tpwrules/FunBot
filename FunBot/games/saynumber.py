__gamename__ = "saynumber"
__helptext__ = "Say your number!"
__players__ = 1

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
		self.irc.send(self.irc.getnick(self.userlist[self.curruser]) + ", state your number using !number")
	def handlecmd(self, cmd, args, user, nick):
		if cmd == "number":
			if user != self.userlist[self.curruser]:
				self.irc.notice(nick, "It's not your turn!")
				return
			try:
				num = int(args[0])
			except ValueError:
				self.irc.send("Guess what? " + args[0] + " is not a number!")
				return
			except:
				self.irc.send("What's your number?")
				return
			self.userdata[self.curruser][0] += 1
			self.userdata[self.curruser][1] += num
			if num > self.biggestnumber:
				self.biggestnumber = num
			self.curruser += 1
			if self.curruser == len(self.userlist):
				self.irc.send("The game has ended! The biggest number said was " + str(self.biggestnumber))
				for x in xrange(len(self.userlist)):
					self.irc.setuserdata(self.userlist[x], self.userdata[x])
				return True
			self.doturn()
	
def start(irc, options):
	global x
	x = Saynumber(irc, options)
	return x
	
def disp_stats(irc, userdata):
	irc.send("Total numbers said: "+str(userdata[0])+" Total of numbers: "+str(userdata[1]))