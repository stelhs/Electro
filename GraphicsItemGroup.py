from GraphicsItem import *
from GraphicsItemLine import *
from GraphicsItemRect import *
from GraphicsItemEllipse import *
from GraphicsItemText import *
from PyQt4.Qt import QGraphicsEllipseItem, QPoint, QGraphicsPolygonItem
from math import *



class GraphicsItemGroup(GraphicsItem):
    def __init__(self):
        GraphicsItem.__init__(self)
        self.selectedPoint = None
        self.markRect = None
        self._scene = None
        self.mountPoint = QPointF(0, 0)
        self._prefixName = None
        self._index = 0
        self.indexNameLabel = QGraphicsSimpleTextItem()
        self.indexNameLabel.setBrush(QBrush(Qt.black))
        self.indexNameLabel.setZValue(0)
        self._dimensions = None
        self._parentComponentGroup = None
        self.needToRecalculateBoundingRect = True
        self._boundingRect = None

        self.r1 = None
        self.r2 = None


    def type(self):
        return GROUP_TYPE


    def prefixName(self):
        return self._prefixName


    def index(self):
        return self._index


    def indexName(self):
        if self._parentComponentGroup:
            return "%s.%d" % (self._parentComponentGroup.indexName(),
                                  self._index)

        if self._prefixName:
            if self._index:
                return "%s%d" % (self._prefixName, self._index)
            return "%s" % self._prefixName
        return ""


    def setPrefixName(self, name):
        if self._prefixName != name:
            self._index = 0
        self._prefixName = name


    def setIndex(self, index):
        self._index = int(index)
        self.updateView()


    def updateView(self):
        text = "%s" % self.indexName()
        if self._parentComponentGroup:
            text += "(%s)" % self._parentComponentGroup.addr()
        self.indexNameLabel.setText(text)
        self.indexNameLabel.setPos(self.pos() - QPointF(MAX_GRID_SIZE, 0))

        self.setZValue(self._zIndex)
        if self.highlighted:
            for item in self.graphicsItemsList:
                item.highlight()
            return
        if self.selected:
            for item in self.graphicsItemsList:
                item.select()
            return

        for item in self.graphicsItemsList:
            item.resetSelection()
            item.unHighlight()


    def generateNewId(self):
        GraphicsItem.generateNewId(self)
        for item in self.graphicsItemsList:
            item.generateNewId()


    def setPen(self, pen):
        GraphicsItem.setItemsPen(self, pen)


    def setThickness(self, thickness):
        return


    def setPenStyle(self, penStyle):
        return


    def posFromParent(self):
        return self.mountPoint


    def pos(self):
        if not self.parent():
            return self.mountPoint
        return self.parentPos() + self.mountPoint


    def setPos(self, point, withoutChildrens=False):
        newMountPoint = point - self.parentPos()
        delta = newMountPoint - self.mountPoint

        if not withoutChildrens:
            for item in self.items():
                item.setPos(item.pos() + delta)

        if not self.parent():
            self.mountPoint += delta
        self.updateView()


    def highlight(self):
        GraphicsItem.highlight(self)
        parentGroup = self.parentComponentGroup()
        if parentGroup:
            parentGroup.highlight()


    def unHighlight(self):
        GraphicsItem.unHighlight(self)
        parentGroup = self.parentComponentGroup()
        if parentGroup:
            parentGroup.unHighlight()


    def addItems(self, items):
        if len(items) < 2:
            return False

        self.needToRecalculateBoundingRect = True

        for item in items:
            item.removeFromQScene()
            item.setId(0)
            self.graphicsItemsList.append(item)

        poligon = QPolygonF()
        for item in self.graphicsItemsList:
            rect = item.boundingRect()
            p = QPolygonF([rect.topLeft() + item.pos(),
                           rect.topRight() + item.pos(),
                           rect.bottomRight() + item.pos(),
                           rect.bottomLeft() + item.pos()])
            poligon += p

        groupBoundingRect = poligon.boundingRect()
        self.mountPoint = mapToGrid(groupBoundingRect.topLeft() - self.parentPos(),
                                    MAX_GRID_SIZE)
        self._dimensions = QSizeF(round(groupBoundingRect.width() / MAX_GRID_SIZE) * MAX_GRID_SIZE,
                                  round(groupBoundingRect.height() / MAX_GRID_SIZE) * MAX_GRID_SIZE)


    def setScene(self, scene):
        self._scene = scene

        for item in self.items():
            item.setScene(scene)

        for item in self.items():
            item.setParent(self)

        scene.addItem(self.indexNameLabel)



    def scene(self):
        return self._scene


    def parentPos(self):
        parentPos = QPointF(0, 0)
        if self.parent():
            parentPos = self.parent().pos()
        return parentPos


    def setParent(self, newParent):
        parent = self.parent()
        if newParent and parent:
            return
        if newParent:
            self.mountPoint = self.pos() - newParent.pos()
        else:
            if parent:
                self.mountPoint += parent.posFromParent()
        GraphicsItem.setParent(self, newParent)


    def mapToScene(self, arg):
        argType = arg.__class__.__name__
        if argType == 'QRectF':
            rect = arg
            return QPolygonF([rect.topLeft() + self.pos(),
                              rect.topRight() + self.pos(),
                              rect.bottomRight() + self.pos(),
                              rect.bottomLeft() + self.pos()])

        if argType == 'QPointF':
            point = arg
            return point + self.pos()


    def boundingRect(self):
        if not self.needToRecalculateBoundingRect:
            return self._boundingRect

        poligon = QPolygonF()
        for item in self.items():
            rect = item.boundingRect()
            p = QPolygonF([rect.topLeft() + item.pos(),
                           rect.topRight() + item.pos(),
                           rect.bottomRight() + item.pos(),
                           rect.bottomLeft() + item.pos()])

            poligon += p
        if not poligon:
            return None

        sceneRect = poligon.boundingRect()
        rect = QRectF(sceneRect.topLeft() - self.pos(),
                      sceneRect.bottomRight() - self.pos())
        self._boundingRect = rect
        self.needToRecalculateBoundingRect = False
        return rect


    def setZIndex(self, index):
        return


    def zIndex(self):
        return None


    def setZValue(self, zIndex):
        return None


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['name'] = self.name()
        properties['type'] = self.typeName()
        properties['mountPoint'] = {'x': self.mountPoint.x(),
                                    'y': self.mountPoint.y()}
        if self.prefixName():
            properties['prefixName'] = self.prefixName()
            properties['index'] = self.index()

        parentComponentGroup = self.parentComponentGroup()
        if parentComponentGroup:
            properties['parentComponentId'] = parentComponentGroup.id()

        itemProperties = []
        for item in self.items():
            itemProperties.append(item.properties())
        properties['graphicsObjects'] = itemProperties

        return properties


    def setProperties(self, properties, setId=False):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != GROUP_TYPE:
            return

        if setId:
            self.setId(properties['id'])
        self.markPointsHide()
        self.setName(properties['name'])
        if 'prefixName' in properties:
            self.setPrefixName(properties['prefixName'])
            self.setIndex(properties['index'])

        newMountPoint = QPointF(properties['mountPoint']['x'],
                                properties['mountPoint']['y'])
        if self.parent():
            newMountPoint += self.parent().pos()
        self.setPos(newMountPoint)

        if not len(properties['graphicsObjects']):
            return

        newItems = []
        for itemProperties in properties['graphicsObjects']:
            found = False
            for item in self.graphicsItemsList:
                if item.id() == itemProperties['id']:
                    item.setProperties(itemProperties)
                    found = True
                    break
            if not found:
                itemMountPoint = QPointF(itemProperties['mountPoint']['x'],
                                         itemProperties['mountPoint']['y'])
                itemMountPoint += self.pos()
                itemProperties['mountPoint']['x'] = itemMountPoint.x()
                itemProperties['mountPoint']['y'] = itemMountPoint.y()

                if typeByName(itemProperties['type']) == LINE_TYPE:
                    item = GraphicsItemLine()

                if typeByName(itemProperties['type']) == RECT_TYPE:
                    item = GraphicsItemRect()

                if typeByName(itemProperties['type']) == ELLIPSE_TYPE:
                    item = GraphicsItemEllipse()

                if typeByName(itemProperties['type']) == TEXT_TYPE:
                    item = GraphicsItemText()

                if typeByName(itemProperties['type']) == GROUP_TYPE:
                    item = GraphicsItemGroup()

                item.setProperties(itemProperties)
                newItems.append(item)

        self.addItems(newItems)


    def compareProperties(self, properties):
        selfProperties = self.properties()

        for name, value in selfProperties.items():
            if name == 'graphicsObjects':
                continue
            if not name in properties or properties[name] != value:
                return False

        if len(properties['graphicsObjects']) != len(selfProperties['graphicsObjects']):
            return False

        for itemProperties in properties['graphicsObjects']:
            for item in self.graphicsItemsList:
                if item.id() != itemProperties['id']:
                    continue

                if not item.compareProperties(itemProperties):
                    return False

        return True



    def rotate(self, center, angle, parentOldMountPoint=None):
        self.needToRecalculateBoundingRect = True
        if parentOldMountPoint:
            delta = self.parent().mountPoint - parentOldMountPoint
            self.mountPoint -= delta

        localCenter = center - self.parentPos()
        t = QTransform()
        t.translate(localCenter.x(), localCenter.y())
        t.rotate(angle)
        t.translate(-localCenter.x(), -localCenter.y())

        rect = QRectF(self.mountPoint, self._dimensions)
        points = []
        points.append(rect.topLeft())
        points.append(rect.topRight())
        points.append(rect.bottomRight())
        points.append(rect.bottomLeft())

        rotatePoints = []
        for p in points:
            rotatePoints.append(t.map(p))
        oldMountPoint = self.mountPoint
        self.mountPoint = rotatePoints[3]
        self._dimensions = QSizeF(self._dimensions.height(),
                                  self._dimensions.width())

        for item in self.items():
            if item.type() == GROUP_TYPE:
                item.rotate(center, angle, oldMountPoint)
            else:
                item.rotate(center, angle)
        self.updateView()


    def allSubItems(self, type=None):
        subItems = []
        for item in self.graphicsItemsList:
            if item.type() == GROUP_TYPE:
                subItems += item.allSubItems(type)
            if type and item.type() == type:
                subItems.append(item)
        return subItems


    def setParentComponentGroup(self, group):
        self._parentComponentGroup = group
        self.updateView()


    def parentComponentGroup(self):
        return self._parentComponentGroup


    def __str__(self):
        str = GraphicsItem.__str__(self)
        if not len(self.graphicsItemsList):
            return str

        str += ", mountPoint:(%d, %d), dimesions:(%d:%d) " % (
                                    self.mountPoint.x(),
                                    self.mountPoint.y(),
                                    self._dimensions.width(),
                                    self._dimensions.height())

        if self.prefixName():
            str += "indexName:%s " % self.indexName()

        str += "contained items:\n"
        for item in self.graphicsItemsList:
            str += "\t\t\t%s\n" % item.__str__()

        return str


    def removeAllItems(self):
        self.removeFromQScene()
        self.graphicsItemsList = []


    def removeFromQScene(self):
        self.resetSelection()
        if self.indexNameLabel.scene():
            scene = self.indexNameLabel.scene()
            scene.removeItem(self.indexNameLabel)
        for item in self.items():
            item.removeFromQScene()
        # self.graphicsItemsList = []
        self._scene = None


