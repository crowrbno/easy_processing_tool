from qgis.core import *

def getFeaturesByGeometry(layer, geometry):
    featureRequest=QgsFeatureRequest(geometry.boundingBox())
    return layer.getFeatures(featureRequest)