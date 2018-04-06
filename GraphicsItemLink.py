from GraphicsItem import *



class GraphicsItemLink(GraphicsItem, QGraphicsItem):
    def __init__(self):
        QGraphicsItem.__init__(self)
        GraphicsItem.__init__(self)
        self.setZValue(1)
        self._angle = 0
        self._pen = QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap)
        self._linkId = 184
        self._boundingRect = QRectF()
        self.graphicsItemsList.append(self)


    def setLinkId(self, linkId):
        self._linkId = linkId


    def type(self):
        return LINK_TYPE


    def setPen(self, pen):
        self._pen = pen
        self.update()




    def paint(self, painter, style, widget):
        painter.setPen(self._pen)
        circleDiameter = 8

        if self._angle == 0:
            lineX = MAX_GRID_SIZE
            lineY = 0
            circleX = lineX
            circleY = -(circleDiameter / 2)
            rotate = 0
            align = Qt.AlignRight
            linkIdRect = QRectF(0, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 1.5, MAX_GRID_SIZE)


        elif self._angle == 90:
            lineX = 0
            lineY = MAX_GRID_SIZE
            circleX = -(circleDiameter / 2)
            circleY = lineY
            rotate = 90
            align = Qt.AlignRight
            linkIdRect = QRectF(0, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 1.5, MAX_GRID_SIZE)

        elif self._angle == 180:
            lineX = -MAX_GRID_SIZE
            lineY = 0
            circleX = lineX - circleDiameter
            circleY = -(circleDiameter / 2)
            rotate = 0
            align = Qt.AlignLeft
            linkIdRect = QRectF(-MAX_GRID_SIZE * 1.5, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 1.5, MAX_GRID_SIZE)

        elif self._angle == 270:
            lineX = 0
            lineY = -MAX_GRID_SIZE
            circleX = -(circleDiameter / 2)
            circleY = lineY - circleDiameter
            rotate = -90
            align = Qt.AlignRight
            linkIdRect = QRectF(0, -MAX_GRID_SIZE,
                                MAX_GRID_SIZE * 1.5, MAX_GRID_SIZE)

        painter.drawLine(0, 0, lineX, lineY)
        painter.drawEllipse(circleX, circleY,
                            circleDiameter, circleDiameter)

        painter.rotate(rotate);
        painter.drawText(linkIdRect, align, "%d" % self._linkId)
        painter.drawText(QRectF(0, circleDiameter,
                                MAX_GRID_SIZE * 1.5, MAX_GRID_SIZE),
                                align, "12/A7")
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
        properties['linkId'] = 1  # TODO !!!!
        return properties


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != LINK_TYPE:
            return


    def rotate(self, center, angle):
        self._angle += angle
        self._angle = self._angle % 360
        self.prepareGeometryChange()
        self.update()


    def __str__(self):
        str = GraphicsItem.__str__(self)
        str += ", link with id: %d" % properties['linkId']

        return str



