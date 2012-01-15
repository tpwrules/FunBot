__gamename__ = "scramble"
__helptext__ = "A trivia scramble game.\n!play scramble [max word len (default 10)] [num words (default 10)]"
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

import os.path
import random

print "[scramble] Loading wordlist..."
wordlist = []
numwords = 0
loaded = False
try:
	f = open(os.path.dirname(__file__)+"/scramble_wordlist.txt")
		
	for x in f.xreadlines():
		wordlist.append(x)
		numwords += 1
		
	loaded = True
	print "[scramble] Wordlist loaded successfully!"
except:
	print "[scramble] Wordlist could not be loaded!"

class Scramble:
	def __init__(self, irc, options):
		self.irc = irc
		if loaded == False:
			self.irc.send("Error! Wordlist was never loaded! Complain to owner!")
			raise Exception
		try:
			self.maxwordlen = int(options[0])
		except:
			self.maxwordlen = 10
		try:
			self.numwords = int(options[1])
		except:
			self.numwords = 10
	def join(self, user):
		if self.irc.getuserdata(user) == None:
			self.irc.setuserdata(user, [0])
	def canstart(self):
		return 0
	def start(self):
		self.irc.send("Choosing words, be patient!")
		chosenwords = []
		tries = 0
		random.shuffle(wordlist)
		for x in wordlist:
			if len(x) > self.maxwordlen:
				continue
			chosenwords.append(x[:-1])
		if len(chosenwords) < self.numwords:
			self.irc.send("Warning: Not enough suitable words were found!")
		self.words = chosenwords[:self.numwords]
		random.shuffle(self.words)
		self.currwordnum = 0
		self.nextword()
	def stop(self):
		pass
	def nextword(self):
		arr = [y for y in self.words[self.currwordnum]]
		random.shuffle(arr)
		self.currword = self.words[self.currwordnum]
		self.discovered = [False]*len(self.currword)
		self.irc.send(str(self.currwordnum+1)+"/"+str(len(self.words))+". Unscramble this: "+"".join(arr))
		print self.currword, "<-- the word"
	def handlecmd(self, cmd, args, playing, user, nick):
		if cmd == "w":
			try:
				submission = args[0]
			except:
				self.irc.notice(nick, "What do you want to tell me?")
				return
			x = submission
			y = self.currword
			if len(submission) > len(self.currword):
				y, x = x, y
			for z in xrange(len(x)):
				if x[z] == y[z]:
					self.discovered[z] = True
			alldiscovered = True
			for x in self.discovered:
				alldiscovered = alldiscovered and x
			if alldiscovered == True:
				self.irc.send(nick+" got it! The word was "+self.currword)
				self.irc.setuserdata(user, [self.irc.getuserdata(user)[0]+1])
				self.currwordnum += 1
				if self.currwordnum == len(self.words):
					self.irc.send("No more words! Come back next time!")
					return True
				self.nextword()
				return
			wordreveal = ""
			for x in xrange(len(self.currword)):
				if self.discovered[x] == True:
					wordreveal += self.currword[x]
				else:
					wordreveal += "."
			self.irc.send("Word: "+wordreveal)

def start(irc, options):
	return Scramble(irc, options)
	
def disp_stats(irc, userdata):
	irc.send("Total words unscrambled: "+str(userdata[0]))