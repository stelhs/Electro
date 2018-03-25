from ElectroScene import *
from PyQt4.QtGui import *
import json

EDITOR_GRAPHICS_ITEM = QGraphicsItem.UserType + 1
graphicsItemLastId = 0


def createGraphicsObjectsByProperties(properties):
    items = []
    for itemProp in properties:
        if itemProp['type'] == 'LineItem':
            item = LineItem()
            item.setProperties(itemProp)
            items.append(item)
    return items


class LineItem(QGraphicsLineItem):
    MARK_SIZE = 14


    def __init__(self):
        self.markP1 = None
        self.markP2 = None
        QGraphicsLineItem.__init__(self)
        self.mouseMoveDelta = None
        self.selectedPoint = None
        self.selected = False
        self.center = None
        self.setZValue(1)
        self.copyOf = None
        self.normalPen = QPen(Qt.black, 3, Qt.SolidLine, Qt.RoundCap)
        self.selectedPen = QPen(Qt.magenta, 3, Qt.SolidLine, Qt.RoundCap)
        self.highLightPen = QPen(Qt.blue, 5, Qt.SolidLine, Qt.RoundCap)
        self.setPen(self.normalPen)
        self.deltaCenter = None

        global graphicsItemLastId
        graphicsItemLastId += 1
        self.itemId = graphicsItemLastId


    def id(self):
        return self.itemId


    def type(self):
        return EDITOR_GRAPHICS_ITEM


    def name(self):
        return self.__class__.__name__


    def markPointsShow(self):
        self.markPointsHide()
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


    def setColor(self, color):
        self.normalPen.setColor(color)
        self.setPen(self.normalPen)


    def color(self):
        return self.normalPen.color()


    def setThickness(self, size):
        self.normalPen.setWidth(size)
        self.setPen(self.normalPen)


    def thickness(self):
        return self.normalPen.width()


    def isSelected(self):
        return self.selected


    def select(self):
        self.setPen(self.selectedPen)
        self.selected = True


    def highlight(self):
        self.setPen(self.highLightPen)


    def unHighlight(self):
        if self.isSelected():
            self.setPen(self.selectedPen)
        else:
            self.setPen(self.normalPen)


    def resetSelection(self):
        self.markPointsHide()
        self.setPen(self.normalPen)
        self.selected = False


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
        properties = {}
        properties['id'] = self.id()
        properties['type'] = self.name()
        properties['color'] = {"red" : self.color().red(),
                               "green" : self.color().green(),
                               "blue" : self.color().blue()}
        properties['thickness'] = self.thickness()
        properties['p1'] = {"x" : self.p1().x(), "y": self.p1().y()}
        properties['p2'] = {"x" : self.p2().x(), "y": self.p2().y()}
        return properties


    def setProperties(self, properties):
        self.resetSelection()
        self.setColor(QColor(properties['color']['red'],
                             properties['color']['green'],
                             properties['color']['blue']))
        self.setThickness(properties['thickness'])
        self.setP1(QPointF(properties['p1']['x'], properties['p1']['y']))
        self.setP2(QPointF(properties['p2']['x'], properties['p2']['y']))


    def setCenter(self, point):
        self.deltaCenter = self.pos() - point


    def moveByCenter(self, point):
        self.setPos(QPointF(point + self.deltaCenter))
        if self.isSelected():
            self.markPointsShow()


    def __str__(self):
        str = "Graphics line %d: %d,%d - %d,%d" % (self.id(),
                                  self.p1().x(), self.p1().y(),
                                  self.p2().x(), self.p2().y())

        if self.copyOf:
            str += " | copyOf %d" % self.copyOf

        if self.isSelected():
            str += " | selected"

        if self.deltaCenter:
            str += " | deltaCenter %d,%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str


    def __exit__(self):
        self.markPointsHide()
