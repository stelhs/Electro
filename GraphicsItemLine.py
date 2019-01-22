"""
 * Schematic graphic line unit
 *
 * Copyright (c) 2018 Michail Kurochkin
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 """

from PyQt5.QtGui import *
from PyQt5.Qt import QPoint
from GraphicsItem import *


class GraphicsItemLine(GraphicsItem, QGraphicsLineItem):
    tracePen = QPen(Color(0, 0, 0), 2, Qt.SolidLine, Qt.RoundCap)

    def __init__(self, type='line'):
        QGraphicsLineItem.__init__(self)
        GraphicsItem.__init__(self)
        self._typeLine = type
        self.markP1 = None
        self.markP2 = None
        self.selectedPoint = None
        self.graphicsItemsList.append(self)
        self._zIndex = 2
        self.resetSelection()
        self.arrowsType = None

        self.setTypeLine(self._typeLine)


    def type(self):
        return LINE_TYPE


    def setTypeLine(self, type):
        self._typeLine = type
        self.updateView()


    def updateView(self):
        if self._typeLine == 'trace':
            self.normalPen = self.tracePen
        else:
            self.normalPen = self.defaultPen
        GraphicsItem.updateView(self)


    def typeLine(self):
        return self._typeLine


    def changeArrows(self, arrowsType):
        self.arrowsType = arrowsType


    def paint(self, painter, style, widget):
        # TODO: implement arrows
        QGraphicsLineItem.paint(self, painter, style, widget)


    def setPenStyle(self, penStyle):
        if self._typeLine == 'trace':
            return
        return GraphicsItem.setPenStyle(self, penStyle)


    def setThickness(self, thickness):
        if self._typeLine == 'trace':
            return
        return GraphicsItem.setThickness(self, thickness)


    def markPointsShow(self):
        self.markPointsHide()
        if self.parent():
            return

        self.markP1 = QGraphicsRectItem(None)
        self.scene().addItem(self.markP1)
        self.markP1.setZValue(0)
        self.markP1.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        x1 = self.p1().x() - self.MARK_SIZE / 2
        y1 = self.p1().y() - self.MARK_SIZE / 2
        self.markP1.setRect(x1, y1, self.MARK_SIZE, self.MARK_SIZE)

        self.markP2 = QGraphicsRectItem(None)
        self.scene().addItem(self.markP2)
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
        return False


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
            return True

        if self.selectedPoint == 2:
            self.setP2(new_point)
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
        properties = GraphicsItem.properties(self)
        properties['typeLine'] = self.typeLine()
        if self.typeLine() == 'trace':
            del properties['color']
        properties['p1'] = {"x" : self.line().p1().x(), "y": self.line().p1().y()}
        properties['p2'] = {"x" : self.line().p2().x(), "y": self.line().p2().y()}
        return properties


    def setProperties(self, properties, setId=False):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != LINE_TYPE:
            return

        self.setTypeLine(properties['typeLine'])
        if self.typeLine() == 'trace' and 'color' in properties:
            del properties['color']
        GraphicsItem.setProperties(self, properties, setId)
        line = QLineF(QPointF(properties['p1']['x'], properties['p1']['y']),
                      QPointF(properties['p2']['x'], properties['p2']['y']))
        self.setLine(line)


    def __str__(self):
        str = GraphicsItem.__str__(self)
        str += ", (%d:%d - %d:%d), z=%d" % (self.p1().x(), self.p1().y(),
                                     self.p2().x(), self.p2().y(), self.zValue())

        if self.deltaCenter:
            str += " | deltaCenter %d:%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str


