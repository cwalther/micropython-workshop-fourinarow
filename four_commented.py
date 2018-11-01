# plain import: import a whole module and make it available under its own name
import pew

# -- initialization ----

pew.init()
# the framebuffer
screen = pew.Pix()

# -- game loop ----

while True:

	# -- input handling ----

	k = pew.keys()
	# modify state

	# -- drawing ----

	# draw on screen

    # when done, send it to the display
	pew.show(screen)
	# wait until it's time for the next frame
	pew.tick(0.15)
