import win32gui,win32api,win32con
import time
from random import randint
from doubleChainedList import DCList
from classes import Road,Driver,Car,Cell,Traffic
import os
import pygame
from pygame.locals import *
from display import displayCalculs, drawRoad, drawCell 

#_________________________________CARACTERISTIQUES FENETRE PYGAME
HEIGHT,WIDTH = 840,1530
dim = (HEIGHT, WIDTH)
BACKGROUND = (50,50,50) #couleur du fond
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT)) #Setting WINDOW
pygame.display.set_caption('Traffic SIM') #Window Name
WINDOW.fill(BACKGROUND)
pygame.init()
#_________________________________


def main():
	run = True
	road = Road('default road.txt') #objet route
	traffic = Traffic(road)
	timestamp = time.time()
	CLOCK = pygame.time.Clock()
	drawRoad(road, WINDOW, dim)
	
	taillePort, nbPortions, gap, roadTness, tness = displayCalculs(road, dim)
	
	cell = None
	while run:
		dt = time.time()-timestamp
		timestamp = time.time()
		road.update(dt)
		# ~ if win32api.GetKeyState(0x1B) < 0:	run = False #échap met fin a la boucle while sans fermer la fenêtre
		
		#_________________________________AFFICHAGE
		CLOCK.tick(60)
		drawRoad(road, WINDOW, dim)
		drawCell(road, WINDOW, dim)
		
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
			  run = False
			if event.type == pygame.MOUSEBUTTONDOWN: #dynamic cell spawner
				
				a,b = pygame.mouse.get_pos()
				indPort = (b-5)//(roadTness+gap)
				v = ((b-5)-indPort*(roadTness+gap))//tness
				if v >= len(road.voies) :
					v = v//4
				x = (a/WIDTH)*taillePort + indPort*taillePort
				cell = traffic.spawnCell(x, v)
			
		pressed = pygame.key.get_pressed()
		if pressed[pygame.K_ESCAPE]:    
			run = False

		if pressed[pygame.K_RIGHT]:   
			cell.v += 1
		if pressed[pygame.K_LEFT]:    
			cell.v -= 1
		if pressed[pygame.K_DOWN]:
			cell.change = 1
		if pressed[pygame.K_UP]:
			cell.change = 0
		pygame.display.update()
		#_________________________________FIN AFFICHAGE

if __name__ == '__main__':
	main()
