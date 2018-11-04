# plain import: import a whole module and make it available under its own name
import pew
# partial import: import a module and make only part of its contents available
# like `import main; menugen = main.menugen` but without clobbering the name `main`
from main import menugen
# renaming import: import a module and make it available under a different name
# like `import umqtt.simple; mqtt = umqtt.simple` but without clobbering the name `umqtt`
import umqtt.simple as mqtt

# Check the given 7-by-6 board for winning rows.
# If one is found, return it as a list of four (x, y) tuples in board coordinates.
# If not, return False.
def check(board):
	# horizontal rows can start in the leftmost 4 columns and all rows
	for x in range(4):
		for y in range(6):
			# "if the start pixel is set and all three to the right of it match it",
			# expressed using a generator expression passed to the all() function
			if board.pixel(x, y) != 0 and all(board.pixel(x+i, y) == board.pixel(x, y) for i in range(1, 4)):
				# using a list comprehension to generate the output
				return [(x+i, y) for i in range(4)]
	# vertical rows can start in the topmost 3 rows and all columns
	for x in range(7):
		for y in range(3):
			# "if the start pixel is set and all three below it match it"
			if board.pixel(x, y) != 0 and all(board.pixel(x, y+i) == board.pixel(x, y) for i in range(1, 4)):
				return [(x, y+i) for i in range(4)]
	# main diagonal rows can start in the top left 4-by-3 rectangle
	for x in range(4):
		for y in range(3):
			# "if the start pixel is set and all three down and to the right match it"
			if board.pixel(x, y) != 0 and all(board.pixel(x+i, y+i) == board.pixel(x, y) for i in range(1, 4)):
				return [(x+i, y+i) for i in range(4)]
	# secondary diagonal rows can start in the bottom left 4-by-3 rectangle
	for x in range(4):
		for y in range(3, 6):
			# "if the start pixel is set and all three up and to the right match it"
			if board.pixel(x, y) != 0 and all(board.pixel(x+i, y-i) == board.pixel(x, y) for i in range(1, 4)):
				return [(x+i, y-i) for i in range(4)]
	return False

# The main function contains the whole game. Called at the bottom.
def main():

	# -- animations ----

	# these functions need access to `screen`, which is a local variable of the main() function, so they must be defined locally as well (or, alternatively, they could take it passed as an argument)

	# Generator function that takes a winning row in the format returned by
	# check() and makes it blink by alternatingly doing nothing (leaving the
	# pixels in their original color) and overwriting them with black.
	def blink(row):
		# as long as a drop animation is still running, do nothing
		while len(animations) > 1:
			yield
		# infinite loop, the blinking does not end by itself
		while True:
			# odd iterations: do nothing -> colored pixels
			yield
			# even iterations: black pixels
			for x, y in row:
				# x, y are in board coordinates, add 2 to convert to screen coordinates
				screen.pixel(x, y+2, 0)
			yield

	# Generator function that takes the color and final position of a piece and
	# animates it dropping from the top down to that position.
	# Drawn over a board where the piece is already in the final position, so
	# - the final pixel must be erased
	# - the animation ends one before the final position
	def drop(color, x, y):
		# start at 1 (because the cursor was already at 0) and run up to and excluding y
		for i in range(1, y):
			# erase final position with black
			screen.pixel(x, y, 0)
			# draw at current position
			screen.pixel(x, i, color)
			yield

	# -- initialization ----

	pew.init()
	# the framebuffer
	screen = pew.Pix()
	# the board
	board = pew.Pix(7, 6)
	# x coordinate of my cursor
	cursor = 3
	# color value of whose turn it is (1=green, 2=red)
	turn = 1
	# keys pressed in the previous game loop iteration (pew.keys() value),
	# initialized to "all keys pressed" in binary so that there cannot be a
	# rising edge in the first iteration
	prevk = 0b111111
	# whether the game has ended, expressed by the return value of check():
	# either False or the winning row, which counts as "true" becaues it is a
	# non-empty sequence
	won = False
	# a list of generators that implement any currently running animations
	animations = []

	# read the player name from the configuration file
	# open for reading ('r'), in binary mode ('b') because we want the name as bytes, not as a string
	with open('four-name', 'rb') as f:
		myname = f.read()
	# various common parts of MQTT topics as bytes
	lobbyprefix = b'fourinarow/lobby/'
	lobbytopic = lobbyprefix + myname
	# set up the MQTT client object
	client = mqtt.MQTTClient('', 'mqtt.kolleegium.ch')
	# last will is the "leaving the lobby" message
	client.set_last_will(lobbytopic, b'', True)
	client.connect()
	# Whatever happens from now on, whether we exit by an error or by a
	# deliberate return, we want to close the connection in the end. Use a
	# try-finally statement for that.
	try:

		# -- lobby initialization ----

		# I am present
		client.publish(lobbytopic, b'1', True)
		# all the player names in the lobby, as a set so we can easily add and remove them by value without getting duplicates
		lobby = set()
		# the lobby as a list for the menu, which can't directly take a set, and with the additional "exit" entry at the end
		lobbylist = ['>exit']
		# create the menu generator, it keeps a reference to the list and will automatically pick up changes to it
		menu = menugen(screen, lobbylist)
		# callback for handling incoming MQTT messages while we're in the lobby
		def onMessageLobby(topic, message):
			# messages about players arriving and leaving
			if topic.startswith(lobbyprefix):
				username = topic[len(lobbyprefix):]
				# message is b'', which counts as false, or non-empty (expected b'1'), which counts as true
				if message:
					lobby.add(username)
					# flash a green bar at the bottom to indicate arrival
					# this works because onMessageLobby is called from client.check_msg(), which occurs after drawing the menu (in `for selected in menu`) but before `pew.show(screen)`
					screen.box(1, 0, 7, 8, 1)
				else:
					# use discard(), not remove() to avoid an exception if the name is not there
					# (it should, but we have no control over what messages others send us)
					lobby.discard(username)
					# red bar at the bottom to indicate departure
					screen.box(2, 0, 7, 8, 1)
				# update the list form of the lobby by
				# - transforming the elements of the set form using a list comprehension (they are bytes but the menu wants strings)
				# - inserting them using a slice index that replaces everything but the ">exit" item at the end
				# it's important that we modify this list in place, not create a totally new list, because this list is the one the menu generator has a reference to
				lobbylist[:-1] = [str(n, 'ascii') for n in lobby if n != myname]
		client.set_callback(onMessageLobby)
		# subscribe to all topics 1 level deep in the lobby (= user names)
		client.subscribe(lobbyprefix + b'+')

		# -- lobby loop ----

		# repeatedly poke the menu generator, which draws the menu and handles buttons, until the user selects an entry - conveniently done by a for loop
		# assigns the returned index to `selected` every time - we don't need it during the loop, we only need the value from the last iteration afterwards
		for selected in menu:
			# while in the menu, we also repeatedly need to check for incoming MQTT messages - this calls onMessageLobby if there is any
			client.check_msg()
			pew.show(screen)
			# this is the frame rate expected by the menu for an appropriate animation speed
			pew.tick(1/24)
		return

		# -- game loop ----

		while True:

			# -- input handling ----

			k = pew.keys()
			# key handling is different depending on whether the game is running or over
			if not won:
				# check for bits in k using the bitwise AND operator - the result is zero or nonzero, which count as false or true
				if k & pew.K_LEFT:
					# move cursor left if possible
					if cursor > 0:
						cursor -= 1
				if k & pew.K_RIGHT:
					# move cursor right if possible
					if cursor < 6:
						cursor += 1
				# drop only if the respective key was not pressed in the last iteration, otherwise we would repeatedly drop while the key is held down (edge detection)
				if k & ~prevk & (pew.K_DOWN | pew.K_O | pew.K_X):
					# determine the topmost occupied (or beyond-the-bottom) place in the column by iterating from the top
					y = 0
					while y < 6 and board.pixel(cursor, y) == 0:
						y += 1
					# now either y == 6 (all were free) or place y was occupied, in both cases y-1 is the desired free place
					# unless the whole column was full (y == 0)
					if y != 0:
						# place the piece in the final position
						board.pixel(cursor, y-1, turn)
						# start the drop animation - doesn't draw anything yet, just sets up the generator that will draw when poked
						animations.append(drop(turn, cursor, y+1))
						# check for winning rows
						won = check(board)
						# won is either False or a non-empty sequence that counts as true
						if won:
							# start the blink animation
							animations.append(blink(won))
						# reverse the turn: 1 -> 2, 2 -> 1
						turn = 3 - turn
			else:
				# when the game is over, exit on a key press - several conditions to check:
				# - the first time we're getting here, the key that dropped the final piece may still be pressed - do nothing until all keys have been up in the previous iteration
				# - do nothing until the drop animation has completed and only the blink animation (which is endless) remains
				if prevk == 0 and k != 0 and len(animations) == 1:
					return
			# save the pressed keys for the next iteration to detect edges
			prevk = k

			# -- drawing ----

			# clear previous cursor and dropping piece
			screen.box(0, 0, 0, 7, 2)
			if not won:
				# draw cursor
				screen.pixel(cursor, 0, turn)
			# draw the board (in unanimated state)
			screen.blit(board, 0, 2)
			# poke all active animations to draw one iteration each
			# we'll be removing items from the list while iterating over it, so we need to do it backwards to avoid skipping items
			# start at the last position (len-1), continue to 0 inclusively which is -1 exclusively, in steps of -1
			for i in range(len(animations)-1, -1, -1):
				try:
					# next() pokes, it raises StopIteration when the generator is exhausted (animation is over)
					next(animations[i])
				except StopIteration:
					# remove completed animations
					del animations[i]
			# done drawing into the framebuffer, send it to the display
			pew.show(screen)
			# wait until it's time for the next frame
			# 0.15 seconds is an appropriate frame time for our animations and key repeating - increase it if you still find it hard to move the cursor by exactly one pixel
			# drawing at a faster rate would require more complex key repeat handling
			pew.tick(0.15)

		# end of game loop

	finally:
		# however we exited from the try block, by an error or by a deliberate return, leave the lobby and close the connection
		client.publish(lobbytopic, b'', True)
		client.disconnect()

# run the game when this file is imported
main()
