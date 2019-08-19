# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PrintPineWiltDiseaseCompositionExcelDialog
                                 A QGIS plugin
 소나무재선충병 구성 출력 자동화 (엑셀)
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

from openpyxl import *

from .boundary_utils import *
from .layout_utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'print_pwd_composition_excel_dialog_base.ui'))

class PrintPineWiltDiseaseCompositionExcelDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PrintPineWiltDiseaseCompositionExcelDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.radioButton_PDF.toggled.connect(self.radioButton_toggled)
        self.radioButton_PNG.toggled.connect(self.radioButton_toggled)
        self.radioButton_Printer.toggled.connect(self.radioButton_toggled)
        
        self.pushButton_SetSaveFilePath.clicked.connect(self.pushButton_setSavePath_Clicked)
        
        self.pushButton_Print.clicked.connect(self.pushButton_Print_Clicked)
        self.pushButton_OpenExcelFile.clicked.connect(self.pushButton_OpenExcelFile_Clicked)
        
        self.sidoList=getBoundarySDList()
        
        tableWidget = self.tableWidget;
        tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tableWidget.setColumnCount(17);
        columnHeaders = [u'시도', u'시군구', u'읍면동', u'리', u'제목', u'산림면적', u'소나무면적', u'최초발생연도', u'최초발생장소', u'구분1', u'수량1', u'구분2', u'수량2', u'구분3', u'수량3', u'정보항목위치', u'스케일바위치']
        tableWidget.setHorizontalHeaderLabels(columnHeaders)
        
    
    def showEvent(self, event):
        super(PrintPineWiltDiseaseCompositionExcelDialog, self).showEvent(event)
        
        self.initializePrinterComboBox()
        
    def initializePrinterComboBox(self):
        defaultPrinterInfo = QPrinterInfo.defaultPrinter()
        
        printerInfos = QPrinterInfo.availablePrinters()
        for printerInfo in printerInfos:
            self.comboBox_Printer.addItem(printerInfo.printerName(), printerInfo)
            
        index = self.comboBox_Printer.findData(defaultPrinterInfo)
        if index >= 0:
            self.comboBox_Printer.setCurrentIndex(index)
                
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
        
    def pushButton_OpenExcelFile_Clicked(self):
        tuple=QFileDialog.getOpenFileName(self, u'엑셀 파일 열기', QgsProject.instance().homePath(), 'Excel Files (*.xls *.xlsx)')
        if tuple:
            fileName=tuple[0]
            if not fileName:
                return
            else:
                self.lineEdit_ExcelFilePath.setText(fileName)
                self.openExcelFile(fileName)
            
    def openExcelFile(self, fileName):
        wb = load_workbook(fileName)
        ws = wb.active
        
        count=3
        
        rows=[]
        while True:
            row = self.getExcelRow(ws, count)
            if not row:
                break
            else:
                rows.append(row)
            count = count+1
        
        rowCount=0
        tableWidget = self.tableWidget
        tableWidget.setRowCount(0)
        tableWidget.setRowCount(len(rows))
        for row in rows:
            columnCount=0
            for value in row:
                if value:
                    tableWidget.setItem(rowCount, columnCount, QTableWidgetItem(str(value)))
                columnCount=columnCount+1
            rowCount=rowCount+1
        
    def getExcelRow(self, sheet, rowIndex):
        row = []
        row.append(sheet['A'+str(rowIndex)].value)
        row.append(sheet['B'+str(rowIndex)].value)
        row.append(sheet['C'+str(rowIndex)].value)
        row.append(sheet['D'+str(rowIndex)].value)
        row.append(sheet['E'+str(rowIndex)].value)
        row.append(sheet['F'+str(rowIndex)].value)
        row.append(sheet['G'+str(rowIndex)].value)
        row.append(sheet['H'+str(rowIndex)].value)
        row.append(sheet['I'+str(rowIndex)].value)
        row.append(sheet['J'+str(rowIndex)].value)
        row.append(sheet['K'+str(rowIndex)].value)
        row.append(sheet['L'+str(rowIndex)].value)
        row.append(sheet['M'+str(rowIndex)].value)
        row.append(sheet['N'+str(rowIndex)].value)
        row.append(sheet['O'+str(rowIndex)].value)
        row.append(sheet['P'+str(rowIndex)].value)
        row.append(sheet['Q'+str(rowIndex)].value)
        
        if not row[0]:
            return None
            
        return row;

    def getFontSize(self, text):
        strLen=len(text)
        if strLen>=10:
            return 16
        elif strLen==9:
            return 18
        elif strLen==8:
            return 20
        elif strLen==7:
            return 22
        elif strLen==6:
            return 24
        return 28

    def setLayout(self, values):
        bounds=values['bounds']
        title=values['title']
        forestArea=values['forestArea']
        finewiltArea=values['finewiltArea']
        firstOccuredTime=values['firstOccuredTime']
        firstOccuredPlace=values['firstOccuredPlace']
        text_0_0=values['t_0_0']
        text_0_1=values['t_0_1']
        text_1_0=values['t_1_0']
        text_1_1=values['t_1_1']
        text_2_0=values['t_2_0']
        text_2_1=values['t_2_1']
        isLeftInfo=values['isLeftInfo']
        isLeftScale=values['isLeftScale']
        
        targetLayoutName=u'소나무재선충병 R'
        if isLeftInfo:
            targetLayoutName=u'소나무재선충병 L'

        targetLayout=getLayout(targetLayoutName)
        if not targetLayout:
            pass
        
        #title
        item=getLayoutItemById(targetLayout, 'title')
        if title is not None:
            item.setText(title)
            fontSize=self.getFontSize(title)
            font=item.font()
            font.setPointSize(fontSize)
            item.setFont(font)

        #forestArea
        item = getLayoutItemById(targetLayout, 'forestArea')
        if forestArea is not None:
            item.setText(forestArea)
        
        #finewiltArea
        item = getLayoutItemById(targetLayout, 'finewiltArea')
        if finewiltArea is not None:
            item.setText(finewiltArea)
        
        #firstOccuredTime
        item = getLayoutItemById(targetLayout, 'firstOccuredTime')
        if firstOccuredTime is not None:
            item.setText(u'· 최초발생(' + firstOccuredTime + u')')
        
        #firstOccuredPlace
        item = getLayoutItemById(targetLayout, 'firstOccuredPlace')
        if firstOccuredPlace is not None:
            item.setText(u' - ' + firstOccuredPlace)
        
        #table_0_0
        item = getLayoutItemById(targetLayout, 'table_0_0')
        if text_0_0 is not None:
            item.setText(text_0_0)
            text = text_0_0.replace(u'년', '')
            item = getLayoutItemById(targetLayout, 'axisX_0')
            item.setText(text)
        
        #table_0_1
        item = getLayoutItemById(targetLayout, 'table_0_1')
        t0 = '0'
        if text_0_1 is not None:
            t0 = text_0_1.replace(',', '')
        v0 = int(t0)
        item.setText("{:,}".format(v0))
        
        #table_1_0
        item = getLayoutItemById(targetLayout, 'table_1_0')
        if text_1_0 is not None:
            item.setText(text_1_0)
            text = text_1_0.replace(u'년', '')
            item = getLayoutItemById(targetLayout, 'axisX_1')
            item.setText(text)
        
        #table_1_1
        t1 = '0'
        item = getLayoutItemById(targetLayout, 'table_1_1')
        if text_1_1 is not None:
            t1 = text_1_1.replace(',', '')
        v1 = int(t1)
        item.setText("{:,}".format(v1))
        
        #table_2_0
        item = getLayoutItemById(targetLayout, 'table_2_0')
        if text_2_0 is not None:
            item.setText(text_2_0)
            text = text_2_0.replace(u'년', '')
            item = getLayoutItemById(targetLayout, 'axisX_2')
            item.setText(text)
        
        #table_2_1
        item = getLayoutItemById(targetLayout, 'table_2_1')
        t2 = '0'
        if text_2_1 is not None:
            t2 = text_2_1.replace(',', '')
        v2 = int(t2)
        item.setText("{:,}".format(v2))
        
        #Graph
        intervalList = [5, 10, 25]
        
        n = [int(t0), int(t1), int(t2)]
        
        maxValue = max(n)
        
        maxAxisY = None
        
        power = 0
        while True:
            for interval in intervalList:
                v = interval * (10**power)
                if maxValue <= v:
                    maxAxisY = v
                    break
            
            if maxAxisY != None:
                break
                
            power += 1
        
        interval = maxAxisY / 5
        
        for i in range(6):
            item = getLayoutItemById(targetLayout, 'axisY_' + str(i))
            item.setText("{:,}".format(int(interval) * i))
        
        
        for i in range(3):
            height = n[i] * 25 / maxAxisY
            item = getLayoutItemById(targetLayout, 'bar_' + str(i))
            if height <= 0 : height = 0.1
            item.setFixedSize(QgsLayoutSize(5, height))
            item.setY(195.6)
            item.refresh()
        
        #Set Map
        item = getLayoutItemById(targetLayout, 'map_main')
        item.zoomToExtent(bounds)

        #scalebar
        x=5
        if isLeftInfo:
            x+=75
        if not isLeftScale:
            x+=285
        item=getLayoutItemById(targetLayout, 'scalebar')
        item.setX(x)
        
        targetLayout.deselectAll()
        targetLayout.refresh()

        return targetLayout
        
    def getBoundsByName(self, sidoName, sggName, emdName, riName):
        if sidoName:
            sido=self.getMatchByName(self.sidoList, sidoName)
            if sido:
                if sggName:
                    sgg=self.getMatchByName(sido.getChildren(), sggName)
                    if sgg:
                        if emdName:
                            emd=self.getMatchByName(sgg.getChildren(), emdName)
                            if emd:
                                if riName:
                                    ri=self.getMatchByName(emd.getChildren(), riName)
                                    if ri:
                                        return ri.bound
                                else:
                                    return emd.bound
                        else:
                            return sgg.bound
                else:
                    return sido.bound
    
    def getMatchByName(self, list, name):
        matches=[item for item in list if item.name==name]
        if len(matches)>0:
            return matches[0]
        return None
            
    def pushButton_setSavePath_Clicked(self):
        if self.radioButton_PDF.isChecked() or self.radioButton_PNG.isChecked():
            dir = QFileDialog.getExistingDirectory(self, u'폴더 지정', QgsProject.instance().homePath(), QFileDialog.ShowDirsOnly)
            self.lineEdit_SaveFilePath.setText(dir)
    
    def getSelectedRows(self):
        tableWidget=self.tableWidget
        selectionModel=tableWidget.selectionModel()
        rows=[]
        for selectedCell in selectionModel.selectedRows():
            rowIndex = selectedCell.row()
            row=[]
            for columIndex in range(0, tableWidget.columnCount()):
                item = tableWidget.item(rowIndex, columIndex)
                if item:
                    row.append(item.text())
                else:
                    row.append(None)
            rows.append(row)
        return rows
        
    def pushButton_Print_Clicked(self):
        selectedRows = self.getSelectedRows()
            
        if len(selectedRows)<=0:
            self.showMessage(u'출력할 항목을 선택해주세요.', u'출력 설정')
            return
        
        self.setEnabled(False)
        
        count=0
        totalCount=len(selectedRows)
        self.setProgress(0)
        
        if self.radioButton_PDF.isChecked():
            savePath = self.lineEdit_SaveFilePath.text()
            if not savePath:
                msg = QMessageBox()
                msg.setText(u'파일 경로를 설정해주세요.')
                msg.setWindowTitle(u'파일 경로 설정')
                msg.exec_()
                return
            
            for selectedRow in selectedRows:
                try:
                    values=self.getValues(selectedRow)

                    targetLayout=self.setLayout(values)
                    
                    fileName=''
                    if values['sido']:
                        fileName+=values['sido']
                    if values['sgg']:
                        fileName+='_'+values['sgg']
                    if values['emd']:
                        fileName+='_'+values['emd']
                    if values['ri']:
                        fileName+='_'+values['ri']
                    fileName+='.pdf'
                    
                    saveFilePath = savePath+'\\'+fileName
                    exporter = QgsLayoutExporter(targetLayout)
                    exporter.exportToPdf(saveFilePath, QgsLayoutExporter.PdfExportSettings())
                except:
                    self.writeLog(u"Unexcepted error :" + str(traceback.format_exc()))
                    
                count=count+1
                percentage=count*100/totalCount
                self.setProgress(percentage)
                
            self.setProgress(100)
                
            self.showMessage(u'PDF 저장을 완료하였습니다.\n저장 경로 :' + savePath)
            
        elif self.radioButton_PNG.isChecked():
            savePath = self.lineEdit_SaveFilePath.text()
            if not savePath:
                msg = QMessageBox()
                msg.setText(u'파일 경로를 설정해주세요.')
                msg.setWindowTitle(u'파일 경로 설정')
                msg.exec_()
                return
                
            for selectedRow in selectedRows:
                try:
                    values=self.getValues(selectedRow)

                    targetLayout=self.setLayout(values)
                    
                    fileName=''
                    if values['sido']:
                        fileName+=values['sido']
                    if values['sgg']:
                        fileName+='_'+values['sgg']
                    if values['emd']:
                        fileName+='_'+values['emd']
                    if values['ri']:
                        fileName+='_'+values['ri']
                    fileName+='.png'
                    
                    saveFilePath = savePath+'\\'+fileName
                    exporter = QgsLayoutExporter(targetLayout)
                    exporter.exportToImage(saveFilePath, QgsLayoutExporter.ImageExportSettings())
                except:
                    self.writeLog(u"Unexcepted error :" + str(traceback.format_exc()))
                    
                count=count+1
                percentage=count*100/totalCount
                self.setProgress(percentage)
                
            self.setProgress(100)
            
            self.showMessage(u'이미지 저장을 완료하였습니다.\n저장 경로 :' + savePath)
        elif self.radioButton_Printer.isChecked():
            for selectedRow in selectedRows:
                try:
                    values=self.getValues(selectedRow)

                    targetLayout=self.setLayout(values)
                
                    index = self.comboBox_Printer.currentIndex()
                    printerInfo = self.comboBox_Printer.itemData(index)
                    printer = QPrinter(printerInfo)
                    printer.setOrientation(QPrinter.Landscape)
                    printer.setPageSize(QPageSize(QPageSize.A3))
                    printer.setFullPage(True)
                    exporter = QgsLayoutExporter(targetLayout)
                    exporter.print(printer, QgsLayoutExporter.PrintExportSettings())
                except:
                    self.writeLog(u"Unexcepted error :" + str(traceback.format_exc()))
                    
                count=count+1
                percentage=count*100/totalCount
                self.setProgress(percentage)
                
            self.setProgress(100)
            
            self.showMessage(u'프린트 완료하였습니다.')
            
        self.setProgress(0)
        self.setEnabled(True)
        
    def setProgress(self, value):
        self.progressBar.setValue(value)
        
    def getValues(self, selectedRow):
        values={}
        values['sido'] = selectedRow[0]
        values['sgg'] = selectedRow[1]
        values['emd'] = selectedRow[2]
        values['ri'] = selectedRow[3]
        values['title'] =selectedRow[4]
        values['forestArea'] = selectedRow[5]
        values['finewiltArea']=selectedRow[6]
        values['firstOccuredTime']=selectedRow[7]
        values['firstOccuredPlace']=selectedRow[8]
        values['t_0_0']=selectedRow[9]
        values['t_0_1']=selectedRow[10]
        values['t_1_0']=selectedRow[11]
        values['t_1_1']=selectedRow[12]
        values['t_2_0']=selectedRow[13]
        values['t_2_1']=selectedRow[14]
        infoPosition=selectedRow[15]
        scalePosition=selectedRow[16]
        
        sido=values['sido']
        sgg=values['sgg']
        emd=values['emd']
        ri=values['ri']
        
        values['bounds']=self.getBoundsByName(sido, sgg, emd, ri)
        if not values['bounds']:
            name = u''
            if sido: name += sido
            if sgg: name += u' ' + sgg
            if emd : name += u' ' + emd
            if ri : name += u' ' + ri
            raise Exception(u'{} not found.'.format(name))
        
        values['isLeftInfo']=infoPosition=='L' or infoPosition==u'L'
        values['isLeftScale']=scalePosition=='L' or scalePosition==u'L'
        return values
            
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