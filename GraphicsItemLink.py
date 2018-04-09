from GraphicsItem import *



class GraphicsItemLink(GraphicsItem, QGraphicsItem):
    def __init__(self, pos):
        QGraphicsItem.__init__(self)
        GraphicsItem.__init__(self)
        self.setPos(pos)
        self.setZValue(1)
        self._angle = 0
        self._pen = self.normalPen
        self._connection = None
        self._boundingRect = QRectF()
        self.graphicsItemsList.append(self)


    def type(self):
        return LINK_TYPE


    def setPen(self, pen):
        self._pen = pen
        self.update()


    def paint(self, painter, style, widget):
        painter.setPen(self._pen)
        circleDiameter = 6

        if self._angle == 0:
            lineX = MAX_GRID_SIZE
            lineY = 0
            circleX = lineX
            circleY = -(circleDiameter / 2)
            rotate = 0
            align = Qt.AlignCenter
            connIdRect = QRectF(0, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)
            addrRect = QRectF(0, circleDiameter,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)

        elif self._angle == 90:
            lineX = 0
            lineY = MAX_GRID_SIZE
            circleX = -(circleDiameter / 2)
            circleY = lineY
            rotate = 90
            align = Qt.AlignCenter
            connIdRect = QRectF(0, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)
            addrRect = QRectF(0, circleDiameter,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)

        elif self._angle == 180:
            lineX = -MAX_GRID_SIZE
            lineY = 0
            circleX = lineX - circleDiameter
            circleY = -(circleDiameter / 2)
            rotate = 0
            align = Qt.AlignCenter
            connIdRect = QRectF(-MAX_GRID_SIZE * 2, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)
            addrRect = QRectF(-MAX_GRID_SIZE * 2, circleDiameter,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)

        elif self._angle == 270:
            lineX = 0
            lineY = -MAX_GRID_SIZE
            circleX = -(circleDiameter / 2)
            circleY = lineY - circleDiameter
            rotate = -90
            align = Qt.AlignCenter
            connIdRect = QRectF(0, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)
            addrRect = QRectF(0, circleDiameter,
                                MAX_GRID_SIZE * 2, MAX_GRID_SIZE)

        painter.drawLine(0, 0, lineX, lineY)
        painter.setBrush(QBrush(self._pen.color()))
        painter.drawEllipse(circleX, circleY,
                            circleDiameter, circleDiameter)

        painter.rotate(rotate);
        if self.connection():
            painter.drawText(connIdRect, align, "%d" % self.connection().id())
            painter.drawText(addrRect, align, self.addressRemote())
        painter.rotate(-rotate);


    def boundingRect(self):
        if self._angle == 0:
            return QRectF(0,
                          - MAX_GRID_SIZE,
                          MAX_GRID_SIZE * 2,
                          MAX_GRID_SIZE * 2)

        if self._angle == 90:
            return QRectF(-MAX_GRID_SIZE,
                          0,
                          MAX_GRID_SIZE * 2,
                          MAX_GRID_SIZE * 2)

        if self._angle == 180:
            return QRectF(-MAX_GRID_SIZE * 2,
                          - MAX_GRID_SIZE,
                          MAX_GRID_SIZE * 2,
                          MAX_GRID_SIZE * 2)

        if self._angle == 270:
            return QRectF(-MAX_GRID_SIZE,
                          - MAX_GRID_SIZE * 2,
                          MAX_GRID_SIZE * 2,
                          MAX_GRID_SIZE * 2)


    def posFromParent(self):
        if not self.parent():
            return QGraphicsItem.pos(self)
        return QGraphicsItem.pos(self) - self.parent().pos()


    def properties(self):
        properties = GraphicsItem.properties(self)
        return properties


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != LINK_TYPE:
            return
        GraphicsItem.setProperties(self, properties)


    def rotate(self, center, angle):
        self._angle += angle
        self._angle = self._angle % 360
        self.prepareGeometryChange()
        self.update()


    def setConnection(self, conn):
        self._connection = conn
        self.update()


    def connection(self):
        return self._connection


    def addressRemote(self):
        if not self._connection:
            return
        otherLinkPoint = None
        for linkPoint in self._connection.linkPoints():
            if linkPoint != self:
                otherLinkPoint = linkPoint
        scene = otherLinkPoint.scene()
        quadrant = scene.quadrantByPos(otherLinkPoint.pos())
        return "%d/%s" % (scene.num(), quadrant)


    def setPos(self, pos):
        QGraphicsItem.setPos(self, pos)
        self.update()


    def __str__(self):
        str = GraphicsItem.__str__(self)
        if self.deltaCenter:
            str += " | deltaCenter %d:%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str



connection_last_id = 0
class Connection():
    def __init__(self, linkPoint1, linkPoint2):
        global connection_last_id
        self._linkPoints = []
        self._linkPoints.append(linkPoint1)
        self._linkPoints.append(linkPoint2)
        connection_last_id += 1
        self._id = connection_last_id
        for linkPoint in self._linkPoints:
            linkPoint.setConnection(self)


    def id(self):
        return self._id


    def linkPoints(self):
        return self._linkPoints


    def remove(self):
        for linkPoint in self._linkPoints:
            linkPoint.setConnection(None)




