from PyQt4.QtGui import *
from PyQt4.QtCore import *
from ElectroEditor import *
from GraphicsItems import *
from gtk.keysyms import ordfeminine


class ElectroScene(QGraphicsScene):


    def __init__(self, editor):
        QGraphicsScene.__init__(self)
        self.editor = editor
        self.drawingLine = None
        self.multiSelected = False  # Shift key is pressed
        self.selectingByMouse = None  # select rectangular area for selecting items
        self.movingItem = None  # Moving item object
        self.moveMode = None

        self.cursorX = QGraphicsLineItem(None, self)
        self.cursorY = QGraphicsLineItem(None, self)
        self.cursorX.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        self.cursorY.setPen(QPen(Qt.blue, 1, Qt.SolidLine))


    def getPointAttachedToMatrix(self, x, y):
        s = self.editor.matrixStep
        x = round(x / s) * s
        y = round(y / s) * s
        return QPointF(x, y)


    def drawCursor(self, point):
        self.cursorX.setLine(point.x(), 0, point.x(), self.height())
        self.cursorY.setLine(0, point.y(), self.width(), point.y())
        self.cursorX.show()
        self.cursorY.show()


    def hideCursor(self):
        self.cursorX.hide()
        self.cursorY.hide()


    def resetSelectionItems(self):
        for item in self.graphicsItems():
            item.resetSelection()


    def mousePressEventStartRectSelection(self, ev):
        item = self.itemAt(ev.scenePos().x(), ev.scenePos().y())
        if item:
            return False

        self.selectingByMouse = {}
        self.selectingByMouse["startSelectRectPoint"] = ev.scenePos()
        self.selectingByMouse["selectedItems"] = self.selectedGraphicsItems()
        self.selectingByMouse["selectRect"] = None


    def mouseMoveEventMoveRectSelection(self, ev):
        if not self.selectingByMouse:
            return False

        if self.selectingByMouse["selectRect"]:
            self.removeItem(self.selectingByMouse["selectRect"])
            self.selectingByMouse["selectRect"] = None

        x1 = self.selectingByMouse["startSelectRectPoint"].x()
        y1 = self.selectingByMouse["startSelectRectPoint"].y()
        x2 = ev.scenePos().x()
        y2 = ev.scenePos().y()

        topLeft = None
        bottomRight = None
        if x1 < x2 and y1 < y2:
            topLeft = self.selectingByMouse["startSelectRectPoint"]
            bottomRight = ev.scenePos()
        elif x1 > x2 and y1 < y2:
            topLeft = QPointF(x2, y1)
            bottomRight = QPointF(x1, y2)
        elif x1 < x2 and y1 > y2:
            topLeft = QPointF(x1, y2)
            bottomRight = QPointF(x2, y1)
        elif x1 > x2 and y1 > y2:
            topLeft = QPointF(x2, y2)
            bottomRight = QPointF(x1, y1)

        if topLeft:
            selectRect = QGraphicsRectItem(None, self)
            selectRect.setPen(QPen(Qt.black, 1, Qt.DashLine))
            rect = QRectF(topLeft, bottomRight)
            selectRect.setRect(rect)
            self.selectingByMouse["selectRect"] = selectRect

            # unSelect all besides selected early
            for item in self.graphicsItems():
                selected = False
                for selItem in self.selectingByMouse["selectedItems"]:
                    if item == selItem:
                        selected = True

                if selected:
                    continue

                item.resetSelection()

            # Select all items in rectangle
            items = self.items(rect)
            for item in items:
                if item.type() != EDITOR_GRAPHICS_ITEM:
                    continue
                if item == selectRect:
                    continue
                item.select()

        return True


    def mousePressEventSelectItem(self, ev):
        item = self.itemAt(ev.scenePos().x(), ev.scenePos().y())
        if not item:
            if not self.multiSelected:
                self.resetSelectionItems()
            return False

        if not item.isSelected() and len(self.selectedGraphicsItems()) and not self.multiSelected:
            self.resetSelectionItems()

        if item.isSelected() and self.multiSelected:
            item.resetSelection()
        else:
            item.select()
        return True


    def mousePressEvent(self, ev):
        if ev.button() != 1:
            QGraphicsScene.mousePressEvent(self, ev)
            return

        if self.editor.drawState == 'select':
            if self.mousePressEventMovePoint(ev):
                return

            self.mousePressEventMoveItem(ev)

            if self.mousePressEventSelectItem(ev):
                return

            if self.mousePressEventStartRectSelection(ev):
                return
            return

        if self.editor.drawState == 'drawLine':
            p = self.getPointAttachedToMatrix(ev.scenePos().x(), ev.scenePos().y())
            self.drawingLine = LineItem(None, self)
            self.drawingLine.setPen(QPen(Qt.black, 3, Qt.SolidLine))
            self.drawingLine.setP1(p)
            QGraphicsScene.mousePressEvent(self, ev)
            return


    def mousePressEventMovePoint(self, ev):
        if not len(self.items()):
            return False

        point = self.getPointAttachedToMatrix(ev.scenePos().x(), ev.scenePos().y())
        found = False
        for item in self.graphicsItems():
            if item.setSelectPoint(point):
                found = True

        if found:
            self.moveMode = 'Point'
        return found


    def mouseMoveEventMovePoint(self, ev):
        if self.moveMode != 'Point':
            return False

        p = self.getPointAttachedToMatrix(ev.scenePos().x(), ev.scenePos().y())
        for item in self.graphicsItems():
            if not item.isPointSelected():
                continue
            item.modifySelectedPoint(p)
        return True


    def mousePressEventMoveItem(self, ev):
        item = self.itemAt(ev.scenePos())
        if not item:
            return False
        if item.type() != EDITOR_GRAPHICS_ITEM:
            return False

        item.mouseMoveDelta = ev.scenePos() - item.pos()
        # item.select()
        self.movingItem = item
        return True


    def mouseMoveEventMoveItem(self, ev):
        if not self.movingItem:
            return False

        delta = self.movingItem.mouseMoveDelta
        p = QPointF(ev.scenePos() - delta)
        p = self.getPointAttachedToMatrix(p.x(), p.y())
        pos = self.movingItem.pos()
        self.movingItem.setPos(p)

        items = self.selectedGraphicsItems()
        print("move items %d" % len(items))
        for item in items:
            if item == self.movingItem:
                continue
            item.setPos(QPointF(p + item.pos() - pos))

        return True


    def mouseMoveEventDisplayPoints(self, ev):
        items = self.graphicsItems()
        if not len(items):
            return

        for item in items:
            item.markPointsHide()

        item = self.itemAt(ev.scenePos())
        if not item:
            return

        if item.type() != EDITOR_GRAPHICS_ITEM:
            return
        item.markPointsShow()


    def mouseMoveEvent(self, ev):
        if self.editor.drawState == 'select':
            self.mouseMoveEventDisplayPoints(ev)

            if self.mouseMoveEventMoveItem(ev):
                return
            if self.mouseMoveEventMovePoint(ev):
                return
            if self.mouseMoveEventMoveRectSelection(ev):
                return

            QGraphicsScene.mouseMoveEvent(self, ev)
            return

        if self.editor.drawState == 'drawLine':
            p = self.getPointAttachedToMatrix(ev.scenePos().x(), ev.scenePos().y())
            self.drawCursor(p)
            if not self.drawingLine:
                return

            self.drawingLine.setP2(p)
            return


    def mouseReleaseEvent(self, ev):
        drawingLine = self.drawingLine
        selectingByMouse = self.selectingByMouse

        if self.moveMode == 'Point':
            for item in self.graphicsItems():
                item.resetSelectionPoint()

        self.movingItem = None
        self.moveMode = None
        self.drawingLine = None
        self.selectingByMouse = None

        if drawingLine:
            line = drawingLine.line()
            if line.p1() == line.p2():
                self.removeGraphicsItem(drawingLine)
            return

        if selectingByMouse and selectingByMouse["selectRect"]:
            self.removeItem(selectingByMouse["selectRect"])
            return

        QGraphicsScene.mouseReleaseEvent(self, ev)


    def keyPressEvent(self, event):
        key = event.key()
        if key == 16777223:  # DEL
            for item in self.selectedGraphicsItems():
                self.removeGraphicsItem(item)
                item.__exit__()
            return

        if key == 16777248:  # Shift
            print("Shift press")
            self.multiSelected = True
            return

        QGraphicsScene.keyPressEvent(self, event)


    def keyReleaseEvent(self, event):
        key = event.key()
        if key == 16777248:  # Shift
            print("Shift unpress")
            self.multiSelected = False
            return

        QGraphicsScene.keyPressEvent(self, event)


    def graphicsItems(self):
        items = []
        for item in self.items():
            if item.type() != EDITOR_GRAPHICS_ITEM:
                continue
            items.append(item)
        return items


    def selectedGraphicsItems(self):
        items = []
        for item in self.graphicsItems():
            if not item.isSelected():
                continue
            items.append(item)
        return items


    def removeGraphicsItem(self, item):
        item.__exit__()
        self.removeItem(item)
        del item
