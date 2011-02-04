#
# Title: Chatango Lib
# Author: Lumirayz/Lumz <lumirayz@gmail.com>
# Credits:
#  - Guyfox for explaining some things, don't remember what.
#  - Soda, because I've looked at part of his modified chatango.py for banning.
# Description:
#  An event-based library for connecting to one Chatango room, has support for
#  several things including: messaging, message font, name color, deleting,
#  banning, recent history, 2 userlist modes(recent and all), flagging,
#  avoiding flood bans, detecting flags.
#  Event-based does not mean that this is asynchronous, it still uses a thread
#  for the ping loop, but that shouldn't cause much overhead... I hope.
#

#
# Imports
#
import socket
import threading
import time
import random
import re

#
# Constants
#
Userlist_Recent = 0
Userlist_All    = 1

#
# Tagserver stuff
#
specials = {'mitvcanal': 26, 'aztecatv': 22, 'livenfree': 18, 'onepinoytvto': 10, 'animalog24': 8, 'portalsports': 18, 'pinoyakocg': 5, 'pinoy-online-tv-chat': 22, 'wowchatango': 20, 'narutowire': 10, 'bateriafina3': 21, 'flowhot-chat-online': 12, 'todoanimes': 22, 'phnoy': 21, 'winningtheinnergame': 26, 'fullsportshd2': 18, 'chia-anime': 12, 'narutochatt': 20, 'show-sports-chat': 5, 'pinoyakoinfocg': 5, 'futboldirectochat': 22, 'pnoytvroom': 18, 'pinoycable2': 20, 'stream2watch3': 26, 'ttvsports': 26, 'sport24lt': 26, 'ver-anime': 34, 'fezzer': 18, 'vipstand': 21, 'worldfootballusch2': 18, 'soccerjumbo': 21, 'myfoxdfw': 22, 'animelinkz': 20, 'worldfootballdotus': 26, 'as-chatroom': 10, 'dbzepisodeorg': 12, 'cebicheros': 21, 'watch-dragonball': 19, 'vip----tv': 18, 'tvanimefreak': 27}
tsweights = [['5', 61], ['6', 61], ['7', 61], ['8', 61], ['16', 61], ['17', 61], ['9', 90], ['11', 90], ['13', 90], ['14', 90], ['15', 90], ['23', 110], ['24', 110], ['25', 110], ['28', 104], ['29', 104], ['30', 104], ['31', 104], ['32', 104], ['33', 104], ['35', 101], ['36', 101], ['37', 101], ['38', 101], ['39', 101], ['40', 101], ['41', 101], ['42', 101], ['43', 101], ['44', 101], ['45', 101], ['46', 101], ['47', 101], ['48', 101], ['49', 101], ['50', 101]]

def getServer(group):
	"""
	Get the server host for a certain room.
	
	@type group: str
	@param group: room name
	
	@rtype: str
	@return: the server's hostname
	"""
	try:
		sn = specials[group]
	except KeyError:
		group = group.replace("_", "q")
		group = group.replace("-", "q")
		fnv = float(int(group[0:min(5, len(group))], 36))
		lnv = group[6: (6 + min(3, len(group) - 5))]
		if(lnv):
			lnv = float(int(lnv, 36))
			if(lnv <= 1000):
				lnv = 1000
		else:
			lnv = 1000
		num = (fnv % lnv) / lnv
		maxnum = 0
		for wgt in tsweights:
			maxnum += wgt[1]
		accu = 0
		sn = 0
		for wgt in tsweights:
			accu += float(wgt[1]) / maxnum
			if(num <= accu):
				sn = int(wgt[0])
				break
	return "s" + str(sn) + ".chatango.com"

#
# Uid
#
def genUid():
	return str(random.randrange(10 ** 15, 10 ** 16))

#
# Message stuff
#
def clean_message(msg):
	"""
	Clean a message and return the message, n tag and f tag.
	
	@type msg: str
	@param msg: the message
	
	@rtype: str, str, str
	@returns: cleaned message, n tag contents, f tag contents
	"""
	n = re.search("<n(.*?)/>", msg)
	if n: n = n.group(1)
	f = re.search("<f(.*?)>", msg)
	if f: f = f.group(1)
	msg = re.sub("<n.*?/>", "", msg)
	msg = re.sub("<f.*?>", "", msg)
	msg = strip_html(msg)
	msg = msg.replace("&lt;", "<")
	msg = msg.replace("&gt;", ">")
	msg = msg.replace("&quot;", "\"")
	msg = msg.replace("&apos;", "'")
	msg = msg.replace("&amp;", "&")
	return msg, n, f

def strip_html(msg):
	"""Strip HTML."""
	li = msg.split("<")
	if len(li) == 1:
		return li[0]
	else:
		ret = list()
		for data in li:
			data = data.split(">", 1)
			if len(data) == 1:
				ret.append(data[0])
			elif len(data) == 2:
				ret.append(data[1])
		return "".join(ret)

def parseNameColor(n):
	"""This just returns its argument, should return the name color."""
	#probably is already the name
	return n

def parseFont(f):
	"""Parses the contents of a f tag and returns color, face and size."""
	#' xSZCOL="FONT"'
	size = int(f[2:4])
	col = f[4:7]
	face = f.split("\"")[1]
	return col, face, size

#
# Anon id
#
def getAnonId(n, ssid):
	"""Gets the anon's id."""
	if n == None: n = "5504"
	try:
		return "".join(list(
			map(lambda x: str(x[0] + x[1])[-1], list(zip(
				list(map(lambda x: int(x), n)),
				list(map(lambda x: int(x), ssid[4:]))
			)))
		))
	except ValueError:
		return "NNNN"

def getAnonN(aid, uid):
	"""Gets the n tag number you should have to have a certain anon id."""
	if aid == "NNNN": return "NNNN"
	try:
		res = list()
		for c1, c2 in zip(list(map(lambda x: int(x), str(aid))), list(map(lambda x: int(x), uid[4:8]))):
			var = c1 - c2
			if var < 0:
				var = 10 + var
			res.append(str(var))
		return "".join(res)
	except ValueError:
		return "0000"

#
# RoomConnection class
#
class RoomConnection:
	"""Manages a connection with a Chatango room."""
	#
	# Some settings
	#
	_pingDelay = 20
	_userlistMode = Userlist_Recent
	_userlistUnique = True
	_userlistMemory = 50
	_userlistEventUnique = False
	
	#
	# Init
	#
	def __init__(self, room, name = None, password = None, uid = None, server = None, port = None):
		self._room = room
		self._server = server or getServer(room)
		self._port = port or 443
		self._uid = uid or genUid()
		self._aid = "0000"
		self._updateAnonName()
		self._name_req = name
		self._password_req = password
		self._user = None
		self._owner = None
		self._mods = set()
		self._mqueue = dict()
		self._history = list()
		self._userlist = list()
		self._loggedIn = False
		self._nameColor = "000"
		self._fontColor = "000"
		self._fontFace = "0"
		self._fontSize = 12
		self._connected = False
		self._reconnecting = False
		self._firstCommand = True
		self._firstConnect = True
		self._mbg = False
		self._mrec = False
		self._premium = False
		self._connect()
	
	#
	# Connect/disconnect
	#
	def _connect(self):
		"""Connect to the server."""
		self._sock = socket.socket()
		self._sock.connect((self._server, self._port))
		self._firstCommand = True
		self._auth()
		if not self._reconnecting: self.connected = True
	
	def reconnect(self):
		"""Reconnect."""
		self._reconnect()
	
	def _reconnect(self):
		"""Reconnect."""
		self._reconnecting = True
		if self.connected:
			self._disconnect()
		self._name_req = self._name
		self._password_req = self._password
		self._uid = genUid()
		self._connect()
		self._reconnecting = False
	
	def _disconnect(self):
		"""Disconnect from the server."""
		if not self._reconnecting: self.connected = False
		self._sock.close()
	
	def _auth(self):
		"""Authenticate."""
		if self._name_req:
			if self._password_req:
				self._sendCommand("bauth", self._room, self._uid, self._name_req, self._password_req)
			else:
				self._sendCommand("bauth", self._room, self._uid)
		else:
			self._sendCommand("bauth", self._room, self._uid)
	
	#
	# Properties
	#
	def getName(self):
		if self._isAnon:
			return self._anonName
		else:
			return self._name
	def getUserlist(self):
		ul = None
		if self._userlistMode == Userlist_Recent:
			ul = map(lambda x: x.user, self._history[-self._userlistMemory:])
		elif self._userlistMode == Userlist_All:
			ul = self._userlist
		if self._userlistUnique:
			return list(set(ul))
		else:
			return ul
	def getUserNames(self):
		ul = self.userlist
		return list(map(lambda x: x.name, ul))
	def getUser(self): return User(self.name)
	def getLevel(self): return self.user.level
	def getOwner(self): return self._owner
	def getMods(self):
		newset = set()
		for mod in self._mods:
			newset.add(mod)
		newset.add(self.owner)
		return newset
	def getModNames(self):
		mods = self.mods
		return list(map(lambda x: x.name, mods))
	
	name = property(getName)
	userlist = property(getUserlist)
	usernames = property(getUserNames)
	user = property(getUser)
	level = property(getLevel)
	owner = property(getOwner)
	mods = property(getMods)
	modnames = property(getModNames)
	
	#
	# Virtual methods
	#
	def onConnect(self): pass
	def onReconnect(self): pass
	def onConnectFail(self): pass
	def onDisconnect(self): pass
	def onLoginFail(self): pass
	def onLoginSuccess(self): pass
	def onFloodBan(self): pass
	def onFloodBanRepeat(self): pass
	def onFloodWarning(self): pass
	def onMessageDelete(self, msg): pass
	def onModChange(self): pass
	def onMessage(self, user, message): pass
	def onHistoryMessage(self, user, message): pass
	def onJoin(self, user): pass
	def onLeave(self, user): pass
	def onRaw(self, raw): pass
	def onPing(self): pass
	
	#
	# Ping
	#
	def pingloop(self):
		"""Ping loop."""
		while self.connected:
			self._sendCommand("")
			self.onPing()
			time.sleep(self._pingDelay)
	
	#
	# Main
	#
	def main(self):
		"""Main loop."""
		threading._start_new_thread(self.pingloop, ())
		while True:
			cmd = self._receiveCommand()
			self.onRaw(cmd)
			cmd, *args = cmd.split(":")
			if   cmd == "ok":
				if args[2] == "M": #succesful login
					self._isAnon = False
					self._loggedIn = True
					self._name = self._name_req
					self._password = self._password_req
				else:
					self._isAnon = True
					self._loggedIn = False
					self._name = None
					self._password = None
					self._updateAnonName()
				del self._name_req
				del self._password_req
				self._owner = User(args[0])
				self._owner._level = 2
				self._uid = args[1]
				self._aid = args[1][4:8]
				self._mods = set(map(lambda x: User(x), args[6].split(";")))
				for mod in self._mods:
					mod._level = 1
				self._i_log = list()
			elif cmd == "inited":
				for msg in reversed(self._i_log):
					user = msg._user
					user._msgs.append(msg)
					self.onHistoryMessage(user, msg)
					self._addHistory(msg)
				del self._i_log
				self._sendCommand("g_participants", "start")
				self._sendCommand("getpremium", "1")
				if self._firstConnect:
					self.onConnect()
					self._firstConnect = False
				else:
					self.onReconnect()
			elif cmd == "premium":
				if float(args[1]) > time.time():
					self._premium = True
					if self._mbg: self.enableBg()
					if self._mrec: self.enableRecording()
				else:
					self._premium = False
			elif cmd == "denied":
				self._disconnect()
				self.onConnectFail()
			elif cmd == "mods":
				modnames = args[0].split(";")
				mods = set(map(lambda x: User(x), modnames))
				premods = set(map(lambda x: User(x), self._mods))
				for user in mods - premods: #demodded
					user._level = 0
					self._mods.remove(user)
				for user in premods - mods: #modded
					user._level = 1
					self._mods.add(user)
				self.onModChange()
			elif cmd == "pwdok":
				self._loggedIn = True
				self._name = self._name_req
				self._password = self._password_req
				del self._name_req
				del self._password_req
				self._sendCommand("getpremium", "1")
				self.onLoginSuccess()
			elif cmd == "badlogin":
				del self._name_req
				del self._password_req
				self.onLoginFail()
			elif cmd == "tb":
				self.onFloodBan()
			elif cmd == "fw":
				self.onFlagged()
			elif cmd == "b":
				mtime = float(args[0])
				puid = args[3]
				ip = args[6]
				name = args[1]
				rawmsg = ":".join(args[8:])
				msg, n, f = clean_message(rawmsg)
				if name == "":
					nameColor = "000"
					name = "#" + args[2]
					if name == "#":
						name = "!anon" + getAnonId(n, puid)
				else:
					if n: nameColor = parseNameColor(n)
					else: nameColor = "000"
				i = args[5]
				unid = args[4]
				#Create an anonymous message and queue it because msgid is unknown.
				msg = Message(None, mtime, User(name), msg)
				msg._ip = ip
				msg.user._unid = unid
				msg._nameColor = nameColor
				msg._raw = rawmsg
				if f: msg._fontColor, msg._fontFace, msg._fontSize = parseFont(f)
				self._mqueue[i] = msg
			elif cmd == "u":
				msg = self._mqueue[args[0]]
				del self._mqueue[args[0]]
				msg.attach(args[1])
				msg.user._msgs.append(msg)
				self._addHistory(msg)
				self.onMessage(msg.user, msg)
			elif cmd == "i":
				mtime = float(args[0])
				puid = args[3]
				ip = args[6]
				if ip == "": ip = None
				name = args[1]
				rawmsg = ":".join(args[8:])
				msg, n, f = clean_message(rawmsg)
				msgid = args[5]
				if name == "":
					nameColor = "000"
					name = "#" + args[2]
					if name == "#":
						name = "!anon" + getAnonId(n, puid)
				else:
					nameColor = parseNameColor(n)
				msg = Message(msgid, mtime, User(name), msg)
				if f: msg._fontColor, msg._fontFace, msg._fontSize = parseFont(f)
				msg._ip = args[6]
				msg._nameColor = nameColor
				msg.user._unid = args[4]
				msg._raw = rawmsg
				self._i_log.append(msg)
			elif cmd == "g_participants":
				args = ":".join(args)
				args = args.split(";")
				for data in args:
					data = data.split(":")
					name = data[3].lower()
					if name == "none": continue
					user = User(name)
					user.jtime = float(data[1])
					user._sids.add(data[0])
					self._userlist.append(user)
			elif cmd == "participant":
				if args[0] == "0": #leave
					name = args[3].lower()
					if name == "none": continue
					user = User(name)
					user._sids.remove(args[1])
					self._userlist.remove(user)
					if not user in self._userlist or not self._userlistEventUnique:
						self.onLeave(user)
				else: #join
					name = args[3].lower()
					if name == "none": continue
					user = User(name)
					user.jtime = float(args[6])
					user._sids.add(args[1])
					if not user in self._userlist: doEvent = True
					else: doEvent = False
					self._userlist.append(user)
					if doEvent or not self._userlistEventUnique: self.onJoin(user)
			elif cmd == "show_fw": #flood warning
				self.onFloodWarning()
			elif cmd == "show_tb": #timedban, first
				self.onFloodBan()
			elif cmd == "tb": #timedban, repeat
				self.onFloodBanRepeat()
			elif cmd == "delete":
				msg = Message(args[0])
				self._history.remove(msg)
				msg.user._msgs.remove(msg)
				self.onMessageDelete(msg)
				msg.detach()
			elif cmd == "deleteall":
				for msgid in args:
					msg = Message(msgid)
					self._history.remove(msg)
					msg.user._msgs.remove(msg)
					self.onMessageDelete(msg)
					msg.detach()
	
	@classmethod
	def easy_start(cl, room = None, name = None, password = None):
		"""
		Prompts the user for missing info, then starts.
		
		@type room: str
		@param room: room to join ("" = None, None = unspecified)
		@type name: str
		@param name: name to join as ("" = None, None = unspecified)
		@type password: str
		@param password: password to join with ("" = None, None = unspecified)
		"""
		if not room: room = str(input("Room name: "))
		if not name: name = str(input("User name: "))
		if name == "": name = None
		if not password: password = str(input("User password: "))
		if password == "": password = None
		self = cl(room, name, password)
		self.main()
	
	#
	# Commands
	#
	def message(self, msg):
		"""
		Send a message.
		
		@type msg: str
		@param msg: message
		"""
		if self._loggedIn:
			if not self._name.startswith("#"):
				msg = "<n" + self._nameColor + "/>" + msg
				msg = "<f x%0.2i%s=\"%s\">" %(self._fontSize, self._fontColor, self._fontFace) + msg
		else:
			msg = "<n" + getAnonN(self._aid, self._uid) + "/>" + msg
		self._sendCommand("bmsg", msg)
	
	def logout(self):
		"""Log out."""
		if self._loggedIn:
			self._sendCommand("blogout")
			self._loggedIn = False
	
	def setName(self, name):
		"""
		Set a temporary name.
		
		@type name: str
		@param name: name
		"""
		if self._loggedIn:
			self.logout()
		self._sendCommand("blogin", name)
	
	def login(self, name, password):
		"""Log in.
		
		@type name: str
		@param name: user name
		@type password: str
		@param password: user password
		"""
		if self._loggedIn:
			self.logout()
		self._name_req = name
		self._password_req = password
		self._sendCommand("blogin", name, password)
	
	def flag(self, message):
		"""
		Flag a message.
		
		@type message: Message
		@param message: message to flag
		"""
		self._sendCommand("g_flag", message.msgid)
	
	def delete(self, message):
		"""
		Delete a message. (Moderator only)
		
		@type message: Message
		@param message: message to delete
		"""
		if self.user.level > 0:
			self._sendCommand("delmsg", message.msgid)
	
	def clearall(self):
		"""Clear all messages. (Owner only)"""
		if self.user.level == 2:
			self._sendCommand("clearall")
	
	def ban(self, msg):
		"""
		Ban a message's sender. (Moderator only)
		
		@type message: Message
		@param message: message to ban sender of
		"""
		if self.user.level > 0:
			print(msg.user.unid)
			self._sendCommand("block", msg.user.unid, msg.ip, msg.user.name)
	
	def enableBg(self):
		"""Enable background if available."""
		self._mbg = True
		self._sendCommand("msgbg", "1")
	
	def disableBg(self):
		"""Disable background."""
		self._mbg = False
		self._sendCommand("msgbg", "0")
	
	def enableRecording(self):
		"""Enable recording if available."""
		self._mrec = True
		self._sendCommand("msgmedia", "1")
	
	def disableRecording(self):
		"""Disable recording."""
		self._mrec = False
		self._sendCommand("msgmedia", "0")
	
	def setNameColor(self, color3x):
		"""
		Set name color.
		
		@type color3x: str
		@param color3x: a 3-char RGB hex code for the color
		"""
		self._nameColor = color3x
	
	def setFontColor(self, color3x):
		"""
		Set font color.
		
		@type color3x: str
		@param color3x: a 3-char RGB hex code for the color
		"""
		self._fontColor = color3x
	
	def setFontFace(self, face):
		"""
		Set font face/family.
		
		@type face: str
		@param face: the font face
		"""
		self._fontFace = face
	
	def setFontSize(self, size):
		"""
		Set font size.
		
		@type size: int
		@param size: the font size (limited: 9 to 22)
		"""
		if size < 9: size = 9
		if size > 22: size = 22
		self._fontSize = size
	
	#
	# Util
	#
	def _sendCommand(self, *args):
		"""
		Send a command.
		
		@type args: [str, str, ...]
		@param args: command and list of arguments
		"""
		if self._firstCommand:
			terminator = b"\x00"
			self._firstCommand = False
		else:
			terminator = b"\r\n\x00"
		self._sock.send(":".join(args).encode() + terminator)
	
	def _receiveCommand(self):
		"""
		Receive a command, blocks.
		
		@rtype: str
		@return: command string
		"""
		rbuf = b""
		while not rbuf.endswith(b"\x00"):
			try:
				rbuf += self._sock.recv(1)
			except socket.error:
				self._disconnect()
				self.onDisconnect()
		return rbuf.decode().rstrip("\r\n\x00")
	
	#
	# History
	#
	def _addHistory(self, msg):
		"""
		Add a message to history.
		
		@type msg: Message
		@param msg: message
		"""
		self._history.append(msg)
	
	#
	# Misc
	#
	def setAnonId(self, aid):
		"""
		Set anon Id.
		
		@type aid: str
		@param aid: anon id, 4-char string of numbers
		"""
		self._aid = aid
		self._updateAnonName()
	
	def _updateAnonName(self):
		"""Update anon name."""
		self._anonName = "!anon" + self._aid

#
# User class
#
class User:
	"""Class that represents a user."""
	#
	# User dict
	#
	_users = dict()
	
	#
	# New
	#
	def __new__(cl, name, *args, **kw):
		if name == None: name = "!anon"
		name = name.lower()
		user = cl._users.get(name)
		if not user:
			user = object.__new__(cl)
			user.__init(name)
			cl._users[name] = user
		return user
	
	#
	# __getattr__
	# To suppress AttributeErrors. Disabled for now.
	#
	#def __getattr__(self, attr):
	#	return None
	
	#
	# Init, not __init__ this time!
	#
	def __init(self, name):
		self._name = name.lower()
		self._level = 0
		self._sids = set()
		self._msgs = list()
		self._unid = None
	
	#
	# Properties
	#
	def getName(self): return self._name
	def getLevel(self): return self._level
	def getSessionIds(self): return self._sids
	def getMessages(self): return self._msgs
	def getUnid(self): return self._unid
	
	name = property(getName)
	level = property(getLevel)
	sessionids = property(getSessionIds)
	messages = property(getMessages)
	unid = property(getUnid)
	
	#
	# Helper methods
	#
	def getLastMessage(self):
		"""
		Get the last sent message of this user.
		
		@rtype: msg
		@return: last message of user or none
		"""
		try:
			return self.messages[-1]
		except IndexError:
			return None

#
# Message class
#
class Message:
	"""Class that represents a message."""
	#
	# User dict
	#
	_msgs = dict()
	
	#
	# New
	#
	def __new__(cl, msgid, *args, **kw):
		if msgid == None:
			msg = object.__new__(cl)
			msg.__init(msgid, *args, **kw)
			return msg
		msg = cl._msgs.get(msgid)
		if not msg:
			msg = object.__new__(cl)
			msg.__init(msgid, *args, **kw)
			cl._msgs[msgid] = msg
		return msg
	
	def attach(self, msgid):
		"""
		Attach the Message to a message id.
		
		@type msgid: str
		@param msgid: message id
		"""
		self._msgid = msgid
		self._msgs[msgid] = self
	
	def detach(self):
		self._msgid = None
		del self._msgs[msgid]
	
	#
	# __getattr__
	# To suppress AttributeErrors. Disabled for now.
	#
	#def __getattr__(self, attr):
	#	return None
	
	#
	# Init, not __init__ this time!
	#
	def __init(self, msgid, mtime, user, body):
		self._msgid = msgid
		self._time = mtime
		self._user = user
		self._body = body
		self._raw = ""
		self._ip = None
		self._nameColor = "000"
		self._fontSize = 12
		self._fontFace = "0"
		self._fontColor = "000"
	
	#
	# Properties
	#
	def getId(self): return self._msgid
	def getTime(self): return self._time
	def getUser(self): return self._user
	def getBody(self): return self._body
	def getIP(self): return self._ip
	def getFontColor(self): return self._fontColor
	def getFontFace(self): return self._fontFace
	def getFontSize(self): return self._fontSize
	def getNameColor(self): return self._nameColor
	def getRaw(self): return self._raw
	
	msgid = property(getId)
	time = property(getTime)
	user = property(getUser)
	body = property(getBody)
	ip = property(getIP)
	fontColor = property(getFontColor)
	fontFace = property(getFontFace)
	fontSize = property(getFontSize)
	raw = property(getRaw)
	nameColor = property(getNameColor)
