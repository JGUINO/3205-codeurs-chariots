#!/usr/bin/env python3

################################################################################
# 
# codeursMQTTIO3.py is a python based daemon for persistant monitoring of the state of
#   3 quadrature rotary encoders attached to a raspberry pi
# 
# Written by: 
#    Matthew Ebert 
#    Department of Physics
#    University of Wisconsin - Madison
#    mfe5003@gmail.com
# 
# modified by :
#    Jerome GUILLON
#    CMC - BREZOLLES - FRANCE
# Python Daemon bootstrap code by:
#    Sander Marechal
#    http://www.jejik.com/ 
#    http://web.archive.org/web/20160305151936/http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#
# This daemon will poll the GPIO pins for each attached rotary encoder and
#   convert the count to an angle.
#   Settings are listed in encoder-settings.py file.
#
################################################################################

import os, sys, time
from daemon import Daemon
import logging
from codeurs_rotatifsJGUI import RotaryEncoder
import codeurs_rotatifsJGUI as rotary_encoder

import encoderd_settings as settings
import os.path

sys.path.insert(0,os.path.join("/home/pi/yoctolib_python","Sources"))
sys.path.append(os.path.join("..","yoctolib_python","Sources"))
sys.path.append(os.path.join("..","yoctolib_python","Sources","cdll"))
sys.path.insert(0, "/home/pi/Adafruit_Python_SSD1306")

import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from yoctopuce.yocto_api import *
from yoctopuce.yocto_digitalio import *
from functools import partial
import RPi.GPIO as GPIO

class affichageOLED:

	def __init__(self, Pixel=64):

# Raspberry Pi pin configuration:
		RST = None     # on the PiOLED this pin isnt used
# 128x32 ou 128x64 display with hardware I2C:
		if Pixel==32:
			self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
		elif Pixel==64:
			self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
		else:
			print("Reference nombre de ligne inconnue")
# Initialize library.
		self.disp.begin()
# Clear display.
		self.disp.clear()
		self.disp.display()
# Create blank image for drawing.

# Make sure to create image with mode '1' for 1-bit color.
		self.width = self.disp.width
		self.height = self.disp.height
		self.image = Image.new('1', (self.width, self.height))
# Get drawing object to draw on image.
		self.draw = ImageDraw.Draw(self.image)
# Draw a black filled box to clear the image.
		self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
		padding = -4
		self.top = padding
		self.bottom = self.height-padding
# Move left to right keeping track of the current x position for drawing shapes.
		self.x = 2
# Load default font.
		self.fontstandard = ImageFont.load_default()
# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
		self.font = ImageFont.truetype('/home/pi/3205-codeurs-chariots/Starjedi.ttf', 16)
#        self.petiteFont=ImageFont.truetype('/home/pi/3189-capteurs-pressions/Starjedi.ttf', 10)
#        self.trespetiteFont=ImageFont.truetype('/home/pi/3189-capteurs-pressions/Starjedi.ttf', 8)

	def affNettoie(self):
	   self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
	   self.disp.image(self.image)
	   self.disp.display()
	   return True   
   
	def affJauge(self, x1, y1, x2, y2, pourcentage=0.5):
		self.draw.rectangle((x1,y1,x2,y2),255,255)
		self.draw.rectangle((x1+int(pourcentage*(x2-x1)),y1,x2-2,y2),0,255)
		return True

	def affVal(self, valangAR=0, valangAVG=0, valangAVD=0, Mode=1):
		self.affNettoie()
		self.draw.text((self.x, self.top),"Ar: "+str(valangAR)+" deg", font=self.font, fill=255)
		self.draw.text((self.x, self.top+16),"Avg: "+str(valangAVG)+" deg", font=self.font, fill=255)
		self.draw.text((self.x, self.top+32),"Avd: "+str(valangAVD)+" deg", font=self.font, fill=255)
		#self.affJauge(0,self.top+24,self.width,self.top+52,ratioPression)
		self.draw.text((self.x, self.top+52),"CMC(c)2018"+" Mode:"+str(Mode),  font=self.fontstandard, fill=255)
		self.disp.image(self.image)
		self.disp.display()
		return True

class MyDaemon(Daemon):
	global Vcontrole_angles
	Vcontrole_angles = False
	def run(self):
		global Vcontrole_angles
		Vcontrole_angles = False
		self.mode=1
		self.setup()
		angleAVG = 0
		angleAVD = 0
		angleAR = 0
		FangAR0 = False
		FangCaroussel = 0
		#JGUI TEST
		compteur = 0
		affichage = 0
		angleARsav=0
		angleAVGsav=0
		angleAVDsav=0
		Precision = settings.PRECISION

		while True:
			for enc in self.encoders:
				steps = enc['obj'].get_cycles()
				# JGUI steps = enc['obj'].get_steps()
				if steps != 0:
					enc['angle'] += enc['calibration']*steps
		  ###self.saveAngle(enc) 
		  #self.logger.info("Encoder {}: {} movement detected. Angle is now {} degrees.".format(enc['number'],enc['name'],enc['angle']))
				if enc['number'] == 0:
					angleAVG=int(enc['angle'])
				elif enc['number'] == 1:
					angleAVD=int(enc['angle'])
				elif enc['number'] == 2:
					angleAR=int(enc['angle'])
		# zone de controle des angles un a la fois   
				if Vcontrole_angles == False :
					Vcontrole_angles = True
					FangAR0 = self.controle_angleAR (angleAVD, angleAVG, angleAR, FangAR0, 0, Precision)
					FangCaroussel = self.controle_anglesCaroussel (angleAVD, angleAVG, angleAR, FangCaroussel, Precision)
					if daemon.debug!=True:
						if self.litRelais(7) == True :
						# initialisation mode Carroussel
							self.zero(2)
							self.mode=2
						elif self.litRelais(6) == True :
						# initialisation mode roulage droit
							self.zero(1)
							self.mode=1
					Vcontrole_angles = False
			time.sleep(settings.REFRESH_RATE)
			#time.sleep(0.01)
			compteur = compteur +1
			if compteur == 30:
				if angleAR != angleARsav or angleAVG!=angleAVGsav or angleAVD!=angleAVDsav:
					self.d.affVal(angleAR,angleAVG,angleAVD)
					angleARsav=angleAR
					angleAVGsav=angleAVG
					angleAVDsav=angleAVD
					affichage = affichage +1
				compteur = 0
				

	def setup(self):
		self.d=affichageOLED(64)
		self.setupEncoders()
		#mise en mode 1 par defaut au demarrage du programme avant la radiocommande
		self.zero(mode=1)
		self.d.affNettoie()
		if daemon.debug!=True:
			self.setupMaxiIO(sys.argv)
		return

	def setupEncoders(self):
		self.encoders=[]
		enc_cnt = 0
		for enc in settings.ENCODERS:
			self.encoders.append(enc)
			# ligne JGUI
			#gpio = gaugette.gpio.GPIO()
			pinA=enc['pinA']
			pinB=enc['pinB']
			# start a monitoring thread sans gpio par JGUI
			self.encoders[enc_cnt]['obj'] = rotary_encoder.RotaryEncoder.Worker(pinA,pinB)
			self.encoders[enc_cnt]['number'] = enc_cnt
			self.encoders[enc_cnt]['obj'].start()
			#self.readAngle(enc)
			enc_cnt += 1
		self.encoder_count = enc_cnt
 # Initalisation des angles    
	def zero(self, mode):
		## positionne les angles de depart  en mode 1 droit ou mode 2 caroussel
		for enc in self.encoders:
			if enc['number'] == 0:
				#angleAVG
				if mode == 1 :
					enc['angle'] = 0.0
				elif mode == 2 :
					enc['angle'] = -110.0  
			elif enc['number'] == 1:
				#angleAVD
				if mode == 1 :     
					enc['angle'] = 0.0
				elif mode == 2 :
					enc['angle'] = 110.0 
			elif enc['number'] == 2:
				#angleAR
				if mode == 1 :     
					enc['angle'] = -20.0
				elif mode == 2 :
					enc['angle'] = 90.0
		return True

	def setupMaxiIO(self, pargv):
		if len(pargv) < 3:
			sys.exit("Parametre manquant pour initialiser IO")
			
		target = pargv[2].upper()

		### Setup the API to use local USB devices
		##errmsg = YRefParam()
		##if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
		##    sys.exit("init error" + errmsg.value)
		
		# Setup the API to virtual hub
		errmsg = YRefParam()
		if YAPI.RegisterHub("127.0.0.1", errmsg) != YAPI.SUCCESS:
			sys.exit("init error" + errmsg.value)

		if target == 'ANY':
		# retreive any Relay then find its serial #
			self.io = YDigitalIO.FirstDigitalIO()
			if self.io is None:
				die('No module connected')
			m = self.io.get_module()
			target = m.get_serialNumber()

		print('using ' + target)
		self.io = YDigitalIO.FindDigitalIO(target + '.digitalIO')

		if not (self.io.isOnline()):
			die('device not connected')

	    # lets configure the channels direction
		# bits 0..3 as output
		# bits 4..7 as input
		self.io.set_portDirection(0x0F)
		self.io.set_portPolarity(0)  # polarity set to regular
		self.io.set_portOpenDrain(0)  # No open drain

		print("Channels 0..3 are configured as outputs and channels 4..7")
		print("are configured as inputs, you can connect some inputs to ")
		print("ouputs and see what happens")

		self.io.set_portState(0)
		return


	def litRelais (self, IdRelais):
		valRelais = self.io.get_bitState(IdRelais)
		return valRelais

	def allumeRelais (self, IdRelais):
		self.io.set_bitState(IdRelais,1)
	def eteintRelais (self, IdRelais):
		self.io.set_bitState(IdRelais,0)
	def changeRelais (self, IdRelais):
		etat=self.io.get_bitState(IdRelais)
		if etat == 0 :
			self.io.set_bitState(IdRelais,1)
		else :
			self.io.set_bitState(IdRelais,0)
		return 

	def controle_angleAR(self, angAVD, angAVG, angAR, FangAR, angVoulu, Precision):
	
		if self.PresqueEgal(angAR, angVoulu, Precision)== True and FangAR == False :
			FangAR = True
			#self.d.affVal(angAR,angAVG,angAVD,self.mode)
			#client.publish("capteurs/angle/AR", str(angVoulu), qos=0, retain=False)
			if daemon.debug!=True:
				self.allumeRelais(0)
		elif self.PresqueEgal(angAR, angVoulu, Precision) == False:
			FangAR = False
			if daemon.debug!=True:
				self.eteintRelais(0)
		return FangAR

	def signe( self,entier):
		if entier != 0:
			vsigne = entier // abs(entier)
		else :
			vsigne = entier
		return vsigne

	def controle_anglesCaroussel(self, angAVD, angAVG, angAR, FangCaroussel, Precision):
		#client.publish("capteurs/angle", str(angAVG)+" "+str(angAVD)+" "+str(angAR)+" "+str(FangCaroussel)+" "+str(self.signe(angAVG+angAVD)), qos=0, retain=False)
		#if FangCaroussel != self.signe(angAVG+angAVD) :    
		if self.PresqueEgal(angAVG + angAVD, 0 , Precision) == True :
			#client.publish("capteurs/angle/avant", "Caroussel", qos=0, retain=False)
			if daemon.debug!=True:
				self.eteintRelais(1)
				self.eteintRelais(2)
			FangCaroussel = 0
		elif abs(angAVG) > abs(angAVD) and FangCaroussel != self.signe(angAVG+angAVD):
			# roue avant gauche en retard on allume son relais 2
			#client.publish("capteurs/angle/Caroussel", "AVG en retard", qos=0, retain=False)
			if daemon.debug!=True:
				self.allumeRelais(2)
				self.eteintRelais(1)
			FangCaroussel = self.signe(angAVG+angAVD)
			self.d.affVal(angAR,angAVG,angAVD,self.mode)
		elif abs(angAVG) < abs(angAVD) and FangCaroussel != self.signe(angAVG+angAVD):
			# roue avant droite en retard on allume son relais 1
			#client.publish("capteurs/angle/Caroussel", "AVD en retard", qos=0, retain=False)
			if daemon.debug!=True:
				self.allumeRelais(1)
				self.eteintRelais(2)
			FangCaroussel = self.signe(angAVG+angAVD)
			self.d.affVal(angAR,angAVG,angAVD,self.mode)
		##FangCaroussel = self.signe(angAVG+angAVD) 
		return FangCaroussel

	def PresqueEgal( self, angA, angB, Precision):
		Vpresquegal = False
		if abs(abs(angA)-abs(angB)) <= Precision:
			Vpresquegal = True
		return Vpresquegal

if __name__ == "__main__":
	daemon = MyDaemon(settings.PID_FILE)
	if len(sys.argv) == 3:
		if 'start' == sys.argv[1]:
			daemon.debug=False
			daemon.start()
		if 'foreground' == sys.argv[1]:# for debugging
			daemon.debug=True
			daemon.start()
		elif 'stop' == sys.argv[1]:
			#GPIO.cleanup() pas dans le bon process
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		else:
			print( "Unknown command")
			sys.exit(2)
			sys.exit(0)
	else:
		print ("usage: ",sys.argv[0], " start|stop|restart|foreground NomduMaxiIOV2 ") 
		sys.exit(2)
