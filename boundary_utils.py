# -*- coding: utf-8 -*-
# boundary_utils
import os

from qgis.core import *
from layer_utils import *

# layer and dataProvider name
SD=u'시도'
SGG=u'시군구'
EMD=u'읍면동'
RI=u'리'

# fields
SIDO_CD=u'SIDO_CD'
SIDO_NM=u'SIDO_NM'
CTPRV_CD = u'CTPRV_CD'
SGG_NM = u'SGG_NM'
STD_SGGCD = u'STD_SGGCD'
EMD_NM = u'EMD_NM'
EMD_CD = u'EMD_CD'
RI_NM = u'RI_NM'
RI_CD = u'RI_CD'

def checkBoundaryLayers():
    if len(getLayers(SD, SD))<=0:
        return False
    if len(getLayers(SGG, SGG))<=0:
        return False
    if len(getLayers(EMD, EMD))<=0:
        return False
    if len(getLayers(RI, RI))<=0:
        return False
        
    return True

def getBound(geometry, marginRatio=0.2):
    bound=geometry.boundingBox()
    maxValue = max(bound.width(), bound.height())
    bound.grow(maxValue * marginRatio)
    return bound

def getBoundarySDList():
    list=[]
    layers=getLayers(SD, SD)
    if len(layers)>0:
        layer=layers[0]
        for feature in layer.getFeatures():
            code=feature[SIDO_CD]
            name=feature[SIDO_NM]
            bound=getBound(feature.geometry())
            list.append(BoundarySD(code, name, bound))
        list.sort(key=lambda x: x.name)
    return list

def getBoundarySGGList(sdCode):
    list=[]
    layers=getLayers(SGG, SGG)
    if len(layers)>0:
        layer=layers[0]
        request = QgsFeatureRequest()
        request.setFilterExpression(CTPRV_CD+'='+sdCode)
        features = layer.getFeatures(request)
        for feature in features:
            code=feature[STD_SGGCD]
            name=feature[SGG_NM]
            bound=getBound(feature.geometry())
            list.append(BoundarySGG(code, name, bound))
        list.sort(key=lambda x: x.name)
    if len(list)>0:
        list.insert(0, Boundary())
    return list
    
def getBoundaryEMDList(sggCode):
    list=[]
    layers=getLayers(EMD, EMD)
    if len(layers)>0:
        layer=layers[0]
        request = QgsFeatureRequest()
        request.setFilterExpression(STD_SGGCD+'='+sggCode)
        features = layer.getFeatures(request)
        for feature in features:
            code=feature[EMD_CD]
            name=feature[EMD_NM]
            bound=getBound(feature.geometry())
            list.append(BoundaryEMD(code, name, bound))
        list.sort(key=lambda x: x.name)
    if len(list)>0:
        list.insert(0, Boundary())
    return list
    
def getBoundaryRIList(emdCode):
    list=[]
    layers=getLayers(RI, RI)
    if len(layers)>0:
        layer=layers[0]
        request = QgsFeatureRequest()
        request.setFilterExpression(RI_CD+" like '"+emdCode+"%'")
        features = layer.getFeatures(request)
        for feature in features:
            code=feature[RI_CD]
            name=feature[RI_NM]
            bound=getBound(feature.geometry())
            list.append(Boundary(code, name, bound))
        list.sort(key=lambda x: x.name)
    if len(list)>0:
        list.insert(0, Boundary())
    return list

class Boundary:
    def __init__(self, code=None, name=None, bound=None):
        self.code=code
        self.name=name
        self.bound=bound
        self.list=None

class BoundarySD(Boundary):
    def getChildren(self):
        if not self.list:
            self.list=getBoundarySGGList(self.code)
        return self.list

class BoundarySGG(Boundary):
    def getChildren(self):
        if not self.list:
            self.list=getBoundaryEMDList(self.code)
        return self.list

class BoundaryEMD(Boundary):
    def getChildren(self):
        if not self.list:
            self.list=getBoundaryRIList(self.code)
        return self.list