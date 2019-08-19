from qgis.core import QgsProject, QgsLayoutItem
from qgis.utils import iface

def getLayouts():
    layoutManager = QgsProject.instance().layoutManager()
    return layoutManager.layouts()
    
def getLayout(name):
    for layout in getLayouts():
        if layout.name() == name:
            return layout
    return None
    
def getLayoutItemById(layout, id):
    for item in layout.items():
        if isinstance(item, QgsLayoutItem):
            if item.id() == id:
                return item
    return None