"""
 * QT electric schemaic window widget
 *    For each schematic page used one instane of this class
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
from PyQt5.QtCore import *
from ElectroEditor import *


class ElectroSceneView(QGraphicsView):


    def __init__(self, editor, scene):
        self.editor = editor
        QGraphicsView.__init__(self, scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoomFactor = 1.25
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMouseTracking(True)
        self.scalePercent = 100
        self.editor.setStatusScale(self.scalePercent)
        self.keyCTRL = False
        self.keyShift = False

        # reset navigation history timer if ElectroSceneView changed
        vbar = self.verticalScrollBar()
        hbar = self.horizontalScrollBar()
        vbar.valueChanged.connect(editor.navigationHistory.resetTimer)
        hbar.valueChanged.connect(editor.navigationHistory.resetTimer)


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
        self.editor.navigationHistory.resetTimer()
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

    def resizeEvent(self, event):
        print("resize event")

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
#        return self.mapToScene(QPoint(self.width() / 2, self.height() / 2))
        return self.mapToScene(self.viewport().rect().center())


    def scenePos(self):
        return SceneViewPosition(self.center(), self.zoom())



class SceneViewPosition():
    def __init__(self, *args):
        if not len(args):
            raise Exception('no enoight constructor arguments')

        if type(args[0]).__name__ == 'QPointF':
            self._pos = args[0];
            self._zoom = args[1]
        elif type(args[0]).__name__ == 'int':
            self._pos = QPointF(args[0], args[1]);
            self._zoom = args[2]
        else:
            raise Exception('incorrect constructor arguments')

    def pos(self):
        return self._pos

    def zoom(self):
        return self._zoom

    def __eq__(self, scenePos):
        if scenePos is None:
            return False
        r = QRect(self.pos().x() - 1,
                  self.pos().y() - 1, 3, 3)
        return r.contains(scenePos.pos().toPoint()) and self.zoom() == scenePos.zoom()

    def __str__(self):
        return '(%d, %d), zoom:%d' % (self._pos.x(),
                                              self._pos.y(),
                                              self._zoom)


