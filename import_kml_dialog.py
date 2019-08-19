# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ImportKMLDialog
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
    os.path.dirname(__file__), 'import_kml_dialog_base.ui'))

class ImportKMLDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ImportKMLDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.pushButton_OpenKMLFiles.clicked.connect(self.pushButton_OpenKMLFiles_Clicked)
        self.pushButton_SetSavePath.clicked.connect(self.pushButton_SetSavePath_Clicked)
        self.pushButton_OK.clicked.connect(self.pushButton_OK_Clicked)
        self.pushButton_Cancel.clicked.connect(self.pushButton_Cancel_Clicked)
        
    def pushButton_OpenKMLFiles_Clicked(self):
        tuple=QFileDialog.getOpenFileNames(self, u'파일 열기', QgsProject.instance().homePath(), 'KML Files (*.kml)')
        if tuple:
            filePaths=tuple[0]
            if filePaths and len(filePaths) > 0:
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
        
        targetDirectory=self.lineEdit_SavePath.text()
        if not targetDirectory:
            self.showMessage(u'레이어 저장 경로를 선택해주세요.')
            return
        
        for filePath in filePaths:
            kmlLayer=QgsVectorLayer(filePath, "kml", "ogr")
            ext=self.getExtension(filePath)
            targetFilePath=filePath.replace(ext, ".shp")
            writer=QgsVectorFileWriter.writeAsVectorFormat(kmlLayer, targetFilePath, "utf-8", QgsCoordinateReferenceSystem(5186), "ESRI Shapefile")
            del writer
            del kmlLayer
            layer=QgsVectorLayer(targetFilePath, self.getFileNameWoExt(targetFilePath), "ogr")
            QgsProject.instance().addMapLayer(layer)
                
        iface.mapCanvas().refreshAllLayers()
        self.showMessage(u'레이어 추가를 완료하였습니다.')
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