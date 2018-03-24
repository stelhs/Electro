from PyQt4.QtGui import *
from PyQt4.QtCore import *
from ElectroEditor import *


class ElectroSceneView(QGraphicsView):


    def __init__(self, editor, scene):
        self.editor = editor
        QGraphicsView.__init__(self, scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoomFactor = 1.25
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft);


    def drawBackground(self, qp, rect):
        x_step = self.editor.matrixStep
        y_step = self.editor.matrixStep
        x_cnt = int(self.scene().width() / x_step)
        y_cnt = int(self.scene().height() / y_step)

        qp.setPen(QPen(QColor(220, 220, 220), 1))
        for i in range(x_cnt):
            qp.drawLine(i * x_step, 0, i * x_step, self.scene().height());

        for i in range(y_cnt):
            qp.drawLine(0, i * y_step, self.scene().width(), i * y_step);


    def zoomIn(self, zoomPos):
        c = QCursor()
        mousePos = c.pos()
        scenePos = self.mapToScene(zoomPos)

        zoomFactor = self.zoomFactor
        self.scale(zoomFactor, zoomFactor)
        self.centerOn(QPointF(scenePos))

        movedPos = self.mapFromScene(scenePos)
        newMousePos = mousePos + (movedPos - zoomPos)
        c.setPos(newMousePos)


    def zoomOut(self, zoomPos):
        c = QCursor()
        mousePos = c.pos()
        scenePos = self.mapToScene(zoomPos)

        zoomFactor = 1 / self.zoomFactor
        self.scale(zoomFactor, zoomFactor)
        self.centerOn(QPointF(scenePos))

        movedPos = self.mapFromScene(scenePos)
        newMousePos = mousePos + (movedPos - zoomPos)
        c.setPos(newMousePos)


    def zoomReset(self, zoomPos):
        c = QCursor()
        mousePos = c.pos()
        scenePos = self.mapToScene(zoomPos)

        self.resetMatrix()
        self.centerOn(QPointF(scenePos))

        movedPos = self.mapFromScene(scenePos)
        newMousePos = mousePos + (movedPos - zoomPos)
        c.setPos(newMousePos)


    def wheelEvent(self, event):
        if event.delta() > 0:
            self.zoomIn(event.pos())
        else:
            self.zoomOut(event.pos())


    def keyPressEvent(self, event):
        key = event.key()
        if key == 16777251:  # ALT
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            return

        QGraphicsView.keyPressEvent(self, event)


    def keyReleaseEvent(self, event):
        key = event.key()
        if key == 16777251:  # ALT
            self.setDragMode(QGraphicsView.NoDrag)
            return

        QGraphicsView.keyPressEvent(self, event)


    def mousePressEvent(self, ev):
        if ev.button() == 2:
            self.editor.drawState = 'select'
            self.scene().hideCursor()
            self.scene().resetSelectionItems()
            return

        QGraphicsView.mousePressEvent(self, ev)

