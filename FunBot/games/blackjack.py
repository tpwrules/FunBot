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
		self.prefix = irc.getprefix()
		self.players = []
		self.started = False
		self.currplayer = 0
		self.deck = [1,2,3,4,5,6,7,8,9,10,11,12,13]*4
		random.shuffle(self.deck)
	def join(self, hostname):
		self.players.append([0, hostname])
		if self.irc.getuserdata(hostname) == None:
			self.irc.setuserdata(hostname, [0])
	def canstart(self):
		if len(self.players) == 1:
			return 1
		return 0
	def start(self):
		self.started = True
		for x in self.players:
			t = self.deck.pop()
			t += self.deck.pop()
			if x[1] != "FunBot":
				self.irc.notice(self.irc.getnick(x[1]), "Your total: "+str(t))
			x[0] = t
		self.askplayer()
	def stop(self):
		pass
	def askplayer(self):
		player = self.players[self.currplayer]
		nick = self.irc.getnick(player[1])
		if player[1] == "FunBot":
			return self.handleai()
		else:
			self.irc.send(nick+": "+self.prefix+"hit or "+self.prefix+"stay ?")
	def handleai(self):
		total = self.players[self.currplayer][0]
		while total < 18:
			self.irc.send("I will hit.")
			total += self.deck.pop()
			if total > 21:
				self.irc.send("I have busted.")
				break
		if total < 22:
			self.irc.send("I will stay.")
		self.players[self.currplayer][0] = total
		self.currplayer += 1
		if self.currplayer == len(self.players):
			self.handlewin()
			return True
	def handlewin(self):
		players = []
		for x in self.players[:]:
			if x[0] < 22:
				players.append(x)
		players.sort()
		self.irc.send(self.irc.getnick(players[0][1])+" has won with "+str(players[0][0])+" cards!")
		for x in self.players:
			userdata = self.irc.getuserdata(x[1])
			self.irc.setuserdata(x[1], [userdata[0]+1])
		return True
	def handlecmd(self, cmd, params, playing, hostname, nick):
		if self.started == False or playing == False:
			return
		if self.players[self.currplayer][1] != hostname:
			self.irc.notice(nick, "It's not your turn!")
			return
		if cmd == "hit":
			self.players[self.currplayer][0] += self.deck.pop()
			self.irc.notice(nick, "Your total: "+str(self.players[self.currplayer][0]))
			if self.players[self.currplayer][0] > 21:
				self.irc.send(nick+": You have busted!")
				self.currplayer += 1
				if self.currplayer == len(self.players):
					return self.handlewin()
			return self.askplayer()
		elif cmd == "stay":
			self.currplayer += 1
			if self.currplayer == len(self.players):
				return self.handlewin()
			return self.askplayer()
		
def start(irc, options):
	return Blackjack(irc, options)
	
def show_stats(stats):
	return "Number of games played: "+str(stats[0])
	
def show_help(cmd):
	if cmd == None:
		return "This is a standard blackjack game, where the goal is to get to 21 without going over.\nCommands: hit, stay"
	if cmd == "hit":
		return "Syntax: hit\nThis command will make you draw a card from the deck when it's your turn."
	if cmd == "stay":
		return "Syntax: stay\nThis command will go to the next player."