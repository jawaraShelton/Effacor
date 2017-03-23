import clr
clr.AddReference('IronPython', 'System.Windows.Forms')

import datetime
import os
import random
import wpf

from IronPython.Compiler import CallTarget0
from System import Action
from System.Windows import *
from System.Windows.Forms import OpenFileDialog, DialogResult
from System.Windows.Threading import Dispatcher
from time import localtime, strftime

class MyWindow(Window):    
    """ Primary UI for the Effacor Utility """
    
    def __init__(self):
        wpf.LoadComponent(self, 'EffacorWPF.xaml')
        self.conDict = {}
        mapControls(self.Content.Children, self.conDict, False)
        
        self.filez = []

        # Used for debugging mapControls()
        # -----
        # fObj = open("F:\ControlList.out", "w")
        # for x in self.conDict.keys():
        #     fObj.write(str(x) + ": " + str(self.conDict[x]) + "\n")        
        # fObj.close()

        self.conDict['Gut'].IsChecked = True

        self.conDict['New'].Click+=self.__createNew
        self.conDict['Add'].Click+=self.__addFileToTask
        self.conDict['GO'].Click+=self.__executeTask
        self.conDict['_Exit'].Click+=self.__exit

        self.conDict['showAbout'].Click+=self.__showAboutEffacor
        
        self.conDict['dGrid'].Drop+=self._drag_drop

    def _drag_drop(self, caller, eventArgs):
        fileList = eventArgs.Data.GetData(DataFormats.FileDrop, False)           
        for x in fileList:
            self.conDict['dGrid'].Items.Add(x)

    def __addFileToTask(self, caller, eventArgs):
        oDialog = OpenFileDialog()

        oDialog.Title = 'Select File to Erase'
        oDialog.Filter = 'All files (*.*)|*.*'

        if oDialog.ShowDialog() == DialogResult.OK:
            self.conDict['dGrid'].Items.Add(oDialog.FileName)

    def __executeTask(self, caller, eventArgs):
        methods=['DoD', 'Gut', 'PRN', 'RCM', 'SP0', 'SP1']
        
        dGrid = self.conDict['dGrid']

        for x in methods:
            if self.conDict[x].IsChecked == True:
                method = x

        # Erase all files in Datagrid
        for x in range(0, dGrid.Items.Count):
            
            # Overwrite file ...
            fObj = open(dGrid.Items[x], "rb+")
            fSiz = os.path.getsize(dGrid.Items[x])

            if method=='DoD':
                efface_viaDoD5220_22M(fObj, fSiz)
            elif method=='Gut':
                efface_viaGutmann(fObj, fSiz)
            elif method=='PRN':
                SinglePassOverwrite(fObj, fSiz, 3)
            elif method=='RCM':
                efface_viaRCMP_TSSIT_OPS11(fObj, fSiz)
            elif method=='SP0':
                SinglePassOverwrite(fObj, fSiz, 0)                
            elif method=='SP1':
                SinglePassOverwrite(fObj, fSiz, 1)
        
            fObj.close()
         
            # Erase the file ...
            os.remove(dGrid.Items[x])                            

        # Clean up the DataGrid
        dGrid.Items.Clear()
        
    def __exit(self, caller, eventArgs):
        self.Close()

    def __createNew(self, caller, eventArgs):
       self.conDict['dGrid'].Items.Clear()

    def __showAboutEffacor(self, caller, eventArgs):
        AboutWindow().Show()

class AboutWindow(Window):
    def __init__(self):
        wpf.LoadComponent(self, 'EffacorAbout.xaml')
        
def main():
    xaml_UI = MyWindow()
    Application().Run(xaml_UI)        

def mapControls(winObj, dict, items):
    if items == True:
        for x in winObj.Items: 
            dict[x.Name] = x
            if hasattr(x, "Items") and x.Items.Count > 0:
                mapControls(x, dict, True)        
    else:
        for x in winObj:
            if "System.Windows.Controls." in str(x) and hasattr(x,"Name") and x.Name.Length>0:
                dict[x.Name] = x
            if hasattr(x, "Items") and x.Items.Count > 0:
                mapControls(x, dict, True) 
    
def SinglePassOverwrite(fObj, fSiz, oneZeroRandom):
    # Performs a single pass over the data.
    #   - If oneZeroRandom is a 1 or 0, it writes that. Otherwise, it randomizes 
    #     the output (I use "3" for that).
    #   - By nature, function serves as the Single Pass 0, Single Pass 1, and PRNG 
    #     algorithms as well (use oneZeroRandom = 3 to use the PRNG algorithm).

    fObj.seek(0)
    for x in range(0, fSiz):
        if oneZeroRandom in (0,1):
            fObj.write(chr(oneZeroRandom))
        else:
            fObj.write(chr(random.randrange(0,255)))

def efface_viaDoD5220_22M(fObj, fSiz):
    dOdPat = [0,1,3,0,1,0,3]
    for x in range(0, 6):
        SinglePassOverwrite(fObj, fSiz, dOdPat[x])

def efface_viaRCMP_TSSIT_OPS11(fObj, fSiz):
    rcmpPat = [1,0,1,0,1,0,3]
    for x in range(0, 6):
        SinglePassOverwrite(fObj, fSiz, rcmpPat[x])

def efface_viaGutmann(fObj, fSiz):

    # gPat stores the pre-determined patterns used during the overwrite process used
    #   in the gutmann method.
    gPat = [[0x55], [0xAA], [0x92,0x49,0x24], [0x49,0x24,0x92], [0x24,0x92,0x49], [0x00], [0x11], [0x22], [0x33]]
    gPat[len(gPat):] = [[0x44], [0x55], [0x66], [0x77], [0x88], [0x99], [0xAA], [0xBB], [0xCC], [0xDD], [0xEE]]
    gPat[len(gPat):] = [[0xFF], [0x92,0x49,0x24], [0x49,0x24,0x92], [0x24,0x92,0x49], [0x6D,0xB6,0xDB]]
    gPat[len(gPat):] = [[0xB6,0xDB,0x6D], [0xDB,0x6D,0xB6]]

    fPass = 0

    # Make 4 passes writing over the data
    #   Each pass overwrites the data in the file with random data.
    #   This is the first step in the Gutmann process.
    for x in range(0, 3):
        SinglePassOverwrite(fObj, fSiz, 3)
        fPass = fPass + 1
    
    # Make 27 passes writing over the data using a set of 27 pre-determined patterns.
    #   The ORDER those patterns are written in is randomized. 
    #   I'm determining that order here.
    x = random.randrange(0,26)
    gPatOrder = []
    while len(gPatOrder) < 26:
        # It is necessary to check to insure that a pattern is not selected twice.
        #   Hence the additional while clause.
        while x in gPatOrder:
            x = random.randrange(0,26)
            print(x)
        gPatOrder[len(gPatOrder):] = [x]

    # Make the 27 passes to overwrite the data.
    #   Use the pre-determined, pseudo-random order as determined by gPatOrder.
    for x in gPatOrder:
        fObj.seek(0)
        for y in range(0, fSiz):
            fObj.write(chr(gPat[x][y%len(gPat[x])]))
        fPass = fPass + 1

    # Make 4 passes writing over the data
    #   Each pass overwrites the data in the file with random data.
    #   This is the final step in the Gutmann process.
    for x in range(0, 3):
        SinglePassOverwrite(fObj, fSiz, 3)
        fPass = fPass + 1

if __name__ == '__main__':
	main()