import pew

# -- initialization ----

pew.init()
screen = pew.Pix()

# -- game loop ----

while True:

	# -- input handling ----

	k = pew.keys()
	# modify state

	# -- drawing ----

	# draw on screen
	pew.show(screen)
	pew.tick(0.15)
