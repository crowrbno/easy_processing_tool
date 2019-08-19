# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoCodingDialog
                                 A QGIS plugin
 주소 입력
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

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'geo_coding_dialog_base.ui'))

DP_SGG=u'시군구'
DP_EMD=u'읍면동'
DP_RI=u'리'
DP_CADASTER=u'지적도'

L_SGG=DP_SGG
L_EMD=DP_EMD
L_RI=DP_RI
L_CADASTER=DP_CADASTER

PNU=u'PNU'
CTP_KOR_NM=u'CTP_KOR_NM'
CTPRV_CD=u'CTPRV_CD'
SGG_NM=u'SGG_NM'
STD_SGGCD=u'STD_SGGCD'
EMD_NM=u'EMD_NM'
EMD_CD=u'EMD_CD'
RI_NM=u'RI_NM'
RI_CD=u'RI_CD'

MT_KR=u'산'
MNUM_KR=u'본번'
SNUM_KR=u'부번'
ADDRESS_KR=u'주소'

def showMessage(text, title=''):
    msg = QMessageBox()
    msg.setText(text)
    msg.exec_()    
    
def getFeaturesByGeometry(layer, geometry):
    featureRequest=QgsFeatureRequest(geometry.boundingBox())
    return layer.getFeatures(featureRequest)
    
def getPNU(geometry):
    requestLayer=None
    for layer in getLayers(L_CADASTER, DP_CADASTER):
        requestLayer=layer
        break
            
    if requestLayer:
        features=getFeaturesByGeometry(requestLayer, geometry)
        for feature in features:
            return feature.attribute(PNU)
    
def getSDName(pnu):
    layers=getLayers(L_SGG)
    requestLayer=None
    for layer in layers:
        dpName=getDataProviderUriName(layer.dataProvider())
        if dpName==DP_SGG:
            requestLayer=layer
            break
    if requestLayer:
        code=pnu[:2]
        request=QgsFeatureRequest()
        request.setFilterExpression(CTPRV_CD+'='+code)
        features=requestLayer.getFeatures(request)
        for feature in features:
            return feature.attribute(CTP_KOR_NM)

def getSGGName(pnu):
    layers=getLayers(L_SGG)
    requestLayer=None
    for layer in layers:
        dpName=getDataProviderUriName(layer.dataProvider())
        if dpName==DP_SGG:
            requestLayer=layer
            break
    if requestLayer:
        code=pnu[:5]
        request=QgsFeatureRequest()
        request.setFilterExpression(STD_SGGCD+'='+code)
        features=requestLayer.getFeatures(request)
        for feature in features:
            return feature.attribute(SGG_NM)

def getEMDName(pnu):
    layers=getLayers(L_EMD)
    requestLayer=None
    for layer in layers:
        dpName=getDataProviderUriName(layer.dataProvider())
        if dpName==DP_EMD:
            requestLayer=layer
            break
    if requestLayer:
        code=pnu[:8]
        request=QgsFeatureRequest()
        request.setFilterExpression(EMD_CD+'='+code)
        features=requestLayer.getFeatures(request)
        for feature in features:
            return feature.attribute(EMD_NM)
    
def getRIName(pnu):
    layers=getLayers(L_RI)
    requestLayer=None
    for layer in layers:
        dpName=getDataProviderUriName(layer.dataProvider())
        if dpName==DP_RI:
            requestLayer=layer
            break
    if requestLayer:
        code=pnu[:10]
        request=QgsFeatureRequest()
        request.setFilterExpression(RI_CD+'='+code)
        features=requestLayer.getFeatures(request)
        for feature in features:
            return feature.attribute(RI_NM)
    
def isMountain(pnu):
    code=pnu[10:]
    try:
        return int(code[0])==2
    except:
        return False
    
def getMasterNum(pnu):
    code=pnu[10:]
    masterNum=code[1:5]
    return int(masterNum)
    
def getSubNum(pnu):
    code=pnu[10:]
    subNum=code[5:]
    subNum=int(subNum)
    return subNum if not 0 else None 
    
def getDataProviderUriName(dataProvider):
    uri=dataProvider.dataSourceUri()
    return os.path.splitext(os.path.basename(uri))[0]
    
class GeoCodingDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(GeoCodingDialog, self).__init__(parent)
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
        super(GeoCodingDialog, self).showEvent(event)
        
        model=QStandardItemModel()
        for layer in getLayers():
            if isinstance(layer, QgsVectorLayer) and layer.geometryType()==QgsWkbTypes.PointGeometry:
                item=QStandardItem(layer.name())
                item.setData(layer)
                model.appendRow(item)
        
        self.listView_Layers.setModel(model)
    
    def pushButton_OK_Clicked(self):
        indexes=self.listView_Layers.selectedIndexes()
        model=self.listView_Layers.model()
        layers=[]
        for index in indexes:
            item=model.itemFromIndex(index)
            layer=item.data()
            layers.append(layer)
        
        if len(layers)<=0:
            self.showMessage(u'대상 레이어를 선택해주세요.')
            return
        
        task=QgsTask.fromFunction('주소 입력', self.run, layers=layers)
        task.taskCompleted.connect(self.taskCompleted)
        task.taskTerminated.connect(self.taskCompleted)
        
        QgsApplication.taskManager().addTask(task)
            
        self.progressDialog = QProgressDialog(self)
        self.progressDialog.setModal(True)
        self.progressDialog.setWindowTitle('주소 입력')
        self.progressDialog.setLabelText('주소 입력 중...')
        self.progressDialog.setCancelButton(None)
        self.progressDialog.show()
        
        task.progressChanged.connect(self.progressDialog.setValue)
        
        self.setEnabled(False)
        
    def taskCompleted(self):
        self.setEnabled(True)
        self.closeProgressDialog()
        self.showMessage('주소 생성을 완료하였습니다.')
        self.close()
        
    def closeProgressDialog(self):
        if self.progressDialog:
            self.progressDialog.close()
            del self.progressDialog
        
    def run(self, task, layers):
        task.setProgress(0)
        
        for layer in layers:
            if layer.isEditable():
                layer.commitChanges()
                
            dataProvider=layer.dataProvider()
            dataProvider.addAttributes([QgsField(PNU, QVariant.String), QgsField(CTP_KOR_NM, QVariant.String), QgsField(SGG_NM, QVariant.String), QgsField(EMD_NM, QVariant.String), QgsField(RI_NM, QVariant.String), QgsField(MT_KR, QVariant.String), QgsField(MNUM_KR, QVariant.String), QgsField(SNUM_KR, QVariant.String), QgsField(ADDRESS_KR, QVariant.String, 'char', 250)])
            layer.updateFields()
            layer.startEditing()
            
            count=0
            totalCount=layer.featureCount()
            for feature in layer.getFeatures():
                try:
                    geometry=feature.geometry()
                    pnu=getPNU(geometry)
                    if pnu:
                        feature[PNU]=pnu
                        sdName=getSDName(pnu)
                        feature[CTP_KOR_NM]=sdName
                        address=sdName
                        sggName=getSGGName(pnu)
                        if sggName:
                            address+=' '+sggName
                        feature[SGG_NM]=sggName
                        emdName=getEMDName(pnu)
                        feature[EMD_NM]=emdName
                        if emdName:
                            address+=' '+emdName
                        riName=getRIName(pnu)
                        feature[RI_NM]=riName
                        if riName:
                            address+=' '+riName
                        if isMountain(pnu):
                            feature[MT_KR]=MT_KR
                            address+=' '+MT_KR
                        mNum=getMasterNum(pnu)
                        feature[MNUM_KR]=str(mNum)
                        if mNum:
                            address+=' '+str(mNum)
                        snum=getSubNum(pnu)
                        if snum:
                            feature[SNUM_KR]=str(snum)
                            address+='-'+str(snum)
                        feature[ADDRESS_KR]=address
                        layer.updateFeature(feature)
                        
                    count=count+1
                    percentage=count*100/totalCount
                    task.setProgress(percentage)
                except:
                    self.writeLog(u"Unexcepted error :" + str(traceback.format_exc()))
                    
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
        
    def writeLog(self, message):
        QgsMessageLog.logMessage(message, 'PrintPineWiltDiseaseComposition')