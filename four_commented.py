# plain import: import a whole module and make it available under its own name
import pew

# The main function contains the whole game. Called at the bottom.
def main():

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

	# -- game loop ----

	while True:

		# -- input handling ----

		k = pew.keys()
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
				# reverse the turn: 1 -> 2, 2 -> 1
				turn = 3 - turn
		# save the pressed keys for the next iteration to detect edges
		prevk = k

		# -- drawing ----

		# clear previous cursor
		screen.box(0, 0, 0, 7, 1)
		# draw cursor
		screen.pixel(cursor, 0, turn)
		# draw the board
		screen.blit(board, 0, 2)
		# done drawing into the framebuffer, send it to the display
		pew.show(screen)
		# wait until it's time for the next frame
		# 0.15 seconds is an appropriate frame time for our animations and key repeating - increase it if you still find it hard to move the cursor by exactly one pixel
		# drawing at a faster rate would require more complex key repeat handling
		pew.tick(0.15)

	# end of game loop

# run the game when this file is imported
main()
