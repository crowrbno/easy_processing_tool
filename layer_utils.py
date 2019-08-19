import os

from qgis.core import *

def getDataProviderUriName(dataProvider):
    uri=dataProvider.dataSourceUri()
    return os.path.splitext(os.path.basename(uri))[0]
    
def getLayer(layerName):
    layers = getLayers()
    layerMatches = [layer for layer in layers if layer.name() == layerName]
    if len(layerMatches) > 0:
        return layerMatches[0]

def getLayers(layerName=None, dataProviderName=None, isVectorOnly=False):
    project = QgsProject.instance()
    layers=[]
    for key, layer in sorted(project.mapLayers().items()):
        if layer:
            appendLayer=False
            
            if layerName:
                try:
                    if layer.name()==layerName:
                        if dataProviderName:
                            if dataProviderName==getDataProviderUriName(layer.dataProvider()):
                                appendLayer=True
                        else:
                            appendLayer=True
                except Exception as ex:
                    ex
            else:
                appendLayer=True
            
            if isVectorOnly:
                if not isinstance(layer,QgsVectorLayer):
                    appendLayer=False
                
            if appendLayer:
                layers.append(layer)
    return layers