# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PrintPineWiltDiseaseCompositionDialog
                                 A QGIS plugin
 소나무재선충병 구성 출력 자동화
                             -------------------
        begin                : 2018-04-20
        git sha              : $Format:%H$
        copyright            : (C) 2018 by iGiS
        email                : idscorea1@naver.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtPrintSupport import *

from qgis.core import *
from qgis.utils import *

from .layer_utils import *
from .boundary_utils import *
from .layout_utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'print_pwd_composition_dialog_base.ui'))

class PrintPineWiltDiseaseCompositionDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PrintPineWiltDiseaseCompositionDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.progressDialog=None
        
        self.comboBox_SiDo.currentIndexChanged.connect(self.comboBox_SiDo_currentIndexChanged)
        self.comboBox_SGG.currentIndexChanged.connect(self.comboBox_SGG_currentIndexChanged)
        self.comboBox_EMD.currentIndexChanged.connect(self.comboBox_EMD_currentIndexChanged)
        
        self.groupBox_SetDistrict.toggled.connect(self.groupBox_SetDistrict_toggled)
        self.groupBox_SetCoordinateAndScale.toggled.connect(self.groupBox_SetCoordinateAndScale_toggled)
        
        self.radioButton_PDF.toggled.connect(self.radioButton_toggled)
        self.radioButton_PNG.toggled.connect(self.radioButton_toggled)
        self.radioButton_Printer.toggled.connect(self.radioButton_toggled)
        
        self.pushButton_SetCoordinate.clicked.connect(self.pushButton_SetCoordinate_Clicked)
        self.pushButton_SetSaveFilePath.clicked.connect(self.pushButton_setSavePath_Clicked)
        
        self.pushButton_Apply.clicked.connect(self.pushButton_Apply_Clicked)
        self.pushButton_Print.clicked.connect(self.pushButton_Print_Clicked)
        
    
    def showEvent(self, event):
        super(PrintPineWiltDiseaseCompositionDialog, self).showEvent(event)
            
        self.initializeComboBox()
        
        self.initializePrinterComboBox()
        
    def initializePrinterComboBox(self):
        defaultPrinterInfo = QPrinterInfo.defaultPrinter()
        
        printerInfos = QPrinterInfo.availablePrinters()
        for printerInfo in printerInfos:
            self.comboBox_Printer.addItem(printerInfo.printerName(), printerInfo)
            
        index = self.comboBox_Printer.findData(defaultPrinterInfo)
        if index >= 0:
            self.comboBox_Printer.setCurrentIndex(index)
        
    def initializeComboBox(self):
        list=getBoundarySDList()
        for boundary in list:
            self.comboBox_SiDo.addItem(boundary.name, boundary)
    
    def comboBox_SiDo_currentIndexChanged(self):
        self.comboBox_SGG.setEnabled(False)
        self.comboBox_SGG.clear()
        index = self.comboBox_SiDo.currentIndex()
        if index >= 0 :
            sido = self.comboBox_SiDo.itemData(index)
            children=sido.getChildren()
            if len(children)>0:
                self.comboBox_SGG.setEnabled(True)
                for sgg in children:
                    self.comboBox_SGG.addItem(sgg.name, sgg)
            
    def comboBox_SGG_currentIndexChanged(self):
        self.comboBox_EMD.setEnabled(False)
        self.comboBox_EMD.clear()
        index = self.comboBox_SGG.currentIndex()
        if index >= 0:
            sgg = self.comboBox_SGG.itemData(index)
            if sgg.name:
                children=sgg.getChildren()
                if len(children)>0:
                    self.comboBox_EMD.setEnabled(True)
                    for emd in children:
                        self.comboBox_EMD.addItem(emd.name, emd)
        
    def comboBox_EMD_currentIndexChanged(self):
        self.comboBox_Ri.setEnabled(False)
        self.comboBox_Ri.clear()
        index = self.comboBox_EMD.currentIndex()
        if index >= 0:
            emd = self.comboBox_EMD.itemData(index)
            if emd.name:
                children=emd.getChildren()
                if len(children)>0:
                    self.comboBox_Ri.setEnabled(True)
                    for ri in children:
                        self.comboBox_Ri.addItem(ri.name, ri)
            
    def radioButton_toggled(self, checked):
        self.lineEdit_SaveFilePath.setEnabled(self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked())
        self.pushButton_SetSaveFilePath.setEnabled(self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked())
        self.comboBox_Printer.setEnabled(self.radioButton_Printer.isChecked())
        
        self.lineEdit_SaveFilePath.setText('')
    
    def isLeftInfo(self):
        return self.radioButton_LeftInfo.isChecked()

    def isLeftScale(self):
        return self.radioButton_LeftScale.isChecked()

    def getTargetLayoutName(self):
        if self.radioButton_LeftInfo.isChecked():
            return u'소나무재선충병 L'
        else:
            return u'소나무재선충병 R'

    def getFontSize(self, text):
        strLen=len(text)
        if strLen>=10:
            return 16
        elif strLen==9:
            return 18
        elif strLen==8:
            return 20
        elif strLen==7:
            return 22
        elif strLen==6:
            return 24
        return 28

    def pushButton_Apply_Clicked(self):
        targetLayoutName=self.getTargetLayoutName()
        targetLayout=getLayout(targetLayoutName)
        if not targetLayout:
            pass
        
        targetLayoutDesigner=None
        openLayoutDesigners=iface.openLayoutDesigners()
        for openLayoutDesigner in openLayoutDesigners:
            layout=openLayoutDesigner.layout()
            if targetLayout != layout:
                openLayoutDesigner.close()
                
        iface.openLayoutDesigner(targetLayout)
        
        #title
        text=self.lineEdit_Title.text()
        item=getLayoutItemById(targetLayout, 'title')
        item.setText(text)
        fontSize=self.getFontSize(text)
        font=item.font()
        font.setPointSize(fontSize)
        item.setFont(font)

        #forestArea
        text = self.lineEdit_ForestArea.text()
        item = getLayoutItemById(targetLayout, 'forestArea')
        item.setText(text)
        
        #finewiltArea
        text = self.lineEdit_PinewiltArea.text()
        item = getLayoutItemById(targetLayout, 'finewiltArea')
        item.setText(text)
        
        #firstOccuredTime
        text = self.lineEdit_DiscoveredYear.text()
        item = getLayoutItemById(targetLayout, 'firstOccuredTime')
        item.setText(u'· 최초발생(' + text + u')')
        
        #firstOccuredPlace
        text = self.lineEdit_DiscoveredArea.text()
        item = getLayoutItemById(targetLayout, 'firstOccuredPlace')
        item.setText(u' - ' + text)
        
        #table_0_0
        text = self.lineEdit_Table_0_0.text()
        item = getLayoutItemById(targetLayout, 'table_0_0')
        item.setText(text)
        
        text = text.replace(u'년', '')
        item = getLayoutItemById(targetLayout, 'axisX_0')
        item.setText(text)
        
        #table_0_1
        text = self.lineEdit_Table_0_1.text()
        item = getLayoutItemById(targetLayout, 'table_0_1')
        item.setText(text)
        
        t0 = text.replace(',', '')
        
        #table_1_0
        text = self.lineEdit_Table_1_0.text()
        item = getLayoutItemById(targetLayout, 'table_1_0')
        item.setText(text)
        
        text = text.replace(u'년', '')
        item = getLayoutItemById(targetLayout, 'axisX_1')
        item.setText(text)
        
        #table_1_1
        text = self.lineEdit_Table_1_1.text()
        item = getLayoutItemById(targetLayout, 'table_1_1')
        item.setText(text)
        
        t1 = text.replace(',', '')
        
        #table_2_0
        text = self.lineEdit_Table_2_0.text()
        item = getLayoutItemById(targetLayout, 'table_2_0')
        item.setText(text)
        
        text = text.replace(u'년', '')
        item = getLayoutItemById(targetLayout, 'axisX_2')
        item.setText(text)
        
        #table_2_1
        text = self.lineEdit_Table_2_1.text()
        item = getLayoutItemById(targetLayout, 'table_2_1')
        item.setText(text)
        
        t2 = text.replace(',', '')
        
        #Graph
        intervalList = [5, 10, 25]
        
        n = [int(t0), int(t1), int(t2)]
        
        maxValue = max(n)
        
        maxAxisY = None
        
        power = 0
        while True:
            for interval in intervalList:
                v = interval * (10**power)
                if maxValue <= v:
                    maxAxisY = v
                    break
            
            if maxAxisY != None:
                break
                
            power += 1
        
        interval = maxAxisY / 5
        
        for i in range(6):
            item = getLayoutItemById(targetLayout, 'axisY_' + str(i))
            item.setText(str(int(interval) * i))
        
        
        for i in range(3):
            height = n[i] * 25 / maxAxisY
            item = getLayoutItemById(targetLayout, 'bar_' + str(i))
            item.setRect(0, 0, 5, height)
            if height <= 0 : height = 0.1
            item.setFixedSize(QgsLayoutSize(5, height))
            item.setY(195.6)
            item.refresh()
        
        #Set Map
        mapItem = getLayoutItemById(targetLayout, 'map_main')
        if self.groupBox_SetDistrict.isChecked():
            bound = self.getBounds()
            targetCrs=QgsProject.instance().crs()
            sourceCrs=QgsCoordinateReferenceSystem("EPSG:5186")
            ct=QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance())
            bound=ct.transformBoundingBox(bound)
            mapItem.zoomToExtent(bound)
        else:
            x=int(self.lineEdit_X.text())
            y=int(self.lineEdit_Y.text())
            scale=int(self.lineEdit_Scale.text())
            extent=mapItem.extent()
            extent.scale(1, x, y)
            mapItem.setExtent(extent)
            mapItem.setScale(scale)

        #scalebar
        x=5
        if self.isLeftInfo():
            x+=75
        if not self.isLeftScale():
            x+=285
        item=getLayoutItemById(targetLayout, 'scalebar')
        item.setX(x)
        
        targetLayout.deselectAll()
        targetLayout.refresh()
            
    def getBounds(self):
        index=self.comboBox_Ri.currentIndex()
        if index>=0:
            data=self.comboBox_Ri.itemData(index)
            if data.bound:
                return data.bound
                
        index=self.comboBox_EMD.currentIndex()
        if index>=0:
            data=self.comboBox_EMD.itemData(index)
            if data.bound:
                return data.bound
            
        index=self.comboBox_SGG.currentIndex()
        if index>=0:
            data=self.comboBox_SGG.itemData(index)
            if data.bound:
                return data.bound
        
        index=self.comboBox_SiDo.currentIndex()
        if index>=0:
            data=self.comboBox_SiDo.itemData(index)
            if data.bound:
                return data.bound
            
    def pushButton_SetCoordinate_Clicked(self):
        mapcanvas=iface.mapCanvas()
        center=mapcanvas.center()
        x=int(center.x())
        y=int(center.y())
        self.lineEdit_X.setText(str(x))
        self.lineEdit_Y.setText(str(y))
        
    def pushButton_setSavePath_Clicked(self):
        if self.radioButton_PDF.isChecked():
            tuple=QFileDialog.getSaveFileName(self, u'경로 지정', QgsProject.instance().homePath(), 'PDF (*.pdf)')
            if tuple:
                fileName=tuple[0]
                self.lineEdit_SaveFilePath.setText(fileName)
        elif self.radioButton_PNG.isChecked():
            tuple=QFileDialog.getSaveFileName(self, u'경로 지정', QgsProject.instance().homePath(), 'Images (*.png)')
            if tuple:
                fileName=tuple[0]
                self.lineEdit_SaveFilePath.setText(fileName)
    
    def pushButton_Print_Clicked(self):
        targetLayoutName=self.getTargetLayoutName()
        targetLayout=getLayout(targetLayoutName)
        
        self.progressDialog=None
        self.task=None
        if self.radioButton_PDF.isChecked():
            savePath = self.lineEdit_SaveFilePath.text()
            if not savePath:
                self.showMessage(u'파일 경로를 설정해주세요.')
                return
            exporter = QgsLayoutExporter(targetLayout)
            self.task=QgsTask.fromFunction('PDF 출력', self.exportToPdf, exporter=exporter, savePath=savePath)
            self.task.completeMessage='PDF 저장을 완료하였습니다.\n저장 경로 :' + savePath
            self.task.terminateMessage='PDF 저장을 실패하였습니다.'
        elif self.radioButton_PNG.isChecked():
            savePath = self.lineEdit_SaveFilePath.text()
            if not savePath:
                self.showMessage(u'파일 경로를 설정해주세요.')
                return
            exporter = QgsLayoutExporter(targetLayout)
            self.task=QgsTask.fromFunction('이미지 출력', self.exportToImage, exporter=exporter, savePath=savePath)
            self.task.completeMessage='이미지 저장을 완료하였습니다.\n저장 경로 :' + savePath
            self.task.terminateMessage='이미지 저장을 실패하였습니다.'
        elif self.radioButton_Printer.isChecked():
            index = self.comboBox_Printer.currentIndex()
            printerInfo = self.comboBox_Printer.itemData(index)
            printer = QPrinter(printerInfo)
            printer.setOrientation(QPrinter.Landscape)
            printer.setPageSize(QPageSize(QPageSize.A3))
            printer.setFullPage(True)
            exporter = QgsLayoutExporter(targetLayout)
            self.task=QgsTask.fromFunction('프린터 출력', self.print, exporter=exporter, printer=printer)
            self.task.completeMessage='프린트를 완료하였습니다.'
            self.task.terminateMessage='프린트를 실패하였습니다.'
            
        if self.task:
            self.task.taskCompleted.connect(self.taskCompleted)
            self.task.taskTerminated.connect(self.taskTerminated)
            
            QgsApplication.taskManager().addTask(self.task)
            
            self.progressDialog = QProgressDialog(self)
            self.progressDialog.setModal(True)
            self.progressDialog.setWindowTitle('레이아웃 출력')
            self.progressDialog.setLabelText('레이아웃 출력 중...')
            self.progressDialog.setCancelButton(None)
            self.progressDialog.setMinimum(0)
            self.progressDialog.setMaximum(0)
            self.progressDialog.setValue(0)
            self.progressDialog.show()
            
    def taskCompleted(self):
        self.closeProgressDialog()
        if self.task:
            self.showMessage(self.task.completeMessage)
        self.task=None
        pass
        
    def taskTerminated(self):
        self.closeProgressDialog()
        if self.task:
            self.showMessage(self.task.terminateMessage)
        self.task=None
        pass
        
    def closeProgressDialog(self):
        if self.progressDialog:
            self.progressDialog.close()
            del self.progressDialog
            
    def exportToPdf(self, task, exporter, savePath):
        exporter.exportToPdf(savePath, QgsLayoutExporter.PdfExportSettings())
        
    def exportToImage(self, task, exporter, savePath):
        exporter.exportToImage(savePath, QgsLayoutExporter.ImageExportSettings())
        
    def print(self, task, exporter, printer):
        exporter.print(printer, QgsLayoutExporter.PrintExportSettings())
            
    def groupBox_SetDistrict_toggled(self, checked):
        self.groupBox_SetCoordinateAndScale.setChecked(not checked)
        
    def groupBox_SetCoordinateAndScale_toggled(self, checked):
        self.groupBox_SetDistrict.setChecked(not checked)
        
    def showMessage(self, text, title=''):
        msg = QMessageBox()
        msg.setText(text)
        if title:
            msg.setWindowTitle(title)
        else:
            msg.setWindowTitle(self.windowTitle())
        msg.exec_()