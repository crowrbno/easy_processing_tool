# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CreateLengthAreaAttributesDialog
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

from qgis.core import *
from qgis.utils import *
from qgis.analysis import *
from qgis.gui import *

from .layer_utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'calculate_raster_area_dialog_base.ui'))

class CalculateRasterAreaDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(CalculateRasterAreaDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.progressDialog=None
        
        self.pushButton_PickColor.clicked.connect(self.pickColor)
        self.pushButton_CalculateArea.clicked.connect(self.calculateArea)
        
        self.canvas=iface.mapCanvas()
        self.currentMapTool=QgsMapToolEmitPoint(self.canvas)
        self.currentMapTool.canvasClicked.connect(self.canvasClicked)
    
    def showEvent(self, event):
        super(CalculateRasterAreaDialog, self).showEvent(event)
        
        self.initializeLayers()
        
    def initializeLayers(self):
        layers=getLayers()
        for layer in layers:
            if isinstance(layer, QgsRasterLayer):
                self.comboBox_Layers.addItem(layer.name(), layer)
                
        activeLayer=iface.activeLayer()
        if activeLayer:
            index=self.comboBox_Layers.findData(activeLayer)
            if index>=0:
                self.comboBox_Layers.setCurrentIndex(index)
                
    def pickColor(self):
        self.oldMapTool=self.canvas.mapTool()
        self.canvas.setMapTool(self.currentMapTool)
        
    def canvasClicked(self, point):
        layer=self.getSelectedLayer()
        if layer:
            point=self.getTransformedPoint(point, QgsProject.instance().crs(), layer.crs())
            dp=layer.dataProvider()
            result=dp.identify(point, QgsRaster.IdentifyFormatValue)
            results=result.results()
            if 1 in results and results[1] != None:
                self.spinBox_R.setValue(results[1])
            if 2 in results and results[2] != None:
                self.spinBox_G.setValue(results[2])
            if 3 in results and results[3] != None:
                self.spinBox_B.setValue(results[3])
            if 4 in results and results[4] != None:
                self.spinBox_A.setValue(results[4])
                
        self.canvas.setMapTool(self.oldMapTool)
        
    def getTransformedPoint(self, point, srcCrs, dstCrs):
        qct=QgsCoordinateTransform(srcCrs, dstCrs, QgsProject.instance())
        return qct.transform(point)
    
    def calculateArea(self):
        samplingInterval=self.doubleSpinBox_SamplingInterval.value()
        
        layer=self.getSelectedLayer()
        if layer:
            exceptValues={}
            exceptValues[1]=self.spinBox_R.value()
            exceptValues[2]=self.spinBox_G.value()
            exceptValues[3]=self.spinBox_B.value()
            exceptValues[4]=self.spinBox_A.value()
            
            self.area=0
            self.task=QgsTask.fromFunction('래스터 면적 추출', self.run, layer=layer, samplingInterval=samplingInterval, exceptValues=exceptValues)
            self.task.taskCompleted.connect(self.taskCompleted)
            self.task.taskTerminated.connect(self.taskCompleted)
            QgsApplication.taskManager().addTask(self.task)
            
            self.progressDialog = QProgressDialog(self)
            self.progressDialog.setModal(True)
            self.progressDialog.setWindowTitle('래스터 면적 추출')
            self.progressDialog.setLabelText('래스터 면적 추출 중...')
            self.progressDialog.setCancelButton(None)
            self.progressDialog.show()
            
            self.task.progressChanged.connect(self.progressDialog.setValue)
            
            self.setEnabled(False)
        
    def taskCompleted(self):
        self.closeProgressDialog()
        self.lineEdit_Area.setText(str(self.area))
        self.showMessage('면적 계산을 완료하였습니다.')
        self.setEnabled(True)
    
    def closeProgressDialog(self):
        if self.progressDialog:
            self.progressDialog.close()
            del self.progressDialog
        
    def run(self, task, layer, samplingInterval, exceptValues):
        extent=layer.extent()
        
        targetCrs=QgsCoordinateReferenceSystem('EPSG:5186')
        qct=QgsCoordinateTransform(layer.crs(), targetCrs, QgsProject.instance())
        rqct=QgsCoordinateTransform(targetCrs, layer.crs(), QgsProject.instance())
        extent=qct.transformBoundingBox(extent)
        
        xo=extent.xMinimum() + (extent.width()%samplingInterval)/2
        yo=extent.yMinimum() + (extent.height()%samplingInterval)/2
        xcount=int(extent.width()/samplingInterval)
        ycount=int(extent.height()/samplingInterval)
        
        matchCount=0
        count=0
        totalCount=xcount*ycount
        for i in range(0, xcount):
            for j in range(0, ycount):
                x=xo+samplingInterval*i
                y=yo+samplingInterval*j
                point=QgsPointXY(x, y)
                point=rqct.transform(point)
                result = layer.dataProvider().identify(point, QgsRaster.IdentifyFormatValue)
                if result:
                    match=True
                    for k in range(1, 5):
                        if k in result.results():
                            if result.results()[k] != exceptValues[k]:
                                match=False
                                break
                            
                if match:
                    matchCount=matchCount+1
                    
                count=count+1
                percentage=count*100/totalCount
                task.setProgress(percentage)
                    
        task.setProgress(100)
        self.area=extent.width()*extent.height()*(1-matchCount/(xcount*ycount))
    
    def getSelectedLayer(self):
        index=self.comboBox_Layers.currentIndex()
        if index>=0:
            return self.comboBox_Layers.itemData(index)
        
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