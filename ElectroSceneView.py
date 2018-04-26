from PyQt4.QtGui import *
from PyQt4.QtCore import *
from ElectroEditor import *


class ElectroSceneView(QGraphicsView):


    def __init__(self, editor, scene):
        self.editor = editor
        QGraphicsView.__init__(self, scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoomFactor = 1.25
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # self.horizontalScrollBar().setValue(scene.sceneRect().left())
        # self.verticalScrollBar().setValue(scene.sceneRect().top())
        self.setMouseTracking(True)
        self.scalePercent = 100
        self.editor.setStatusScale(self.scalePercent)
        # self.setFocusPolicy(Qt.NoFocus)


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
        self.scalePercent *= self.zoomFactor
        self.editor.setStatusScale(self.scalePercent)


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
        self.scalePercent /= self.zoomFactor
        self.editor.setStatusScale(self.scalePercent)


    def zoomReset(self, zoomPos):
        c = QCursor()
        mousePos = c.pos()
        scenePos = self.mapToScene(zoomPos)

        self.resetMatrix()
        self.centerOn(QPointF(scenePos))

        movedPos = self.mapFromScene(scenePos)
        newMousePos = mousePos + (movedPos - zoomPos)
        c.setPos(newMousePos)
        self.scalePercent = 100
        self.editor.setStatusScale(self.scalePercent)


    def setZoom(self, percent, center=None):
        self.scalePercent = percent
        self.editor.setStatusScale(self.scalePercent)
        self.resetMatrix()
        if percent == 100:
            self.centerOn(center)
            return
        zoomFactor = percent / 100
        self.scale(zoomFactor, zoomFactor)
        if not center:
            return
        self.centerOn(center)


    def zoom(self):
        return self.scalePercent


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

        self.editor.keyPressEvent(event)


    def keyReleaseEvent(self, event):
        key = event.key()
        if key == 16777251:  # ALT
            self.setDragMode(QGraphicsView.NoDrag)
            return

        self.editor.keyReleaseEvent(event)


    def focusOutEvent(self, event):
        self.editor.focusOutEvent(event)


    def center(self):
        return self.mapToScene(QPoint(self.width() / 2, self.height() / 2))




