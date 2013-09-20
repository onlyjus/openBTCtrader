# -*- coding: utf-8 -*-

#python core imports
import sys, datetime, hashlib, time, random

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




        self.markets



    def saveAPIdata(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Select Data File to Open', filter = '*.dat')

        if len(fname)<1:
            return

        try:
            f = open('./salt.txt','r')
            salt = f.read()
            f.close()
        except:
            pre_salt = str(time.time() * random.random() * 1000000) + 'H7gfJ8756Jg7HBJGtbnm856gnnblkjiINBMBV734'
            salt = hashlib.sha512(pre_salt).digest()
            f = open('./salt.txt','w')
            f.write(salt)
            f.close()


    def newMarket(self):
        '''
        Create a new market entry.
        '''
        rows = self.ui.tableWidget_APIs.rowCount()
        self.ui.tableWidget_APIs.insertRow(rows)

        cob = QtGui.QComboBox(self.ui.tableWidget_APIs)
        cob.addItems(marketList.keys())
        self.ui.tableWidget_APIs.setCellWidget(rows, 0, cob)

        keyEdit = QtGui.QLineEdit()
        keyEdit.setEchoMode(QtGui.QLineEdit.Password)
        keyEdit.setMaximumWidth(120)
        self.ui.tableWidget_APIs.setCellWidget(rows, 1, keyEdit)
        secEdit = QtGui.QLineEdit()
        secEdit.setEchoMode(QtGui.QLineEdit.Password)
        secEdit.setMaximumWidth(120)
        self.ui.tableWidget_APIs.setCellWidget(rows, 2, secEdit)
        samEdit = QtGui.QLineEdit()
        samEdit.setMaximumWidth(140)
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
