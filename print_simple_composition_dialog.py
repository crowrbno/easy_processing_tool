# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PrintPineWiltDiseaseCompositionDialog
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
from qgis.core import *
from qgis.utils import *
from qgis.analysis import *

from .layer_utils import *
from .boundary_utils import *
from .layout_utils import *

import processing

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'print_simple_composition_dialog_base.ui'))

class PrintSimpleCompositionDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PrintSimpleCompositionDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.progDialog=None
        
        self.pushButton_SetLayerBufferPath.clicked.connect(self.pushButton_SetLayerBufferPath_Clicked)
        self.pushButton_CreateBuffer.clicked.connect(self.pushButton_CreateBuffer_Clicked)
        
        self.comboBox_SiDo.currentIndexChanged.connect(self.comboBox_SiDo_currentIndexChanged)
        self.comboBox_SGG.currentIndexChanged.connect(self.comboBox_SGG_currentIndexChanged)
        self.comboBox_EMD.currentIndexChanged.connect(self.comboBox_EMD_currentIndexChanged)
        
        self.groupBox_SetDistrict.toggled.connect(self.groupBox_SetDistrict_toggled)
        self.groupBox_SetCoordinateAndScale.toggled.connect(self.groupBox_SetCoordinateAndScale_toggled)
        
        self.comboBox_Layers.currentIndexChanged.connect(self.comboBox_Layers_currentIndexChanged)
        
        self.radioButton_PDF.toggled.connect(self.radioButton_toggled)
        self.radioButton_PNG.toggled.connect(self.radioButton_toggled)
        self.radioButton_Printer.toggled.connect(self.radioButton_toggled)
        
        self.pushButton_SetCoordinate.clicked.connect(self.pushButton_SetCoordinate_Clicked)
        self.pushButton_SetSaveFilePath.clicked.connect(self.pushButton_setSavePath_Clicked)
        
        self.pushButton_Apply.clicked.connect(self.pushButton_Apply_Clicked)
        self.pushButton_Print.clicked.connect(self.pushButton_Print_Clicked)
        
    
    def showEvent(self, event):
        super(PrintSimpleCompositionDialog, self).showEvent(event)
        self.initializeComboBox()
        self.initializeLayers()
        self.initializeLegend()
        self.initializeAttributeTable()
        self.initializePrinterComboBox()
        
    def initializeLayers(self):
        layers=getLayers()
        model=QStandardItemModel()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                item=QStandardItem(layer.name())
                item.setData(layer)
                model.appendRow(item)
        
        self.listView_Layers.setModel(model)
        
    def initializeComboBox(self):
        list=getBoundarySDList()
        for boundary in list:
            self.comboBox_SiDo.addItem(boundary.name, boundary)
        
    def initializePrinterComboBox(self):
        defaultPrinterInfo = QPrinterInfo.defaultPrinter()
        
        printerInfos = QPrinterInfo.availablePrinters()
        for printerInfo in printerInfos:
            self.comboBox_Printer.addItem(printerInfo.printerName(), printerInfo)
            
        index = self.comboBox_Printer.findData(defaultPrinterInfo)
        if index >= 0:
            self.comboBox_Printer.setCurrentIndex(index)
            
    def initializeLegend(self):
        layers=getLayers()
        
        model=QStandardItemModel()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                item=QStandardItem(layer.name())
                item.setData(layer)
                model.appendRow(item)
        
        self.listView_Legend.setModel(model)
        
    def initializeAttributeTable(self):
        self.comboBox_Layers.clear()
        layers=getLayers()
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
    
    def comboBox_SiDo_currentIndexChanged(self):
        self.comboBox_SGG.setEnabled(False)
        self.comboBox_SGG.clear()
        index = self.comboBox_SiDo.currentIndex()
        if index >= 0 :
            sido = self.comboBox_SiDo.itemData(index)
            children=sido.getChildren()
            if len(children)>0:
                self.comboBox_SGG.setEnabled(True)
                for sgg in children:
                    self.comboBox_SGG.addItem(sgg.name, sgg)
            
    def comboBox_SGG_currentIndexChanged(self):
        self.comboBox_EMD.setEnabled(False)
        self.comboBox_EMD.clear()
        index = self.comboBox_SGG.currentIndex()
        if index >= 0:
            sgg = self.comboBox_SGG.itemData(index)
            if sgg.name:
                children=sgg.getChildren()
                if len(children)>0:
                    self.comboBox_EMD.setEnabled(True)
                    for emd in children:
                        self.comboBox_EMD.addItem(emd.name, emd)
        
    def comboBox_EMD_currentIndexChanged(self):
        self.comboBox_Ri.setEnabled(False)
        self.comboBox_Ri.clear()
        index = self.comboBox_EMD.currentIndex()
        if index >= 0:
            emd = self.comboBox_EMD.itemData(index)
            if emd.name:
                children=emd.getChildren()
                if len(children)>0:
                    self.comboBox_Ri.setEnabled(True)
                    for ri in children:
                        self.comboBox_Ri.addItem(ri.name, ri)
                
    def comboBox_Layers_currentIndexChanged(self):
        #set attribute columns
        index = self.comboBox_Layers.currentIndex()
        layer=self.comboBox_Layers.itemData(index)
        #get attribute columns of layer
        itemModel=QStandardItemModel()
        if layer:
            fields=layer.fields()
            for field in fields:
                item=QStandardItem(field.name())
                item.setData(field)
                itemModel.appendRow(item)
            
        self.listView_AttributeTable.setModel(itemModel)
                
    def getLayer(self, layerName):
        project = QgsProject.instance()
        
        layerTreeRoot = project.layerTreeRoot()
        
        treeLayers = layerTreeRoot.findLayers()
        
        layers = []
        for treeLayer in treeLayers:
            layers.append(treeLayer.layer())
            
        emdLayerMatches = [layer for layer in layers if layer.name() == layerName]
        
        layer = None
        
        if len(emdLayerMatches) > 0:
            layer = emdLayerMatches[0]
        
        return layer
            
    def radioButton_toggled(self, checked):
        self.lineEdit_SaveFilePath.setEnabled(self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked())
        self.pushButton_SetSaveFilePath.setEnabled(self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked())
        self.comboBox_Printer.setEnabled(self.radioButton_Printer.isChecked())
        
        self.lineEdit_SaveFilePath.setText('')
                
    def pushButton_SetLayerBufferPath_Clicked(self):
        tuple=QFileDialog.getSaveFileName(self, u'저장 경로 설정', QgsProject.instance().homePath(), 'Shape Files (*.shp)')
        if tuple:
            fileName=tuple[0]
            self.lineEdit_LayerBufferPath.setText(fileName)
        
    def pushButton_CreateBuffer_Clicked(self):
        saveFilePath=self.lineEdit_LayerBufferPath.text()
        if not saveFilePath:
            self.showMessage(u'버퍼를 저장 경로 선택해주세요.')
            return
        indexes=self.listView_Layers.selectedIndexes()
        model=self.listView_Layers.model()
        selectedLayers=[]
        for index in indexes:
            item=model.itemFromIndex(index)
            layer=item.data()
            selectedLayers.append(layer)
            
        if len(selectedLayers)<=0:
            self.showMessage(u'버퍼를 생성할 레이어를 선택해주세요.')
            return
        try:
            bufferDistance=float(self.lineEdit_BufferRadius.text())
        except:
            self.showMessage(u'버퍼 반경을 입력해주세요.')
            return
            
        try:
            segments=float(self.lineEdit_Segments.text())
        except:
            self.showMessage(u'세그먼트를 입력해주세요.')
            return
        '''
        bufferedLayers=[]
        for layer in selectedLayers:
            res=processing.run('native:buffer', { "INPUT": layer, "DISTANCE": bufferDistance, "SEGMENTS": segments, "DISSOLVE": True, "OUTPUT": "memory:"})
            
            if res and res['OUTPUT']:
                bufferedLayer=res['OUTPUT']
                bufferedLayers.append(bufferedLayer)
        
        if len(bufferedLayers)<=0:
            self.showMessage(u'버퍼를 성공한 레이어가 없습니다.')
            return
        '''
        
        if self.progDialog is None:
            self.progDialog=QProgressDialog(self)
            self.progDialog.setWindowTitle(self.windowTitle())
            self.progDialog.setLabelText('버퍼 생성 중 ...')
            self.progDialog.setModal(True)
            self.progDialog.setCancelButton(None)
            
        self.task=QgsTask.fromFunction('버퍼 생성', self.runBuffer, selectedLayers, bufferDistance, segments, saveFilePath)
        
        self.task.taskCompleted.connect(self.bufferTaskCompleted)
        self.task.taskTerminated.connect(self.bufferTaskCompleted)
        self.task.progressChanged.connect(self.progDialog.setValue)
        
        QgsApplication.taskManager().addTask(self.task)
        
        self.setEnabled(False)
        
    def bufferTaskCompleted(self):
        if self.bufferResult:
            saveFilePath=self.bufferResult
            fileName=self.getFileNameWoExt(saveFilePath)
            qvl=QgsVectorLayer(saveFilePath, fileName, 'ogr')
            symbol=qvl.renderer().symbol()
            oldColor=QColor(symbol.color())
            oldColor.setAlpha(51)
            symbol.setColor(oldColor)
            QgsProject.instance().addMapLayer(qvl)
            #iface.layerTreeView().refreshLayerSymbology(qvl.id())
            iface.mapCanvas().refreshAllLayers()
            self.initializeLayers()
            self.initializeLegend()
            self.initializeAttributeTable()
            
        self.progDialog.close()
        self.progDialog=None
        self.setEnabled(True)
        self.showMessage(self.taskMessage)
    
    def runBuffer(self, task, selectedLayers, bufferDistance, segments, saveFilePath):
        feedback=QgsProcessingFeedback()
        feedback.progressChanged.connect(task.setProgress)
        bufferedLayers=[]
        for layer in selectedLayers:
            res=processing.run('native:buffer', { "INPUT": layer, "DISTANCE": bufferDistance, "SEGMENTS": segments, "DISSOLVE": True, "OUTPUT": "memory:"}, feedback=feedback)
            
            if res and res['OUTPUT']:
                bufferedLayer=res['OUTPUT']
                bufferedLayers.append(bufferedLayer)
        
        if len(bufferedLayers)<=0:
            self.taskMessage='버퍼를 성공한 레이어가 없습니다.'
            return
        
        provider=bufferedLayers[0].dataProvider()
        crs=provider.crs().authid()
        uri='Polygon?crs={}'.format(crs)
        
        mergedLayer=QgsVectorLayer(uri, '', 'memory')
        mergedLayer.startEditing()
        
        feature=QgsFeature(mergedLayer.dataProvider().fields())
        for layer in bufferedLayers:
            for bufferedFeature in layer.getFeatures():
                feature.setGeometry(bufferedFeature.geometry())
                mergedLayer.dataProvider().addFeatures([feature])
                mergedLayer.updateExtents()
                
        mergedLayer.commitChanges()
        
        del bufferedLayers
        
        if processing.run('native:dissolve', {'FIELD' : [], "INPUT": mergedLayer, "OUTPUT": saveFilePath}, feedback=feedback):
            self.bufferResult=saveFilePath
            self.taskMessage='버퍼 생성을 완료하였습니다.'
        else:
            self.taskMessage='버퍼 생성을 실패하였습니다.'
            
        del mergedLayer
            
    def getFileNameWoExt(self, path):
        return os.path.splitext(os.path.basename(path))[0]
        
    def pushButton_Apply_Clicked(self):
        targetLayoutName=u'단순 구성'
        targetLayout=getLayout(targetLayoutName)
        if not targetLayout:
            pass
        
        targetLayoutDesigner=None
        openLayoutDesigners=iface.openLayoutDesigners()
        for openLayoutDesigner in openLayoutDesigners:
            layout=openLayoutDesigner.layout()
            if targetLayout != layout:
                openLayoutDesigner.close()
                
        iface.openLayoutDesigner(targetLayout)
        
        #set title
        title=self.lineEdit_Title.text()
        item=getLayoutItemById(targetLayout, 'title')
        item.setText(title)
        
        #set legend
        checked=self.groupBox_Legend.isChecked()
        legendItem=getLayoutItemById(targetLayout, 'legend')
        legendItem.setVisibility(checked)
        if checked:
            indexes=self.listView_Legend.selectedIndexes()
            model=self.listView_Legend.model()
            selectedLayers=[]
            for index in indexes:
                item=model.itemFromIndex(index)
                layer=item.data()
                selectedLayers.append(layer)
            
            legendItem.setAutoUpdateModel(True)
            legendItem.updateLegend()
            legendItem.setAutoUpdateModel(False)
            
            rootGroup=self.buildingLegendLayerTree(legendItem.model().rootGroup(), selectedLayers)
            legendItem.model().setRootGroup(rootGroup)
        
        #set attributetable
        checked=self.groupBox_AttributeTable.isChecked()
        item=getLayoutItemById(targetLayout, 'attributetable')
        item.setVisibility(checked)
        if checked:
            attributetableItem=item.multiFrame()
            
            index=self.comboBox_Layers.currentIndex()
            layer=self.comboBox_Layers.itemData(index)
            attributetableItem.setVectorLayer(layer)
            
            #listview selected items
            indexes=self.listView_AttributeTable.selectedIndexes()
            model=self.listView_AttributeTable.model()
            selectedFields=[]
            for index in indexes:
                fieldName=model.data(index)
                selectedFields.append(fieldName)
            
            attributetableItem.setDisplayedFields(selectedFields)
        
        #set scalebar
        checked=self.checkBox_ScaleBar.isChecked()
        scalebarItem=getLayoutItemById(targetLayout, 'scalebar')
        scalebarItem.setVisibility(checked)
        
        #set northarrow
        checked=self.checkBox_NorthArrow.isChecked()
        northarrowItem=getLayoutItemById(targetLayout, 'northarrow')
        northarrowItem.setVisibility(checked)
        
        #Set Map
        mapItem = getLayoutItemById(targetLayout, 'map_main')
        if self.groupBox_SetDistrict.isChecked():
            bound = self.getBounds()
            mapItem.zoomToExtent(bound)
        else:
            x=int(self.lineEdit_X.text())
            y=int(self.lineEdit_Y.text())
            scale=int(self.lineEdit_Scale.text())
            extent=mapItem.extent()
            extent.scale(1, x, y)
            mapItem.setExtent(extent)
            mapItem.setScale(scale)
            
        targetLayout.deselectAll()
        targetLayout.refresh()
        
    def buildingLegendLayerTree(self, parent, layers):
        for child in parent.children():
            if child.nodeType()==0:
                child=self.buildingLegendLayerTree(child, layers)
            else:
                if child.layer() not in layers:
                    parent.removeChildNode(child)
                    
        return parent
        
    def getBounds(self):
        index=self.comboBox_Ri.currentIndex()
        if index>=0:
            data=self.comboBox_Ri.itemData(index)
            if data.bound:
                return data.bound
                
        index=self.comboBox_EMD.currentIndex()
        if index>=0:
            data=self.comboBox_EMD.itemData(index)
            if data.bound:
                return data.bound
            
        index=self.comboBox_SGG.currentIndex()
        if index>=0:
            data=self.comboBox_SGG.itemData(index)
            if data.bound:
                return data.bound
        
        index=self.comboBox_SiDo.currentIndex()
        if index>=0:
            data=self.comboBox_SiDo.itemData(index)
            if data.bound:
                return data.bound
            
    def pushButton_SetCoordinate_Clicked(self):
        mapcanvas=iface.mapCanvas()
        center=mapcanvas.center()
        x=int(center.x())
        y=int(center.y())
        self.lineEdit_X.setText(str(x))
        self.lineEdit_Y.setText(str(y))
        
    def pushButton_setSavePath_Clicked(self):
        if self.radioButton_PDF.isChecked():
            tuple=QFileDialog.getSaveFileName(self, u'경로 지정', QgsProject.instance().homePath(), 'PDF (*.pdf)')
            if tuple:
                fileName=tuple[0]
                self.lineEdit_SaveFilePath.setText(fileName)
        elif self.radioButton_PNG.isChecked():
            tuple=QFileDialog.getSaveFileName(self, u'경로 지정', QgsProject.instance().homePath(), 'Images (*.png)')
            if tuple:
                fileName=tuple[0]
                self.lineEdit_SaveFilePath.setText(fileName)
    
    def pushButton_Print_Clicked(self):
        targetLayout=getLayout('단순 구성')
        
        self.progressDialog=None
        self.task=None
        if self.radioButton_PDF.isChecked():
            savePath = self.lineEdit_SaveFilePath.text()
            if not savePath:
                self.showMessage(u'파일 경로를 설정해주세요.')
                return
            exporter = QgsLayoutExporter(targetLayout)
            self.task=QgsTask.fromFunction('PDF 출력', self.exportToPdf, exporter=exporter, savePath=savePath)
            self.task.completeMessage='PDF 저장을 완료하였습니다.\n저장 경로 :' + savePath
            self.task.terminateMessage='PDF 저장을 실패하였습니다.'
        elif self.radioButton_PNG.isChecked():
            savePath = self.lineEdit_SaveFilePath.text()
            if not savePath:
                self.showMessage(u'파일 경로를 설정해주세요.')
                return
            exporter = QgsLayoutExporter(targetLayout)
            self.task=QgsTask.fromFunction('이미지 출력', self.exportToImage, exporter=exporter, savePath=savePath)
            self.task.completeMessage='이미지 저장을 완료하였습니다.\n저장 경로 :' + savePath
            self.task.terminateMessage='이미지 저장을 실패하였습니다.'
        elif self.radioButton_Printer.isChecked():
            index = self.comboBox_Printer.currentIndex()
            printerInfo = self.comboBox_Printer.itemData(index)
            printer = QPrinter(printerInfo)
            printer.setOrientation(QPrinter.Landscape)
            printer.setPageSize(QPageSize(QPageSize.A3))
            printer.setFullPage(True)
            exporter = QgsLayoutExporter(targetLayout)
            self.task=QgsTask.fromFunction('프린터 출력', self.print, exporter=exporter, printer=printer)
            self.task.completeMessage='프린트를 완료하였습니다.'
            self.task.terminateMessage='프린트를 실패하였습니다.'
            
        if self.task:
            self.task.taskCompleted.connect(self.taskCompleted)
            self.task.taskTerminated.connect(self.taskTerminated)
            
            QgsApplication.taskManager().addTask(self.task)
            
            self.progressDialog = QProgressDialog(self)
            self.progressDialog.setModal(True)
            self.progressDialog.setWindowTitle('레이아웃 출력')
            self.progressDialog.setLabelText('레이아웃 출력 중...')
            self.progressDialog.setCancelButton(None)
            self.progressDialog.setMinimum(0)
            self.progressDialog.setMaximum(0)
            self.progressDialog.setValue(0)
            self.progressDialog.show()
            
    def taskCompleted(self):
        self.closeProgressDialog()
        if self.task:
            self.showMessage(self.task.completeMessage)
        self.task=None
        pass
        
    def taskTerminated(self):
        self.closeProgressDialog()
        if self.task:
            self.showMessage(self.task.terminateMessage)
        self.task=None
        pass
        
    def closeProgressDialog(self):
        if self.progressDialog:
            self.progressDialog.close()
            del self.progressDialog
            
    def exportToPdf(self, task, exporter, savePath):
        exporter.exportToPdf(savePath, QgsLayoutExporter.PdfExportSettings())
        
    def exportToImage(self, task, exporter, savePath):
        exporter.exportToImage(savePath, QgsLayoutExporter.ImageExportSettings())
        
    def print(self, task, exporter, printer):
        exporter.print(printer, QgsLayoutExporter.PrintExportSettings())
            
    def groupBox_SetDistrict_toggled(self, checked):
        self.groupBox_SetCoordinateAndScale.setChecked(not checked)
        
    def groupBox_SetCoordinateAndScale_toggled(self, checked):
        self.groupBox_SetDistrict.setChecked(not checked)
        
    def showMessage(self, text, title=''):
        msg = QMessageBox()
        msg.setText(text)
        if title:
            msg.setWindowTitle(title)
        else:
            msg.setWindowTitle(self.windowTitle())
        msg.exec_()