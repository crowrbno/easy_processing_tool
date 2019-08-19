# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SetCoordinateDialog
                                 A QGIS plugin
 좌표 설정
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

from .layer_utils import *
from .coordinates import *

import processing

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'set_coordinate_dialog_base.ui'))

class SetCoordinateDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(SetCoordinateDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.comboBox_Layers.currentIndexChanged.connect(self.comboBox_Layers_currentIndexChanged)
        
        self.pushButton_ApplyCRS.clicked.connect(self.pushButton_ApplyCRS_Clicked)
        self.pushButton_Cancel.clicked.connect(self.pushButton_Cancel_Clicked)
        
        self.progDialog=None
        self.result=None
        
    def showEvent(self, event):
        super(SetCoordinateDialog, self).showEvent(event)
        
        self.initializeComboBoxLayers()
        self.initializeComboBoxCoordinates();
        
    def initializeComboBoxLayers(self):
        layers=getLayers()
        for layer in layers:
            self.comboBox_Layers.addItem(layer.name(), layer)
            
        activeLayer=iface.activeLayer()
        if activeLayer:
            activeIndex=self.comboBox_Layers.findData(activeLayer)
            self.comboBox_Layers.setCurrentIndex(activeIndex)
            
    def comboBox_Layers_currentIndexChanged(self):
        self.refreshCurrentCrs()
            
    def refreshCurrentCrs(self):
        self.lineEdit_CurrentCRS.setText('')
        index = self.comboBox_Layers.currentIndex()
        if index >= 0 :
            layer = self.comboBox_Layers.itemData(index)
            crs=layer.crs()
            self.lineEdit_CurrentCRS.setText('{} - {}'.format(crs.description(), crs.authid()))
            
    def initializeComboBoxCoordinates(self):
        #comboBox_TargetCoordinates
        for name, sub_coordinates in coordinates.items():
            self.comboBox_TargetCoordinates.addItem(name, None)
            for coordinate_name, code in sub_coordinates.items():
                if code<990000:
                    self.comboBox_TargetCoordinates.addItem('{} - EPSG:{}'.format(coordinate_name, code), code)
                else:
                    parentCode=code%990000
                    self.comboBox_TargetCoordinates.addItem('{} - EPSG:{}'.format(coordinate_name, parentCode), code)
                
        self.comboBox_TargetCoordinates.setCurrentIndex(1)

    def pushButton_ApplyCRS_Clicked(self):
        layer=self.getSelectedLayer()
        if not layer:
            self.showMessage('레이어를 선택해주세요.')
            return
        
        targetEpsgCode=self.getSelectedEpsgCode()
        if not targetEpsgCode:
            self.showMessage('좌표계를 선택해주세요.')
            return
            
        targetCrs = None
        if targetEpsgCode>=990000:
            parentCrsCode=targetEpsgCode%990000
            parentCrs=QgsCoordinateReferenceSystem.fromEpsgId(parentCrsCode)
            proj4=parentCrs.toProj4()
            proj4=proj4+' +towgs84=-145.907,505.034,685,0,0,0,0'
            targetCrs=QgsCoordinateReferenceSystem.fromProj4(proj4)
            if not targetCrs.authid():
                targetCrs.saveAsUserCrs('{} with 7 Parameters'.format(parentCrs.description()))
        else:
            targetCrs=QgsCoordinateReferenceSystem.fromEpsgId(targetEpsgCode)
        
        layer.setCrs(targetCrs)
        
        iface.mapCanvas().refreshAllLayers()
        
        self.refreshCurrentCrs()
        
    def getSelectedLayer(self):
        index=self.comboBox_Layers.currentIndex()
        return self.comboBox_Layers.itemData(index)
        
    def getSelectedEpsgCode(self):
        index=self.comboBox_TargetCoordinates.currentIndex()
        return self.comboBox_TargetCoordinates.itemData(index)
        
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
        
    def log(self, message):
        QgsMessageLog.logMessage(message)