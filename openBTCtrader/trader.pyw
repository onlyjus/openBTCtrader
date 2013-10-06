# -*- coding: utf-8 -*-
"""
If you find this software useful please donate BTC to:
    1MBGoL4bTtkUNK9mATosdgb8X9V6QA7LiV


openBTCtrader License Agreement (MIT License)
--------------------------------------

Copyright (c) 2013 Justin Weber

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

__version__ = '0.1'
__license__ = __doc__
__project_url__ = 'https://github.com/onlyjus/openBTCtrader'

#python core imports
import sys, datetime, hashlib, time, random, json
from Crypto.Cipher import AES
from Crypto import Random

#additional libraries
import pandas
from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
#import numpy as np

#QtDesigner python files
from trader_designer import Ui_MainWindow

#market API modules
from apis import mtGoxAPI
marketList = {}
marketList['MtGox'] = mtGoxAPI.Mtgox

availableMarkets = set(marketList.keys())



class mainWindow(QtGui.QMainWindow):
    '''
    Main window class handeling all gui interactions
    '''
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('BTC Trader')

        self.markets={}

        self.ui.toolButton_New.pressed.connect(self.newMarket)
        self.ui.toolButton_Delete.pressed.connect(self.deleteMarket)
        self.ui.toolButtonLoadAPIs.pressed.connect(self.loadAPIdata)
        self.ui.toolButtonSaveAPIs.pressed.connect(self.saveAPIdata)

        # matplotwidget
        self.mplWidget = DynamicMplCanvas(self.ui.frame, width=5, height=4, dpi=100)

        self.ui.gridLayout_mpl.addWidget(self.mplWidget)


    def loadAPIdata(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Select Data File to Open', filter = '*.dat')

        if len(fname)<1:
            return

        password, ok = QtGui.QInputDialog.getText(self, "Enter Password", "Password:", QtGui.QLineEdit.Password, "")
        if ok:

            #read salt
            f = open('./salt.dat','r')
            salt = f.read()
            f.close()

            #read encrypted file
            f = open(str(fname),'r')
            d = f.read()
            f.close()

            #decrypt file
            hash_pass = hashlib.sha256(password + salt).digest()
            decryptor = AES.new(hash_pass, AES.MODE_CBC,d[:AES.block_size])
            text = decryptor.decrypt(d[AES.block_size:])

            #read data
            data = json.loads(text)

            for market in data:
                self.newMarket(data = {'market':market, 'key':data[market]['key'],
                                       'secret':data[market]['secret'],
                                       'sample':data[market]['sample']})

        else:
            return

        #self.markets

    def saveAPIdata(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Select Data File to Open', filter = '*.dat')

        if len(fname)<1:
            return


        #look for salt, if no salt, generate salt.
        try:
            f = open('./salt.dat','r')
            salt = f.read()
            f.close()
        except:
            pre_salt = str(time.time() * random.random() * 1000000) + 'H7gfJ8756Jg7HBJGtbnm856gnnblkjiINBMBV734'
            salt = hashlib.sha512(pre_salt).digest()
            f = open('./salt.dat','w')
            f.write(salt)
            f.close()

        #Ask for password
        while True:
            password1, ok = QtGui.QInputDialog.getText(self, "Enter Password", "Password:", QtGui.QLineEdit.Password, "")
            if len(password1)<2:
                msgBox = QtGui.QMessageBox.warning(self,'Error', 'Error: Password must be greater\nthen two characters')
            else:
                if ok:
                    password2, ok = QtGui.QInputDialog.getText(self, "Re-Enter Password", "Re-Enter:", QtGui.QLineEdit.Password, "")
                    if ok:
                        if password1 == password2:
                            password = password1
                            break
                        else:
                            msgBox = QtGui.QMessageBox.warning(self,'Error', 'Error: Passwords do not match!')
                    else:
                        return
                else:
                    return

        #Generate file
        hash_pass = hashlib.sha256(password + salt).digest()
        iv = Random.new().read(AES.block_size)
        encryptor = AES.new(hash_pass, AES.MODE_CBC,iv)

        saveData = {}
        for market in self.markets.keys():
            saveData[market] = {'key':self.markets[market]['key'],
                                'secret':self.markets[market]['secret'],
                                'sample':str(self.markets[market]['sample'])}

        text = json.dumps(saveData)

        #pad the text
        pad_len = 16 - len(text)%16
        text += " " * pad_len
        ciphertext = iv + encryptor.encrypt(text)   #prepend the iv parameter to the encrypted data

        #save encrypted file
        f = open(str(fname),'w')
        f.write(ciphertext)
        f.close()

    def newMarket(self, data = None):
        '''
        Create a new market entry.
        '''

        rows = self.ui.tableWidget_APIs.rowCount()
        self.ui.tableWidget_APIs.insertRow(rows)

        cob = QtGui.QComboBox(self.ui.tableWidget_APIs)
        cob.addItems(marketList.keys())
        if data:
            cob.setCurrentIndex(marketList.keys().index(data['market']))
        self.ui.tableWidget_APIs.setCellWidget(rows, 0, cob)

        keyEdit = QtGui.QLineEdit()
        keyEdit.setEchoMode(QtGui.QLineEdit.Password)
        keyEdit.setMaximumWidth(120)
        if data:
            keyEdit.setText(data['key'])
        self.ui.tableWidget_APIs.setCellWidget(rows, 1, keyEdit)
        secEdit = QtGui.QLineEdit()
        secEdit.setEchoMode(QtGui.QLineEdit.Password)
        secEdit.setMaximumWidth(120)
        if data:
            secEdit.setText(data['secret'])
        self.ui.tableWidget_APIs.setCellWidget(rows, 2, secEdit)
        samEdit = QtGui.QLineEdit()
        samEdit.setMaximumWidth(140)
        if data:
            samEdit.setText(data['sample'])
        self.ui.tableWidget_APIs.setCellWidget(rows, 3, samEdit)

        lastSample = QtGui.QLineEdit('NA')
        lastSample.setEnabled(False)
        self.ui.tableWidget_APIs.setCellWidget(rows, 4, lastSample)

        btn = QtGui.QPushButton(self.ui.tableWidget_APIs)
        btn.setText('Start')
        btn.pressed.connect(lambda: self.startMarket(rows, btn))
        self.ui.tableWidget_APIs.setCellWidget(rows, 5, btn)

        self.ui.tableWidget_APIs.resizeColumnsToContents()

    def deleteMarket(self):
        '''
        Delete market entry.
        '''
        currRow = self.ui.tableWidget_APIs.currentRow()
        market = str(self.ui.tableWidget_APIs.cellWidget(currRow,0).currentText())
        self.ui.tableWidget_APIs.removeRow(currRow)

        itm = None
        for i in range(self.ui.treeWidgetValues.topLevelItemCount()):
            if market == self.ui.treeWidgetValues.topLevelItem(i).text(0):
                itm = i
                break

        if type(itm) != type(None):
            root = self.ui.treeWidgetValues.invisibleRootItem()
            root.removeChild(self.ui.treeWidgetValues.topLevelItem(itm))

        if market in self.markets.keys():
            self.markets[market]['timer'].stop()

    def startMarket(self, row, btn):
        '''
        Start market sampler.
        '''

        market = str(self.ui.tableWidget_APIs.cellWidget(row,0).currentText())
        key = str(self.ui.tableWidget_APIs.cellWidget(row,1).text())
        secret = str(self.ui.tableWidget_APIs.cellWidget(row,2).text())
        sample = float(self.ui.tableWidget_APIs.cellWidget(row,3).text())

        apiObj = marketList[market](key=key, secret=secret)

        self.markets[market] = {'apiObj':apiObj, 'row':row, 'key':key, 'secret':secret, 'sample':sample}

        btn.deleteLater()
        self.ui.tableWidget_APIs.setCellWidget(row, 5, QtGui.QLabel('Running'))

        # Get First ticker data
        data = apiObj.getTicker()
        sampleTime = datetime.datetime.now()
        self.ui.tableWidget_APIs.cellWidget(row,4).setText(datetime.datetime.strftime(sampleTime,'%Y-%m-%d %H:%M:%S'))
        dataFrame = pandas.DataFrame(data = [data.values()], columns = data.keys())
        dataFrame.index = [sampleTime]
        self.markets[market]['data'] = dataFrame

        newEntry = QtGui.QTreeWidgetItem([market])

        keyList = data.keys()
        keyList.remove('currency')
        for key in keyList:
            child = QtGui.QTreeWidgetItem(newEntry)
            child.setText(0, key)
            child.setText(1, '{0:.2f}'.format(data[key]))
            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
            child.setCheckState(0, QtCore.Qt.Checked)

        itm = self.ui.treeWidgetValues.topLevelItemCount()
        self.ui.treeWidgetValues.insertTopLevelItem(itm, newEntry)

        #timer
        self.markets[market]['timer'] = QtCore.QTimer()
        self.markets[market]['timer'].timeout.connect(lambda: self.refreshData(market))
        self.markets[market]['timer'].start(sample*1000)

    def refreshData(self, market):
        '''
        Get new ticker data, refresh GUI.
        '''

        for i in range(self.ui.tableWidget_APIs.rowCount()):
            if market == str(self.ui.tableWidget_APIs.cellWidget(i,0).currentText()):
                row = i
                break

        data = self.markets[market]['apiObj'].getTicker()
        sampleTime = datetime.datetime.now()
        self.ui.tableWidget_APIs.cellWidget(row,4).setText(datetime.datetime.strftime(sampleTime,'%Y-%m-%d %H:%M:%S'))
        dataFrame = pandas.DataFrame(data = [data.values()], columns = data.keys())
        dataFrame.index = [sampleTime]
        self.markets[market]['data'] = self.markets[market]['data'].append(dataFrame)

        for i in range(self.ui.treeWidgetValues.topLevelItemCount()):
            if market == self.ui.treeWidgetValues.topLevelItem(i).text(0):
                itm = i
                break

        topItm = self.ui.treeWidgetValues.topLevelItem(itm)
        child_count = topItm.childCount()
        keyList = []
        for i in range(child_count):
            item = topItm.child(i)
            key = str(item.text(0))
            if item.checkState(0):
                keyList.append(key)
            item.setText(1, '{0:.2f}'.format(data[key]))

        self.mplWidget.update_figure(self.markets[market]['data'], keyList)

class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.set_facecolor('lightgrey')
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

class DynamicMplCanvas(MplCanvas):
    """A canvas that updates itself every second with a new plot."""
    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)


    def compute_initial_figure(self):
         self.axes.plot([0, 1, 2, 3], [1, 2, 0, 4], 'r')
         self.axes.grid()
         self.axes.set_ylabel('Price')

    def update_figure(self, data, keys):

        for key in keys:
            self.axes.plot_date(data.index, data[key], '-')

        self.axes.grid()
        self.draw()



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    BTCTrader = mainWindow()
    BTCTrader.show()
    app.exec_()
