# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ExportKMLDialog
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
    os.path.dirname(__file__), 'export_kml_dialog_base.ui'))

class ExportKMLDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ExportKMLDialog, self).__init__(parent)
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
        super(ExportKMLDialog, self).showEvent(event)
        
        self.initializeLayers()
        
    def initializeLayers(self):
        layers=getLayers()
        model=QStandardItemModel()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
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
            self.showMessage(u'레이어 저장 경로를 선택해주세요.')
            return
            
        indexes=self.listView_Layers.selectedIndexes()
        model=self.listView_Layers.model()
        selectedLayers=[]
        for index in indexes:
            item=model.itemFromIndex(index)
            selectedLayers.append(item.data())
        if len(selectedLayers)<=0:
            self.showMessage(u'KML으로 내보내기 할 레이어를 선택해주세요.')
            return
        
        for layer in selectedLayers:
            targetFileName=targetDirectory + u'/' + layer.name() + u'.kml'
            writer=QgsVectorFileWriter.writeAsVectorFormat(layer, targetFileName, "utf-8", QgsCoordinateReferenceSystem(4326), "KML")
            del writer
                
        self.showMessage(u'레이어 내보내기를 완료하였습니다.')
        self.close()
                
    def getFileNameWoExt(self, filePath):
        return os.path.splitext(os.path.basename(filePath))[0]
        
    def getExtension(self, filePath):
        return os.path.splitext(os.path.basename(filePath))[1]
        
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