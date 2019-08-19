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

from .layer_utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'create_length_area_attributes_dialog_base.ui'))

LENGTH=u'길이'
AREA=u'면적'
AREAHA=u'면적_ha'

class CreateLengthAreaAttributesDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(CreateLengthAreaAttributesDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.progressDialog=None
        
        self.pushButton_OK.clicked.connect(self.pushButton_OK_Clicked)
        self.pushButton_Cancel.clicked.connect(self.pushButton_Cancel_Clicked)
    
    def showEvent(self, event):
        super(CreateLengthAreaAttributesDialog, self).showEvent(event)
        
        self.initializeLayers()
        
    def initializeLayers(self):
        layers=getLayers()
        model=QStandardItemModel()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and (layer.geometryType()==QgsWkbTypes.LineGeometry or layer.geometryType()==QgsWkbTypes.PolygonGeometry):
                item=QStandardItem(layer.name())
                item.setData(layer)
                model.appendRow(item)
        
        self.listView_Layers.setModel(model)
        
    def pushButton_OK_Clicked(self):
        indexes=self.listView_Layers.selectedIndexes()
        model=self.listView_Layers.model()
        selectedLayers=[]
        for index in indexes:
            item=model.itemFromIndex(index)
            selectedLayers.append(item.data())
        if len(selectedLayers)<=0:
            self.showMessage(u'면적 또는 길이 속성을 생성할 레이어를 선택해주세요.')
            return
            
        task=QgsTask.fromFunction('면적 또는 길이 생성', self.run, layers=selectedLayers)
        task.taskCompleted.connect(self.taskCompleted)
        task.taskTerminated.connect(self.taskCompleted)
        
        QgsApplication.taskManager().addTask(task)
            
        self.progressDialog = QProgressDialog(self)
        self.progressDialog.setModal(True)
        self.progressDialog.setWindowTitle('면적 또는 길이 생성')
        self.progressDialog.setLabelText('면적 또는 길이 생성 중...')
        self.progressDialog.setCancelButton(None)
        self.progressDialog.show()
        
        task.progressChanged.connect(self.progressDialog.setValue)
        
        self.setEnabled(False)
        
    def taskCompleted(self):
        self.setEnabled(True)
        self.closeProgressDialog()
        self.showMessage('면적 또는 길이 속성 입력을 완료하였습니다.')
        self.close()
        
    def closeProgressDialog(self):
        if self.progressDialog:
            self.progressDialog.close()
            del self.progressDialog
        
    def run(self, task, layers):
        task.setProgress(0)
        
        for layer in layers:
            if layer.geometryType()==QgsWkbTypes.LineGeometry:
                layer.dataProvider().addAttributes([QgsField(LENGTH, QVariant.Double)])
                layer.updateFields()
                layer.startEditing()
                count=0
                totalCount=layer.featureCount()
                for feature in layer.getFeatures():
                    # calculate length and set attribute
                    geometry=feature.geometry()
                    length=geometry.length()
                    feature[LENGTH]=length
                    layer.updateFeature(feature)
                    count=count+1
                    percentage=count*100/totalCount
                    task.setProgress(percentage)
                layer.commitChanges()
            elif layer.geometryType()==QgsWkbTypes.PolygonGeometry:
                # create area attribute
                layer.dataProvider().addAttributes([QgsField(AREA, QVariant.Double), QgsField(AREAHA, QVariant.Double)])
                layer.updateFields()
                layer.startEditing()
                count=0
                totalCount=layer.featureCount()
                for feature in layer.getFeatures():
                    # calculate area and set attribute
                    geometry=feature.geometry()
                    area=geometry.area()
                    feature[AREAHA]=area/10000.0
                    feature[AREA]=area
                    layer.updateFeature(feature)
                    count=count+1
                    percentage=count*100/totalCount
                    task.setProgress(percentage)
                layer.commitChanges()
                
        task.setProgress(100)
                
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