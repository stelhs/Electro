from PyQt4.QtGui import *
from PyQt4.QtCore import *
from ElectroEditor import *
from GraphicsItems import *
from History import *
from gtk.keysyms import ordfeminine
import json


class ElectroScene(QGraphicsScene):


    def __init__(self, editor):
        QGraphicsScene.__init__(self)
        self.editor = editor
        self.graphicsItemsList = []
        self.drawingLine = None
        self.multiSelected = False  # Shift key is pressed
        self.selectingByMouse = None  # select rectangular area for selecting items
        self.movingItem = None  # Moving item
        self.movedPointItems = []  # List of Moving point items
        self.mode = 'select'
        self.selectedCenter = None
        self.keyCTRL = False
        self.mousePos = QPointF(0, 0)
        self.drawLinesHistory = []  # temporary array of drawed lines between mouse left and right clicks

        self.history = History(self)

        self.cursorX = QGraphicsLineItem(None, self)
        self.cursorY = QGraphicsLineItem(None, self)
        self.cursorX.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        self.cursorY.setPen(QPen(Qt.blue, 1, Qt.SolidLine))


    def mapToSnap(self, point):
        s = self.editor.matrixStep
        x = round(point.x() / s) * s
        y = round(point.y() / s) * s
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
        for item in self.selectedGraphicsItems():
            self.itemRemoveFromSelection(item)


    def mousePressEventStartRectSelection(self, ev):
        item = self.itemAt(ev.scenePos())
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

                self.itemRemoveFromSelection(item)

            # Select all items in rectangle
            items = self.items(rect)
            for item in items:
                if not self.isGraphicsItem(item):
                    continue
                if item == selectRect:
                    continue
                self.itemAddToSelection(item)

        return True


    def mousePressEventSelectItem(self, ev):
        item = self.itemAt(ev.scenePos())
        if not item or (not self.isGraphicsItem(item)) or item.group():
            if not self.multiSelected:
                self.resetSelectionItems()
            return False

        if not item.isSelected() and len(self.selectedGraphicsItems()) and not self.multiSelected:
            self.resetSelectionItems()

        if self.multiSelected:
            self.itemAddToSelection(item)
            return

        print("start moving")
        self.itemAddToSelection(item)
        return True


    def mousePressEvent(self, ev):
        if ev.button() == 1:
            if self.mode == 'select':
                if self.mousePressEventMovePoint(ev):
                    return

                self.mousePressEventSelectItem(ev)
                self.mousePressEventMoveItem(ev)

                if self.mousePressEventStartRectSelection(ev):
                    return
                return

            if self.mode == 'drawLine':
                if self.drawingLine:
                    self.drawLinesHistory.append(self.drawingLine)

                p = self.mapToSnap(ev.scenePos())
                self.drawingLine = GraphicItemLine()
                self.drawingLine.setP1(p)
                self.addGraphicsItem(self.drawingLine)
                QGraphicsScene.mousePressEvent(self, ev)
                return

            if self.mode == 'pasteFromClipboard':
                self.mode = 'select'
                return

        if ev.button() == 2:
            if self.mode == 'select':
                self.resetSelectionItems()
                return

            if self.mode == 'drawLine':
                if self.drawingLine:
                    self.stopLineDrawing()
                else:
                    self.setMode('select')
                return

            if self.mode == 'pasteFromClipboard':
                self.setMode('select')
                return

        QGraphicsScene.mousePressEvent(self, ev)


    def stopLineDrawing(self):
        if not self.drawingLine:
            return

        self.removeGraphicsItem(self.drawingLine)
        self.drawingLine = None
        self.history.addItems(self.drawLinesHistory)
        self.drawLinesHistory = []


    def mousePressEventMovePoint(self, ev):
        if not len(self.graphicsItems()):
            return False

        point = self.mapToSnap(ev.scenePos())
        for item in self.graphicsItems():
            if item.setSelectPoint(point):
                self.movedPointItems.append(item)

        if not len(self.movedPointItems):
            return False

        self.history.changeItemsBefore(self.movedPointItems)
        return True


    def mouseMoveEventMovePoint(self, ev):
        if not len(self.movedPointItems):
            return False

        p = self.mapToSnap(ev.scenePos())
        for item in self.graphicsItems():
            if item.isPointSelected():
                item.modifySelectedPoint(p)
        self.calculateSelectionCenter()
        return True


    def mousePressEventMoveItem(self, ev):
        item = self.itemAt(ev.scenePos())
        if not item or not self.isGraphicsItem(item) or item.group():
            return False

        item.mouseMoveDelta = ev.scenePos() - item.pos()
        self.movingItem = item
        self.history.changeItemsBefore(self.selectedGraphicsItems())
        return True


    def mouseMoveEventMoveItem(self, ev):
        if not self.movingItem:
            return False

        delta = self.movingItem.mouseMoveDelta
        p = QPointF(ev.scenePos() - delta)
        p = self.mapToSnap(p)
        pos = self.movingItem.pos()
        self.movingItem.setPos(p)
        if not self.movingItem.isSelected():
            self.itemAddToSelection(self.movingItem)

        items = self.selectedGraphicsItems()
        for item in items:
            if item == self.movingItem:
                continue
            item.setPos(QPointF(p + item.pos() - pos))
            item.markPointsShow()
        self.calculateSelectionCenter()
        return True


    def mouseMoveEventDisplayPoints(self, ev):
        items = self.graphicsItems()
        if not len(items):
            return

        for item in items:
            item.unHighlight()
            if not item.isSelected():
                item.markPointsHide()

        item = self.itemAt(ev.scenePos())
        if not item or not self.isGraphicsItem(item) or item.group():
            return

        item.markPointsShow()
        item.highlight()


    def mouseMoveEvent(self, ev):
        self.mousePos = ev.scenePos()
        if self.mode == 'select':
            self.mouseMoveEventDisplayPoints(ev)

            if self.mouseMoveEventMoveItem(ev):
                return
            if self.mouseMoveEventMovePoint(ev):
                return
            if self.mouseMoveEventMoveRectSelection(ev):
                return

            QGraphicsScene.mouseMoveEvent(self, ev)
            return

        if self.mode == 'drawLine':
            p = self.mapToSnap(ev.scenePos())
            self.drawCursor(p)
            self.editor.setCursorCoordinates(p)

            if not self.drawingLine:
                return

            self.drawingLine.setP2(p)
            return

        if self.mode == 'pasteFromClipboard':
            for item in self.selectedGraphicsItems():
                item.moveByCenter(self.mapToSnap(ev.scenePos()))
            self.calculateSelectionCenter()
            return


    def mouseReleaseEvent(self, ev):
#        drawingLine = self.drawingLine
        selectingByMouse = self.selectingByMouse

        if len(self.movedPointItems):
            self.history.changeItemsAfter(self.movedPointItems)
            for item in self.movedPointItems:
                item.resetSelectionPoint()
            self.movedPointItems = []

        if self.movingItem:
            self.history.changeItemsAfter(self.selectedGraphicsItems())
            self.movingItem = None

        self.selectingByMouse = None

        if selectingByMouse and selectingByMouse["selectRect"]:
            self.removeItem(selectingByMouse["selectRect"])
            return

        QGraphicsScene.mouseReleaseEvent(self, ev)


    def keyPressEvent(self, event):
        key = event.key()
        if key == 16777223:  # DEL
            items = self.selectedGraphicsItems()
            self.history.removeItems(items)
            for item in items:
                self.removeGraphicsItem(item)
                item.__exit__()
            return

        if key == 16777248:  # Shift
            print("Shift press")
            self.multiSelected = True
            return

        if key == 16777249:  # CTRL
            self.keyCTRL = True
            return

        if key == 83:  # S
            print(self)
            print(self.history)
            return

        if key == 16777219:  # Backspace
            if self.mode == 'drawLine':
                if not len(self.drawLinesHistory):
                    return

                self.removeGraphicsItem(self.drawingLine)
                self.drawingLine = self.drawLinesHistory.pop()
                self.drawingLine.setP2(self.mousePos)
                return

        if key == 32:  # Space
            self.history.changeItemsBefore(self.selectedGraphicsItems())
            for item in self.selectedGraphicsItems():
                item.rotate(self.selectedCenter, 90)
                item.setCenter(self.selectedCenter)
            self.history.changeItemsAfter(self.selectedGraphicsItems())
            return

        if self.keyCTRL and key == 65:  # CTLR + A
            for item in self.graphicsItems():
                self.itemAddToSelection(item)

        if self.keyCTRL and key == 90:  # CTLR + Z
            self.history.undo()
            return

        if self.keyCTRL and key == 89:  # CTLR + Y
            self.history.redo()
            return

        if self.keyCTRL and key == 67:  # CTLR + C
            self.copySelectedToClipboard()
            return

        if self.keyCTRL and key == 88:  # CTLR + X
            self.copySelectedToClipboard()
            self.removeGraphicsItems(self.selectedGraphicsItems())
            return

        if self.keyCTRL and key == 86:  # CTLR + V
            self.pastFromClipboard(self.editor.fromClipboard())
            return

        if key == 76:  # l (lock)
            self.selectedToNewGroup("lock objects")
            return

        if key == 85:  # u (unlock)
            self.unpackSelectedGroup()
            return

        if key == 16777235:  # UP
            p = self.selectedCenter
            p.setY(p.y() - self.editor.matrixStep)
            self.moveSelectedItems(p)
            return

        if key == 16777237:  # DOWN
            p = self.selectedCenter
            p.setY(p.y() + self.editor.matrixStep)
            self.moveSelectedItems(p)
            return

        if key == 16777234:  # LEFT
            p = self.selectedCenter
            p.setX(p.x() - self.editor.matrixStep)
            self.moveSelectedItems(p)
            return

        if key == 16777236:  # RIGHT
            p = self.selectedCenter
            p.setX(p.x() + self.editor.matrixStep)
            self.moveSelectedItems(p)
            return

        QGraphicsScene.keyPressEvent(self, event)


    def keyReleaseEvent(self, event):
        key = event.key()
        if key == 16777248:  # Shift
            print("Shift unpress")
            self.multiSelected = False
            return

        if key == 16777249:  # CTRL
            self.keyCTRL = False
            return

        QGraphicsScene.keyPressEvent(self, event)


    def moveSelectedItems(self, point):
        items = self.selectedGraphicsItems()
        if not len(items):
            return

        self.history.changeItemsBefore(items)
        for item in items:
            item.moveByCenter(point)
        self.history.changeItemsAfter(items)


    def selectedGraphicsItems(self):
        items = []
        for item in self.graphicsItems():
            if not item.isSelected():
                continue
            items.append(item)
        return items


    def removeGraphicsItem(self, item):
        item.__exit__()
        self.graphicsItemsList.remove(item)
        self.removeItem(item)


    def removeGraphicsItems(self, items):
        for item in items:
            self.removeGraphicsItem(item)


    def removeGraphicsItemById(self, id):
        item = self.itemById(id)
        if not item:
            return False
        self.removeGraphicsItem(item)
        return True


    def itemById(self, id):
        for item in self.graphicsItems():
            if item.id() == id:
                return item
        return None


    def setMode(self, mode):
        if self.mode == 'pasteFromClipboard':
            self.removeGraphicsItems(self.selectedGraphicsItems())

        if mode == "select":
            self.mode = 'select'
            self.hideCursor()
            self.resetSelectionItems()
            self.stopLineDrawing()

        if mode == "drawLine":
            self.drawCursor(self.mapToSnap(self.mousePos))

        self.mode = mode


    def calculateSelectionCenter(self):
        poligon = QPolygonF()
        for item in self.selectedGraphicsItems():
            poligon += item.mapToScene(item.boundingRect())
        if not poligon:
            return

        rect = poligon.boundingRect()
        self.selectedCenter = self.mapToSnap(rect.center())


    def itemAddToSelection(self, item):
        item.select()
        item.markPointsShow()
        self.calculateSelectionCenter()
        for item in self.selectedGraphicsItems():
            item.setCenter(self.selectedCenter)


    def itemRemoveFromSelection(self, item):
        item.resetSelection()
        item.markPointsHide()
        item.unHighlight()
        self.calculateSelectionCenter()


    def copySelectedToClipboard(self):
        items = self.selectedGraphicsItems()
        if not len(items):
            return

        ItemsProperties = []
        for item in items:
            ItemsProperties.append(item.properties())

        jsonText = json.dumps(ItemsProperties)
        self.editor.toClipboard(jsonText)


    def pastFromClipboard(self, jsonText):
        items = self.graphicsObjectFromJson(jsonText)
        if not len(items):
            return False

        for item in items:
            self.addGraphicsItem(item)
            self.itemAddToSelection(item)

        for item in self.selectedGraphicsItems():
            item.moveByCenter(self.mapToSnap(self.mousePos))

        self.history.addItems(items)

        self.setMode("pasteFromClipboard")
        return True


    def graphicsObjectFromJson(self, jsonText):
        try:
            ItemsProperties = json.loads(str(jsonText))
        except:
            print("Bad clipboard data")
            return []

        self.resetSelectionItems()
        return createGraphicsObjectsByProperties(ItemsProperties)


    def graphicsItems(self):
        return self.graphicsItemsList


    def addGraphicsItem(self, item):
        if not self.isGraphicsItem(item):
            return
        self.graphicsItemsList.append(item)
        self.addItem(item)


    def isGraphicsItem(self, item):
        if item.type() <= NOT_DEFINED_TYPE:
            return False
        return True


    def selectedToNewGroup(self, name="undefined"):
        if len(self.selectedGraphicsItems()) < 2:
            return None
        group = GraphicItemGroup()
        group.setName(name)
        items = self.selectedGraphicsItems()
        self.resetSelectionItems()
        group.addItems(items)
        for item in items:
            item.markPointsHide()
            self.graphicsItemsList.remove(item)
        self.addGraphicsItem(group)
        self.history.addGroup(group)
        return group


    def unpackGroup(self, group):
        if group.type() != GROUP_TYPE:
            return
        group.markPointsHide()
        self.removeGraphicsItem(group)


    def unpackSelectedGroup(self):
        for item in self.selectedGraphicsItems():
            if item.type() == GROUP_TYPE:
                self.unpackGroup(item)
                self.history.removeGroup(item)


    def __str__(self):
        str = "\n--------------\n"
        str += "Scene contain:\n"
        for item in self.graphicsItems():
            str += "%s\n" % item
        return str

