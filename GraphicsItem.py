from ElectroScene import *
from PyQt4.QtGui import *
from PyQt4.Qt import QPoint
from Color import *
from pprint import *
import json
from curses.textpad import rectangle
import copy


MAX_GRID_SIZE = 20


# TODO: implements enum
NOT_DEFINED_TYPE = QGraphicsItem.UserType + 1
LINE_TYPE = QGraphicsItem.UserType + 2
GROUP_TYPE = QGraphicsItem.UserType + 3
RECT_TYPE = QGraphicsItem.UserType + 4
ELLIPSE_TYPE = QGraphicsItem.UserType + 5
LINK_TYPE = QGraphicsItem.UserType + 6
TEXT_TYPE = QGraphicsItem.UserType + 7

graphicsObjectsTypeNames = {
    NOT_DEFINED_TYPE: "not_defined",
    LINE_TYPE: "line",
    GROUP_TYPE: "group",
    RECT_TYPE: "rectangle",
    ELLIPSE_TYPE: "ellipse",
    LINK_TYPE: "link",
    TEXT_TYPE: "text"
}

graphicsObjectsPenStyleNames = {
    1: "solid",
    2: "dashLine",
    3: "dotLine",
    4: "dashDotLine",
    5: "dashDotDotLine",
}


def typeByName(name):
    for type, value in graphicsObjectsTypeNames.items():
        if name == value:
            return type
    return NOT_DEFINED_TYPE


def penStyleByName(name):
    for type, value in graphicsObjectsPenStyleNames.items():
        if name == value:
            return type
    return 1


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
        return rect


def createGraphicsObjectByProperties(ogjectProperties, withId=False):
    import GraphicsItemLine
    import GraphicsItemRect
    import GraphicsItemEllipse
    import GraphicsItemText
    import GraphicsItemGroup
    import GraphicsItemLink

    item = None
    if typeByName(ogjectProperties['type']) == GROUP_TYPE:
        item = GraphicsItemGroup.GraphicsItemGroup()
        item.setProperties(ogjectProperties, withId)

    if typeByName(ogjectProperties['type']) == LINE_TYPE:
        item = GraphicsItemLine.GraphicsItemLine()
        item.setProperties(ogjectProperties, withId)

    if typeByName(ogjectProperties['type']) == RECT_TYPE:
        item = GraphicsItemRect.GraphicsItemRect()
        item.setProperties(ogjectProperties, withId)

    if typeByName(ogjectProperties['type']) == ELLIPSE_TYPE:
        item = GraphicsItemEllipse.GraphicsItemEllipse()
        item.setProperties(ogjectProperties, withId)

    if typeByName(ogjectProperties['type']) == TEXT_TYPE:
        item = GraphicsItemText.GraphicsItemText()
        item.setProperties(ogjectProperties, withId)

    if typeByName(ogjectProperties['type']) == LINK_TYPE:
        item = GraphicsItemLink.GraphicsItemLink()
        item.setProperties(ogjectProperties, withId)

    return item


class GraphicsItem():
    idList = []
    MARK_SIZE = 8

    def __init__(self):
        self.selected = False
        self.highlighted = False
        self.copyOf = None
        self.deltaCenter = None
        self.graphicsItemsList = []
        self._name = ""
        self._parentItem = None
        self.mouseMoveDelta = None
        self.generateNewId()
        self._color = Color(0, 0, 200)
        print("new item was created %d" % self.id())
        self.defaultPen = QPen(self._color, 2, Qt.SolidLine, Qt.RoundCap)
        self.normalPen = self.defaultPen
        self.selectedPen = QPen(Qt.magenta, 3, Qt.SolidLine, Qt.RoundCap)
        self.highLightPen = QPen(Qt.blue, 4, Qt.SolidLine, Qt.RoundCap)
        self._currentPen = self.normalPen
        self._zIndex = 1


    def type(self):
        return NOT_DEFINED_TYPE


    def typeName(self):
        return graphicsObjectsTypeNames[self.type()]


    def id(self):
        return self._id


    def setName(self, name):
        self._name = name


    def name(self):
        return self._name


    def generateNewId(self):
        self._id = GraphicsItem.getFreeId()


    def setId(self, id):
        if id == 0:
            print("ZERO id incorrect! id = %d" % id)

        for existId in GraphicsItem.idList:
            if id == existId and self.id() != id:
                print("\nDULICATE id detected for %d!\n" % id)
                break

        GraphicsItem.idList.remove(self.id())
        self._id = id
        GraphicsItem.idList.append(id)


    @staticmethod
    def checkDuplicateId():
        for id1 in GraphicsItem.idList:
            cnt = 0
            for id2 in GraphicsItem.idList:
                if id1 == id2:
                    cnt += 1
            if cnt > 1:
                print("\n!!!detected duplicate!!! %d count %d\n" % (id1, cnt))


    def removeId(self):
        if not self._id:
            return
        print("remove id %d" % self.id())
        GraphicsItem.idList.remove(self.id())
        self._id = 0


    @staticmethod
    def getFreeId():
        GraphicsItem.idList.sort()
        freeId = 1
        for id in GraphicsItem.idList:
            if id != freeId:
                GraphicsItem.idList.append(freeId)
                return freeId
            freeId += 1
        GraphicsItem.idList.append(freeId)
        return freeId


    def addr(self):
        scene = self.scene()
        quadrant = scene.quadrantByPos(self.pos())
        return "%d/%s" % (scene.num(), quadrant)


    def setItemsPen(self, pen):
        for item in self.graphicsItemsList:
            item.setPen(pen)


    def setColor(self, color):
        self._color.setColor(color)
        self.normalPen.setColor(self._color)
        self.updateView()


    def resetColor(self):
        self.setItemsPen(self.defaultPen)


    def color(self):
        return self._color


    def setThickness(self, size):
        self.normalPen.setWidth(size)
        self.selectedPen.setWidth(size + 1)
        self.highLightPen.setWidth(size + 2)
        self.updateView()


    def thickness(self):
        return self.normalPen.width()


    def increaseThickness(self):
        thickness = self.thickness()
        if thickness < 6:
            thickness += 1
        else:
            thickness = 1
        self.setThickness(thickness)


    def decreaseThickness(self):
        thickness = self.thickness()
        if thickness > 1:
            thickness -= 1
        else:
            thickness = 6
        self.setThickness(thickness)


    def increaseZIndex(self):
        for item in self.graphicsItemsList:
            if item.zIndex() == 10:
                return
        for item in self.graphicsItemsList:
            print("increase zIndex for %d" % item.id())
            item._zIndex += 1
            item.updateView()


    def decreaseZIndex(self):
        for item in self.graphicsItemsList:
            if item.zIndex() == 1:
                return
        for item in self.graphicsItemsList:
            item._zIndex -= 1
            item.updateView()


    def setZIndex(self, index):
        self._zIndex = index


    def zIndex(self):
        return self._zIndex


    def setPenStyle(self, penStyle):
        self.normalPen.setStyle(penStyle)
        self.selectedPen.setStyle(penStyle)
        self.highLightPen.setStyle(penStyle)
        self.updateView()


    def penStyle(self):
        return self.normalPen.style()


    def increasePenStyle(self):
        penStyle = self.penStyle()
        if penStyle < Qt.DashDotDotLine:
            penStyle += 1
        else:
            penStyle = Qt.SolidLine
        self.setPenStyle(penStyle)


    def decreasePenStyle(self):
        penStyle = self.penStyle()
        if penStyle > Qt.SolidLine:
            penStyle -= 1
        else:
            penStyle = Qt.DashDotDotLine
        self.setPenStyle(penStyle)


    def penStyleName(self):
        return graphicsObjectsPenStyleNames[self.penStyle()]


    def isSelected(self):
        return self.selected


    def select(self):
        self.selected = True
        self.updateView()


    def resetSelection(self):
        self.selected = False
        self.markPointsHide()
        self.updateView()


    def highlight(self):
        for item in self.graphicsItemsList:
            item.highlighted = True
            item.updateView()
        self.highlighted = True
        self.updateView()


    def unHighlight(self):
        for item in self.graphicsItemsList:
            item.highlighted = False
            item.updateView()
        self.highlighted = False
        self.updateView()


    def updateView(self):
        self.setZValue(self._zIndex)
        if self.highlighted:
            self.setItemsPen(self.highLightPen)
            return
        if self.selected:
            self.setItemsPen(self.selectedPen)
            return
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


    def points(self):
        return []


    def center(self):
        rect = self.mapToScene(self.boundingRect()).boundingRect()
        return rect.center()


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


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['type'] = self.typeName()
        properties['name'] = self.name()
        properties['mountPoint'] = {'x': self.posFromParent().x(),
                                    'y': self.posFromParent().y()}
        properties['penStyle'] = self.penStyleName()
        properties['color'] = {'R': self.color().red(),
                               'G': self.color().green(),
                               'B': self.color().blue()}
        properties['zIndex'] = self.zIndex()
        properties['thickness'] = self.thickness()
        return properties;


    def setProperties(self, properties, setId=False):
        properties = copy.deepcopy(properties)
        self.resetSelection()

        newMountPoint = QPointF(properties['mountPoint']['x'],
                                properties['mountPoint']['y'])
        if self.parent():
            newMountPoint += self.parent().pos()
        self.setPos(newMountPoint)
        self.setName(properties['name'])
        if 'penStyle' in properties:
            self.setPenStyle(penStyleByName(properties['penStyle']))
        if 'color' in properties:
            self.setColor(QColor(properties['color']['R'],
                                 properties['color']['G'],
                                 properties['color']['B']))
        if 'thickness' in properties:
            self.setThickness(properties['thickness'])
        if 'zIndex' in properties:
            self.setZIndex(properties['zIndex'])
        if setId:
            self.setId(properties['id'])
        self.updateView()


    def compareProperties(self, properties):
        for name, value in self.properties().items():
            if not name in properties or properties[name] != value:
                return False
        return True


    def isNullSize(self):
        points = self.points()
        point1 = points[0]
        points = points[1:]
        for point2 in points:
            if point2 == point1:
                return True
        return False


    def setScene(self, scene):
        scene.addItem(self)


    def removeFromQScene(self):
        self.resetSelection()
        scene = self.scene()
        if scene:
            scene.removeItem(self)


    def remove(self):
        self.color().remove()
        if self.id() in GraphicsItem.idList:
            GraphicsItem.idList.remove(self.id())
        self._id = 0
        for item in self.graphicsItemsList:
            if item.id() in GraphicsItem.idList:
                item.remove()


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





