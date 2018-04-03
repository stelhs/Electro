from ElectroScene import *
from PyQt4.QtGui import *
from pprint import *
import json
from PyQt4.Qt import QPoint
from curses.textpad import rectangle
import copy
import pprint


MAX_GRID_SIZE = 20


graphicsItemLastId = 0

# TODO: implements enum
NOT_DEFINED_TYPE = QGraphicsItem.UserType + 1
LINE_TYPE = QGraphicsItem.UserType + 2
GROUP_TYPE = QGraphicsItem.UserType + 3
RECT_TYPE = QGraphicsItem.UserType + 4

graphicsObjectsTypeNames = {
    NOT_DEFINED_TYPE: "not_defined",
    LINE_TYPE: "line",
    GROUP_TYPE: "group",
    RECT_TYPE: "rectangle",
}


def typeByName(name):
    for type, value in graphicsObjectsTypeNames.items():
        if name == value:
            return type
    return NOT_DEFINED_TYPE


def mapToGrid(arg, gridSize):
    argType = arg.__class__.__name__
    if argType == 'QPointF':
        point = arg
        s = gridSize
        x = round(point.x() / s) * s
        y = round(point.y() / s) * s
        return QPointF(x, y)

    if argType == 'QRectF':
        rect = arg
        x = rect.topLeft().x() - gridSize
        y = rect.topLeft().y() - gridSize
        topLeft = mapToGrid(QPointF(x, y), gridSize)
        x = rect.bottomRight().x() + gridSize
        y = rect.bottomRight().y() + gridSize
        bottomRight = mapToGrid(QPointF(x, y), gridSize)
        rect = QRectF(topLeft, bottomRight)
        print("mapToGrid rect = %s" % rect)
        return rect


def createGraphicsObjectByProperties(ogjectProperties):
    item = None
    if typeByName(ogjectProperties['type']) == GROUP_TYPE:
        item = GraphicItemGroup()
        item.setProperties(ogjectProperties)

    if typeByName(ogjectProperties['type']) == LINE_TYPE:
        item = GraphicItemLine()
        item.setProperties(ogjectProperties)

    if typeByName(ogjectProperties['type']) == RECT_TYPE:
        item = GraphicItemRect()
        item.setProperties(ogjectProperties)

    return item


def createGraphicsObjectsByProperties(properties):
    items = []
    for itemProp in properties:
        item = createGraphicsObjectByProperties(itemProp)
        if item:
            items.append(item)

    return items


class GraphicItem():
    MARK_SIZE = 14
    normalPen = QPen(QColor(0, 0, 200), 2, Qt.SolidLine, Qt.RoundCap)
    selectedPen = QPen(Qt.magenta, 3, Qt.SolidLine, Qt.RoundCap)
    highLightPen = QPen(Qt.blue, 4, Qt.SolidLine, Qt.RoundCap)

    def __init__(self):
        self.selected = False
        self.copyOf = None
        self.deltaCenter = None
        self.graphicsItemsList = []
        self._name = ""
        self._parentItem = None
        self.mouseMoveDelta = None

        global graphicsItemLastId
        graphicsItemLastId += 1
        self.itemId = graphicsItemLastId


    def type(self):
        return NOT_DEFINED_TYPE


    def typeName(self):
        return graphicsObjectsTypeNames[self.type()]


    def id(self):
        return self.itemId


    def setName(self, name):
        self._name = name


    def name(self):
        return self._name


    def setItemsPen(self, pen):
        if not len(self.graphicsItemsList):
            return
        for item in self.graphicsItemsList:
            if item.type() == GROUP_TYPE:
                item.setItemsPen(pen)
                continue
            item.setPen(pen)


    def setColor(self, color):
        self.normalPen.setColor(color)
        self.setItemsPen(self.normalPen)


    def color(self):
        return self.normalPen.color()


    def setThickness(self, size):
        self.normalPen.setWidth(size)
        self.setItemsPen(self.normalPen)


    def thickness(self):
        return self.normalPen.width()


    def isSelected(self):
        return self.selected


    def select(self):
        self.setItemsPen(self.selectedPen)
        self.selected = True


    def resetSelection(self):
        self.markPointsHide()
        self.setItemsPen(self.normalPen)
        self.selected = False


    def highlight(self):
        self.setItemsPen(self.highLightPen)


    def unHighlight(self):
        if self.isSelected():
            self.setItemsPen(self.selectedPen)
        else:
            self.setItemsPen(self.normalPen)


    def setCenter(self, point):
        self.deltaCenter = self.pos() - point


    def moveByCenter(self, point):
        self.setPos(QPointF(point + self.deltaCenter))
        if self.isSelected():
            self.markPointsShow()


    def items(self):
        return self.graphicsItemsList


    def setParent(self, parentItem):
        self._parentItem = parentItem


    def parent(self):
        return self._parentItem


    def root(self):
        if self.parent():
            return self.parent().root()
        return self


    def setSelectPoint(self, point):
        return False


    def resetSelectionPoint(self):
        pass


    def isPointSelected(self):
        return False


    def markPointsShow(self):
        return


    def markPointsHide(self):
        return


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['type'] = self.typeName()
        properties['name'] = self.name()
        properties['mountPoint'] = {'x': self.posFromParent().x(),
                                    'y': self.posFromParent().y()}
        return properties;


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        self.resetSelection()

        newMountPoint = QPointF(properties['mountPoint']['x'],
                                properties['mountPoint']['y'])
        if self.parent():
            newMountPoint += self.parent().pos()
        self.setPos(newMountPoint)

        self.setName(properties['name'])


    def compareProperties(self, properties):
        for name, value in self.properties().items():
            if not name in properties or properties[name] != value:
                print("%d base not matched" % self.id())
                return False

        print("%d base matched" % self.id())
        return True


    def setScene(self, scene):
        scene.addItem(self)


    def removeFromQScene(self):
        self.resetSelection()
        scene = self.scene()
        if scene:
            scene.removeItem(self)


    def __str__(self):
        str = "%d: (%d:%d) Graphic type:%s" % (self.id(),
                                                self.pos().x(),
                                                self.pos().y(),
                                                self.typeName())

        if self.parent():
            str += ", parent: %d" % self.parent().id()

        if self.name():
            str += ", name: '%s'" % self.name()

        if self.copyOf:
            str += ", copyOf: %d" % self.copyOf

        if self.isSelected():
            str += ", selected"

        return str


class GraphicItemGroup(GraphicItem):


    def __init__(self):
        GraphicItem.__init__(self)
        self.selectedPoint = None
        self.markRect = None
        self._scene = None
        self.mountPoint = QPointF(0, 0)


    def type(self):
        return GROUP_TYPE


    def posFromParent(self):
        return self.mountPoint


    def setPos(self, point):
        parentMountPoint = QPointF(0, 0)
        if self.parent():
            parentMountPoint = self.parent().pos()

        newMountPoint = point - parentMountPoint
        delta = newMountPoint - self.mountPoint
        for item in self.items():
            item.setPos(item.pos() + delta)

        self.mountPoint = newMountPoint
        # print("%d setPos %s, mountPoint = %s, pos = %s" % (self.id(), point, self.mountPoint, self.pos()))


    def addItems(self, items):
        if len(items) < 2:
            return False

        for item in items:
            item.removeFromQScene()
            self.graphicsItemsList.append(item)

        return True


    def calculateMountPoint(self):
        poligon = QPolygonF()
        for item in self.items():
            rect = item.boundingRect()
            p = QPolygonF([rect.topLeft() + item.pos(),
                           rect.topRight() + item.pos(),
                           rect.bottomRight() + item.pos(),
                           rect.bottomLeft() + item.pos()])

            poligon += p
        if not poligon:
            return

        parentMountPoint = QPointF(0, 0)
        if self.parent():
            parentMountPoint = self.parent().pos()

        ItemsBoundingRect = poligon.boundingRect()
        self.mountPoint = mapToGrid(ItemsBoundingRect.topLeft() -
                                    parentMountPoint,
                                    MAX_GRID_SIZE)


    def setScene(self, scene):
        self._scene = scene

        for item in self.items():
            item.setScene(scene)

        if not self.pos():
            self.calculateMountPoint()

        for item in self.items():
            item.setParent(self)


    def scene(self):
        return self._scene


    def setParent(self, parentItem):
        if self.parent() and parentItem:
            return
        GraphicItem.setParent(self, parentItem)
        if parentItem:
            self.mountPoint -= parentItem.pos()


    def pos(self):
        if not self.parent():
            return self.mountPoint
        return self.parent().pos() + self.mountPoint


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
        return QRectF(sceneRect.topLeft() - self.pos(),
                      sceneRect.bottomRight() - self.pos())


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['name'] = self.name()
        properties['type'] = self.typeName()
        properties['mountPoint'] = {'x': self.mountPoint.x(),
                                    'y': self.mountPoint.y()}

        itemProperties = []
        for item in self.items():
            itemProperties.append(item.properties())
        properties['graphicsObjects'] = itemProperties

        return properties


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != GROUP_TYPE:
            return

        self.markPointsHide()
        self.setName(properties['name'])
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
                    item = GraphicItemLine()
                    item.setProperties(itemProperties)
                    newItems.append(item)

                if typeByName(itemProperties['type']) == RECT_TYPE:
                    item = GraphicItemRect()
                    item.setProperties(itemProperties)
                    newItems.append(item)

                if typeByName(itemProperties['type']) == GROUP_TYPE:
                    item = GraphicItemGroup()
                    item.setProperties(itemProperties)
                    newItems.append(item)

        self.addItems(newItems)


    def compareProperties(self, properties):
        selfProperties = self.properties()

        for name, value in selfProperties.items():
            if name == 'graphicsObjects':
                continue
            if not name in properties or properties[name] != value:
                print("%d group not matched" % self.id())
                return False

        if len(properties['graphicsObjects']) != len(selfProperties['graphicsObjects']):
            print("%d group not matched count subitems" % self.id())
            return False

        for itemProperties in properties['graphicsObjects']:
            for item in self.graphicsItemsList:
                if item.id() != itemProperties['id']:
                    continue

                if not item.compareProperties(itemProperties):
                    print("%d group not matched sub item %d" % (self.id(), item.id()))
                    return False

        print("%d group matched" % self.id())
        return True


    def rotate(self, center, angle):
        for item in self.items():
            item.rotate(center, angle)
#        self.calculateMountPoint()


    def __str__(self):
        str = GraphicItem.__str__(self)
        if not len(self.graphicsItemsList):
            return str

        str += ", contained items:\n"
        for item in self.graphicsItemsList:
            str += "\t\t\t%s\n" % item.__str__()

        return str


    def removeAllItems(self):
        self.removeFromQScene()
        self.graphicsItemsList = []


    def removeFromQScene(self):
        self.resetSelection()

        for item in self.items():
            item.setParent(None)
            item.removeFromQScene()


class GraphicItemLine(GraphicItem, QGraphicsLineItem):


    def __init__(self, type='line'):
        QGraphicsLineItem.__init__(self)
        GraphicItem.__init__(self)
        self._typeLine = type
        self.markP1 = None
        self.markP2 = None
        self.selectedPoint = None
        self.graphicsItemsList.append(self)
        self.setZValue(1)
        self.resetSelection()
        self.linePen = GraphicItem.normalPen
        self.tracePen = QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap)
        self.normalPen = self.linePen

        self.setTypeLine(self._typeLine)


    def type(self):
        return LINE_TYPE


    def setTypeLine(self, type):
        self._typeLine = type
        self.normalPen = self.linePen
        if type == 'trace':
            self.normalPen = self.tracePen
        self.setPen(self.normalPen)


    def typeLine(self):
        return self._typeLine


    def markPointsShow(self):
        self.markPointsHide()
        if self.parent():
            return

        self.markP1 = QGraphicsRectItem(None, self.scene())
        self.markP1.setZValue(0)
        self.markP1.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        x1 = self.p1().x() - self.MARK_SIZE / 2
        y1 = self.p1().y() - self.MARK_SIZE / 2
        self.markP1.setRect(x1, y1, self.MARK_SIZE, self.MARK_SIZE)

        self.markP2 = QGraphicsRectItem(None, self.scene())
        self.markP2.setZValue(0)
        self.markP2.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        x1 = self.p2().x() - self.MARK_SIZE / 2
        y1 = self.p2().y() - self.MARK_SIZE / 2
        self.markP2.setRect(x1, y1, self.MARK_SIZE, self.MARK_SIZE)


    def markPointsHide(self):
        if self.markP1:
            self.scene().removeItem(self.markP1)
            self.markP1 = None
        if self.markP2:
            self.scene().removeItem(self.markP2)
            self.markP2 = None


    def posFromParent(self):
        if not self.parent():
            return QGraphicsLineItem.pos(self)
        return QGraphicsLineItem.pos(self) - self.parent().pos()


    def p1(self):
        return QPointF(self.line().p1() + self.pos())


    def p2(self):
        return QPointF(self.line().p2() + self.pos())


    def setP1(self, point):
        self.setPos(point)
        self.setLine(0, 0, 0, 0)


    def setP2(self, point):
        line = self.line()
        point = QPointF(point - self.pos())
        line.setP2(point)
        self.setLine(line)
        if self.isSelected():
            self.markPointsShow()


    def points(self):
        return [self.p1(), self.p2()]


    def setSelectPoint(self, point):
        if self.p1() == point:
            self.selectedPoint = 1
            return True

        if self.p2() == point:
            self.selectedPoint = 2
            return True


    def resetSelectionPoint(self):
        self.markPointsHide()
        self.selectedPoint = None


    def isPointSelected(self):
        if self.selectedPoint:
            return True
        return False


    def modifySelectedPoint(self, new_point):
        if self.selectedPoint == 1:
            delta = self.p2() - new_point
            self.setP1(new_point)
            self.setP2(QPointF(new_point + delta))
            if self.p1() == self.p2():
                self.scene().removeGraphicsItem(self)
            return True

        if self.selectedPoint == 2:
            self.setP2(new_point)
            if self.p1() == self.p2():
                self.scene().removeGraphicsItem(self)
            return True

        return False


    def rotate(self, center, angle):
        t = QTransform()
        t.translate(center.x(), center.y())
        t.rotate(angle)
        t.translate(-center.x(), -center.y())
        p1 = t.map(self.p1())
        p2 = t.map(self.p2())
        self.setP1(p1)
        self.setP2(p2)


    def copy(self):
        new = LineItem()
        new.setP1(self.p1())
        new.setP2(self.p2())
        new.copyOf = self.id()
        return new


    def properties(self):
        properties = GraphicItem.properties(self)
        properties['typeLine'] = self.typeLine()
        properties['p1'] = {"x" : self.line().p1().x(), "y": self.line().p1().y()}
        properties['p2'] = {"x" : self.line().p2().x(), "y": self.line().p2().y()}
        return properties


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != LINE_TYPE:
            return

        self.setTypeLine(properties['typeLine'])
        GraphicItem.setProperties(self, properties)
        line = QLineF(QPointF(properties['p1']['x'], properties['p1']['y']),
                      QPointF(properties['p2']['x'], properties['p2']['y']))
        self.setLine(line)


    def __str__(self):
        str = GraphicItem.__str__(self)
        str += ", (%d:%d - %d:%d), z=%d" % (self.p1().x(), self.p1().y(),
                                     self.p2().x(), self.p2().y(), self.zValue())

        if self.deltaCenter:
            str += " | deltaCenter %d:%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str




class GraphicItemRect(GraphicItem, QGraphicsRectItem):
    def __init__(self, rect=None):
        QGraphicsRectItem.__init__(self)
        GraphicItem.__init__(self)
        if rect:
            self.setPos(rect.topLeft())
            self.setRect(QRectF(0, 0, rect.width(), rect.height()))
        self.setZValue(1)
        self.setPen(self.normalPen)
        self.graphicsItemsList.append(self)
        self.markPoints = []
        self.selectedPoint = None


    def type(self):
        return RECT_TYPE


    def markPointsShow(self):
        self.markPointsHide()
        if self.parent():
            return

        for point in self.points():
            markPoint = QGraphicsRectItem(None, self.scene())
            markPoint.setZValue(0)
            markPoint.setPen(QPen(Qt.black, 1, Qt.SolidLine))
            x1 = point.x() - self.MARK_SIZE / 2
            y1 = point.y() - self.MARK_SIZE / 2
            markPoint.setRect(x1, y1, self.MARK_SIZE, self.MARK_SIZE)
            self.markPoints.append(markPoint)


    def markPointsHide(self):
        for markPoint in self.markPoints:
            self.scene().removeItem(markPoint)
        self.markPoints = []


    def posFromParent(self):
        if not self.parent():
            return QGraphicsRectItem.pos(self)
        return QGraphicsRectItem.pos(self) - self.parent().pos()


    def points(self):
        points = []
        points.append(self.topLeft())
        points.append(self.topRight())
        points.append(self.bottomLeft())
        points.append(self.bottomRight())
        return points


    def topLeft(self):
        rect = self.rect()
        return self.pos() + rect.topLeft()


    def topRight(self):
        rect = self.rect()
        return self.pos() + rect.topRight()


    def bottomLeft(self):
        rect = self.rect()
        return self.pos() + rect.bottomLeft()


    def bottomRight(self):
        rect = self.rect()
        return self.pos() + rect.bottomRight()


    def width(self):
        return self.rect().width()


    def height(self):
        return self.rect().height()


    def setSelectPoint(self, selPoint):
        if selPoint == self.pos():
            self.selectedPoint = 'pos'
            print("setSelectPoint pos")
        elif selPoint == self.topRight():
            self.selectedPoint = 'topRight'
            print("setSelectPoint topRight")
        elif selPoint == self.bottomLeft():
            self.selectedPoint = 'bottomLeft'
            print("setSelectPoint bottomLeft")
        elif selPoint == self.bottomRight():
            self.selectedPoint = 'bottomRight'
            print("setSelectPoint bottomRight")

        if self.selectedPoint:
            return True
        return False


    def resetSelectionPoint(self):
        print("resetSelectionPoint")
        self.markPointsHide()
        self.selectedPoint = None


    def isPointSelected(self):
        if self.selectedPoint:
            return True
        return False


    def modifySelectedPoint(self, new_point):
        if self.selectedPoint == 'pos':
            delta = self.pos() - new_point
            self.setPos(new_point)
            self.setRect(QRectF(0, 0,
                                self.width() + delta.x(),
                                self.height() + delta.y()))

            if not self.width() or not self.height():
                self.scene().removeGraphicsItem(self)
            return True

        if self.selectedPoint == 'topRight':
            delta = self.topRight() - new_point
            self.setPos(QPointF(self.pos().x(),
                                self.pos().y() - delta.y()))
            self.setRect(QRectF(0, 0,
                                self.width() - delta.x(),
                                self.height() + delta.y()))

            if not self.width() or not self.height():
                self.scene().removeGraphicsItem(self)
            return True

        if self.selectedPoint == 'bottomLeft':
            delta = self.bottomLeft() - new_point
            self.setPos(QPointF(self.pos().x() - delta.x(),
                                self.pos().y()))
            self.setRect(QRectF(0, 0,
                                self.width() + delta.x(),
                                self.height() - delta.y()))

            if not self.width() or not self.height():
                self.scene().removeGraphicsItem(self)
            return True

        if self.selectedPoint == 'bottomRight':
            delta = new_point - self.pos()
            self.setRect(QRectF(0, 0,
                                delta.x(),
                                delta.y()))

            if not self.width() or not self.height():
                self.scene().removeGraphicsItem(self)
            return True
        return False


    def properties(self):
        properties = GraphicItem.properties(self)
        properties['rectSize'] = {"w": self.rect().width(),
                                  "h": self.rect().height()}
        return properties


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != RECT_TYPE:
            return

        GraphicItem.setProperties(self, properties)
        rect = QRectF(0, 0,
                      properties['rectSize']['w'],
                      properties['rectSize']['h'])
        self.setRect(rect)


    def rotate(self, center, angle):
        t = QTransform()
        t.translate(center.x(), center.y())
        t.rotate(angle)
        t.translate(-center.x(), -center.y())
        pos = t.map(self.pos())
        topRight = t.map(self.topRight())
        bottomLeft = t.map(self.bottomLeft())
        bottomRight = t.map(self.bottomRight())
        rect = QPolygonF([pos, topRight, bottomLeft, bottomRight]).boundingRect()
        self.setPos(rect.topLeft())
        self.setRect(QRectF(0, 0, rect.width(), rect.height()))
        self.markPointsShow()


    def __str__(self):
        str = GraphicItem.__str__(self)
        str += ", size:(%d x %d), z=%d" % (self.width(), self.height(), self.zValue())

        if self.deltaCenter:
            str += " | deltaCenter %d:%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str



