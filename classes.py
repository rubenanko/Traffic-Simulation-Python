from doubleChainedList import DCList
from random import randint
from random import uniform
from math import sqrt
from states import *
import win32gui,win32api,win32con
import sys
import time

class Road:
		
	def __init__(self, profile : str):
		self.profile = open(profile,'r')
		self.voies = []
		self.nbV = int(self.profile.readline())
		for voie in range(self.nbV):
			self.voies.append(DCList(None,None,None))
		self.limitation = float(self.profile.readline())
		self.taille = int(self.profile.readline()) #longueur de la route en mètres
	
	def __repr__(self):
		s = ""
		voie = 1
		for cell in self.voies:
			s += "voie : " + str(voie) + "\n"
			if cell.content == None: s += "\tempty\n"
			else:
				while cell.next != None:
					s += str(cell.content) + "\n"
					cell = cell.next
				voie += 1
		return s
		
	def accidentManager(self,cell):
		print("ACCIDENT : " + cell.content.name)
		run = True
		while run:
			if win32api.GetKeyState(0x1B) < 0:	run = False #échap met fin a la boucle while sans fermer la fenêtre
			sys.exit()
			
	def distance_inter_cell(self,cell,front_cell):
		if front_cell.content.x + front_cell.content.car.longueur < cell.content.x:	distance = self.taille - cell.content.x + front_cell.content.x-cell.content.car.longueur
		else:	distance = front_cell.content.x-cell.content.x-cell.content.car.longueur
		return max(0.1,distance)			
#_________________________________________
	def change(self,cell,side_back_cell,voie : int): #retourne la tête de liste chainée
		if voie == 1:	cell.content.driver.vitesse_voulue = cell.content.driver.vitesse_moyenne*self.limitation
		ancienne_voie = cell.content.voie
		content = cell.content
		if cell.next == cell: #si la cellule était seule sur sa voie
			self.voies[ancienne_voie].content = None
			self.voies[ancienne_voie].next = None
			self.voies[ancienne_voie].previous = None
		else: #sinon si la cellule n'était pas seule sur sa voie
			cell.next.previous = cell.previous
			cell.previous.next = cell.next
			#si la cellule était la tête maintient de la tête dans l'ancinne voie
			if cell == self.voies[ancienne_voie]:
				if cell.previous.content.x < cell.content.x:
					self.voies[ancienne_voie] = cell.previous
				else: self.voies[ancienne_voie] = cell.next
		post_cell = DCList(content)
		if side_back_cell.content == None: #si la cellule est seule sur la nouvelle voie
			post_cell.next = post_cell
			post_cell.previous = post_cell
			self.voies[voie] = post_cell
		else:
			post_cell.previous = side_back_cell
			post_cell.next = side_back_cell.next
			post_cell.next.previous = post_cell
			post_cell.previous.next = post_cell
		post_cell.content.voie = voie
		post_cell.content.change = -1
		# ~ if self.voies[voie].previous.content.x < self.voies[voie].content.x:	self.voies[voie] = self.voies[voie].previous
		return self.voies[ancienne_voie]
			
	def changeManager(self,cell,side_front_cell): #retourne la tête de liste chainée/peloton
		#vérification des préconditions sur cell.content.change (voie demandée existante)
		if cell.content.change < 0 or cell.content.change > len(self.voies)-1 or cell.content.change == cell.content.voie:
			cell.content.change = -1
			return self.voies[cell.content.voie] #on retourne la tete de liste inchangée
		#fin vérifications
		#début du changement de voie
		elif cell.content.voie < cell.content.change:	step = cell.content.voie + 1
		else: step = cell.content.voie - 1 #assignation de l'indice de la prochaine voie à atteindre à la variable step
		#on trouve la cellule leader sur la voie step
		side_back_cell = side_front_cell.previous
		if side_front_cell.content == None:	return self.change(cell,side_front_cell,step)
		
		#calcul des conditions de changement de voie
		
		#calcul condition voiture de devant
		#calcul distance
		distance = self.distance_inter_cell(cell,side_front_cell)
		#calcul acceleraction
		if distance < 3:	a_fictive_next = -cell.content.driver.deceleration_avant_toleree
		else:	a_fictive_next = self.IDM(cell,side_front_cell,distance)
		
		#calcul condition voiture de derrière
		#calcul distance
		distance2 = self.distance_inter_cell(side_back_cell,cell)
		#calcul acceleraction
		if distance2 < 3:	a_fictive_previous = -cell.content.driver.deceleration_arriere_toleree
		else:	a_fictive_previous = self.IDM(side_back_cell,cell,distance2)
		
		#vérification des condition de déportation sur la voie step
		# ~ print(side_back_cell.content.name,distance2,side_front_cell.content.name,distance)
		if a_fictive_next > -cell.content.driver.deceleration_avant_toleree and a_fictive_previous > -cell.content.driver.deceleration_arriere_toleree:	return self.change(cell,side_back_cell,step)
		else:	return self.voies[cell.content.voie]
		# ~ return self.change(cell,side_back_cell,step)
	
	def IDM(self,cell,front_cell,distance, DV=None):		
		#déclarations par défaut
		if DV == None:	DV = cell.content.v - front_cell.content.v
		#définition contraste de vitesse
		if cell.content.v != 0:	CV = max(0.00000000001,(DV)/(cell.content.v + front_cell.content.v))
		else:	CV = 1
		if distance < cell.content.v*2:	respect_distance_secu = cell.content.v*2/distance
		else:	respect_distance_secu = 1
		CV = CV**(1/8)*respect_distance_secu #pseudo contraste de vitesse, pour exacerber les petits contrastes et ainsi tendre rapidement vers l'IDM
		
		Did = (cell.content.driver.coeff_distance_secu*2 + max(0, cell.content.driver.coeff_distance_secu*cell.content.v*2+((cell.content.v*(DV))/(2*sqrt(cell.content.driver.coeff_acceleration*cell.content.car.acceleration_max*cell.content.car.freinage_max*cell.content.driver.coeff_deceleration)))))
		if Did < cell.content.car.longueur * 1000 : #on majore la distance idéale par 5000 (arbitraire, juste grand devant la taille du problème)
			interact = (  Did  /  (distance/CV)  )**2
			a = cell.content.driver.coeff_acceleration * cell.content.car.acceleration_max   *   (  1 - (  cell.content.v  /  (cell.content.driver.vitesse_voulue) )**4  -   interact)
		else :
			a = -(cell.content.driver.coeff_deceleration * cell.content.car.freinage_max) #on minore l'accell par le freinage max 
		return a
	
	def find_leader(self,cell,voie):
		back_cell = self.voies[voie]
		head = self.voies[voie]
		if head.content == None: #si la voie step est vide
			return head
		else: #sinon, on itère sur les cellules jusqu'a trouver celles entre lesquelles s'intercaler
			if head.previous.content.x < head.content.x:	head = head.previous #maintient de la tête de liste comme cellule d'abscisse minimale
			if back_cell.content.x >= cell.content.x:
				back_cell = back_cell.previous
			while back_cell.next != head and back_cell.next.content.x < cell.content.x:
				back_cell = back_cell.next
			front_cell = back_cell.next
		return front_cell
	
	def gestionaire_evenements(self,dt,cell,front_cell,distance):
		DV = None
		if cell.content.TCDC[0] + cell.content.TCDC[1] < time.time(): #cooldown 	est-ce le temps de changer d'état ? si oui allons-y	
			side_front_cell = self.find_leader(cell,(cell.content.voie+1)%2)
		#_______________________________
		#_______________________________
		#DECISION CIRCONSTENTIELLES
		#_______________________________
		#_______________________________
			
		#______REGIME LENT__________________

			if cell.content.v < cell.content.driver.condition_vitesse_regime_lent and distance < cell.content.driver.condition_distance_regime_lent and cell.content.v > front_cell.content.v:  #déclenchement de l'état
				proba_regime_lent = uniform(0,1)
				#CHANGEMENT DE VOIE REGIME LENT
				if (proba_regime_lent > (1-cell.content.driver.proba_changement_de_voie_regime_lent)) and (cell.content.v > front_cell.content.v) and ((side_front_cell.content == None) or (side_front_cell.content.v > front_cell.content.v) or (distance < self.distance_inter_cell(cell,side_front_cell))):
					cell.content.etat_c = VOIE_REGIME_LENT
					cell.content.change = (cell.content.voie+1)%2
					cell.content.TCDC[1] = cell.content.driver.temps_etat_changement_voie_regime_lent
					cell.content.TCDC[0] = time.time()					
				#STOP AND GO
				elif proba_regime_lent < cell.content.driver.proba_stop_and_go:
					cell.content.etat_c = STOP
					cell.content.distance_fictive = distance
					cell.content.TCDC[0] = time.time()
					cell.content.TCDC[1] = cell.content.driver.temps_etat_stop_and_go
				#NEUTRE
				else:
					cell.content.etat_c = NEUTRE
					cell.content.TCDC[0] = time.time()
					cell.content.TCDC[1] = cell.content.driver.temps_etat_neutre_regime_lent
				
		#______VOIE GAUCHE REGIME NORMAL___________________
			elif (cell.content.voie == 1) and (abs(cell.content.driver.vitesse_voulue-cell.content.v) >= cell.content.driver.condition_difference_de_vitesse_voulue_voie_gauche) and (cell.content.v-front_cell.content.v) >= -1 and (distance <= cell.content.v*6) and (front_cell.content.a < 1):
				cell.content.etat_c = VOIE_GAUCHE
				cell.content.driver.vitesse_voulue = max(cell.content.driver.vitesse_voulue, front_cell.content.v + 8.33) #ou je garde la même ou je vais à celle du mec de devant (+entre 20 et 30) afin de vouloir doubler
				cell.content.change = 0
				cell.content.TCDC[1] = cell.content.driver.temps_etat_changement_de_voie
				cell.content.TCDC[0] = time.time()
				
				
		#______VOIE DROITE REGIME NORMAL__________________
			elif (cell.content.voie == 0) and ((side_front_cell.content == None) or ((side_front_cell.content.v-min(cell.content.driver.vitesse_moyenne*self.limitation,cell.content.driver.vitesse_voulue)) >= -1) or (self.distance_inter_cell(cell,side_front_cell) > cell.content.v*10)):
				cell.content.etat_c = VOIE_DROITE
				cell.content.change = 1
				cell.content.TCDC[1] = cell.content.driver.temps_etat_changement_de_voie
				cell.content.TCDC[0] = time.time()
		
		
		if cell.content.TCDNC[0] + cell.content.TCDNC[1] < time.time(): #est-ce le temps de changer d'état ? si oui allons-y	
			
		#______________________________
		#______________________________
		#DECISION NON-CIRCONSTENTIELLES
		#_______________________________
		#_______________________________
			
		#______ACCELERATION__________________
			proba = uniform(0,1)
			if ((cell.content.etat_c != VOIE_DROITE) or (cell.content.voie == 1)) and proba > (1-cell.content.driver.proba_acceleration) and cell.content.change == -1:
				cell.content.etat_nc = ACCELERATION
				cell.content.driver.vitesse_voulue = min(cell.content.driver.vitesse_voulue + uniform(cell.content.driver.etat_acceleration_valeur_inf,cell.content.driver.etat_acceleration_valeur_sup),self.limitation*cell.content.driver.vitesse_sup)
				cell.content.TCDNC[1] = cell.content.driver.temps_etat_acceleration
				cell.content.TCDNC[0] = time.time()
					
		#______RALENTISSEMENT__________________
			elif ((cell.content.etat_c != VOIE_GAUCHE) or (cell.content.voie == 0)) and proba < cell.content.driver.proba_ralentissement and cell.content.change == -1:
				cell.content.etat_nc = RALENTISSEMENT
				cell.content.change = -1
				cell.content.driver.vitesse_voulue = max(cell.content.driver.vitesse_voulue - uniform(cell.content.driver.etat_ralentissement_valeur_inf,cell.content.driver.etat_ralentissement_valeur_sup),self.limitation*cell.content.driver.vitesse_inf)
				cell.content.TCDNC[1] = cell.content.driver.temps_etat_ralentissement
				cell.content.TCDNC[0] = time.time()
					
			
		#______NEUTRE__________________
			else:
				cell.content.etat_nc = NEUTRE
				cell.content.TCDNC[1] = cell.content.driver.temps_etat_neutre
				cell.content.TCDNC[0] = time.time()		
		#_______________________________
		#_______________________________
		#ACTION
		#_______________________________
		#_______________________________Gestion de l'état en cours, or mise à jour, utiliser SLMT par Stop and Go, car c'est une oscillation gérée ici'
				
		if cell.content.etat_c == GO :
			if cell.content.v < cell.content.driver.condition_vitesse_regime_lent and distance < cell.content.driver.condition_distance_regime_lent and cell.content.v > front_cell.content.v: 
				cell.content.distance_fictive = distance
				cell.content.etat_c = STOP

		if cell.content.etat_c == STOP:
			if distance < 10: #on vérifie que la voiture de devant est pas trop loin, si elle n'est pas trop loin on s'arrette et on reste à l'arret
				cell.content.distance_fictive = max(0.1,cell.content.distance_fictive-cell.content.v*dt)
				distance = cell.content.distance_fictive
				DV = cell.content.v
					
			else: #sinon si elle est trop loin on met un temps avant de redémarrer
				if cell.content.temps_de_reaction_stop_and_go[1] == None:	cell.content.temps_de_reaction_stop_and_go[1] = time.time()
				if cell.content.temps_de_reaction_stop_and_go[0] == None:	cell.content.temps_de_reaction_stop_and_go[0] = uniform(cell.content.driver.temps_de_reaction_stop_and_go_inf,cell.content.driver.temps_de_reaction_stop_and_go_sup)
				elif time.time() < cell.content.temps_de_reaction_stop_and_go[1] + cell.content.temps_de_reaction_stop_and_go[0]*((10/distance)**3):
					cell.content.distance_fictive = max(0.1,cell.content.distance_fictive-cell.content.v*dt)
					distance = cell.content.distance_fictive
					DV = cell.content.v
				else:#après ce temps, état go
					cell.content.etat_c = GO
					cell.content.temps_de_reaction_stop_and_go = [None,None]
					
		return distance,DV
	
	def update(self,dt):
		vmin = 35
		for i in range(len(self.voies)):
			cell = self.voies[i]
			head = cell
			count = 0
			while cell.next != head and cell.next != None and count < 70:
				count += 1
				front_cell = cell.next
				#__distance au leader__
				if front_cell.content.x < cell.content.x:
					distance = abs(self.taille - cell.content.x -cell.content.car.longueur + front_cell.content.x)
					self.voies[i] = front_cell #mAj du plus petit x du peloton (la voiture de x le plus petit est la tête de la liste chainée)
				else :
					distance = abs(front_cell.content.x-cell.content.x-cell.content.car.longueur)
				if distance < 0.1:
					self.accidentManager(cell)
			#_______________________________
				#GESTION DES EVENEMENTS
				distance,DV = self.gestionaire_evenements(dt,cell,front_cell,distance)
						
				#______Formule de l'IDM__________________
				cell.content.a = self.IDM(cell,front_cell,distance,DV)
				#______FIN Formule de l'IDM__________________
			
				#updating speed, color and pos
				v = cell.content.v
				v += cell.content.a*dt	
				cell.content.v = max(0, v) #on minore la vitesse par 0
				vmin = min(vmin,cell.content.v)
				cell.content.x = (cell.content.x + cell.content.v*dt) % self.taille
				propLim = (cell.content.v/self.limitation)**2
				cell.content.car.color = (round(((propLim)%1) *250),round((propLim%1)*50) , round((abs(1-propLim)%1)*250)   )
				if cell.content.change != -1:
					side_front_cell = self.find_leader(cell,(cell.content.voie+1)%2)
					head = self.changeManager(cell,side_front_cell)
				temp = cell
				cell = cell.next
				if cell.previous != temp:
					del temp.content
					del temp
				
#_______________________________________________________________________________________________
			if cell.next == head : #cas de la dernière cellule
				if cell == head:#cas ou la cellule est seule sur sa voie
					cell.content.a = (1-((cell.content.v)/(cell.content.driver.vitesse_voulue))**4)* cell.content.car.acceleration_max
				else:#cas ou la cellule n'est pas seule sur sa voie et qu'on est en fin de boucle
					front_cell = cell.next
					#__distance au leader__
					if front_cell.content.x < cell.content.x :
						distance = abs(self.taille - cell.content.x + front_cell.content.x-cell.content.car.longueur)
						self.voies[i] = front_cell
					else :
						distance = abs(front_cell.content.x-cell.content.x-cell.content.car.longueur)
					if distance < 0.1:
						self.accidentManager(cell)		
						
					#GESTION D'EVENEMENTS	
					distance,DV = self.gestionaire_evenements(dt,cell,front_cell,distance)	
							
					#______Formule de l'IDM__________________
					cell.content.a = self.IDM(cell,front_cell,distance,DV)
					#______FIN Formule de l'IDM__________________
				v = cell.content.v
				v += cell.content.a*dt
				cell.content.v = max(0, v)
				vmin = min(vmin,cell.content.v)
				cell.content.x = (cell.content.x + cell.content.v*dt) % self.taille
				#calcul de la couleur
				propLim = (cell.content.v/self.limitation)**2
				cell.content.car.color = (round(((propLim)%1) *250),round((propLim%1)*50) , round((abs(1-propLim)%1)*250)   )
				
				if cell.content.change != -1:   
					side_front_cell = self.find_leader(cell,(cell.content.voie+1)%2) 
					head = self.changeManager(cell,side_front_cell)
		return vmin < 8
				
				
				
class Driver:
	def __init__(self,profile : str):
		self.profile = open(profile,'r') #chargement du fichier du profil
		#chargement des données du profil
		self.vitesse_inf = float(self.profile.readline())   #rapport de la vitesse inf du conducteur sur la vitesse max de la route
		self.vitesse_sup = float(self.profile.readline())   #rapport de la vitesse max du conducteur sur la vitesse max de la route
		
		self.coeff_distance_secu_inf = float(self.profile.readline())
		self.coeff_distance_secu_sup = float(self.profile.readline())
		
		self.coeff_acceleration_inf = float(self.profile.readline())
		self.coeff_acceleration_sup = float(self.profile.readline())
		
		self.coeff_deceleration_inf = float(self.profile.readline())
		self.coeff_deceleration_sup = float(self.profile.readline())
		
		self.temps_de_reaction_stop_and_go_inf = float(self.profile.readline())
		self.temps_de_reaction_stop_and_go_sup = float(self.profile.readline())
		
		self.deceleration_arriere_toleree_inf = float(self.profile.readline())
		self.deceleration_arriere_toleree_sup = float(self.profile.readline())
		
		self.deceleration_avant_toleree_inf = float(self.profile.readline())
		self.deceleration_avant_toleree_sup = float(self.profile.readline())
		
		#TEMPS ETATS
		
		self.temps_etat_stop_and_go_inf = float(self.profile.readline())
		self.temps_etat_stop_and_go_sup = float(self.profile.readline())
		
		self.temps_etat_changement_voie_regime_lent_inf = float(self.profile.readline())
		self.temps_etat_changement_voie_regime_lent_sup = float(self.profile.readline())
		
		self.temps_etat_neutre_regime_lent_inf = float(self.profile.readline())
		self.temps_etat_neutre_regime_lent_sup = float(self.profile.readline())
		
		self.temps_etat_changement_de_voie_inf = float(self.profile.readline())
		self.temps_etat_changement_de_voie_sup = float(self.profile.readline())
		
		self.temps_etat_ralentissement_inf = float(self.profile.readline())
		self.temps_etat_ralentissement_sup = float(self.profile.readline())
		
		self.temps_etat_acceleration_inf = float(self.profile.readline())
		self.temps_etat_acceleration_sup = float(self.profile.readline())
		
		self.temps_etat_neutre_inf = float(self.profile.readline())
		self.temps_etat_neutre_sup = float(self.profile.readline())
		
		#PROBA ETATS
		
		self.proba_stop_and_go_inf = float(self.profile.readline())
		self.proba_stop_and_go_sup = float(self.profile.readline())
		
		self.proba_changement_de_voie_regime_lent_inf = float(self.profile.readline())
		self.proba_changement_de_voie_regime_lent_sup = float(self.profile.readline())
		
		self.proba_acceleration_inf = float(self.profile.readline())
		self.proba_acceleration_sup = float(self.profile.readline())	
		
		self.proba_ralentissement_inf = float(self.profile.readline())	
		self.proba_ralentissement_sup = float(self.profile.readline())	
		
		#CONDITIONS ETATS
		
		self.condition_vitesse_regime_lent_inf = float(self.profile.readline())
		self.condition_vitesse_regime_lent_sup = float(self.profile.readline())
		
		self.condition_distance_regime_lent_inf = float(self.profile.readline())	
		self.condition_distance_regime_lent_sup = float(self.profile.readline())	
		
		self.condition_difference_de_vitesse_voulue_voie_gauche_inf = float(self.profile.readline())	
		self.condition_difference_de_vitesse_voulue_voie_gauche_sup = float(self.profile.readline())	
		
		#BORNES VITESSES VOULUES ETATS ACCELERATION ET RALENTISSEMENTS
		
		self.etat_acceleration_valeur_inf = float(self.profile.readline())	
		self.etat_acceleration_valeur_sup = float(self.profile.readline())	
		
		self.etat_ralentissement_valeur_inf = float(self.profile.readline())	
		self.etat_ralentissement_valeur_sup = float(self.profile.readline())
		
		#attribus propres au conducteur, déterminés aléatoirement a partir des bornes inf et sup du profil
		self.vitesse_moyenne = (self.vitesse_inf+self.vitesse_sup)/2 #centre de l'intervalle précédement défini
		self.coeff_distance_secu = uniform(self.coeff_distance_secu_inf,self.coeff_distance_secu_sup)
		self.coeff_acceleration = uniform(self.coeff_acceleration_inf,self.coeff_acceleration_sup)
		self.coeff_deceleration = uniform(self.coeff_deceleration_inf,self.coeff_deceleration_sup)
		self.deceleration_arriere_toleree = uniform(self.deceleration_arriere_toleree_inf,self.deceleration_arriere_toleree_sup)
		self.deceleration_avant_toleree = uniform(self.deceleration_avant_toleree_inf,self.deceleration_avant_toleree_sup)
		self.temps_etat_stop_and_go = uniform(self.temps_etat_stop_and_go_inf,self.temps_etat_stop_and_go_sup)
		self.temps_etat_changement_voie_regime_lent = uniform(self.temps_etat_changement_voie_regime_lent_inf,self.temps_etat_changement_voie_regime_lent_sup)
		self.temps_etat_neutre_regime_lent = uniform(self.temps_etat_neutre_regime_lent_inf,self.temps_etat_neutre_regime_lent_sup)
		self.temps_etat_changement_de_voie = uniform(self.temps_etat_changement_de_voie_inf,self.temps_etat_changement_de_voie_sup)
		self.temps_etat_ralentissement = uniform(self.temps_etat_ralentissement_inf,self.temps_etat_ralentissement_sup)
		self.temps_etat_acceleration = uniform(self.temps_etat_acceleration_inf,self.temps_etat_acceleration_sup)
		self.temps_etat_neutre = uniform(self.temps_etat_neutre_inf,self.temps_etat_neutre_sup)
		self.proba_stop_and_go = uniform(self.proba_stop_and_go_inf,self.proba_stop_and_go_sup)
		self.proba_changement_de_voie_regime_lent = uniform(self.proba_changement_de_voie_regime_lent_inf,self.proba_changement_de_voie_regime_lent_sup)
		self.proba_acceleration = uniform(self.proba_acceleration_inf,self.proba_acceleration_sup)
		self.proba_ralentissement = uniform(self.proba_ralentissement_inf,self.proba_ralentissement_sup)
		self.condition_vitesse_regime_lent = uniform(self.condition_vitesse_regime_lent_inf,self.condition_vitesse_regime_lent_sup)
		self.condition_distance_regime_lent = uniform(self.condition_distance_regime_lent_inf,self.condition_distance_regime_lent_sup)
		self.condition_difference_de_vitesse_voulue_voie_gauche = uniform(self.condition_difference_de_vitesse_voulue_voie_gauche_inf,self.condition_difference_de_vitesse_voulue_voie_gauche_sup)		
		self.vitesse_voulue = None
		
class Car:
	def __init__(self,profile : str, color : tuple):
		self.profile = open(profile,'r') #chargement du fichier du profil
		self.color = color
		#chargement des données du profil
		self.acceleration_max = float(self.profile.readline())
		self.freinage_max = float(self.profile.readline())
		self.longueur_inf = float(self.profile.readline())
		self.longueur_sup = float(self.profile.readline())
		self.longueur = uniform(self.longueur_inf,self.longueur_sup)
	

class Cell:
	def __init__(self,driver_profile : str, car_profile : str,name : str):
		self.name = name
		self.x = 0.0
		self.v = 0.0
		self.a = 0.0
		self.driver = Driver(driver_profile)
		color = (255, 0, 0)
		self.car = Car(car_profile,color)
		self.change = -1
		self.road = None #Road
		self.voie = None #int
		self.etat_c = NEUTRE 
		self.etat_nc = NEUTRE 
		self.TCDC = [time.time(),0] # Temps Caractéristique de Décision Circonstentielle[Instant de basculement dans l'état, Temps avant le potentiel changement d'état]
		self.TCDNC = [time.time(),0] # Temps Caractéristique de Décision Non Circonstentielle[Instant de basculement dans l'état, Temps avant le potentiel changement d'état]
		self.distance_ficitve = None
		self.temps_de_reaction_stop_and_go = [None,None]
	
		
	
	def setRoad(self,road): #méthode qui définit la route de la cellule
		self.road = road  #premet de garder dans un attribut l'information de la route
		self.driver.vitesse_voulue = self.driver.vitesse_moyenne*road.limitation
	
	def setVoie(self,voie : int): #méthode qui définit la voie de la cellule
		self.voie = voie
		node = DCList(self,None,self.road.voies[voie])
		self.road.voies[voie].previous = node
		self.road.voies[voie] = node
	
	def __repr__(self):
		return (self.name + " \nposition : " + str(round(self.x,2)) + " m\nspeed : " + str(round(self.v,2)) + " m/s\nacceleration : " + str(round(self.a,2)) + " m/s²\n")

class Traffic:
	def __init__(self,road):
		self.road = road
		self.cells = []
	
	def generateTraffic(self,profiles : list,proportion : list,number_of_cells : int,average_distance : float,speed : float):
		cellsToSpawn = []
		true_number_of_cells = 0
		for p in proportion:
			true_number_of_cells += round(p*number_of_cells)
			cellsToSpawn.append(round(p*number_of_cells))
		X = []
		x = randint(0,self.road.taille-1)
		for i in range(self.road.nbV):
			X.append(x)
		n = len(profiles)
		for i in range(true_number_of_cells):
			profile = randint(0,n-1)
			while cellsToSpawn[profile] == 0:
				profile = (profile + 1) % n
			voie = randint(0,self.road.nbV-1)
			cell = self.spawnCell(X[voie],voie,driver_profile=profiles[profile],v=speed)
			cellsToSpawn[profile] -= 1
			X[voie] = (X[voie] + cell.car.longueur + average_distance) % self.road.taille
			
		
	
	def generateCells(self,n : int):
		positions = []
		for i in range(n):
			valid_position = False
			while not valid_position:
				x = randint(0,self.road.taille)
				valid_position = True
				for pos in positions:
					if x < pos + 15 and x > pos - 15:
						valid_position = False
			positions.append(x)			
			self.spawnCell(x,randint(0,len(self.road.voies)-1))
					
	def spawnCell(self,x : float, voie : int,driver_profile : str = 'default driver.txt', car_profile : str = 'default car.txt',v : float = 10):
			cell = Cell(driver_profile,car_profile,'default cell' + str(len(self.cells)))
			self.cells.append(cell)
			cell.setRoad(self.road)
			cell.voie = voie #randint(0,len(self.road.voies)-1)
			cell.x = x
			cell.v = v
			back_cell = self.road.voies[cell.voie]
			head = self.road.voies[cell.voie]
			
			if back_cell.content == None: # liste vide, rien sur la route, on initialise
				
				back_cell.content = cell
				back_cell.previous = back_cell
				back_cell.next = back_cell
				
			elif back_cell.content.x > x : 
				front_cell = self.road.voies[cell.voie]
				back_cell = front_cell.previous
				node = DCList(cell,back_cell,front_cell)
				back_cell.next = node
				front_cell.previous = node
				self.road.voies[cell.voie] = node
			else:
				while back_cell.next != head and back_cell.next.content.x < x:
					back_cell = back_cell.next
				front_cell = back_cell.next
				node = DCList(cell,back_cell,front_cell)
				back_cell.next = node
				front_cell.previous = node
			return cell
			






