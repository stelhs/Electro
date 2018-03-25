from ElectroScene import *
from PyQt4.QtGui import *

EDITOR_GRAPHICS_ITEM = QGraphicsItem.UserType + 1
graphicsItemLastId = 0


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
        global graphicsItemLastId
        graphicsItemLastId += 1
        self.itemId = graphicsItemLastId
        self.copyOf = None
        self.normalPen = QPen(Qt.black, 3, Qt.SolidLine, Qt.RoundCap)
        self.selectedPen = QPen(Qt.magenta, 6, Qt.SolidLine, Qt.RoundCap)
        self.setPen(self.normalPen)


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
        properties['color'] = self.color()
        properties['thickness'] = self.thickness()
        properties['p1'] = self.p1()
        properties['p2'] = self.p2()
        return properties


    def setProperties(self, properties):
        self.resetSelection()
        self.setColor(properties['color'])
        self.setThickness(properties['thickness'])
        self.setP1(properties['p1'])
        self.setP2(properties['p2'])


    def __str__(self):
        str = "Graphics line %d: %dx%d - %dx%d" % (self.id(),
                                  self.p1().x(), self.p1().y(),
                                  self.p2().x(), self.p2().y())

        if self.copyOf:
            str += " | copyOf %d" % self.copyOf

        if self.isSelected():
            str += " | selected"

        return str


    def __exit__(self):
        self.markPointsHide()
