from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ElectroEditor import *


class ElectroSceneView(QGraphicsView):


    def __init__(self, editor, scene):
        self.editor = editor
        QGraphicsView.__init__(self, scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoomFactor = 1.5
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMouseTracking(True)
        self.scalePercent = 100
        self.editor.setStatusScale(self.scalePercent)
        self.keyCTRL = False
        self.keyShift = False


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
        self.resetTransform()
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
        if self.keyCTRL:
            deltaY = 0
            if event.angleDelta().y() > 0:
                deltaY += 80
            else:
                deltaY -= 80
            bar = self.verticalScrollBar()
            bar.setValue(bar.value() + deltaY)
            return

        if self.keyShift:
            deltaX = 0
            if event.angleDelta().y() > 0:
                deltaX += 80
            else:
                deltaX -= 80
            bar = self.horizontalScrollBar()
            bar.setValue(bar.value() + deltaX)
            return

        if event.angleDelta().y() > 0:
            self.zoomIn(event.pos())
        else:
            self.zoomOut(event.pos())


    def keyShiftPress(self):
        self.keyShift = True


    def keyCTRLPress(self):
        self.keyCTRL = True


    def keyShiftRelease(self):
        self.keyShift = False


    def keyCTRLRelease(self):
        self.keyCTRL = False


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




