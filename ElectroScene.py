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
        self.movingItem = False  # Moving selected items mode
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
        item = self.graphicItemByCoordinate(ev.scenePos())
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
                if not self.isGraphicsItem(item) or item == selectRect:
                    continue
                item = item.root()
                self.itemAddToSelection(item)

        return True


    def mousePressEventSelectItem(self, ev):
        item = self.graphicItemByCoordinate(ev.scenePos())
        if not item:
            if not self.multiSelected:
                self.resetSelectionItems()
            return

        if not item.isSelected() and len(self.selectedGraphicsItems()) and not self.multiSelected:
            self.resetSelectionItems()

        if self.multiSelected:
            if not item.isSelected():
                self.itemAddToSelection(item)
            else:
                self.itemRemoveFromSelection(item)
            return

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
                if not self.keyCTRL:
                    self.history.addItems(self.selectedGraphicsItems())
                    self.resetSelectionItems()
                    self.mode = 'select'
                    return
                self.history.addItems(self.selectedGraphicsItems())
                self.resetSelectionItems()
                self.mode = 'select'
                self.pastFromClipboard()
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

        self.history.changeItemsStart(self.movedPointItems)
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
        item = self.graphicItemByCoordinate(ev.scenePos())
        if not item:
            return

        self.selectedCenter = self.mapToSnap(ev.scenePos())
        for item in self.selectedGraphicsItems():
            item.setCenter(self.selectedCenter)
        self.movingItem = True
        return


    def mouseMoveEventMoveItem(self, ev):
        if not self.movingItem:
            return False
        items = self.selectedGraphicsItems()
        if not items:
            return

        for item in items:
            item.moveByCenter(self.mapToSnap(ev.scenePos()))
        return


    def mouseMoveEventDisplayPoints(self, ev):
        items = self.graphicsItems()
        if not len(items):
            return

        for item in items:
            item.unHighlight()
            if not item.isSelected():
                item.markPointsHide()

        item = self.graphicItemByCoordinate(ev.scenePos())
        if not item:
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
            self.moveSelectedItems(self.mapToSnap(ev.scenePos()))
            return


    def mouseReleaseEvent(self, ev):
        if self.mode == 'pasteFromClipboard':
            return

        selectingByMouse = self.selectingByMouse

        if len(self.movedPointItems):
            self.history.changeItemsFinish()
            for item in self.movedPointItems:
                item.resetSelectionPoint()
            self.movedPointItems = []

        if self.movingItem:
            self.history.changeItemsFinish()
            self.movingItem = False

        self.selectingByMouse = None

        if selectingByMouse and selectingByMouse["selectRect"]:
            self.removeItem(selectingByMouse["selectRect"])
            return

        QGraphicsScene.mouseReleaseEvent(self, ev)


    def graphicItemByCoordinate(self, point):
        item = self.itemAt(point)
        if not item or not self.isGraphicsItem(item):
            return False
        return item.root()


    def keyPressEvent(self, event):
        key = event.key()
        if key == 16777223:  # DEL
            items = self.selectedGraphicsItems()
            self.history.removeItems(items)
            self.removeGraphicsItems(items)
            return

        if key == 16777248:  # Shift
            print("Shift press")
            self.multiSelected = True
            return

        if key == 16777249:  # CTRL
            self.keyCTRL = True
            return

        if key == 83:  # S
            print(self.history)
            print(self)
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
            if self.mode == 'pasteFromClipboard':
                self.calculateSelectionCenter()

            if self.mode != 'pasteFromClipboard':
                self.history.changeItemsStart(self.selectedGraphicsItems())

            self.rotateSelectedItems(90)

            if self.mode != 'pasteFromClipboard':
                self.history.changeItemsFinish()
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
            self.pastFromClipboard()
            return

        if key == 76:  # l (lock)
            self.packSelectedIntoGroup("lock objects")
            return

        if key == 85:  # u (unlock)
            self.unpackSelectedGroups()
            return

        if key == 16777235:  # UP
            p = self.selectedCenter
            p.setY(p.y() - self.editor.matrixStep)
            self.moveSelectedItemsByKeys(p)
            self.calculateSelectionCenter()
            return

        if key == 16777237:  # DOWN
            p = self.selectedCenter
            p.setY(p.y() + self.editor.matrixStep)
            self.moveSelectedItemsByKeys(p)
            self.calculateSelectionCenter()
            return

        if key == 16777234:  # LEFT
            p = self.selectedCenter
            p.setX(p.x() - self.editor.matrixStep)
            self.moveSelectedItemsByKeys(p)
            self.calculateSelectionCenter()
            return

        if key == 16777236:  # RIGHT
            p = self.selectedCenter
            p.setX(p.x() + self.editor.matrixStep)
            self.moveSelectedItemsByKeys(p)
            self.calculateSelectionCenter()
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


    def moveSelectedItemsByKeys(self, point):
        items = self.selectedGraphicsItems()
        if not len(items):
            return

        self.history.changeItemsStart(items)
        self.moveSelectedItems(point)
        self.history.changeItemsFinish()


    def moveSelectedItems(self, point):
        items = self.selectedGraphicsItems()
        if not len(items):
            return

        for item in items:
            item.moveByCenter(point)


    def selectedGraphicsItems(self):
        items = []
        for item in self.graphicsItems():
            if not item.isSelected():
                continue
            items.append(item)
        return items


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


    def itemsAddToSelection(self, items):
        for item in items:
            self.itemAddToSelection(item)


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


    def pastFromClipboard(self):
        jsonText = self.editor.fromClipboard()
        print("pastFromClipboard")
        items = self.graphicsObjectFromJson(jsonText)
        if not len(items):
            print("no data")
            return False

        for item in items:
            self.addGraphicsItem(item)
            self.itemAddToSelection(item)

        for item in items:
            item.moveByCenter(self.mapToSnap(self.mousePos))

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


    def rotateSelectedItems(self, angle):
        for item in self.selectedGraphicsItems():
            item.setCenter(self.selectedCenter)
            item.rotate(self.selectedCenter, angle)
            item.setCenter(self.selectedCenter)


    def graphicsItems(self):
        return self.graphicsItemsList


    def addGraphicsItem(self, item):
        if not self.isGraphicsItem(item):
            return

        self.graphicsItemsList.append(item)
        item.setScene(self)


    def addGraphicsItems(self, items):
        for item in items:
            self.addGraphicsItem(item)


    def isGraphicsItem(self, item):
        if item.type() <= NOT_DEFINED_TYPE:
            return False
        return True


    def packSelectedIntoGroup(self, name):
        if len(self.selectedGraphicsItems()) < 2:
            return None
        group = self.packItemsIntoGroup(self.selectedGraphicsItems(), name)
        self.history.packGroup(group)
        self.itemAddToSelection(group)


    def packItemsIntoGroup(self, items, name="undefined"):
        group = GraphicItemGroup()
        group.setName(name)
        self.resetSelectionItems()
        self.removeGraphicsItems(items)
        group.addItems(items)
        self.addGraphicsItem(group)
        return group


    def unpackGroup(self, group):
        if group.type() != GROUP_TYPE:
            return
        group.markPointsHide()
        items = group.items()
        self.removeGraphicsItem(group)
        self.addGraphicsItems(items)
        return items


    def unpackSelectedGroups(self):
        for item in self.selectedGraphicsItems():
            if item.type() == GROUP_TYPE:
                self.history.unpackGroup(item)
                unpackedItems = self.unpackGroup(item)
                self.itemsAddToSelection(unpackedItems)


    def removeGraphicsItem(self, item):
        self.graphicsItemsList.remove(item)
        item.removeFromQScene()


    def removeGraphicsItems(self, items):
        for item in items:
            self.removeGraphicsItem(item)


    def __str__(self):
        str = "\n--------------\n"
        str += "Scene contain:\n"
        for item in self.graphicsItems():
            str += "%s\n" % item
        return str

