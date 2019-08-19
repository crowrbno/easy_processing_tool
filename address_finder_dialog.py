# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AddressFinderDialog
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
from qgis.gui import *

from .layer_utils import *
from .boundary_utils import *

import queue

DP_SD=u'시도'
DP_SGG=u'시군구'
DP_EMD=u'읍면동'
DP_RI=u'리'
DP_CADASTER=u'지적도'

L_SD=DP_SD
L_SGG=DP_SGG
L_EMD=DP_EMD
L_RI=DP_RI
L_CADASTER=DP_CADASTER

PNU=u'PNU'
SIDO_NM=u'SIDO_NM'
CTP_KOR_NM=u'CTP_KOR_NM'
CTPRV_CD=u'CTPRV_CD'
SGG_NM=u'SGG_NM'
SIDO_CD=u'SIDO_CD'
STD_SGGCD=u'STD_SGGCD'
EMD_NM=u'EMD_NM'
EMD_CD=u'EMD_CD'
RI_NM=u'RI_NM'
RI_CD=u'RI_CD'

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'address_finder_dialog_base.ui'))

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)
    
class AddressFinderDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AddressFinderDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.pushButton_Search.clicked.connect(self.searchAddress)
        self.listWidget.currentItemChanged.connect(self.listWidget_currentItemChanged)
        self.rb = None
        
    def closeEvent(self, event):
        self.removePolyline()
        event.accept()

    def getItemFromQue(self, queue):
        if queue.empty():
            return None
        else:
            return queue.get()
        
    def searchAddress(self):
        self.listWidget.clear()
        
        keyword = self.lineEdit_KeyWord.text()
        if keyword:
            splits = keyword.split()
            q = queue.Queue()
            jibun = u''
            for idx in range(len(splits)):
                split = splits[idx]
                if split == u'산':
                    jibun = split
                elif split.startswith(u'산') and hasNumbers(split):
                    jibun = split
                    break
                elif split[0].isdigit() and split[len(split)-1].isdigit():
                    jibun += split
                    break
                else:
                    q.put(split)
                
            g = self.getItemFromQue(q)
            
            sdCodes = self.searchSDCodes(g)
            if sdCodes and len(sdCodes) > 0:
                g = self.getItemFromQue(q)
            
            sggCodes = []
            if sdCodes and len(sdCodes) > 0:
                for sdCode in sdCodes:
                    sggCodeList = self.searchSGGCodes(g, sdCode)
                    if sggCodeList:
                        sggCodes.extend(sggCodeList)
            else:
                sggCodes = self.searchSGGCodes(g)
            
            if sggCodes and len(sggCodes) > 0:
                g = self.getItemFromQue(q)
                
            emdCodes = []
            if g:
                if sggCodes and len(sggCodes) > 0:
                    for sggCode in sggCodes:
                        emdCodeList = self.searchEMDCodes(g, sggCode)
                        if emdCodeList:
                            emdCodes.extend(emdCodeList)
                else:
                    emdCodes = self.searchEMDCodes(g)
                    
                if emdCodes and len(emdCodes) > 0:
                    g = self.getItemFromQue(q)
            
            riCodes = []
            if g:
                if emdCodes and len(emdCodes) > 0:
                    for emdCode in emdCodes:
                        riCodeList = self.searchRiCodes(g, emdCode)
                        if riCodeList:
                            riCodes.extend(riCodeList)
                else:
                    riCodes = self.searchRiCodes(g)
                
            geometries = {}
            if riCodes and len(riCodes) > 0:
                if jibun:
                    for riCode in riCodes:
                        pnu = riCode + self.generateJibunCode(jibun)
                        geometry = self.getCadasterGeometry(pnu)
                        if geometry:
                            geometries[pnu] = geometry
                else:
                    for riCode in riCodes:
                        geometry = self.getRiGeometry(riCode)
                        if geometry:
                            geometries[riCode] = geometry
                    
            elif emdCodes and len(emdCodes) > 0:
                if jibun:
                    for emdCode in emdCodes:
                        pnu = emdCode + '00' + self.generateJibunCode(jibun)
                        geometry = self.getCadasterGeometry(pnu)
                        if geometry:
                            geometries[pnu] = geometry
                else:
                    for emdCode in emdCodes:
                        geometry = self.getEmdGeometry(emdCode)
                        if geometry:
                            geometries[emdCode] = geometry
                            
            elif sggCodes and len(sggCodes) > 0:
                for sggCode in sggCodes:
                    geometry = self.getSggGeometry(sggCode)
                    if geometry:
                        geometries[sggCode] = geometry
                        
            if len(geometries) > 0:
                for pnu, geometry in geometries.items():
                    address=self.generateAddress(pnu)
                    item=QListWidgetItem(address)
                    item.setData(Qt.UserRole, geometry)
                    self.listWidget.addItem(item)
                    
                self.listWidget.setCurrentRow(0)
            else:
                self.showMessage(u'검색어에 해당하는 결과가 없습니다.')
        else:
            self.showMessage(u'검색어를 입력해주세요.')
    
    def listWidget_currentItemChanged(self, current, previous):
        if current:
            geometry = current.data(Qt.UserRole)
            if geometry:
                bounds = getBound(geometry)
                self.drawPolyline(geometry)
                iface.mapCanvas().zoomToFeatureExtent(bounds)
    
    def drawPolyline(self, geometry):
        canvas = iface.mapCanvas()
        
        self.removePolyline()
        
        points = self.getPointsFromGeometry(geometry)
        
        self.rb = QgsRubberBand(canvas)
        self.rb.setToGeometry(geometry, None)
        self.rb.setColor(QColor(255, 0, 0))
        self.rb.setFillColor(QColor('transparent'))
        self.rb.setWidth(5)
        
    def removePolyline(self):
        canvas = iface.mapCanvas()
        
        if self.rb:
            canvas.scene().removeItem(self.rb)
            self.rb = None
            
    def getSggGeometry(self, sggCode):
        layers=getLayers(L_SGG, DP_SGG)
        if len(layers)>0:
            layer=layers[0]
            request = QgsFeatureRequest()
            request.setFilterExpression(STD_SGGCD + " = '" + sggCode + "'")
            features = layer.getFeatures(request)
            for feature in features:
                return feature.geometry()
                
    def getEmdGeometry(self, emdCode):
        layers=getLayers(L_EMD, DP_EMD)
        if len(layers)>0:
            layer=layers[0]
            request = QgsFeatureRequest()
            request.setFilterExpression(EMD_CD + " = '" + emdCode + "'")
            features = layer.getFeatures(request)
            for feature in features:
                return feature.geometry()
    
    def getRiGeometry(self, riCode):
        layers=getLayers(L_RI, DP_RI)
        if len(layers)>0:
            layer=layers[0]
            request = QgsFeatureRequest()
            request.setFilterExpression(RI_CD + " = '" + riCode + "'")
            features = layer.getFeatures(request)
            for feature in features:
                return feature.geometry()
        
    def getCadasterGeometry(self, pnu):
        layers=getLayers(L_CADASTER, DP_CADASTER)
        if len(layers)>0:
            layer=layers[0]
            request = QgsFeatureRequest()
            request.setFilterExpression(PNU + " = '" + pnu + "'")
            features = layer.getFeatures(request)
            for feature in features:
                return QgsGeometry(feature.geometry())
                
    def getPointsFromGeometry(self, geometry):
        points = None
        if geometry.wkbType() == QgsWkbTypes.MultiPolygon:
            mp = geometry.asMultiPolygon()
            points=mp[0]
        elif geometry.wkbType() == QgsWkbTypes.Polygon:
            points=geometry.asPolygon()
        
        return points
    
    def generateJibunCode(self, jibun):
        code = ''
        if jibun.startswith(u'산'):
            code += '2'
            jibun = jibun.replace(u'산', '')
        else:
            code += '1'
            
        if '-' in jibun:
            splits = jibun.split('-')
            split = splits[0]
            while len(split) < 4:
                split = '0' + split
            code += split
            split = splits[1]
            while len(split) < 4:
                split = '0' + split
            code += split
        else:
            while len(jibun) < 4:
                jibun = '0' + jibun
            code += jibun + '0000'
            
        return code
    
    def generateAddress(self, pnu):
        address=''
        value = self.searchSDName(pnu)
        if value:
            address = value
        
        value = self.searchSGGName(pnu)
        if value:
            address = address + ' ' + value
            
        value = self.searchEMDName(pnu)
        if value:
            address = address + ' ' + value
            
        value = self.searchRiName(pnu)
        if value:
            address = address + ' ' + value
            
        if len(pnu) >= 19:
            mountain = pnu[10]
            mainNo = pnu[11:15]
            subNo = pnu[15:19]
            
            if int(mountain) == 2:
                address = address + ' 산'
                
            if int(mainNo) > 0:
                address = address + ' ' + str(int(mainNo))
                
            if int(subNo) > 0:
                address = address + '-' + str(int(subNo))
            
        return address
    
    def searchSDCodes(self, name):
        if name:
            layers = getLayers(L_SD, DP_SD)
            if len(layers) > 0:
                layer = layers[0]
                request = QgsFeatureRequest()
                request.setFilterExpression(SIDO_NM + " like '%"+ name + "%'")
                features = layer.getFeatures(request)
                codes = []
                for feature in features:
                    codes.append(feature.attribute(SIDO_CD))
                return codes
    
    def searchSDName(self, pnu):
        if pnu:
            if len(pnu) >= 2:
                code = pnu[:2]
                layers = getLayers(L_SD, DP_SD)
                if len(layers) > 0:
                    layer = layers[0]
                    request = QgsFeatureRequest()
                    request.setFilterExpression(SIDO_CD + " = '"+ code + "'")
                    features = layer.getFeatures(request)
                    feature = next(features, None)
                    if feature:
                        return feature.attribute(SIDO_NM)
        return None
            
    def searchSGGCodes(self, name, sdCode = None):
        if name:
            layers = getLayers(L_SGG, DP_SGG)
            if len(layers) > 0:
                layer = layers[0]
                filterExpression = SGG_NM + " like '%"+ name + "%'"
                if sdCode:
                    filterExpression +=  " and " + STD_SGGCD + " like '" + sdCode + "%'"
                request = QgsFeatureRequest()
                request.setFilterExpression(filterExpression)
                features = layer.getFeatures(request)
                codes = []
                for feature in features:
                    codes.append(feature.attribute(STD_SGGCD))
                return codes
            
    def searchSGGName(self, pnu):
        if pnu:
            if len(pnu) >= 5:
                code = pnu[:5]
                layers = getLayers(L_SGG, DP_SGG)
                if len(layers) > 0:
                    layer = layers[0]
                    request = QgsFeatureRequest()
                    request.setFilterExpression(STD_SGGCD + " = '"+ code + "'")
                    features = layer.getFeatures(request)
                    feature = next(features, None)
                    if feature:
                        return feature.attribute(SGG_NM)
        return None
            
    def searchEMDCodes(self, name, sggCode = None):
        if name:
            layers = getLayers(L_EMD, DP_EMD)
            if len(layers) > 0:
                layer = layers[0]
                #filterExpression = EMD_NM + " like '%"+ name + "%'"
                filterExpression = EMD_NM + " = '"+ name + "'"
                if sggCode:
                    filterExpression +=  " and " + EMD_CD + " like '" + sggCode + "%'"
                request = QgsFeatureRequest()
                request.setFilterExpression(filterExpression)
                features = layer.getFeatures(request)
                codes = []
                for feature in features:
                    codes.append(feature.attribute(EMD_CD))
                return codes
            
    def searchEMDName(self, pnu):
        if pnu:
            if len(pnu) >= 8:
                code = pnu[:8]
                layers = getLayers(L_EMD, DP_EMD)
                if len(layers) > 0:
                    layer = layers[0]
                    request = QgsFeatureRequest()
                    request.setFilterExpression(EMD_CD + " = '"+ code + "'")
                    features = layer.getFeatures(request)
                    feature = next(features, None)
                    if feature:
                        return feature.attribute(EMD_NM)
        return None
        
    def searchRiCodes(self, name, emdCode = None):
        if name:
            layers = getLayers(L_RI, DP_RI)
            if len(layers) > 0:
                layer = layers[0]
                #filterExpression = RI_NM + " like '%"+ name + "%'"
                filterExpression = RI_NM + " = '"+ name + "'"
                if emdCode:
                    filterExpression +=  " and " + RI_CD + " like '" + emdCode + "%'"
                request = QgsFeatureRequest()
                request.setFilterExpression(filterExpression)
                features = layer.getFeatures(request)
                codes = []
                for feature in features:
                    codes.append(feature.attribute(RI_CD))
                return codes
    
    def searchRiName(self, pnu):
        if pnu:
            if len(pnu) >= 10:
                code = pnu[:10]
                layers = getLayers(L_RI, DP_RI)
                if len(layers) > 0:
                    layer = layers[0]
                    request = QgsFeatureRequest()
                    request.setFilterExpression(RI_CD + " = '"+ code + "'")
                    features = layer.getFeatures(request)
                    feature = next(features, None)
                    if feature:
                        return feature.attribute(RI_NM)
        return None
        
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