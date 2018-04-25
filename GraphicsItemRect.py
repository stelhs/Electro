from GraphicsItem import *



class GraphicsItemRect(GraphicsItem, QGraphicsRectItem):
    def __init__(self, rect=None):
        QGraphicsRectItem.__init__(self)
        GraphicsItem.__init__(self)
        if rect:
            self.setPos(rect.topLeft())
            self.setRect(QRectF(0, 0, rect.width(), rect.height()))
        self._fillColor = None
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
            return True

        if self.selectedPoint == 'topRight':
            delta = self.topRight() - new_point
            self.setPos(QPointF(self.pos().x(),
                                self.pos().y() - delta.y()))
            self.setRect(QRectF(0, 0,
                                self.width() - delta.x(),
                                self.height() + delta.y()))
            return True

        if self.selectedPoint == 'bottomLeft':
            delta = self.bottomLeft() - new_point
            self.setPos(QPointF(self.pos().x() - delta.x(),
                                self.pos().y()))
            self.setRect(QRectF(0, 0,
                                self.width() + delta.x(),
                                self.height() - delta.y()))
            return True

        if self.selectedPoint == 'bottomRight':
            delta = new_point - self.pos()
            self.setRect(QRectF(0, 0,
                                delta.x(),
                                delta.y()))
            return True
        return False


    def setFillColor(self, color):
        if not color:
            if self._fillColor:
                self._fillColor.remove()
            self._fillColor = None
            self.setBrush(QBrush(Qt.NoBrush))
            return

        if not self._fillColor:
            self._fillColor = Color(color)
        else:
            self._fillColor.setColor(color)
        self.setBrush(self._fillColor)


    def fillColor(self):
        return self._fillColor


    def properties(self):
        properties = GraphicsItem.properties(self)
        properties['rectSize'] = {"w": self.rect().width(),
                                  "h": self.rect().height()}
        color = self.fillColor()
        if color:
            properties['fillColor'] = {"R": color.red(),
                                       "G": color.green(),
                                       "B": color.blue(),
                                       "A": color.alpha()}
        else:
            properties['fillColor'] = "None"
        return properties


    def setProperties(self, properties, setId=False):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != RECT_TYPE:
            return

        GraphicsItem.setProperties(self, properties, setId)
        rect = QRectF(0, 0,
                      properties['rectSize']['w'],
                      properties['rectSize']['h'])
        if 'fillColor' in properties:
            if properties['fillColor'] == "None":
                self.setFillColor(None)
            else:
                self.setFillColor(QColor(properties['fillColor']['R'],
                                         properties['fillColor']['G'],
                                         properties['fillColor']['B'],
                                         properties['fillColor']['A']))
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
        str = GraphicsItem.__str__(self)
        str += ", size:(%d x %d), z=%d" % (self.width(), self.height(), self.zValue())

        if self.deltaCenter:
            str += " | deltaCenter %d:%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str



