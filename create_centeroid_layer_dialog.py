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

from .layer_utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'create_centeroid_layer_dialog_base.ui'))

class CreateCenteroidLayerDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(CreateCenteroidLayerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.pushButton_SetSavePath.clicked.connect(self.pushButton_SetSavePath_Clicked)
        self.pushButton_OK.clicked.connect(self.pushButton_OK_Clicked)
        self.pushButton_Cancel.clicked.connect(self.pushButton_Cancel_Clicked)
    
    def showEvent(self, event):
        super(CreateCenteroidLayerDialog, self).showEvent(event)
        
        self.initializeLayers()
        
    def initializeLayers(self):
        layers=getLayers()
        model=QStandardItemModel()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.geometryType()==QgsWkbTypes.PolygonGeometry:
                item=QStandardItem(layer.name())
                item.setData(layer)
                model.appendRow(item)
        
        self.listView_Layers.setModel(model)
        
    def pushButton_SetSavePath_Clicked(self):
        dir = QFileDialog.getExistingDirectory(self, u'폴더 지정', QgsProject.instance().homePath(), QFileDialog.ShowDirsOnly)
        self.lineEdit_SavePath.setText(dir)
        
    def pushButton_OK_Clicked(self):
        targetDirectory=self.lineEdit_SavePath.text()
        if not targetDirectory:
            self.showMessage(u'레이어 저장 경로를 설정해주세요.')
            return
    
        indexes=self.listView_Layers.selectedIndexes()
        model=self.listView_Layers.model()
        selectedLayers=[]
        for index in indexes:
            item=model.itemFromIndex(index)
            selectedLayers.append(item.data())
        if len(selectedLayers)<=0:
            self.showMessage(u'중심점 생성할 레이어를 선택해주세요.')
            return
        
        task=QgsTask.fromFunction('중심점 생성', self.run, layers=selectedLayers, targetDirectory=targetDirectory)
        task.taskCompleted.connect(self.taskCompleted)
        task.taskTerminated.connect(self.taskCompleted)
        QgsApplication.taskManager().addTask(task)
            
        self.progressDialog = QProgressDialog(self)
        self.progressDialog.setModal(True)
        self.progressDialog.setWindowTitle('중심점 생성 추출')
        self.progressDialog.setLabelText('중심점 생성 중...')
        self.progressDialog.setCancelButton(None)
        self.progressDialog.show()
        
        task.progressChanged.connect(self.progressDialog.setValue)
        
        self.setEnabled(False)
        
    def taskCompleted(self):
        if self.resultFiles and len(self.resultFiles)>0:
            for resultFile in self.resultFiles:
                qvl=QgsVectorLayer(resultFile, self.getFileNameWoExt(resultFile), 'ogr')
                QgsProject.instance().addMapLayer(qvl)
                
        self.closeProgressDialog()
        iface.mapCanvas().refreshAllLayers()
        self.showMessage(u'중심점 생성을 완료하였습니다.')
        self.close()
        
    def closeProgressDialog(self):
        if self.progressDialog:
            self.progressDialog.close()
            del self.progressDialog
        
    def run(self, task, layers, targetDirectory):
        
        task.setProgress(0)
        
        self.resultFiles=[]
        for layer in layers:
            targetFileName=targetDirectory + u'/' + layer.name() + u'_중심점.shp'
            dataProvider=layer.dataProvider()
            fields=QgsFields()
            fields.append(QgsField(u'X', QVariant.Double))
            fields.append(QgsField(u'Y', QVariant.Double))
            fields.extend(layer.fields())
            writer=QgsVectorFileWriter(targetFileName,dataProvider.encoding(), fields, QgsWkbTypes.Point, layer.crs(), "ESRI Shapefile")
            
            count=0
            totalCount=layer.featureCount()
            for feature in layer.getFeatures():
                geometry=feature.geometry()
                centroid=geometry.centroid()
                newFeature=QgsFeature()
                newFeature.setGeometry(centroid)
                attributes=feature.attributes()
                attributes.insert(0, centroid.asPoint().x())
                attributes.insert(1, centroid.asPoint().y())
                newFeature.setAttributes(attributes)
                writer.addFeature(newFeature)
                count=count+1
                percentage=count*100/totalCount
                task.setProgress(percentage)
            del writer
            
            self.resultFiles.append(targetFileName)
            
        self.setProgress(100)
                
    def getFileNameWoExt(self, path):
        return os.path.splitext(os.path.basename(path))[0]
        
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