# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PrintPineWiltDiseaseCompositionDialog
                                 A QGIS plugin
 다중 레이어 추가
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
from qgis.core import *
from qgis.utils import *

from openpyxl import *

from .layer_utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'add_layer_multi_dialog_base.ui'))

__alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
def convertColumnNumToLetter(column):
    converted = ""

    #figure out the width of the converted text
    columnCount = 1
    base = len(__alphabet)
    base_exponent = base
    exponent = 1
    while column > base_exponent:
        column = column - base_exponent
        exponent = exponent + 1
        columnCount = columnCount + 1
        base_exponent = base_exponent * base

    #calculate the actual column name
    column = column - 1
    while len(converted) < columnCount:
        digit = column % base
        column = (column - digit) // base
        converted = __alphabet[digit] + converted

    return converted
    
def convertLetterToColumnNum(columnName):
    converted = 0
    columnCount = len(columnName)

    base = len(__alphabet)
    base_exponent = 1
    while len(columnName) != 0:
        #strip the right-most digit, convert to index
        digit = columnName[-1:]
        columnName = columnName[:-1]
        digit = __alphabet.index(digit)

        #add the value it represents to the total, increment base_exponent
        converted = converted + digit * base_exponent
        base_exponent = base_exponent * base

        #add the offset for having passed all the n-width columns
        if len(columnName) != 0:
            converted = converted + base_exponent

    return converted + 1
    
class AddLayerMultiDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AddLayerMultiDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.pushButton_OpenFiles.clicked.connect(self.pushButton_OpenFiles_Clicked)
        self.pushButton_SetSavePath.clicked.connect(self.pushButton_SetSavePath_Clicked)
        self.pushButton_OK.clicked.connect(self.pushButton_OK_Clicked)
        self.pushButton_Cancel.clicked.connect(self.pushButton_Cancel_Clicked)
        
    def pushButton_OpenFiles_Clicked(self):
        tuple=QFileDialog.getOpenFileNames(self, u'파일 열기', QgsProject.instance().homePath(), 'Layer Files (*.shp *.xls *.xlsx)')
        if tuple:
            filePaths=tuple[0]
            if filePaths and len(filePaths) > 0:
                self.groupBox_ExcelSettings.setEnabled(self.isExcelFileContains(filePaths))
                model=QStandardItemModel()
                for filePath in filePaths:
                    fileName=os.path.basename(filePath)
                    item=QStandardItem(fileName)
                    item.setData(filePath)
                    model.appendRow(item)
                self.listView_Files.setModel(model)
        
    def pushButton_SetSavePath_Clicked(self):
        dir = QFileDialog.getExistingDirectory(self, u'폴더 지정', QgsProject.instance().homePath(), QFileDialog.ShowDirsOnly)
        self.lineEdit_SavePath.setText(dir)
        
    def pushButton_OK_Clicked(self):
        model=self.listView_Files.model()
        filePaths=[]
        for index in range(model.rowCount()):
            item=model.item(index)
            filePath=item.data()
            filePaths.append(filePath)
        
        if len(filePaths) <= 0:
            self.showMessage(u'추가할 레이어 파일을 선택해주세요.')
            return
        
        xField=self.lineEdit_XField.text()
        yField=self.lineEdit_YField.text()
        fieldRowIndex=int(self.lineEdit_FieldRowIndex.text())
        
        targetDirectory=self.lineEdit_SavePath.text()
        if not targetDirectory and self.isExcelFileContains(filePaths):
            self.showMessage(u'레이어 저장 경로를 선택해주세요.')
            return
        
        for filePath in filePaths:
            ext=self.getExtension(filePath)
            #self.showMessage(filePath + ' - Extension : ' + ext)
            if self.isShpFile(filePath):
                self.addShapeLayer(filePath)
            elif self.isExcelFile(filePath):
                self.addExcelLayer(targetDirectory, filePath, fieldRowIndex, xField, yField)
                
        iface.mapCanvas().refreshAllLayers()
        self.showMessage(u'레이어 추가를 완료하였습니다.')
    
    def isExcelFileContains(self, filePaths):
        for filePath in filePaths:
            if self.isExcelFile(filePath):
                return True
        return False
    
    def isExcelFile(self, filePath):
        ext=self.getExtension(filePath)
        return ext.lower() == '.xlsx' or ext.lower() == '.xls'
        
    def isShpFile(self, filePath):
        ext=self.getExtension(filePath)
        return ext.lower() == '.shp'
    
    def addShapeLayer(self, filePath):
        fileName=self.getFileName(filePath)
        layer=QgsVectorLayer(filePath, fileName, 'ogr')
        QgsProject.instance().addMapLayer(layer)
        
    def addExcelLayer(self, targetDirectory, filePath, fieldRowIndex, xField, yField):
        defaultLayer = getLayer('시군구')
        if not defaultLayer:
            pass
            
        wb = load_workbook(filePath)
        ws = wb.active
        
        maxColumnNum=self.getMaxColumnNum(ws, fieldRowIndex)
        row=self.getExcelRow(ws, fieldRowIndex, maxColumnNum)
        
        fields=QgsFields()
        for index, column in enumerate(row):
            if column.lower() != xField.lower() and column.lower() != yField.lower():
                fields.append(QgsField(column, QVariant.String))
            elif column.lower() == xField.lower():
                xFieldIndex=index
                fields.append(QgsField(column, QVariant.Double))
            elif column.lower() == yField.lower():
                yFieldIndex=index
                fields.append(QgsField(column, QVariant.Double))
                
        fileName=self.getFileName(filePath)
        targetFilePath=targetDirectory+'/'+fileName+'.shp'
        
        defaultProvider=defaultLayer.dataProvider()
        writer=QgsVectorFileWriter(targetFilePath, defaultProvider.encoding(), fields, QgsWkbTypes.Point, defaultProvider.crs(), "ESRI Shapefile")
        del writer
        
        layer=QgsVectorLayer(targetFilePath, fileName, 'ogr')
        layer.dataProvider().setEncoding(defaultProvider.encoding())
        layer.startEditing()
        
        rowIndex=fieldRowIndex+1
        row=self.getExcelRow(ws, rowIndex, maxColumnNum)
        while(not self.isNone(row)):
            feature=QgsFeature(layer.fields())
            try:
                for index, value in enumerate(row):
                    if index==xFieldIndex:
                        x=float(value)
                        feature.setAttribute(index, x)
                    elif index==yFieldIndex:
                        y=float(value)
                        feature.setAttribute(index, y)
                    else:
                        feature.setAttribute(index, value)
                feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
                layer.dataProvider().addFeatures([feature])
            except:
                pass
            rowIndex+=1
            row=self.getExcelRow(ws, rowIndex, maxColumnNum)
            
        layer.commitChanges()
        QgsProject.instance().addMapLayer(layer)
        
    def isNone(self, row):
        if row:
            for value in row:
                if value:
                    return False
        return True
        
    def getFileName(self, filePath):
        return os.path.splitext(os.path.basename(filePath))[0]
    
    def getExtension(self, filePath):
        return os.path.splitext(os.path.basename(filePath))[1]
            
    def getExcelRow(self, sheet, rowIndex, maxColumnNum):
        row = []
        
        for i in range(maxColumnNum):
            columnLetter=convertColumnNumToLetter(i+1)
            row.append(sheet[columnLetter+str(rowIndex)].value)
            
        return row;
        
    def getMaxColumnNum(self, sheet, rowIndex):
        columnNum=1
        while True:
            columnLetter=convertColumnNumToLetter(columnNum)
            value=sheet[columnLetter+str(rowIndex)].value
            if not value:
                return columnNum-1
            columnNum+=1
        
    def pushButton_Cancel_Clicked(self):
        self.close()
        
    def showMessage(self, text, title=''):
        msg = QMessageBox()
        msg.setText(text)
        if title:
            msg.setWindowTitle(title)
        else:
            msg.setWindowTitle(self.windowTitle())
        msg.exec_()