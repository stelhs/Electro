from GraphicsItem import *
from PyQt4.Qt import QGraphicsRectItem, QGraphicsPolygonItem, \
    QGraphicsEllipseItem



class GraphicsItemText(GraphicsItem, QGraphicsTextItem):
    def __init__(self, pos=None, rect=None):
        QGraphicsTextItem.__init__(self)
        GraphicsItem.__init__(self)
        self._angle = 0
        self._rightPoint = None
        self._pos = QPointF(0, 0)
        if pos:
            self.setPos(pos)
        if rect:
            self.setRect(rect)
        self.setZValue(3)
        self.setPen(self.normalPen)
        self.graphicsItemsList.append(self)
        self.markPoints = []
        self.selectedPoint = None
        self.highLightRect = QGraphicsRectItem()
        self.highLightRect.setPen(QPen(self.highLightPen.color(), 1,
                                  Qt.SolidLine, Qt.RoundCap))


    def type(self):
        return TEXT_TYPE


    def setAlignment(self, alignment):
        self._alignment = alignment
        format = QTextBlockFormat()
        format.setAlignment(alignment)
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(format)
        cursor.clearSelection()
        self.setTextCursor(cursor)


    def editEnable(self):
        self.setTextInteractionFlags(Qt.TextEditorInteraction)


    def editDisable(self):
        self.setTextInteractionFlags(Qt.NoTextInteraction)


    def setRect(self, rect):
        if self._angle % 180:
            self.setTextWidth(rect.height())
        else:
            self.setTextWidth(rect.width())


    def focusInEvent(self, event):
        print("focusInEvent")
        scene = self.scene()
        scene.itemTextfocusInEvent(self)
        QGraphicsTextItem.focusInEvent(self, event)


    def focusOutEvent(self, event):
        print("focusOutEvent")
        scene = self.scene()
        scene.itemTextfocusOutEvent(self)
        QGraphicsTextItem.focusOutEvent(self, event)


    def setPen(self, pen):
        self.setDefaultTextColor(pen.color())


    def highlight(self):
        self.highLightRect.setPos(self.pos())
        self.highLightRect.setRect(self._boundingRect())
        self.scene().addItem(self.highLightRect)


    def unHighlight(self):
        if self.highLightRect.scene():
            self.scene().removeItem(self.highLightRect)


    def setPos(self, pos):
        self._pos = pos
        if self._angle % 180:
            pos = self._boundingRect().topRight() + pos
        QGraphicsTextItem.setPos(self, pos)


    def pos(self):
        return self._pos


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
            return self.pos()
        return self.pos() - self.parent().pos()


    def points(self):
        points = []
        pos = QGraphicsTextItem.pos(self)
        points.append(pos)
        if self._angle % 180:
            points.append(pos + QPointF(0, self.height()))
        else:
            points.append(pos + QPointF(self.width(), 0))
        return points


    def width(self, angle=None):
        if angle == None:
            angle = self._angle
        if angle % 180:
            return self.height(0)
        return self.textWidth()


    def height(self, angle=None):
        if angle == None:
            angle = self._angle
        if angle % 180:
            return self.width(0)
        h = QGraphicsTextItem.boundingRect(self).height()
        return round(h / MAX_GRID_SIZE) * MAX_GRID_SIZE


    def _boundingRect(self):
        return QRectF(0, 0, self.width(), self.height())


    def setSelectPoint(self, selPoint):
        if selPoint == self.points()[0]:
            self.selectedPoint = 'p1'
        elif selPoint == self.points()[1]:
            self.selectedPoint = 'p2'

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
        if self._angle % 180:
            if self.selectedPoint == 'p1':
                delta = self.points()[0] - new_point
                self.setPos(new_point - QPointF(self.width(), 0))
                self.setTextWidth(self.textWidth() + delta.y())
                self.markPointsShow()
                return True

            if self.selectedPoint == 'p2':
                delta = self.points()[1] - new_point
                self.setTextWidth(self.textWidth() - delta.y())
                self.markPointsShow()
                return True

        if self.selectedPoint == 'p1':
            delta = self.points()[0] - new_point
            self.setPos(new_point)
            self.setTextWidth(self.textWidth() + delta.x())
            self.markPointsShow()
            return True

        if self.selectedPoint == 'p2':
            delta = self.points()[1] - new_point
            self.setTextWidth(self.textWidth() - delta.x())
            self.markPointsShow()
            return True

        return False


    def text(self):
        return unicode(self.toPlainText())


    def setText(self, text):
        self.setPlainText(text)


    def properties(self):
        properties = GraphicsItem.properties(self)
        properties['rectSize'] = {"w": self.width(),
                                  "h": self.height()}
        properties['angle'] = self._angle % 180
        properties['text'] = self.text()
        return properties


    def setProperties(self, properties, setId=False):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != TEXT_TYPE:
            return

        self._angle = properties['angle']
        GraphicsItem.setProperties(self, properties, setId)
        self.setRect(QRectF(0, 0,
                            properties['rectSize']['w'],
                            properties['rectSize']['h']))
        self.setText(properties['text'])
        QGraphicsTextItem.setRotation(self, self._angle % 180)




    def rotate(self, center, angle):
        rect = QRectF(self.pos(), QSizeF(self.width(), self.height()))

        self._angle += angle
        self._angle %= 360

        t = QTransform()
        t.translate(center.x(), center.y())
        t.rotate(angle)
        t.translate(-center.x(), -center.y())

        p = []
        p.append(t.map(rect.topLeft()))
        p.append(t.map(rect.topRight()))
        p.append(t.map(rect.bottomLeft()))
        p.append(t.map(rect.bottomRight()))
        rect = QPolygonF(p).boundingRect()
        self.setPos(rect.topLeft())

        QGraphicsTextItem.setRotation(self, self._angle % 180)
        self.markPointsShow()


    def resetRotation(self):
        if self._angle == 0:
            return
        pos = self.pos()
        while self._angle != 0:
            self.rotate(pos, 90)
        self.setPos(pos)


    def __str__(self):
        str = GraphicsItem.__str__(self)
        str += ", width:%d, z=%d" % (self.width(), self.zValue())

        if self.deltaCenter:
            str += " | deltaCenter %d:%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str



