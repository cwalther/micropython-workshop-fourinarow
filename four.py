import pew

def main():

	# -- initialization ----

	pew.init()
	screen = pew.Pix()
	cursor = 3
	turn = 1
	prevk = 0b111111

	# -- game loop ----

	while True:

		# -- input handling ----

		k = pew.keys()
		if k & pew.K_LEFT:
			if cursor > 0:
				cursor -= 1
		if k & pew.K_RIGHT:
			if cursor < 6:
				cursor += 1
		if k & ~prevk & (pew.K_DOWN | pew.K_O | pew.K_X):
			turn = 3 - turn
		prevk = k

		# -- drawing ----

		screen.box(0, 0, 0, 7, 1)
		screen.pixel(cursor, 0, turn)
		pew.show(screen)
		pew.tick(0.15)

main()
