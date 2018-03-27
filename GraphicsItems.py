from ElectroScene import *
from PyQt4.QtGui import *
import json

graphicsItemLastId = 0
NOT_DEFINED_TYPE = QGraphicsItem.UserType + 1
LINE_TYPE = QGraphicsItem.UserType + 2
GROUP_TYPE = QGraphicsItem.UserType + 3


def createGraphicsObjectsByProperties(properties):
    items = []
    for itemProp in properties:
        if itemProp['type'] == 'LineItem':
            item = LineItem()
            item.setProperties(itemProp)
            items.append(item)
    return items


class GraphicItem():
    MARK_SIZE = 14


    def __init__(self):
        self.selected = False
        self.copyOf = None
        self.normalPen = QPen(Qt.black, 3, Qt.SolidLine, Qt.RoundCap)
        self.selectedPen = QPen(Qt.magenta, 3, Qt.SolidLine, Qt.RoundCap)
        self.highLightPen = QPen(Qt.blue, 5, Qt.SolidLine, Qt.RoundCap)
        self.deltaCenter = None
        self.graphicsItemsList = []
        self._name = ""
        self.attachedToGroup = None

        global graphicsItemLastId
        graphicsItemLastId += 1
        self.itemId = graphicsItemLastId


    def type(self):
        return NOT_DEFINED_TYPE


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


    def highlight(self):
        self.setItemsPen(self.highLightPen)


    def unHighlight(self):
        if self.isSelected():
            self.setItemsPen(self.selectedPen)
        else:
            self.setItemsPen(self.normalPen)


    def resetSelection(self):
        self.markPointsHide()
        self.setItemsPen(self.normalPen)
        self.selected = False


    def setCenter(self, point):
        self.deltaCenter = self.pos() - point


    def items(self):
        return self.graphicsItemsList


    def setGroup(self, group):
        self.attachedToGroup = group


    def group(self):
        return self.attachedToGroup


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['name'] = self.name()
        properties['color'] = {"red" : self.color().red(),
                               "green" : self.color().green(),
                               "blue" : self.color().blue()}
        properties['mountPoint'] = {'x': self.pos().x(),
                                    'y': self.pos().y()}
        properties['thickness'] = self.thickness()
        return properties;


    def setProperties(self, properties):
        self.resetSelection()
        self.setColor(QColor(properties['color']['red'],
                             properties['color']['green'],
                             properties['color']['blue']))
        self.setPos(QPointF(properties['mountPoint']['x'],
                            properties['mountPoint']['y']))
        self.setThickness(properties['thickness'])
        self.setName(properties['name'])


    def __str__(self):
        str = "%d: Graphic type: %s" % (self.id(), self.type())

        if self.name():
            str += ", name: '%s'" % self.name()

        if self.copyOf:
            str += ", copyOf: %d" % self.copyOf

        if self.isSelected():
            str += ", selected"

        return str


class GraphicItemGroup(GraphicItem, QGraphicsItemGroup):


    def __init__(self):
        GraphicItem.__init__(self)
        QGraphicsItemGroup.__init__(self)
        self.selectedPoint = None
        self.markRect = None
        self.setZValue(1)


    def type(self):
        return GROUP_TYPE


    def addItem(self, item):
        if not len(self.graphicsItemsList):
            self.setPos(item.pos())

        item.resetSelection()
        self.addToGroup(item)
        self.graphicsItemsList.append(item)


    def addItems(self, items):
        for item in items:
            self.addItem(item)
            item.setGroup(self)
            item.setZValue(0)


    def markPointsShow(self):
        self.markPointsHide()
        if self.group():
            return
        self.markRect = QGraphicsRectItem(None, self.scene())
        self.markRect.setZValue(0)
        self.markRect.setPen(QPen(QColor(100, 100, 100), 1, Qt.DotLine))
        self.markRect.setRect(self.rectangle())


    def markPointsHide(self):
        if self.markRect:
            self.scene().removeItem(self.markRect)
            self.markRect = None


    def rectangle(self):
        poligon = QPolygonF()
        for item in self.items():
            poligon += item.mapToScene(item.boundingRect())
        if not poligon:
            return

        return poligon.boundingRect()


    def setSelectPoint(self, point):
        return False
        # TODO
        self.selectedPoint = None
        for item in self.graphicsItemsList:
            if item.setSelectPoint(point):
                self.selectedPoint = True
        return self.selectedPoint


    def resetSelectionPoint(self):
        self.markPointsHide()
        self.selectedPoint = None


    def isPointSelected(self):
        if self.selectedPoint:
            return True
        return False


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['name'] = self.name()
        properties['type'] = self.type()
        properties['mountPoint'] = {'x': self.pos().x(),
                                    'y': self.pos().y()}

        itemProperties = []
        for item in self.graphicsItemsList:
            itemProperties.append(item.properties())
        properties['graphicsObjects'] = itemProperties
        return properties


    def setProperties(self, properties):
        if properties['type'] != GROUP_TYPE:
            return

        self.setName(properties['name'])
        self.setPos(QPointF(properties['mountPoint']['x'],
                            properties['mountPoint']['y']))

        if not len(properties['graphicsObjects']):
            return

        for itemProperties in properties['graphicsObjects']:
            for item in self.graphicsItemsList:
                if item.id() == itemProperties['id']:
                    item.setProperties(itemProperties)
                    break


    def rotate(self, center, angle):
        for item in self.items():
            item.rotate(QPointF(center - self.pos()), angle)
        if self.markRect:
            self.markPointsShow()


    def __str__(self):
        str = GraphicItem.__str__(self)
        if not len(self.graphicsItemsList):
            return str

        str += ", contained items:\n"
        for item in self.graphicsItemsList:
            str += "\t\t\t%s\n" % item.__str__()

        return str


    def __exit__(self):
        print("destroy group")
        for item in self.graphicsItemsList:
            item.__exit__()
            self.removeFromGroup(item)
            if item.scene():
                scene = item.scene()
                scene.removeItem(item)
                scene.addGraphicsItem(item)
                item.setGroup(None)
                item.setZValue(1)
        self.graphicsItemsList = []


class GraphicItemLine(GraphicItem, QGraphicsLineItem):


    def __init__(self):
        QGraphicsLineItem.__init__(self)
        GraphicItem.__init__(self)
        self.markP1 = None
        self.markP2 = None
        self.mouseMoveDelta = None
        self.selectedPoint = None
        self.graphicsItemsList.append(self)
        self.setZValue(1)
        self.resetSelection()


    def type(self):
        return LINE_TYPE


    def markPointsShow(self):
        self.markPointsHide()
        if self.group():
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
        self.markPointsShow()


    def copy(self):
        new = LineItem()
        new.setP1(self.p1())
        new.setP2(self.p2())
        new.copyOf = self.id()
        return new


    def properties(self):
        properties = GraphicItem.properties(self)
        properties['type'] = self.type()
        properties['p1'] = {"x" : self.p1().x(), "y": self.p1().y()}
        properties['p2'] = {"x" : self.p2().x(), "y": self.p2().y()}
        return properties


    def setProperties(self, properties):
        if properties['type'] != LINE_TYPE:
            return
        GraphicItem.setProperties(self, properties)
        self.setP1(QPointF(properties['p1']['x'], properties['p1']['y']))
        self.setP2(QPointF(properties['p2']['x'], properties['p2']['y']))


    def moveByCenter(self, point):
        self.setPos(QPointF(point + self.deltaCenter))
        if self.isSelected():
            self.markPointsShow()


    def __str__(self):
        str = GraphicItem.__str__(self)
        str += ", (%d,%d - %d,%d)" % (self.p1().x(), self.p1().y(),
                                     self.p2().x(), self.p2().y())

        if self.deltaCenter:
            str += " | deltaCenter %d,%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str


    def __exit__(self):
        print("destroy line")
        self.markPointsHide()
