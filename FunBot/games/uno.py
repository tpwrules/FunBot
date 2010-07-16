__gamename__ = "uno"
__helptext__ = "The classic Uno game!"
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
		self.players = []
		self.currplayer = 0
		self.direction = 1
		self.discard = []
		self.topcard = None
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
	def join(self, user):
		hand = []
		for x in xrange(7):
			hand.append(self.popcard())
		if user != "FunBot":
			self.irc.notice(self.irc.getnick(user), "Your cards: "+" ".join([self.getcardtext(card) for card in hand]))
			if self.irc.getuserdata(user) == None:
				self.irc.setuserdata(user, [0, 0])
		self.players.append([user, hand])
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
	def start(self):
		if len(self.players) == 1:
			self.irc.send("FunBot has joined the game!")
			self.join("FunBot")
		self.topcard = self.popcard()
		self.runturn(True)
	def stop(self):
		pass
	def handleactioncard(self):
		card = self.topcard[0]
		player = self.players[self.currplayer][0]
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
		self.irc.send(player[0] + " is up")
		self.irc.send("Top card: "+self.getcardtext(self.topcard))
		if player[0] != "FunBot":
			self.irc.notice(self.irc.getnick(player[0]), " ".join([self.getcardtext(card) for card in player[1]]))
		if self.topcard[0] > 9 and firstturn == True:
			self.handleactioncard()
			self.runturn()
		if player[0] == "FunBot":
			return self.handleai()
		self.drew = False
	def handleai(self):
		#print "Entering handleai"
		me = self.players[self.currplayer]
		#print me
		playablecards = map(self.appendpoints, filter(self.canbeplayed, me[1]))
		#print "Playable cards:", playablecards
		if len(playablecards) == 0:
			#print "No playable cards!"
			if self.drew == True:
				#print "skipping"
				self.irc.send(".skip")
				return self.handlecmd("s", [], "FunBot", "tpw_rules")
			else:
				#print "drawing"
				self.irc.send(".draw")
				return self.handlecmd("d", [], "FunBot", "tpw_rules")
		playablecards.sort()
		playablecards.reverse()
		#print "sorted playable cards:", playablecards
		preferredcards = []
		for x in playablecards:
			if x[0] == 50:
				continue
			preferredcards.append(x)
		#print "preferred cards", preferredcards
		if len(preferredcards) == 0:
			#print "no preferred cards, using wilds"
			pointvals = [[0,"red"],[0,"green"],[0,"blue"],[0,"yellow"]]
			#print "calculating points"
			for x in me[1]:
				if x[1] == -1:
					continue
				pointvals[x[1]][0] += self.appendpoints(x)[0]
			pointvals.sort()
			pointvals.reverse()
			#print "points:", pointvals
			if playablecards[0][1] == 13:
				#print "playing wild"
				self.irc.send(".play wild "+pointvals[0][1])
				return self.handlecmd("p", ["wild", pointvals[0][1]], "FunBot", "tpw_rules")
			else:
				#print "playing wdf"
				self.irc.send(".play wdf "+pointvals[0][1])
				return self.handlecmd("p", ["wdf", pointvals[0][1]], "FunBot", "tpw_rules")
		preferredcards2 = []
		for x in preferredcards:
			if x[2] != self.topcard[1]:
				continue
			preferredcards2.append(x)
		#print "preferred cards 2", preferredcards2
		if len(preferredcards2) == 0:
			#print "preferred cards 2 empty"
			preferredcards2 = preferredcards
		card_ = preferredcards2[0]
		#print "gonna play", card_
		color = ["red", "green", "blue", "yellow"][card_[2]]
		#print "color", color
		if card_[0] < 10:
			card = str(card_[0])
		else:
			card = ["drawtwo", "reverse", "skip"][card_[1]-10]
		#print "card", card
		self.irc.send(".play "+color+" "+card)
		return self.handlecmd("p", [color, card], "FunBot", "tpw_rules")
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
	def handlewin(self, user):
		self.irc.send(user+" wins!!")
		points = 0
		for player in self.players:
			if player[0] == user:
				continue
			self.irc.send(player[0]+"'s cards: "+" ".join([self.getcardtext(c) for c in player[1]]))
			pointvals = sum([self.appendpoints(c)[0] for c in player[1]])
			userdata = self.irc.getuserdata(player[0])
			if player[0] != "FunBot":
				self.irc.setuserdata(player[0], [userdata[0]-pointvals, userdata[1]+1])
			points += pointvals
		userdata = self.irc.getuserdata(user)
		if player[0] != "FunBot":
			self.irc.setuserdata(user, [userdata[0]+points, userdata[1]+1])
		self.irc.send(user+" gets "+str(points)+" points!")
	def handlecmd(self, cmd, args, user, nick):
		cmd = cmd.lower()
		if cmd == "count":
			self.irc.send("Number of cards: "+", ".join([p[0]+" has "+str(len(p[1])) for p in self.players]))
			return
		if self.players[self.currplayer][0] != user:
			self.irc.notice(nick, "It's not your turn!")
			return
		if cmd == "p" or cmd == "put":
			player = self.players[self.currplayer]
			if len(args) < 2:
				self.irc.notice(nick, "Invalid play!1")
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
					self.irc.notice(nick, "Invalid play!2")
					return
			if card == -1:
				card = self.getcard(args[1].lower())
				if card == -1:
					self.irc.notice(nick, "Invalid play!3")
					return
			if self.canbeplayed([card, color]) == False:
				self.irc.notice(nick, "Invalid play!4")
				return
			try:
				x = player[1].index([card, color])
			except:
				self.irc.notice(nick, "Invalid play!5 "+str(card)+" - "+str(color))
				return
			player[1].remove([card, color])
			if wcolor != -1:
				self.topcard = [card, wcolor]
			else:
				self.topcard = [card, color]
			self.drew = False
			self.irc.send(user+" plays a "+self.getcardtext([card, color]))
			if len(player[1]) < 2:
				if len(player[1]) == 1:
					self.irc.send("\x02"+user+" has UNO!!")
				else:
					self.handlewin(user)
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
			if user != "FunBot":
				self.irc.notice(nick, "You drew: "+self.getcardtext(card))
			self.irc.send(user+" drew a card")
			self.players[self.currplayer][1].append(card)
			if user == "FunBot":
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
	
def disp_stats(irc, userdata):
	irc.send("Total points: "+str(userdata[0])+", Number of games played: "+str(userdata[1]))