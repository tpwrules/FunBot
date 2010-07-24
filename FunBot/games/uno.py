__gamename__ = "uno"

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

#'a\x02<--bold \x1f<--underline \x16<--reverse \x0f<-- reset \x0314 <-- color'

#CARD VALUES
#0-9: 0-9
#10: draw 2
#11: reverse
#12: skip
#13: wild
#14: wdf

colors = [4,9,12,8]

import random

class Uno:
	def __init__(self, irc, options):
		self.irc = irc
		self.started = False
		self.players = []
		self.currplayer = 0
		self.direction = 1
		self.discard = []
		self.topcard = None
		self.drew = False
		tdeck = []
		for x in xrange(1, 13):
			tdeck.append(x)
			tdeck.append(x)
		tdeck.append(0)
		self.deck = []
		for x in tdeck:
			for y in xrange(4):
				self.deck.append([x, y])
		for x in xrange(4):
			self.deck.append([13, -1])
			self.deck.append([14, -1])
		random.shuffle(self.deck)
	def join(self, hostname):
		hand = []
		for x in xrange(7):
			hand.append(self.popcard())
		if hostname != "FunBot":
			self.irc.notice(self.irc.getnick(hostname), "Your cards: "+" ".join([self.getcardtext(card) for card in hand]))
		if self.irc.getuserdata(hostname) == None:
			self.irc.setuserdata(hostname, [0, 0])
		self.players.append([hostname, hand])
	def getcardtext(self, card_):
		text = ""
		card = card_[0]
		color = card_[1]
		if card < 10:
			text = str(card)
		elif card == 10:
			text = "DT"
		elif card == 11:
			text = "R"
		elif card == 12:
			text = "S"
		elif card == 13 or card == 14 and color != -1:
			if color == 0:
				text = "RED"
			elif color == 1:
				text = "GREEN"
			elif color == 2:
				text = "BLUE"
			elif color == 3:
				text = "YELLOW"
		text = " "+text+" "
		if color != -1:
			text = "\x03"+str(colors[color])+",1"+text
		else:
			if card == 13:
				text = "\x038,1W\x0312,1I\x034,1L\x039,1D"
			elif card == 14:
				text = "\x038,1W\x0312,1D\x034,1F"
		text = "\x0300["+text+"\x0F\x0300]\x0F"
		return text
	def popcard(self):
		card = self.deck.pop()
		if len(self.deck) == 0:
			self.deck = self.discard[:]
			self.discard = []
			random.shuffle(self.deck)
		return card
	def canstart(self):
		if len(self.players) == 1:
			return 1
		return 0
	def start(self):
		self.started = True
		self.topcard = self.popcard()
		self.runturn(True)
	def stop(self):
		pass
	def handleactioncard(self):
		card = self.topcard[0]
		player = self.irc.getnick(self.players[self.currplayer][0])
		if card == 10:
			self.irc.send(player + " draws TWO cards and is \x034\x02SKIPPED!")
			for x in xrange(2):
				self.players[self.currplayer][1].append(self.popcard())
		elif card == 11:
			self.direction *= -1
			if self.direction == 1:
				self.irc.send("REVERSE -->")
			else:
				self.irc.send("<-- REVERSE")
		elif card == 12:
			self.irc.send(player + " is \x034\x02SKIPPED!")
		elif card == 14:
			self.irc.send(player + " draws \x02FOUR\x02 cards and is \x034\x02SKIPPED!")
			for x in xrange(4):
				self.players[self.currplayer][1].append(self.popcard())
		else:
			return
		self.currplayer = (self.currplayer+self.direction)%len(self.players)
	def canbeplayed(self, card):
		topcard = self.topcard
		if topcard[0] == card[0]:
			return True
		if topcard[1] == card[1]:
			return True
		if card[0] > 12:
			return True
		if topcard[1] == -1:
			return True
		return False
	def runturn(self, firstturn=False):
		player = self.players[self.currplayer]
		nick = self.irc.getnick(player[0])
		self.irc.send(nick + " is up")
		self.irc.send("Top card: "+self.getcardtext(self.topcard))
		if player[0] != "FunBot":
			self.irc.notice(nick, " ".join([self.getcardtext(card) for card in player[1]]))
		if self.topcard[0] > 9 and firstturn == True:
			self.handleactioncard()
			self.runturn()
		if player[0] == "FunBot":
			return self.handleai()
		self.drew = False
	def handleai(self):
		me = self.players[self.currplayer]
		nick = self.irc.getnick("FunBot")
		prefix = self.irc.getprefix()
		playablecards = map(self.appendpoints, filter(self.canbeplayed, me[1]))
		if len(playablecards) == 0:
			if self.drew == True:
				self.irc.send(prefix+"skip")
				return self.handlecmd("s", [], True, "FunBot", nick)
			else:
				self.irc.send(prefix+"draw")
				return self.handlecmd("d", [], True, "FunBot", nick)
		playablecards.sort()
		playablecards.reverse()
		preferredcards = []
		for x in playablecards:
			if x[0] == 50:
				continue
			preferredcards.append(x)
		if len(preferredcards) == 0:
			pointvals = [[0,"red"],[0,"green"],[0,"blue"],[0,"yellow"]]
			for x in me[1]:
				if x[1] == -1:
					continue
				pointvals[x[1]][0] += self.appendpoints(x)[0]
			pointvals.sort()
			pointvals.reverse()
			if playablecards[0][1] == 13:
				self.irc.send(prefix+"play wild "+pointvals[0][1])
				return self.handlecmd("p", ["wild", pointvals[0][1]], True, "FunBot", nick)
			else:
				#print "playing wdf"
				self.irc.send(prefix+"play wdf "+pointvals[0][1])
				return self.handlecmd("p", ["wdf", pointvals[0][1]], True, "FunBot", nick)
		preferredcards2 = []
		for x in preferredcards:
			if x[2] != self.topcard[1]:
				continue
			preferredcards2.append(x)
		if len(preferredcards2) == 0:
			preferredcards2 = preferredcards
		card_ = preferredcards2[0]
		color = ["red", "green", "blue", "yellow"][card_[2]]
		if card_[0] < 10:
			card = str(card_[0])
		else:
			card = ["drawtwo", "reverse", "skip"][card_[1]-10]
		#print "card", card
		self.irc.send(prefix+"play "+color+" "+card)
		return self.handlecmd("p", [color, card], True, "FunBot", nick)
	def appendpoints(self, card):
		if card[0] < 10:
			return [card[0], card[0], card[1]]
		elif card[0] > 9 and card[0] < 13:
			return [20, card[0], card[1]]
		else:
			return [50, card[0], card[1]]
	def getcolor(self, t):
		if t == "r" or t == "red":
			return 0
		elif t == "g" or t == "green":
			return 1
		elif t == "b" or t == "blue":
			return 2
		elif t == "y" or t == "yellow":
			return 3
		return -1
	def getcard(self, t):
		try:
			x = int(t)
			if x < 0 or x > 9:
				raise Exception
			return x
		except:
			pass
		if t == "d2" or t == "dt" or t == "drawtwo":
			return 10
		elif t == "r" or t == "reverse":
			return 11
		elif t == "s" or t == "skip":
			return 12
		return -1
	def handlewin(self, hostname):
		nick = self.irc.getnick(hostname)
		self.irc.send(nick+" wins!!")
		points = 0
		for player in self.players:
			if player[0] == hostname:
				continue
			self.irc.send(self.irc.getnick(player[0])+"'s cards: "+" ".join([self.getcardtext(c) for c in player[1]]))
			pointvals = sum([self.appendpoints(c)[0] for c in player[1]])
			userdata = self.irc.getuserdata(player[0])
			self.irc.setuserdata(player[0], [userdata[0]-pointvals, userdata[1]+1])
			points += pointvals
		userdata = self.irc.getuserdata(hostname)
		self.irc.setuserdata(hostname, [userdata[0]+points, userdata[1]+1])
		self.irc.send(nick+" gets "+str(points)+" points!")
	def handlecmd(self, cmd, args, playing, hostname, nick):
		cmd = cmd.lower()
		if not self.started:
			return
		if cmd == "count":
			self.irc.send("Number of cards: "+", ".join([self.irc.getnick(p[0])+" has "+str(len(p[1])) for p in self.players]))
			return
		if not playing:
			return
		if self.players[self.currplayer][0] != hostname:
			self.irc.notice(nick, "It's not your turn!")
			return
		if cmd == "p" or cmd == "put":
			player = self.players[self.currplayer]
			if len(args) < 2:
				self.irc.notice(nick, "Invalid play!")
				return
			t = args[0].lower()
			color = self.getcolor(t)
			card = -1
			wcolor = -1
			if color == -1:
				if t == "w" or t == "wild":
					card = 13
					wcolor = self.getcolor(args[1].lower())
				elif t == "wdf" or t == "wd4":
					card = 14
					wcolor = self.getcolor(args[1].lower())
				else:
					self.irc.notice(nick, "Invalid play!")
					return
			if card == -1:
				card = self.getcard(args[1].lower())
				if card == -1:
					self.irc.notice(nick, "Invalid play!")
					return
			if self.canbeplayed([card, color]) == False:
				self.irc.notice(nick, "Invalid play!")
				return
			try:
				x = player[1].index([card, color])
			except:
				self.irc.notice(nick, "Invalid play!")
				return
			player[1].remove([card, color])
			if wcolor != -1:
				self.topcard = [card, wcolor]
			else:
				self.topcard = [card, color]
			self.drew = False
			self.irc.send(nick+" plays a "+self.getcardtext([card, color]))
			if len(player[1]) < 2:
				if len(player[1]) == 1:
					self.irc.send("\x02"+nick+" has UNO!!")
				else:
					self.handlewin(hostname)
					return True
			self.currplayer = (self.currplayer+self.direction)%len(self.players)
			self.handleactioncard()
			return self.runturn()
		elif cmd == "d" or cmd == "draw":
			if self.drew == True:
				self.irc.notice(nick, "You already drew a card!")
				return
			self.drew = True
			card = self.popcard()
			if hostname != "FunBot":
				self.irc.notice(nick, "You drew: "+self.getcardtext(card))
			self.irc.send(nick+" drew a card")
			self.players[self.currplayer][1].append(card)
			if hostname == "FunBot":
				return self.handleai()
		elif cmd == "s" or cmd == "skip":
			if self.drew == False:
				self.irc.notice(nick, "Draw a card first!")
				return
			self.drew = False
			self.currplayer = (self.currplayer+self.direction)%len(self.players)
			return self.runturn()
		elif cmd == "c" or cmd == "cards":
			self.irc.send("Top card: "+self.getcardtext(self.topcard))
			self.irc.notice(nick, " ".join([self.getcardtext(card) for card in self.players[self.currplayer][1]]))

def start(irc, options):
	return Uno(irc, options)
	
def show_stats(userdata):
	return "Total points: "+str(userdata[0])+", Number of games played: "+str(userdata[1])
	
def show_help(cmd):
	if cmd == None:
		return "This is everybody's favorite card game, Uno!\nCommands: count, put, draw, skip, cards\nOther topics: colornames, cardnames, rules, shortforms"
	if cmd == "count":
		return "Syntax: count\nShows how many cards each player has."
	if cmd == "put":
		return "Syntax: <put|p> <color> <card>\nPlays the card that has the color color. If you want to play a wild or wild draw four, the color is wild or wdf and card is the color you want it to change to."
	if cmd == "draw":
		return "Syntax: <draw|d>\nDraws a card from the deck. Once you draw a card, you must skip or play the card."
	if cmd == "skip":
		return "Syntax: <skip|s>\nSkips your turn. You must draw a card before you can skip."
	if cmd == "cards":
		return "Syntax: <cards|c>\nShows the top card and shows you your cards."
	if cmd == "colornames":
		return "Colors: red or r, green or g, blue or b, yellow or y"
	if cmd == "cardnames":
		return "Cards: 0 through 9, reverse or r, skip or s, drawtwo or dt or d2, wild or w, wdf or wd4"
	if cmd == "shortforms":
		return "Short forms: Most commands and cards have a short form that is shorter and easier to type. See the respective help topics for them for the short forms."
	if cmd == "rules":
		return "Rules of UNO: Uno is a card game where the goal is to get rid of all your cards.\nPlaying cards: You can play a card if it matches the color or number of the top card. Wild and wild draw four cards can be played on anything and change the color of the top card\nAction cards: Action cards are cards that affect something in the game. Reverse: Reverses the direction of play. Skip: Skips the next player's turn. Draw two: Makes the next player draw two cards and skips their turn. Wild: Changes the color of the deck. Wild draw four: Same as wild, but makes the next player draw four cards and skips their turn\nIf you have no cards to play, you can draw a card. You must play the card you drew or skip your turn."
	