# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PrintPineWiltDiseaseCompositionDialog
                                 A QGIS plugin
 버퍼 생성
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

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'create_merged_buffer_dialog_base.ui'))

class CreateMergedBufferDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(CreateMergedBufferDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.pushButton_SetSaveFilePath.clicked.connect(self.pushButton_setSavePath_Clicked)
        self.pushButton_OK.clicked.connect(self.pushButton_OK_Clicked)
        self.pushButton_Cancel.clicked.connect(self.pushButton_Cancel_Clicked)
        
    def showEvent(self, event):
        super(CreateMergedBufferDialog, self).showEvent(event)
        
        self.initializeComboBox()
        
    def initializeComboBox(self):
        layers=self.getLayers()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                self.comboBox_Layers.addItem(layer.name(), layer)
                
    def getLayers(self):
        project = QgsProject.instance()
        layerTreeRoot=project.layerTreeRoot()
        treeLayers=layerTreeRoot.findLayers()
        
        layers=[]
        for treeLayer in treeLayers:
            layers.append(treeLayer.layer())
        return layers
        
    def pushButton_setSavePath_Clicked(self):
        tuple = QFileDialog.getSaveFileName(self, u'저장 경로 설정', QgsProject.instance().homePath(), 'Shape Files (*.shp)')
        if tuple:
            fileName=tuple[0]
            self.lineEdit_SaveFilePath.setText(fileName)

    def pushButton_OK_Clicked(self):
        # create buffer and merge
        layer=self.getSelectedLayer()
        
        saveFilePath=self.lineEdit_SaveFilePath.text()
        if not saveFilePath:
            self.showMessage(u'저장 경로를 지정해주세요.')
            return
            
        try:
            bufferDistance=float(self.lineEdit_BufferRadius.text())
        except:
            self.showMessage(u'버퍼 반경을 입력해주세요.')
            return
        
        if QgsGeometryAnalyzer().buffer(layer, saveFilePath, bufferDistance, False, True):
            # create layer with file
            fileName=os.path.splitext(os.path.basename(saveFilePath))[0]
            qvl=QgsVectorLayer(saveFilePath, fileName, 'ogr')
            symbol=qvl.rendererV2().symbols()[0]
            oldColor=QColor(symbol.color())
            oldColor.setAlpha(51)
            symbol.setColor(oldColor)
            QgsProject.instance().addMapLayer(qvl)
            iface.layerTreeView().refreshLayerSymbology(qvl.id())
            iface.mapCanvas().refreshAllLayers()
            self.showMessage(u'버퍼 생성을 완료하였습니다.')
        else:
            self.showMessage(u'버퍼 생성을 실패하였습니다.')
        
    def getSelectedLayer(self):
        index=self.comboBox_Layers.currentIndex()
        return self.comboBox_Layers.itemData(index)
        
    def pushButton_Cancel_Clicked(self):
        # exit program
        self.close()
        
    def showMessage(self, text, title=''):
        msg = QMessageBox()
        msg.setText(text)
        if title:
            msg.setWindowTitle(title)
        else:
            msg.setWindowTitle(self.windowTitle())
        msg.exec_()