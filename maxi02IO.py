import os, sys, tkinter
# add ../../Sources to the PYTHONPATH
#sys.path.append(os.path.join("..", "..", "Sources"))
sys.path.append(os.path.join("..", "yoctolib_python","Sources"))

from tkinter import *
from tkinter import scrolledtext
from yocto_api import *
from yocto_digitalio import *
from functools import partial
#import RPi.GPIO as GPIO

import time

def dieg(self, msg):
        sys.exit(msg + ' (check USB cable)')


class Maxi02IO :
    die = dieg
    #def die(msg):
     #   sys.exit(msg + ' (check USB cable)')

    def __init__(self, pargv):
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

    #Affichage dans une fenetre
##        def ouvreFenetres
##        fenetre = Tk()
##        fenetre.title("Etats des relais")
##        fenetre.geometry('350x200')
##        txt= scrolledtext.ScrolledText(fenetre,width=40,height=10)
##        txt.grid(column=0,row=1)
##        fenetreCommandes = Tk()
##        fenetreCommandes.title("Gestion de relais")
##        fenetreCommandes.geometry('350x200')
        if not (self.io.isOnline()):
            die('device not connected')

  #      initRelais()

   # def initRelais():
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
        #self.changeRelais(0)
        return
    
# fonction ajoute_un pour allumer un relais
        
    def ajoute_un (self):
        entree = self.io.get_portState()
        outputdata = (entree + 1)%16
        self.io.set_portState( outputdata)
        return outputdata


    def changeRelais (self, IOV, IdRelais):
        io=IOV
        die = dieg
        #die(self,'on essaye de rentrer dans change relais')
        if not (IOV.isOnline()):
            die(self,'device not connected')
        die('on rentre dans changeRelais')    

        etat=self.io.get_bitState(IdRelais)
        if etat == 0 :
            self.io.set_bitState(IdRelais,1)
        else :
            self.io.set_bitState(IdRelais,0)
        ##    etat1 = IntVar()
        ##    etat1 = io.get_bitState(0)
        ##    etat1 = var1.get()
        ##    print("Var1"+str(etat1))
        ##    etat2= io.get_bitState(1)
        ##    etat3= io.get_bitState(2)
        ##    etat4= io.get_bitState(3)
        ##    print("etat1"+str(etat1))
        ##    io.set_bitState(0, etat1)
    
        #print("changement des relais"+str(IdRelais)+str(etat))
        #io.set_bitState(3,1)
        #modifdata = (modifdata+(IdRelais+1))%16
        #io.set_portState(modifdata)
        return 

##    def fermefenetres () :
##        fenetre.destroy()
##        fenetreCommandes.destroy()
##        return

    def gererelais(self):
        outputdata = 0
        while self.io.isOnline():
            inputdata = self.io.get_portState()  # read port values
            line = ""  # display part state value as binary
            for i in range(0, 8):
                if (inputdata & (128 >> i)) > 0:
                    line += '1'
                else:
                    line += '0'
        
            
##            txt.insert(INSERT, ' port value = ' + line)
##     
##            fenetre.update_idletasks()
##            fenetre.update()
##        
##            fenetreCommandes.update_idletasks()
##            fenetreCommandes.update()
            YAPI.Sleep(500, errmsg)

        print("Module disconnected")
        YAPI.FreeAPI()

##    menubar = Menu(fenetre)
##    menu1 = Menu(menubar, tearoff=0)
##    menu1.add_command(label="demarrer", command=gererelais)
##    menu1.add_command(label="quitter", command=fermefenetres)
##    menubar.add_cascade(label="Commandes",menu=menu1)
##    button = Button(fenetreCommandes, text = "Ajoute un",command= ajoute_un)
##    button.pack(side = BOTTOM)
##    var1 = IntVar()
##    var2 = IntVar()
##    var3 = IntVar()
##    var4 = IntVar()
##    CB1 = Checkbutton ( fenetreCommandes, text = "Relais 1 : ", variable = var1, command= lambda : changeRelais(0))
##    CB1.pack(side = TOP)
##
##    CB2 = Checkbutton ( fenetreCommandes, text = "Relais 2 : ", command =lambda : changeRelais(1), variable = var2)
##    CB2.pack(side = TOP)
##
##    CB3 = Checkbutton ( fenetreCommandes, text = "Relais 3 : ", command = lambda : changeRelais(2), variable = var3)
##    CB3.pack(side = TOP)
##
##    CB4 = Checkbutton ( fenetreCommandes, text = "Relais 4 : ", command = lambda : changeRelais(3), variable = var4)
##    CB4.pack(side = TOP)
##    fenetre.config(menu=menubar)

 #   initRelais()
  #  gererelais()
