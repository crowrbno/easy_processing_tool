# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PluginInfoDialog
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

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'plugin_info_dialog_base.ui'))

class PluginInfoDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PluginInfoDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.pushButton_close.clicked.connect(self.pushButton_close_clicked)
    
    def showEvent(self, event):
        super(PluginInfoDialog, self).showEvent(event)
        
        icon_path = os.path.join(os.path.dirname(__file__), 'icon', 'kofpi_logo.png')
        pixmap=QPixmap(icon_path)
        self.label_kofpi.setPixmap(pixmap)
        
        icon_path = os.path.join(os.path.dirname(__file__), 'icon', 'igis_logo.png')
        pixmap=QPixmap(icon_path)
        self.label_igis.setPixmap(pixmap)
        
    def pushButton_close_clicked(self):
        self.close()