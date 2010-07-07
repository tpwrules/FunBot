__gamename__ = "gofish"
__helptext__ = "Your standard go fish game"
__players__ = 2

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

cardletters = ["", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
cardletterlookup = {"A":1, "J":11, "Q":12, "K":13}
cardstrs = ["", "ace", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "jack", "queen", "king"]
numstrs = ["zero", "one", "two", "three", "four"]

class GoFish:
	def __init__(self, irc, options):
		self.players = []
		self.irc = irc
		self.deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]*4
		random.shuffle(self.deck)
		self.hands = []
		self.pairs = []
		self.currplayer = 0
	def join(self, user):
		self.players.append(user)
		self.hands.append([])
		self.pairs.append([])
	def start(self):
		self.numplayers = len(self.players)
		numcards = 7
		if self.numplayers < 4:
			numcards = 9
		for x in xrange(numcards):
			for y in xrange(self.numplayers):
				self.hands[y].append(self.deck.pop())
		for x in xrange(self.numplayers):
			self.hands[x].sort()
		self.doturn(0)
	def stop(self):
		pass
	def doturn(self, player):
		oldplayer = player
		while True:
			if len(self.hands[player]) == 0:
				out = "You are out of cards"
				try:
					card = self.deck.pop()
					self.hands[player].append(card)
					out += ", so you picked up a "+self.card2str(card)
				except:
					player += 1
					if player == len(self.players):
						player = 0
					if oldplayer == player:
						self.handlewin()
						return True
					continue
				self.irc.notice(self.irc.getnick(self.players[player]), out+"!")
				break
			else:
				break
		self.currplayer = player
		nick = self.players[player]
		self.irc.send(nick+", your turn! !ask somebody for cards!")
		self.irc.send(nick+"'s pairs: "+", ".join([cardletters[card] for card in self.pairs[player]]))
		self.irc.notice(self.irc.getnick(self.players[player]), "Cards: "+", ".join([cardletters[card] for card in self.hands[player]]))
	def handlewin(self):
		self.irc.send("Everybody is out of cards!")
		pairlens = [(len(self.pairs[x]),x) for x in xrange(len(self.pairs))]
		pairlens.sort()
		pairlens.reverse()
		self.irc.send(self.players[pairlens[0][1]]+" is the winner with "+str(pairlens[0][0]) + " pairs! Congratulations!")
	def card2str(self, card, plural=False):
		name = cardstrs[card]
		if plural == True:
			if card == 6:
				name += "es"
			else:
				name += "s"
		return name
	def handlecmd(self, cmd, args, user, nick):
		cmd = cmd.lower()
		if self.players[self.currplayer] != user:
			self.irc.notice(nick, "Error! It's not your turn!")
			return
		if cmd == "a" or cmd == "ask":
			if len(args) < 2:
				self.irc.notice(nick, "Not enough parameters! !ask <player> <card>")
				return
			askee = args[0]
			card = args[1].upper()
			try:
				card = int(card)
			except:
				try:
					card = cardletterlookup[card]
				except:
					self.irc.notice(nick, "Invalid card!")
					return
			if askee not in self.players:
				self.irc.notice(nick, "No such player!")
				return
			if askee == user:
				self.irc.notice(nick, "You can't ask yourself!")
				return
			currhand = self.hands[self.currplayer]
			if card not in currhand:
				self.irc.notice(nick, "You don't have any of that card!")
				return
			askeenum = self.players.index(askee)
			numcards = self.hands[askeenum].count(card)
			if len(self.hands[askeenum]) == 0:
				self.irc.send(askee+" has no cards!")
				numcards = 1
			elif numcards == 0:
				self.irc.send(askee+" has no "+self.card2str(card, True)+"! Go fish!")
				pickedupcard = self.deck.pop()
				self.irc.notice(nick, "You got a "+self.card2str(pickedupcard))
				currhand.append(pickedupcard)
			else:
				self.irc.send(askee+" has "+numstrs[numcards]+" "+self.card2str(card, numcards>1)+"!")
				for x in xrange(numcards):
					self.hands[askeenum].remove(card)
					currhand.append(card)
				if len(self.hands[askeenum]) == 0:
					out = "You are out of cards"
					try:
						card = self.deck.pop()
						self.hands[askeenum].append(card)
						out += ", so you picked up a "+self.card2str(card)
					except:
						pass
					self.irc.notice(self.irc.getnick(askee), out+"!")
			cards = set(currhand)
			pairs = []
			for x in cards:
				cardcount = currhand.count(x)
				if cardcount > 1:
					pairs.append(x)
					currhand.remove(x)
					currhand.remove(x)
				if cardcount == 4:
					pairs.append(x)
					currhand.remove(x)
					currhand.remove(x)
			self.pairs[self.currplayer].extend(pairs)
			if len(pairs) > 0:
				out = ""
				for x in pairs[:-1]:
					out += "a pair of "+self.card2str(x, True)+", "
				if len(pairs) > 1:
					out = out[:-2]
					out += " and "
				out += "a pair of "+self.card2str(pairs[-1], True)+"!"
				self.irc.send(user+" has "+out)
			if len(currhand) == 0:
				out = "You are out of cards"
				try:
					card = self.deck.pop()
					currhand.append(card)
					out += ", so you picked up a "+self.card2str(card)
				except:
					pass
				self.irc.notice(nick, out+"!")
			if numcards == 0:
				self.currplayer = askeenum
			return self.doturn(self.currplayer)

def start(irc, options):
	return GoFish(irc, options)
	
def disp_stats(irc, userdata):
	pass