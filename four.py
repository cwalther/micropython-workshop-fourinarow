import pew
from main import menugen
import umqtt.simple as mqtt

def check(board):
	for x in range(4):
		for y in range(6):
			if board.pixel(x, y) != 0 and all(board.pixel(x+i, y) == board.pixel(x, y) for i in range(1, 4)):
				return [(x+i, y) for i in range(4)]
	for x in range(7):
		for y in range(3):
			if board.pixel(x, y) != 0 and all(board.pixel(x, y+i) == board.pixel(x, y) for i in range(1, 4)):
				return [(x, y+i) for i in range(4)]
	for x in range(4):
		for y in range(3):
			if board.pixel(x, y) != 0 and all(board.pixel(x+i, y+i) == board.pixel(x, y) for i in range(1, 4)):
				return [(x+i, y+i) for i in range(4)]
	for x in range(4):
		for y in range(3, 6):
			if board.pixel(x, y) != 0 and all(board.pixel(x+i, y-i) == board.pixel(x, y) for i in range(1, 4)):
				return [(x+i, y-i) for i in range(4)]
	return False

def main():

	# -- animations ----

	def blink(row):
		while len(animations) > 1:
			yield
		while True:
			yield
			for x, y in row:
				screen.pixel(x, y+2, 0)
			yield

	def drop(color, x, y):
		for i in range(1, y):
			screen.pixel(x, y, 0)
			screen.pixel(x, i, color)
			yield

	# -- initialization ----

	pew.init()
	screen = pew.Pix()
	board = pew.Pix(7, 6)
	cursor = 3
	turn = 1
	prevk = 0b111111
	won = False
	animations = []

	with open('four-name', 'rb') as f:
		myname = f.read()
	lobbyprefix = b'fourinarow/lobby/'
	lobbytopic = lobbyprefix + myname
	joinprefix = b'fourinarow/join/'
	jointopic = joinprefix + myname
	client = mqtt.MQTTClient('', 'mqtt.kolleegium.ch')
	client.set_last_will(lobbytopic, b'', True)
	client.connect()
	try:

		# -- lobby initialization ----

		client.publish(lobbytopic, b'1', True)
		joined = None
		lobby = set()
		lobbylist = ['>exit']
		menu = menugen(screen, lobbylist)
		def onMessageLobby(topic, message):
			nonlocal joined, mycolor
			if topic.startswith(lobbyprefix):
				username = topic[len(lobbyprefix):]
				if message:
					lobby.add(username)
					screen.box(1, 0, 7, 8, 1)
				else:
					lobby.discard(username)
					screen.box(2, 0, 7, 8, 1)
				lobbylist[:-1] = [str(n, 'ascii') for n in lobby if n != myname]
			elif topic == jointopic:
				joined = message
				mycolor = 2
		client.set_callback(onMessageLobby)
		client.subscribe(lobbyprefix + b'+')
		client.subscribe(jointopic)

		# -- lobby loop ----

		for selected in menu:
			client.check_msg()
			if joined:
				break
			pew.show(screen)
			pew.tick(1/24)
		else:
			if selected < len(lobbylist) - 1:
				joined = bytes(lobbylist[selected], 'ascii')
				client.publish(joinprefix + joined, myname)
				mycolor = 1
		client.publish(lobbytopic, b'', True)
		screen.box(0)
		pew.show(screen)

		if not joined:
			return
		print('joined', joined, 'as color', mycolor)

		# -- game loop ----

		while True:

			# -- input handling ----

			k = pew.keys()
			if not won:
				if k & pew.K_LEFT:
					if cursor > 0:
						cursor -= 1
				if k & pew.K_RIGHT:
					if cursor < 6:
						cursor += 1
				if k & ~prevk & (pew.K_DOWN | pew.K_O | pew.K_X):
					y = 0
					while y < 6 and board.pixel(cursor, y) == 0:
						y += 1
					if y != 0:
						board.pixel(cursor, y-1, turn)
						animations.append(drop(turn, cursor, y+1))
						won = check(board)
						if won:
							animations.append(blink(won))
						turn = 3 - turn
			else:
				if prevk == 0 and k != 0 and len(animations) == 1:
					return
			prevk = k

			# -- drawing ----

			screen.box(0, 0, 0, 7, 2)
			if not won:
				screen.pixel(cursor, 0, turn)
			screen.blit(board, 0, 2)
			for i in range(len(animations)-1, -1, -1):
				try:
					next(animations[i])
				except StopIteration:
					del animations[i]
			pew.show(screen)
			pew.tick(0.15)

	finally:
		client.publish(lobbytopic, b'', True)
		client.disconnect()

main()
