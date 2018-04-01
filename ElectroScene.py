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
        self.minGridSize = 5
        self.maxGridSize = self.minGridSize * 4
        self.gridSize = self.minGridSize
        self.history = History(self)

        self.cursorX = QGraphicsLineItem(None, self)
        self.cursorY = QGraphicsLineItem(None, self)
        self.cursorX.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        self.cursorY.setPen(QPen(Qt.blue, 1, Qt.SolidLine))

        self.interceptionPoints = []

        self.horizontalFieldsCount = 20
        self.verticalFieldsCount = 10

        self.horizontalFieldsHeight = 4  # in minGridSize
        self.verticalFieldsWidth = 4  # in minGridSize

        self.sceneRectSize = QPointF(400, 200)  # in minGridSize

        self.setGrid(self.maxGridSize)


        # configure graphic paper
        def pix(val):
            return val * self.minGridSize


        self.setSceneRect(-pix(self.horizontalFieldsHeight + 1),
                          - pix(self.verticalFieldsWidth + 1),
                          pix(self.sceneRectSize.x()),
                          pix(self.sceneRectSize.y()))
        self.bottomRight = QPointF(pix(self.sceneRectSize.x()),
                                   pix(self.sceneRectSize.y()))


    def setGrid(self, gridSize):
        self.gridSize = gridSize
        self.editor.setGridSize(gridSize)
        self.update()


    def changeGridSize(self):
        gridSize = self.gridSize
        gridSize /= 2
        if gridSize < self.minGridSize:
            gridSize = self.maxGridSize
        self.setGrid(gridSize)


    def drawBackground(self, qp, viewRect):
#        print("drawBackground scene")

        letters = ['A', 'B', 'C', 'D',
                   'E', 'F', 'G', 'H',
                   'I', 'J', 'K', 'L']


        def pix(val):
            return val * self.minGridSize


        # draw grid in viewRect
        p = self.mapToGrid(viewRect.topLeft())
        startX = p.x() - self.gridSize
        startY = p.y() - self.gridSize
        if startX < 0:
            startX = 0
        if startY < 0:
            startY = 0

        viewWidth = startX + viewRect.width() + self.gridSize
        viewHeight = startY + viewRect.height() + self.gridSize
        if viewWidth > pix(self.sceneRectSize.x()):
            viewWidth = pix(self.sceneRectSize.x())
        if viewHeight > pix(self.sceneRectSize.y()):
            viewHeight = pix(self.sceneRectSize.y())

        qp.setPen(QPen(QColor(230, 230, 230), 1))

        x_step = self.gridSize
        y_step = self.gridSize
        x_cnt = int(viewWidth / x_step)
        y_cnt = int(viewHeight / y_step)

        for i in range(x_cnt - 1):
            qp.drawLine(startX + (i + 1) * x_step, startY + 1,
                        startX + (i + 1) * x_step, startY + viewHeight - 1);

        for i in range(y_cnt - 1):
            qp.drawLine(startX + 1, startY + (i + 1) * y_step,
                        startX + viewWidth - 1, startY + (i + 1) * y_step);

        if self.gridSize != self.maxGridSize:
            # draw Max grid
            p = self.mapToGrid(QPointF(startX - self.maxGridSize, startY - self.maxGridSize),
                           self.maxGridSize)
            startX = p.x()
            startY = p.y()
            x_step = self.maxGridSize
            y_step = self.maxGridSize
            x_cnt = int(viewWidth / x_step)
            y_cnt = int(viewHeight / y_step)
            qp.setPen(QPen(Qt.black, 1))
            for x in range(x_cnt - 1):
                for y in range(y_cnt - 1):
                    qp.drawPoint(startX + (x + 1) * x_step,
                                 startY + (y + 1) * y_step)

        # draw graphics region in all scene
        horizontalFieldSize = self.sceneRectSize.x() / self.horizontalFieldsCount
        verticalFieldSize = self.sceneRectSize.y() / self.verticalFieldsCount

        startX = -pix(self.horizontalFieldsHeight)
        startY = -pix(self.verticalFieldsWidth)

        qp.setPen(QPen(Qt.black, 1))
        qp.setFont(QFont("System", 10, QFont.Normal))

        qp.drawRect(startX, startY,
                    pix(self.horizontalFieldsHeight) + pix(self.sceneRectSize.x()),
                    pix(self.verticalFieldsWidth) + pix(self.sceneRectSize.y()))

        qp.setBrush(Qt.white)

        # draw top horizontal bar
        sx = startX + pix(self.verticalFieldsWidth)
        sy = startY

        for i in range(self.horizontalFieldsCount):
            rect = QRectF(sx + i * pix(horizontalFieldSize),
                          sy,
                          pix(horizontalFieldSize),
                          pix(self.horizontalFieldsHeight))
            qp.drawRect(rect)
            qp.drawText(rect, Qt.AlignCenter, "%d" % (i + 1))

        # draw top vertical bar
        sx = startX
        sy = startY + pix(self.verticalFieldsWidth)

        for i in range(self.verticalFieldsCount):
            rect = QRectF(sx,
                          sy + i * pix(verticalFieldSize),
                          pix(self.verticalFieldsWidth),
                          pix(verticalFieldSize))
            qp.drawRect(rect)
            qp.drawText(rect, Qt.AlignCenter, "%s" % letters[i])


    def mapToGrid(self, point, gridSize=None):
        if not gridSize:
            gridSize = self.gridSize
        s = gridSize
        x = round(point.x() / s) * s
        y = round(point.y() / s) * s
        return QPointF(x, y)


    def inGraphicPaper(self, point):
        if point.x() < 0 or point.y() < 0:
            return False
        if point.x() > self.bottomRight.x() or point.y() > self.bottomRight.y():
            return False
        return True


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
        if not self.inGraphicPaper(ev.scenePos()):
            return

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

                p = self.mapToGrid(ev.scenePos())
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

            if self.mode == 'moveSelectedItems':
                self.history.changeItemsFinish()
                self.resetSelectionItems()
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

            if self.mode == 'moveSelectedItems':
                self.history.changeItemsFinish()
                self.mode = 'select'
                self.history.undo()
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

        point = self.mapToGrid(ev.scenePos())
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

        p = self.mapToGrid(ev.scenePos())
        for item in self.graphicsItems():
            if item.isPointSelected():
                item.modifySelectedPoint(p)
        self.calculateSelectionCenter()
        return True


    def mousePressEventMoveItem(self, ev):
        item = self.graphicItemByCoordinate(ev.scenePos())
        if not item:
            return

        self.selectedCenter = self.mapToGrid(ev.scenePos())
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
            item.moveByCenter(self.mapToGrid(ev.scenePos()))
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
        if not self.inGraphicPaper(ev.scenePos()):
            return

        self.mousePos = ev.scenePos()

        p = self.mapToGrid(ev.scenePos())
        self.editor.setCursorCoordinates(p)

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
            self.drawCursor(p)

            if not self.drawingLine:
                return

            self.drawingLine.setP2(p)
            return

        if self.mode == 'pasteFromClipboard':
            self.moveSelectedItems(self.mapToGrid(ev.scenePos()))
            return

        if self.mode == 'moveSelectedItems':
            self.moveSelectedItems(self.mapToGrid(ev.scenePos()))
            return


    def mouseReleaseEvent(self, ev):
        if self.mode == 'pasteFromClipboard':
            return

        if self.mode == 'moveSelectedItems':
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

        if key == 87:  # W
            print(self.history)
            print(self)
            return

        if key == 83:  # S
            self.changeGridSize()

        if key == 68:  # D
            self.intersectionPointsShow()
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
            items = self.selectedGraphicsItems()
            self.history.removeItems(items)
            self.removeGraphicsItems(items)
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

        if key == 88:  # x (cut and move selected items)
            items = self.selectedGraphicsItems()
            self.history.changeItemsStart(items)
            for item in items:
                item.moveByCenter(self.mapToGrid(self.mousePos))

            self.setMode("moveSelectedItems")
            return

        if key == 16777235:  # UP
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setY(p.y() - self.gridSize)
            self.moveSelectedItemsByKeys(p)
            return

        if key == 16777237:  # DOWN
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setY(p.y() + self.gridSize)
            self.moveSelectedItemsByKeys(p)
            return

        if key == 16777234:  # LEFT
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setX(p.x() - self.gridSize)
            self.moveSelectedItemsByKeys(p)
            return

        if key == 16777236:  # RIGHT
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setX(p.x() + self.gridSize)
            self.moveSelectedItemsByKeys(p)
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

        QGraphicsScene.keyReleaseEvent(self, event)


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
            self.drawCursor(self.mapToGrid(self.mousePos))

        self.mode = mode


    def calculateSelectionCenter(self):
        poligon = QPolygonF()
        for item in self.selectedGraphicsItems():
            poligon += item.mapToScene(item.boundingRect())
        if not poligon:
            return

        rect = poligon.boundingRect()
        self.selectedCenter = self.mapToGrid(rect.center())


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
            item.moveByCenter(self.mapToGrid(self.mousePos))

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


    def graphicsUnpackedItems(self):
        list = []
        for item in self.items():
            if item.type() <= NOT_DEFINED_TYPE:
                continue
            if item.type() == GROUP_TYPE:
                continue
            list.append(item)
        return list


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


    def intersectionPointsShow(self):
        if self.interceptionPoints:
            for point in self.interceptionPoints:
                self.removeItem(point)

        items = self.graphicsUnpackedItems()
        if not len(items):
            return

        listPoints = {}
        for item in items:
            points = item.points()
            for itemP in points:
                pointStr = "%dx%d" % (itemP.x(), itemP.y())
                if pointStr in listPoints:
                    listPoints[pointStr]['cnt'] += 1
                else:
                    listPoints[pointStr] = {'cnt': 1, 'point': itemP, 'item': item}

        showPoints = []
        for point, data in listPoints.items():
            if data['cnt'] > 2:
                showPoints.append(data['point'])
                continue

            for item in self.graphicsUnpackedItems():
                if item == data['item']:
                    continue

                localPos = data['point'] - item.pos()
                if not item.contains(localPos):
                    continue

                busy = False
                for p in item.points():
                    if p == data['point']:
                        busy = True

                if busy:
                    continue

                showPoints.append(data['point'])

        for point in showPoints:
            pointEllipse = QGraphicsEllipseItem()
            pointEllipse.setBrush(Qt.black)
            pointEllipse.setPos(point - QPointF(4, 4))
            pointEllipse.setRect(QRectF(0, 0, 8, 8))
            self.addItem(pointEllipse)
            self.interceptionPoints.append(pointEllipse)


    def __str__(self):
        str = "\n--------------\n"
        str += "Scene contain:\n"
        for item in self.graphicsItems():
            str += "%s\n" % item
        return str

