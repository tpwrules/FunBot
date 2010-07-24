__gamename__ = "blackjack"

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

import random

class Blackjack:
	def __init__(self, irc, options):
		self.irc = irc
		self.players = []
		self.started = False
		self.currplayer = 0
		self.deck = [1,2,3,4,5,6,7,8,9,10,11,12,13]*4
		random.shuffle(self.deck)
	def join(self, hostname):
		self.players.append([hostname, []])
		if self.irc.getuserdata(hostname) == None:
			self.irc.setuserdata(hostname, [0])
	def start(self):
		if len(self.players) == 1:
			self.started = True
			return 1
		elif len(self.players) == 0:
			return "You need at least one player!"
		self.started = True
		return 0
	def stop(self):
		pass
	def handlecmd(self, cmd, params, playing, hostname, nick):
		self.irc.send("yaaay! Hi "+nick+"! You are playing: "+str(playing))
		
def start(irc, options):
	return Blackjack(irc, options)
	
def show_stats(stats):
	return "Number of games played: "+str(stats[0])
	
def show_help(cmd):
	return False