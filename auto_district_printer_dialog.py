# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AutoDistrictPrinterDialog
                                 A QGIS plugin
 Print by district (sido, sigungu)
                             -------------------
        begin                : 2018-10-04
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
    os.path.dirname(__file__), 'auto_district_printer_dialog_base.ui'))


class AutoDistrictPrinterDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AutoDistrictPrinterDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.comboBox_Layers.currentIndexChanged.connect(self.comboBox_Layers_currentIndexChanged)
        
        self.checkBox_UseTitle.toggled.connect(self.checkBox_UseTitle_toggled)
        
        self.radioButton_PDF.toggled.connect(self.radioButton_toggled)
        self.radioButton_PNG.toggled.connect(self.radioButton_toggled)
        self.radioButton_Printer.toggled.connect(self.radioButton_toggled)
        
        self.pushButton_SetSavePath.clicked.connect(self.pushButton_SetSavePath_Clicked)
        self.pushButton_Print.clicked.connect(self.print)
        
    def radioButton_toggled(self, checked):
        self.lineEdit_SavePath.setEnabled(self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked())
        self.pushButton_SetSavePath.setEnabled(self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked())
        self.comboBox_Printer.setEnabled(self.radioButton_Printer.isChecked())
        
        self.lineEdit_SavePath.setText('')
        
    def checkBox_UseTitle_toggled(self, checked):
        self.comboBox_FieldsForTitle.setEnabled(checked)
        
    def comboBox_Layers_currentIndexChanged(self):
        layer=self.getSelectedLayer()
        
        self.comboBox_FieldsForFileName.clear()
        self.comboBox_FieldsForTitle.clear()
        
        if layer:
            for field in layer.fields():
                self.comboBox_FieldsForFileName.addItem(field.name())
                self.comboBox_FieldsForTitle.addItem(field.name())
                
    def showEvent(self, event):
        super(AutoDistrictPrinterDialog, self).showEvent(event)
        
        self.initializeComboBoxLayout()
        self.initializeComboBoxLayers()
        self.initializePrinterComboBox()
        
    def initializePrinterComboBox(self):
        defaultPrinterInfo = QPrinterInfo.defaultPrinter()
        
        printerInfos = QPrinterInfo.availablePrinters()
        for printerInfo in printerInfos:
            self.comboBox_Printer.addItem(printerInfo.printerName(), printerInfo)
            
        index = self.comboBox_Printer.findData(defaultPrinterInfo)
        if index >= 0:
            self.comboBox_Printer.setCurrentIndex(index)
        
    def initializeComboBoxLayout(self):
        layouts=getLayouts()
        for layout in layouts:
            self.comboBox_Layouts.addItem(layout.name(), layout)
            
    def initializeComboBoxLayers(self):
        layers=getLayers(isVectorOnly=True)
        for layer in layers:
            if layer.geometryType()==QgsWkbTypes.PolygonGeometry or layer.geometryType()==QgsWkbTypes.LineGeometry:
                self.comboBox_Layers.addItem(layer.name(), layer)
            
    def getSelectedLayer(self):
        index=self.comboBox_Layers.currentIndex()
        if index>=0:
            data=self.comboBox_Layers.itemData(index)
            return data
        return None
        
    def getSelectedLayoutName(self):
        return self.comboBox_Layouts.currentText()
        
    def getSelectedFieldForFileName(self):
        return self.comboBox_FieldsForFileName.currentText()
        
    def getSelectedFieldForTitle(self):
        return self.comboBox_FieldsForTitle.currentText()
        
    def print(self):
        layoutName=self.getSelectedLayoutName()
        layout=getLayout(layoutName)
        
        if not layout:
            self.showMessage('레이아웃을 선택해주세요.')
            return
                
        layer=self.getSelectedLayer()
        if not layer:
            self.showMessage('레이어를 선택해주세요.')
            return
            
        fieldForFileName=self.getSelectedFieldForFileName()
        if not fieldForFileName:
            self.showMessage('파일명 필드를 선택해주세요.')
            return
            
        margin=self.spinBox_MarginRatio.value()/100.0
            
        fieldForTitle=None
        if self.checkBox_UseTitle.checkState():
            fieldForTitle=self.getSelectedFieldForTitle()
            if not fieldForTitle:
                self.showMessage('제목명 필드를 선택해주세요.')
                
        mapItems=[]
        labelItem=None
        for layoutItem in layout.items():
            if isinstance(layoutItem, QgsLayoutItemMap):
                mapItems.append(layoutItem)
                
            if isinstance(layoutItem, QgsLayoutItemLabel) and layoutItem.id() == 'title':
                labelItem=layoutItem
                
        if self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked():
            savePath = self.getSavePath()
            if not savePath:
                self.showMessage('파일 경로를 설정해주세요.', '파일 경로 설정')
                return
        elif self.radioButton_Printer.isChecked():
            printer=self.getSelectedPrinter()
            
        self.setEnabled(False)
        
        count=0
        totalCount=layer.featureCount()
        features=layer.getFeatures()
        for feature in features:
            try:
                geometry=feature.geometry()
                bounds=getBound(geometry, margin)
                for mapItem in mapItems:
                    targetCrs=mapItem.crs()
                    sourceCrs=layer.crs()
                    qct=QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance())
                    convertedBounds=qct.transformBoundingBox(bounds)
                    mapItem.zoomToExtent(convertedBounds)
                    mapItem.refresh()
                
                if labelItem and fieldForTitle:
                    title=feature.attribute(fieldForTitle)
                    labelItem.setText(str(title))
                    labelItem.refresh()
                    
                fileName=feature.attribute(fieldForFileName)
                
                layout.deselectAll()
                layout.refresh()
                
                if self.radioButton_PDF.isChecked():
                    saveFilePath=os.path.join(savePath, '{}.pdf'.format(fileName))
                    exporter=QgsLayoutExporter(layout)
                    exporter.exportToPdf(saveFilePath, QgsLayoutExporter.PdfExportSettings())
                elif self.radioButton_PNG.isChecked():
                    saveFilePath=os.path.join(savePath, '{}.png'.format(fileName))
                    exporter=QgsLayoutExporter(layout)
                    exporter.exportToImage(saveFilePath, QgsLayoutExporter.ImageExportSettings())
                elif self.radioButton_Printer.isChecked():
                    exporter = QgsLayoutExporter(layout)
                    exporter.print(printer, QgsLayoutExporter.PrintExportSettings())
            except:
                self.writeLog(u"Unexcepted error :" + str(traceback.format_exc()))
            
            count=count+1
            percentage=count*100/totalCount
            self.setProgress(percentage)
            
        self.setProgress(100)
        self.showMessage(u'프린트 완료하였습니다.')
        
        self.setProgress(0)
        self.setEnabled(True)
        
    def setProgress(self, value):
        self.progressBar.setValue(value)
        
    def getSelectedPrinter(self):
        index = self.comboBox_Printer.currentIndex()
        printerInfo = self.comboBox_Printer.itemData(index)
        printer = QPrinter(printerInfo)
        printer.setOrientation(QPrinter.Landscape)
        printer.setPageSize(QPageSize(QPageSize.A3))
        printer.setFullPage(True)
        return printer
        
    def getSavePath(self):
        return self.lineEdit_SavePath.text()
        
    def pushButton_SetSavePath_Clicked(self):
        dir = QFileDialog.getExistingDirectory(self, u'폴더 지정', QgsProject.instance().homePath(), QFileDialog.ShowDirsOnly)
        self.lineEdit_SavePath.setText(dir)
        
    def showMessage(self, text, title=''):
        msg = QMessageBox()
        msg.setText(text)
        if title:
            msg.setWindowTitle(title)
        else:
            msg.setWindowTitle(self.windowTitle())
        msg.exec_()
        
    def writeLog(self, message):
        QgsMessageLog.logMessage(message, 'PrintPineWiltDiseaseComposition')
