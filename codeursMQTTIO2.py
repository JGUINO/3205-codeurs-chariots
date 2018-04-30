#!/usr/bin/env python3

################################################################################
# 
# codeursMQTTIO2.py is a python based daemon for persistant monitoring of the state of
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
from codeurs_rotatifs import RotaryEncoder
import codeurs_rotatifs as rotary_encoder
# JGUI

import gaugette.gpio
#import gaugette.platform
import paho.mqtt.client as mqtt
#from maxi02IO import Maxi02IO

import encoderd_settings as settings
import os.path

#JGUI MaxiIO
#add ../yoctolib_python/Sources to the PYTHONPATH
sys.path.insert(0,os.path.join("/home/pi/yoctolib_python","Sources"))
sys.path.append(os.path.join("..","yoctolib_python","Sources"))
sys.path.append(os.path.join("..","yoctolib_python","Sources","cdll"))

from yocto_api import *
from yocto_digitalio import *
from functools import partial
#import RPi.GPIO as GPIO

def on_connect(client, userdata, flags, rc):
      userdata.logger.info("Connected with result code "+str(rc))
      
def on_message(client, userdata, msg):
      userdata.logger.info(msg.topic+" "+str(msg.payload))
  
def on_publish(client, obj , mid):
      obj.logger.debug("publication reussie")

client=mqtt.Client()

class MyDaemon(Daemon):
  global Vcontrole_angles
  Vcontrole_angles = False
  def run(self):
    global Vcontrole_angles
    Vcontrole_angles = False
    self.setup()
    angleAVG = 0
    angleAVD = 0
    angleAR = 0
    FangAR0 = False
    FangCaroussel = 0
    #JGUI TEST
    compteur = 0
    Precision = settings.PRECISION
    
    while True:
      for enc in self.encoders:
        steps = enc['obj'].get_cycles()
        # JGUI steps = enc['obj'].get_steps()
        if steps != 0:
          enc['angle'] += enc['calibration']*steps
          self.saveAngle(enc) 
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
            Vcontrole_angles = False
            if self.litRelais(7) == True :
                # initialisation mode Carroussel
                self.zero(2)
            if self.litRelais(6) == True :
                # initialisation mode roulage droit
                self.zero(1)
      time.sleep(settings.REFRESH_RATE)
      #time.sleep(0.01)
      compteur = compteur +1
      if compteur  == 1000
          client.publish("capteurs/angle","angle AVG "+str(angleAVG)+" angleAVD "+str(angleAVD)+ " angle AR "+str(angleAR),qos=0, retain=False)
          compteur = 0

  def setup(self):
    with open(os.path.join(settings.DIR,'testlog.log'),'w') as log:
      log.write("started\n")
    self.setupLogger()
    #JGUI
    self.setupConnect()
    self.setupEncoders()
    self.logger.info("setups encodeurs finis")
    self.setupMaxiIO(sys.argv)
    return
        
  def setupConnect(self):
     client.reinitialise()
     client.user_data_set(self)
     client.on_connect = on_connect
     client.on_message = on_message
     client.on_publish = on_publish
     client.connect("localhost", 1883, 60)
     client.loop_start()
     client.publish("capteurs/angle", "Demarrage des capteurs", qos=0, retain=False)
         

  def setupLogger(self):
    pass
    # set up logger
    self.logger = logging.getLogger(__name__)
    #self.logger.setLevel(logging.DEBUG)
    self.logger.setLevel(logging.INFO)
    # create a file handler for the logger
    fh = logging.FileHandler(settings.LOG_FILE)
    #fh.setLevel(logging.DEBUG)
    fh.setLevel(logging.INFO)
    # format logging
    fformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fformatter)
    self.logger.addHandler(fh)

  def setupEncoders(self):
    self.encoders=[]
    enc_cnt = 0
    for enc in settings.ENCODERS:
      self.encoders.append(enc)
      # ligne JGUI
      gpio = gaugette.gpio.GPIO()
      pinA=enc['pinA']
      pinB=enc['pinB']
      # start a monitoring thread avec gpio par JGUI
      self.encoders[enc_cnt]['obj'] = rotary_encoder.RotaryEncoder.Worker(gpio,pinA,pinB)
      self.encoders[enc_cnt]['number'] = enc_cnt
      self.encoders[enc_cnt]['obj'].start()
      self.logger.info("Encoder {}: {} registered. Worker thread started.".format(enc_cnt,enc['name']))
      client.publish("capteurs/angle/"+str(enc['name'])+str(enc_cnt),"Demarrage encodeur", qos=0, retain=False)
      # read recorded angle if log file exists
      self.readAngle(enc)

      enc_cnt += 1

    self.encoder_count = enc_cnt
    self.logger.info("Registered encoders: {}".format(str(enc_cnt)))

  def readAngle(self, encoder):
    try: 
      with open(encoder['logfile'], 'r') as fi:
        encoder['angle'] = float(fi.readline())
    except:
      encoder['angle'] = 0.0
      self.saveAngle(encoder)
    msg = "Encoder: {}: {} angle set to {} degrees."
    self.logger.info(msg.format(encoder['number'],encoder['name'],encoder['angle']))
    return encoder['angle']

  def saveAngle(self, encoder):
    angle = encoder['angle']
    client.publish("capteurs/angle/"+str(encoder['name'])+str(encoder['number']), str(int(angle)), qos=0, retain=False)
    with open(encoder['logfile'], 'w') as fo:
      fo.write(str(angle))
    self.logger.debug("Encoder: {}: {} angle recorded as {} degrees.".format(encoder['number'],encoder['name'],angle))
  
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
      
       self.saveAngle(enc)

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

#  def gererelais(self):
#        outputdata = 0
#        while self.io.isOnline():
#            inputdata = self.io.get_portState()  # read port values
#            line = ""  # display part state value as binary
#            for i in range(0, 8):
#                if (inputdata & (128 >> i)) > 0:
#                    line += '1'
#                else:
#                    line += '0'
#            YAPI.Sleep(500, errmsg)
#
#        print("Module disconnected")
#        YAPI.FreeAPI()

  def controle_angleAR(self, angAVD, angAVG, angAR, FangAR, angVoulu, Precision):
    
    if self.PresqueEgal(angAR, angVoulu, Precision)== True and FangAR == False :
        FangAR = True
        client.publish("capteurs/angle/AR", str(angVoulu), qos=0, retain=False)
        self.allumeRelais(0)
    elif self.PresqueEgal(angAR, angVoulu, Precision) == False:
        FangAR = False
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
            self.eteintRelais(1)
            self.eteintRelais(2)
            FangCaroussel = 0
        elif abs(angAVG) > abs(angAVD) and FangCaroussel != self.signe(angAVG+angAVD):
            # roue avant gauche en retard on allume son relais 2
            #client.publish("capteurs/angle/Caroussel", "AVG en retard", qos=0, retain=False)
            self.allumeRelais(2)
            self.eteintRelais(1)
            FangCaroussel = self.signe(angAVG+angAVD)
        elif abs(angAVG) < abs(angAVD) and FangCaroussel != self.signe(angAVG+angAVD):
            # roue avant droite en retard on allume son relais 1
            #client.publish("capteurs/angle/Caroussel", "AVD en retard", qos=0, retain=False)
            self.allumeRelais(1)
            self.eteintRelais(2)
            FangCaroussel = self.signe(angAVG+angAVD)
 
        ##FangCaroussel = self.signe(angAVG+angAVD) 

        return FangCaroussel

  def PresqueEgal( self, angA, angB, Precision):
      Vpresquegal = False
      
      if abs(abs(angA)-abs(angB)) <= Precision:
          Vpresquegal = True
      return Vpresquegal

if __name__ == "__main__":
  daemon = MyDaemon(settings.PID_FILE)
  #daemon = MyDaemon('/tmp/daemon-example.pid')
  if len(sys.argv) == 3:
    if 'start' == sys.argv[1]:
      daemon.start()
    if 'foreground' == sys.argv[1]:# for debugging
      daemon.run()
    elif 'stop' == sys.argv[1]:
      #client.disconnect()
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
