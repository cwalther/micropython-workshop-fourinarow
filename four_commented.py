# plain import: import a whole module and make it available under its own name
import pew

# -- initialization ----

pew.init()
# the framebuffer
screen = pew.Pix()
# x coordinate of my cursor
cursor = 3

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

	# -- drawing ----

	# clear previous cursor
	screen.box(0, 0, 0, 7, 1)
	# draw cursor
	screen.pixel(cursor, 0, 1)
	# done drawing into the framebuffer, send it to the display
	pew.show(screen)
	# wait until it's time for the next frame
	# 0.15 seconds is an appropriate frame time for our animations and key repeating - increase it if you still find it hard to move the cursor by exactly one pixel
	# drawing at a faster rate would require more complex key repeat handling
	pew.tick(0.15)
