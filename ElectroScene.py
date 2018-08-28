from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ElectroEditor import *
from History import *
# from gtk.keysyms import ordfeminine
import json
from GraphicsItem import *
from GraphicsItemLine import *
from GraphicsItemRect import *
from GraphicsItemGroup import *
from GraphicsItemLink import *
from GraphicsItemText import *






class ElectroScene(QGraphicsScene):


    def __init__(self, editor):
        QGraphicsScene.__init__(self)
        self._num = 0  # Scene number
        self.editor = editor
        self.graphicsItemsList = []
        self.drawingLine = None
        self.drawingRect = None
        self.drawingEllipse = None
        self.drawingText = None
        self.newTextItem = None  # temporary storage new textItem
        self.insertedLinkPoint = None
        self.selectingByMouse = None  # select rectangular area for selecting items
        self.movingItem = False  # Moving selected items mode
        self.movedPointItems = []  # List of Moving point items
        self.mode = 'select'
        self._currentTool = None
        self.selectedCenter = QPointF(0, 0)
        self.keyCTRL = False
        self.keyShift = False
        self.mousePos = QPointF(0, 0)
        self.mouseGridPos = QPointF(0, 0)
        self.drawLinesHistory = []  # temporary array of drawed lines between mouse left and right clicks
        self.minGridSize = MAX_GRID_SIZE / 4
        self.gridSize = self.minGridSize
        self.history = History(self)

        self.cursorX = QGraphicsLineItem(None)
        self.cursorY = QGraphicsLineItem(None)
        self.addItem(self.cursorX)
        self.addItem(self.cursorY)
        self.cursorX.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        self.cursorY.setPen(QPen(Qt.blue, 1, Qt.SolidLine))

        self.interceptionPoints = []

        self.horizontalFieldsCount = 20
        self.verticalFieldsCount = 10

        self.horizontalFieldsHeight = 4  # in minGridSize
        self.verticalFieldsWidth = 4  # in minGridSize

        self.sceneRectSize = QPointF(400, 200)  # in minGridSize

        self.setGrid(MAX_GRID_SIZE)



        # configure graphic paper
        def pix(val):
            return val * self.minGridSize


        self.setSceneRect(-pix(self.horizontalFieldsHeight + 1),
                          - pix(self.verticalFieldsWidth + 1),
                          pix(self.sceneRectSize.x()),
                          pix(self.sceneRectSize.y()))
        self.bottomRight = QPointF(pix(self.sceneRectSize.x()),
                                   pix(self.sceneRectSize.y()))



    def setNum(self, num):
        self._num = num


    def num(self):
        return self._num


    def setGrid(self, gridSize):
        self.gridSize = gridSize
        self.editor.setStatusGridSize(gridSize)
        self.update()


    def changeGridSize(self):
        gridSize = self.gridSize
        gridSize = gridSize / 2
        if gridSize < self.minGridSize:
            gridSize = MAX_GRID_SIZE
        self.setGrid(gridSize)


    def quadrantByPos(self, pos):
        h = (self.sceneRectSize.x() / self.horizontalFieldsCount) * self.minGridSize
        v = (self.sceneRectSize.y() / self.verticalFieldsCount) * self.minGridSize
        x = int(pos.x() / h) + 1
        y = int(pos.y() / v)
        return "%s%d" % (chr(65 + y), x)


    def drawBackground(self, qp, viewRect):
#        print("drawBackground scene")
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

        qp.setPen(QPen(QColor(245, 245, 245), 1))

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

        if self.gridSize != MAX_GRID_SIZE:
            # draw Max grid
            p = self.mapToGrid(QPointF(startX - MAX_GRID_SIZE, startY - MAX_GRID_SIZE),
                           MAX_GRID_SIZE)
            startX = p.x()
            startY = p.y()
            x_step = MAX_GRID_SIZE
            y_step = MAX_GRID_SIZE
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
            qp.drawText(rect, Qt.AlignCenter, "%s" % chr(65 + i))


    def mapToGrid(self, arg, gridSize=None):
        if not gridSize:
            gridSize = self.gridSize
        return mapToGrid(arg, gridSize)


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
        self.selectingByMouse = MouseSelectionDrawing(self, ev.scenePos())


    def mouseMoveEventMoveRectSelection(self, ev):
        if not self.selectingByMouse:
            return False
        return self.selectingByMouse.setEndPoint(ev.scenePos())


    def mousePressEventSelectItem(self, ev):
        item = self.graphicItemByCoordinate(ev.scenePos())
        if not item:
            if not self.keyShift:
                self.resetSelectionItems()
            return

        if not item.isSelected() and len(self.selectedGraphicsItems()) and not self.keyShift:
            self.resetSelectionItems()

        if self.keyShift:
            if not item.isSelected():
                self.itemAddToSelection(item)
            else:
                self.itemRemoveFromSelection(item)
            return

        self.itemAddToSelection(item)
        return True


    def mousePressLeftButtonModeUseTool(self, ev):
        p = self.mapToGrid(ev.scenePos())

        if (self.currentTool() == 'traceLine' or
                self.currentTool() == 'line'):
            lineType = 'line'
            if self.currentTool() == 'traceLine':
                lineType = 'trace'

            if self.drawingLine:
                self.drawLinesHistory.append(self.drawingLine)

            # stop drawing if line on component
            if self.drawingLine and lineType == 'trace':
                for item in self.allGraphicsItems():
                    if item == self.drawingLine:
                        continue
                    if item.setSelectPoint(p):
                        self.drawingLine = GraphicsItemLine(lineType)
                        self.drawingLine.assignNewId()
                        self.addGraphicsItem(self.drawingLine)
                        self.stopLineDrawing()
                        return


            self.drawingLine = GraphicsItemLine(lineType)
            self.drawingLine.assignNewId()
            self.drawingLine.setP1(p)
            self.addGraphicsItem(self.drawingLine)
            QGraphicsScene.mousePressEvent(self, ev)
            return

        if self.currentTool() == 'rectangle':
            self.drawingRect = RectDrawing(self, QPen(Qt.black, 2, Qt.SolidLine), p)
            return

        if self.currentTool() == 'ellipse':
            self.drawingEllipse = RectDrawing(self, QPen(Qt.black, 2, Qt.SolidLine),
                                              p, "ellipse")
            return

        if self.currentTool() == 'text':
            self.drawingText = RectDrawing(self, QPen(Qt.black, 2, Qt.SolidLine),
                                           p, "rectangle")
            return




    def mousePressEvent(self, ev):
        if not self.inGraphicPaper(ev.scenePos()):
            return

        if ev.button() == 1:
            if self.mode == 'select' or self.mode == 'textEdit':
                QGraphicsScene.mousePressEvent(self, ev)
                if self.mousePressEventMovePoint(ev):
                    return

                self.mousePressEventSelectItem(ev)
                self.mousePressEventMoveItem(ev)

                if self.mousePressEventStartRectSelection(ev):
                    return
                return

            if self.mode == 'useTool':
                self.mousePressLeftButtonModeUseTool(ev)
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

            if self.mode == 'pastLinkPoint':
                self.itemRemoveFromSelection(self.insertedLinkPoint)
                self.history.addItems([self.insertedLinkPoint])
                self.setMode('pastLinkPoint')


        if ev.button() == 2:
            if self.mode == 'select':
                self.resetSelectionItems()
                return

            if self.mode == 'useTool':
                if (self.currentTool() == 'traceLine' or
                        self.currentTool() == 'line'):

                    if self.drawingLine:
                        self.stopLineDrawing()
                    else:
                        self.editor.setTool(None)
                    return

                if (self.currentTool() == 'rectangle' or
                    self.currentTool() == 'ellipse' or
                    self.currentTool() == 'text'):
                    self.editor.setTool(None)
                    return

            if self.mode == 'pasteFromClipboard':
                self.setMode('select')
                return

            if self.mode == 'moveSelectedItems':
                self.history.changeItemsFinish()
                self.mode = 'select'
                self.history.undo()
                return

            if self.mode == 'pastLinkPoint':
                self.setMode('select')
                return

        QGraphicsScene.mousePressEvent(self, ev)



    def mouseDoubleClickEvent(self, ev):
        if ev.button() == 1:
            if self.mode == 'select':
                print("double")
                item = self.graphicItemByCoordinate(ev.scenePos())
                if not item:
                    return
                print(item.typeName())

                if item.type() == GROUP_TYPE:
                    if self.keyShift:
                        parentGroup = item.parentComponentGroup()
                        if parentGroup:
                            self.resetSelectionItems()
                            self.itemAddToSelection(parentGroup)
                            self.editor.displayItem(parentGroup)
                            return
                        self.editor.showSwitchToSubComponent(item)
                        return

                    self.editor.showEditGroupIndexName(item)
                    return

                if item.type() == LINK_TYPE:
                    print("LINK_TYPE")
                    self.editor.displayRemoteLinkPoint(item)
                    return

                if item.type() == TEXT_TYPE and not self.keyShift:
                    item.editEnable()
                    item.setFocus()
                    return

                # change fill color by Shift + Double click
                if ((item.type() == RECT_TYPE or
                    item.type() == ELLIPSE_TYPE) and
                     self.keyCTRL):
                    newColor = self.editor.dialogColorSelect(item.fillColor(), True)
                    if not newColor.isValid():
                        return

                    if (newColor.red() == 255 and
                        newColor.green() == 255 and
                        newColor.blue() == 255):
                        newColor = None

                    selectedItems = self.selectedGraphicsItems()
                    selectedItems.append(item)
                    neededItems = []
                    for selectedItem in selectedItems:
                        if (selectedItem.type() == RECT_TYPE or
                            selectedItem.type() == ELLIPSE_TYPE):
                            neededItems.append(selectedItem)
                    self.history.changeItemsStart(neededItems)
                    for neededItem in neededItems:
                        neededItem.setFillColor(newColor)
                    self.history.changeItemsFinish()
                    return

                # change color by Double click
                if (item.type() != GROUP_TYPE and
                    item.type() != LINK_TYPE):
                    if item.type() == LINE_TYPE and item.typeLine() == 'trace':
                        return
                    newColor = self.editor.dialogColorSelect(item.color())
                    if not newColor.isValid():
                        return
                    selectedItems = self.selectedGraphicsItems()
                    selectedItems.append(item)
                    self.history.changeItemsStart(selectedItems)
                    for selectedItem in selectedItems:
                        selectedItem.setColor(newColor)
                    self.history.changeItemsFinish()
                    self.resetSelectionItems()
                    return

                # change color by Shift + Double click for Text
                if (item.type() == TEXT_TYPE and self.keyShift):
                    newColor = self.editor.dialogColorSelect(item.color())
                    if not newColor.isValid():
                        return
                    selectedItems = self.selectedGraphicsItems()
                    selectedItems.append(item)
                    self.history.changeItemsStart(selectedItems)
                    for selectedItem in selectedItems:
                        selectedItem.setColor(newColor)
                    self.history.changeItemsFinish()
                    self.resetSelectionItems()
                    return



    def stopLineDrawing(self):
        if not self.drawingLine:
            return

        self.removeGraphicsItem(self.drawingLine)
        self.drawingLine = None
        correctLines = []
        for line in self.drawLinesHistory:
            if line.isNullSize():
                self.removeGraphicsItem(line)
                continue
            correctLines.append(line)
        self.history.addItems(correctLines)
        self.drawLinesHistory = []


    def mousePressEventMovePoint(self, ev):
        if not len(self.graphicsItems()):
            return False

        for item in self.movedPointItems:
            item.resetSelectionPoint()
        self.movedPointItems = []

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
        self.history.changeItemsStart(self.selectedGraphicsItems())
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


    def mouseMoveEventDisplayPoints(self, pos):
        items = self.graphicsItems()
        if not len(items):
            return

        self.editor.setStatusGraphicsItemInfo(None)
        self.editor.showGroupInfo(None)
        for item in items:
            item.unHighlight()
            if item.type() == GROUP_TYPE:
                subItems = self.subComponentGroups(item)
                for subItem in subItems:
                    subItem.unHighlight()

            if not item.isSelected():
                item.markPointsHide()

        item = self.graphicItemByCoordinate(pos)
        if not item:
            return
        item.markPointsShow()
        item.highlight()
        if item.type() == GROUP_TYPE:
            subItems = self.subComponentGroups(item)
            for subItem in subItems:
                subItem.highlight()
        if item.type() == LINK_TYPE:
            remoteItem = item.remoteLinkPoint()
            if remoteItem:
                remoteItem.highlight()
        self.editor.setStatusGraphicsItemInfo(item)
        self.editor.showGroupInfo(item)


    def mouseMoveEventModeUseTool(self, point):
        self.drawCursor(point)
        if (self.currentTool() == 'traceLine' or
                self.currentTool() == 'line'):

            if not self.drawingLine:
                return

            self.drawingLine.setP2(point)

        if self.currentTool() == 'rectangle':
            if not self.drawingRect:
                return
            self.drawingRect.setEndPoint(point)

        if self.currentTool() == 'ellipse':
            if not self.drawingEllipse:
                return
            self.drawingEllipse.setEndPoint(point)

        if self.currentTool() == 'text':
            if not self.drawingText:
                return
            self.drawingText.setEndPoint(point)


    def isPosInHysteresMargin(self, currentPos, currentGridPos):
        delta = self.gridSize / 100 * 75
        if abs(currentGridPos.x() - currentPos.x()) > delta:
            return False
        if abs(currentGridPos.y() - currentPos.y()) > delta:
            return False
        return True


    def mouseMoveEvent(self, ev):
        if not self.inGraphicPaper(ev.scenePos()):
            return

        self.mousePos = ev.scenePos()
        hysteresMoveFlag = not self.isPosInHysteresMargin(self.mousePos, self.mouseGridPos)

        point = self.mapToGrid(ev.scenePos())
        if hysteresMoveFlag:
            self.mouseGridPos = point

        self.editor.setStatusCursorCoordinates(point)

        if self.mode == 'select' or self.mode == 'textEdit':
            self.mouseMoveEventDisplayPoints(self.mousePos)

            if hysteresMoveFlag and self.mouseMoveEventMoveItem(ev):
                return
            if hysteresMoveFlag and self.mouseMoveEventMovePoint(ev):
                return
            if self.mouseMoveEventMoveRectSelection(ev):
                return

            QGraphicsScene.mouseMoveEvent(self, ev)
            return

        if self.mode == 'useTool':
            self.mouseMoveEventModeUseTool(point)
            return

        if self.mode == 'pasteFromClipboard':
            if hysteresMoveFlag:
                self.moveSelectedItems(point)
                self.calculateSelectionCenter()
            return

        if self.mode == 'moveSelectedItems':
            if hysteresMoveFlag:
                self.moveSelectedItems(point)
            return

        if self.mode == 'pastLinkPoint':
            if hysteresMoveFlag:
                self.moveSelectedItems(self.mapToGrid(ev.scenePos(), MAX_GRID_SIZE))
                self.calculateSelectionCenter()
            return



    def mouseReleaseEvent(self, ev):
        self.update()
        if self.mode == 'pasteFromClipboard':
            return

        if self.mode == 'moveSelectedItems':
            return

        if self.mode == 'useTool':
            if self.drawingRect:
                rect = self.drawingRect.rect()
                if not rect:
                    self.drawingRect = None
                    return
                rectangle = GraphicsItemRect(self.drawingRect.rect())
                rectangle.assignNewId()
                if rectangle.isNullSize():
                    return
                self.drawingRect.remove()
                self.addGraphicsItem(rectangle)
                self.history.addItems([rectangle])
                self.drawingRect = None

            if self.drawingEllipse:
                rect = self.drawingEllipse.rect()
                if not rect:
                    self.drawingEllipse = None
                    return
                ellipse = GraphicsItemEllipse(self.drawingEllipse.rect())
                ellipse.assignNewId()
                if ellipse.isNullSize():
                    return
                self.drawingEllipse.remove()
                self.addGraphicsItem(ellipse)
                self.history.addItems([ellipse])
                self.drawingEllipse = None

            if self.drawingText:
                print("mouseReleaseEvent drawingText")
                rect = self.drawingText.rect()
                if not rect:
                    self.drawingText = None
                    return
                text = GraphicsItemText(rect.topLeft(),
                                        QRectF(0, 0, rect.width(), rect.height()))
                text.assignNewId()
                if text.isNullSize():
                    return
                self.drawingText.remove()
                self.addGraphicsItem(text)
                self.newTextItem = text
                self.drawingText = None
                text.editEnable()
                text.setFocus()
                self.setMode('textEdit')
            return

        self.calculateSelectionCenter()

        if self.selectingByMouse:
            self.selectingByMouse.remove()
            self.selectingByMouse = None


        if len(self.movedPointItems):
            self.history.changeItemsFinish()
            for item in self.movedPointItems:
                item.resetSelectionPoint()
            self.movedPointItems = []

        if self.movingItem:
            print("moving finished")
            self.history.changeItemsFinish()
            self.movingItem = False
            self.editor.updateAllComponentsView()

        self.selectingByMouse = None
        QGraphicsScene.mouseReleaseEvent(self, ev)


    def graphicItemByCoordinate(self, point):
        item = self.itemAt(point, self.views()[0].transform())
        if not item or not self.isGraphicsItem(item):
            return False
        return item.root()


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
        if self.mode == 'textEdit':
            QGraphicsScene.keyPressEvent(self, event)
            return

        if key == 16777223:  # DEL
            items = self.selectedGraphicsItems()
            self.history.removeItems(items)
            self.removeGraphicsItems(items)
            self.update()
            return

        if not self.keyCTRL and not self.keyShift:
            # display scene items info
            if key == 80:  # P
                print(self.history)
                print(self)
                return

            # change grid size
            if key == 83:  # S
                self.changeGridSize()
                return

            # change selected lines type
            if key == 84:  # T
                if self.mode == 'useTool':
                    self.changeDrawingLinesType()
                if self.mode == 'select':
                    self.changeSelectedLinesType()
                return

            # cut and move selected items
            if key == 88:  # x
                items = self.selectedGraphicsItems()
                self.history.changeItemsStart(items)
                for item in items:
                    item.moveByCenter(self.mapToGrid(self.mousePos))

                self.setMode("moveSelectedItems")
                return

            # increase zIndex
            if key == 43:  # +
                items = self.selectedGraphicsItems()
                self.history.changeItemsStart(items)
                for item in items:
                    item.increaseZIndex()
                self.history.changeItemsFinish()
                self.mouseMoveEventDisplayPoints(self.mousePos)
                return

            # decrease zIndex
            if key == 45:  # -
                items = self.selectedGraphicsItems()
                self.history.changeItemsStart(items)
                for item in items:
                    item.decreaseZIndex()
                self.history.changeItemsFinish()
                self.mouseMoveEventDisplayPoints(self.mousePos)
                return

        # increase penStyle
        if not self.keyShift and key == 81:  # Q
            items = self.selectedGraphicsItems()
            if not len(items):
                return
            self.history.changeItemsStart(items)
            for item in items:
                 item.increasePenStyle()
            self.history.changeItemsFinish()
            return

        # decrease penStyle
        if self.keyShift and key == 81:  # Shift + Q
            items = self.selectedGraphicsItems()
            if not len(items):
                return
            self.history.changeItemsStart(items)
            for item in items:
                 item.decreasePenStyle()
            self.history.changeItemsFinish()
            return

        # increase thickness
        if not self.keyShift and key == 87:  # W
            items = self.selectedGraphicsItems()
            if not len(items):
                return
            self.history.changeItemsStart(items)
            for item in items:
                 item.increaseThickness()
            self.history.changeItemsFinish()
            return

        # decrease thickness
        if self.keyShift and key == 87:  # Shift + W
            items = self.selectedGraphicsItems()
            if not len(items):
                return
            self.history.changeItemsStart(items)
            for item in items:
                 item.decreaseThickness()
            self.history.changeItemsFinish()
            return

        # undo last inserted line point while drawing line mode
        if key == 16777219:  # Backspace
            if self.mode == 'useTool' and (
                self.currentTool() == 'traceLine' or
                self.currentTool() == 'line'):
                if not len(self.drawLinesHistory):
                    return

                self.removeGraphicsItem(self.drawingLine)
                self.drawingLine = self.drawLinesHistory.pop()
                self.drawingLine.setP2(self.mousePos)
                return

        # rotate selected items
        if key == 32:  # Space
            if self.mode != 'pasteFromClipboard':
                self.history.changeItemsStart(self.selectedGraphicsItems())

            self.rotateSelectedItems(90)

            if self.mode != 'pasteFromClipboard':
                self.history.changeItemsFinish()
            return

        # select all items
        if self.keyCTRL and key == 65:  # CTLR + A
            for item in self.graphicsItems():
                self.itemAddToSelection(item)

        # undo
        if self.keyCTRL and key == 90:  # CTLR + Z
            self.history.undo()
            return

        # redo
        if self.keyCTRL and key == 89:  # CTLR + Y
            self.history.redo()
            return

        # copy selected items
        if self.keyCTRL and key == 67:  # CTLR + C
            self.copySelectedToClipboard()
            return

        # copy and remove selected items
        if self.keyCTRL and key == 88:  # CTLR + X
            self.copySelectedToClipboard()
            items = self.selectedGraphicsItems()
            self.history.removeItems(items)
            self.removeGraphicsItems(items)
            return

        # paste items from clipboard
        if self.keyCTRL and key == 86:  # CTLR + V
            self.pastFromClipboard()
            return

        # pack selected item into group
        if not self.keyShift and key == 71:  # G
            print("G")
            self.packSelectedIntoGroup()
            return

        # unpack selected item from group
        if self.keyShift and key == 71:  # Shift+G
            print("Shift+G")
            self.unpackSelectedGroups()
            return

        # move up selected items
        if key == 16777235:  # UP
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setY(p.y() - self.gridSize)
            self.moveSelectedItemsByKeys(p)
            self.editor.updateAllComponentsView()
            return

        # move down selected items
        if key == 16777237:  # DOWN
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setY(p.y() + self.gridSize)
            self.moveSelectedItemsByKeys(p)
            self.editor.updateAllComponentsView()
            return

        # move left selected items
        if key == 16777234:  # LEFT
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setX(p.x() - self.gridSize)
            self.moveSelectedItemsByKeys(p)
            self.editor.updateAllComponentsView()
            return

        # move right selected items
        if key == 16777236:  # RIGHT
            if not len(self.graphicsItems()):
                return
            self.calculateSelectionCenter()
            p = self.selectedCenter
            p.setX(p.x() + self.gridSize)
            self.moveSelectedItemsByKeys(p)
            self.editor.updateAllComponentsView()
            return

        QGraphicsScene.keyPressEvent(self, event)


    def keyReleaseEvent(self, event):
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


    def selectedGraphicsItems(self, type=None):
        items = []
        for item in self.graphicsItems(type):
            if not item.isSelected():
                continue
            items.append(item)
        return items


    def itemById(self, id):
        for item in self.graphicsItems():
            if item.id() == id:
                return item
        return None


    def setTool(self, tool):
        self._currentTool = tool
        self.editor.setEditorTool(tool)
        if not tool:
            self.setMode("select")
            return
        self.setMode("useTool")


    def currentTool(self):
        return self._currentTool


    def setMode(self, mode):
        if self.mode == 'pasteFromClipboard':
            self.removeGraphicsItems(self.selectedGraphicsItems())

        if mode == "select":
            self.hideCursor()
            self.resetSelectionItems()
            self.stopLineDrawing()
            if self.mode == 'pastLinkPoint':
                self.removeGraphicsItem(self.insertedLinkPoint)
                self.insertedLinkPoint = None

        if mode == "useTool":
            self.drawCursor(self.mapToGrid(self.mousePos))

        if mode == "pastLinkPoint":
            pos = self.mapToGrid(self.mousePos, MAX_GRID_SIZE)
            item = GraphicsItemLink(pos)
            item.assignNewId()
            item.setCenter(pos)
            self.resetSelectionItems()
            self.addGraphicsItem(item)
            self.itemAddToSelection(item, True)
            self.calculateSelectionCenter()
            self.insertedLinkPoint = item

        if mode == "textEdit":
            if self.mode != 'select':
                self.hideCursor()

        self.mode = mode


    def selectedItemsBoundingRect(self):
        poligon = QPolygonF()
        for item in self.selectedGraphicsItems():
            rect = item.boundingRect()
            poligon += item.mapToScene(rect)
        if not poligon:
            return
        return poligon.boundingRect()


    def calculateSelectionCenter(self):
        rect = self.selectedItemsBoundingRect()
        if not rect:
            return
        self.selectedCenter = self.mapToGrid(rect.center())
        for item in self.selectedGraphicsItems():
            item.setCenter(self.selectedCenter)


    def itemAddToSelection(self, item, fast=False):
        item.select()
        item.markPointsShow()
        if not fast:
            self.calculateSelectionCenter()


    def itemsAddToSelection(self, items):
        for item in items:
            self.itemAddToSelection(item)


    def itemRemoveFromSelection(self, item):
        item.resetSelection(True)
        item.markPointsHide()
        item.unHighlight()
        return


    def copySelectedToClipboard(self):
        items = self.selectedGraphicsItems()
        if not len(items):
            return
        ItemsProperties = []
        for item in items:
            ItemsProperties.append(item.properties())
        jsonText = json.dumps(ItemsProperties, indent=2, sort_keys=True, ensure_ascii=False)
        self.editor.toClipboard(jsonText)


    def pastFromClipboard(self):
        jsonText = self.editor.fromClipboard()
        print("pastFromClipboard")
        items = self.editor.graphicsObjectFromJson(jsonText)
        if not len(items):
            print("no data")
            return False

        self.resetSelectionItems()

        # reset old group indexes
        allGroups = self.unpackAllItems(items, GROUP_TYPE)
        for group in allGroups:
            group.setIndex(0)

        # add items to scene
        for item in items:
            self.addGraphicsItem(item)
            self.itemAddToSelection(item)

        for item in items:
            item.moveByCenter(self.mapToGrid(self.mousePos))

        # set index for all groups and subgroups
        for group in allGroups:
            self.editor.setUniqueComponentIndex(group)

        self.setMode("pasteFromClipboard")
        return True


    def pastComponent(self, group):
        # reset all subgroups indexes
        allGroups = self.unpackAllItems([group], GROUP_TYPE)
        for g in allGroups:
            if not g.prefixName():
                continue
            g.setIndex(0)

        self.abortPastComponent()
        self.resetSelectionItems()
        self.addGraphicsItem(group)
        self.itemAddToSelection(group)
        group.moveByCenter(self.mapToGrid(self.mousePos))

        # set all subgroup indexes
        allGroups = self.unpackAllItems([group], GROUP_TYPE)
        for g in allGroups:
            if not g.prefixName():
                continue
            self.editor.setUniqueComponentIndex(g)

        self.setMode("pasteFromClipboard")


    def abortPastComponent(self):
        if self.mode == 'pasteFromClipboard':
            self.removeGraphicsItems(self.selectedGraphicsItems())
            self.setMode('select')


    def rotateSelectedItems(self, angle):
        for item in self.selectedGraphicsItems():
            item.setCenter(self.selectedCenter)
            item.rotate(self.selectedCenter, angle)
            item.setCenter(self.selectedCenter)


    def graphicsItems(self, type=None):
        if not type:
            return self.graphicsItemsList
        items = []
        for item in self.graphicsItemsList:
            if item.type() == type:
                items.append(item)
        return items


    def unpackAllItems(self, items, type):
        itemsList = []
        def addItems(items):
            for item in items:
                if (item.type() == GROUP_TYPE or
                    item.type() == LINK_TYPE):
                    addItems(item.items())

                if type and item.type() != type:
                    continue
                itemsList.append(item)

        addItems(items)
        return itemsList


    def allGraphicsItems(self, type=None):
        return self.unpackAllItems(self.graphicsItems(), type)


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


    def packSelectedIntoGroup(self, name=None):
        if len(self.selectedGraphicsItems()) < 2:
            return None
        group = self.packItemsIntoGroup(self.selectedGraphicsItems(), name)
        self.history.packGroup(group)
        self.itemAddToSelection(group)
        return group


    def packItemsIntoGroup(self, items, name=None):
        cleanItems = []
        for item in items:
            if item.type() != LINK_TYPE:
                cleanItems.append(item)

        if len(cleanItems) < 2:
            return None
        if not name:
            name = "undefined"

        group = GraphicsItemGroup()
        group.assignNewId()
        group.setName(name)
        self.resetSelectionItems()

        # remove items from scene
        for item in cleanItems:
            self.graphicsItemsList.remove(item)
            item.removeFromQScene()
        group.addItems(cleanItems)
        self.addGraphicsItem(group)
        return group


    def unpackGroup(self, group):
        if group.type() != GROUP_TYPE:
            return
        group.markPointsHide()
        items = group.items()

        self.removeGraphicsItem(group)
        for item in items:
            pos = item.pos()
            item.assignNewId()
            item.setParent(None)
            if item.type() == GROUP_TYPE and item.prefixName():
                self.editor.setUniqueComponentIndex(item)
            self.addGraphicsItem(item)
            item.setPos(pos)

        return items


    def unpackSelectedGroups(self):
        for item in self.selectedGraphicsItems():
            if item.type() == GROUP_TYPE:
                self.history.unpackGroup(item)
                unpackedItems = self.unpackGroup(item)
                self.itemsAddToSelection(unpackedItems)


    def removeGraphicsItem(self, item):
        print("removeGraphicsItem %d" % item.id())
        if item in self.graphicsItemsList:
            self.graphicsItemsList.remove(item)
        if item.type() == GROUP_TYPE:
            subComponents = self.editor.subComponentGroups(item)
            for subComponent in subComponents:
                subComponent.setParentComponentGroup(None)
                self.editor.setUniqueComponentIndex(subComponent)
                self.editor.updateSubComponentsView(subComponent)
        item.removeFromQScene()
        item.remove()


    def removeGraphicsItems(self, items):
        copyItems = []
        for item in items:
            copyItems.append(item)
        for item in copyItems:
            self.removeGraphicsItem(item)


    def itemTextfocusInEvent(self, item):
        self.setMode('textEdit')
        if item == self.newTextItem:
            return
        self.history.changeItemsStart([item])


    def itemTextfocusOutEvent(self, item):
        item.editDisable()
        self.setMode('select')
        newTextItem = self.newTextItem
        self.newTextItem = None
        if item == newTextItem:
            if not len(item.text()):
                self.removeGraphicsItem(item)
                return
            self.history.addItems([item])
            return

        actions = self.history.changeItemsFinish()
        if not len(item.text()):
            self.history.removeItems([item], actions)
            self.removeGraphicsItem(item)


    def grabSceneAsImage(self, imageRect):
        self.resetSelectionItems()
        sceneRect = self.sceneRect()
        image = QImage(imageRect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QPainter(image)
        self.render(painter, source=imageRect)
        painter.end()
        return image


    def changeDrawingLinesType(self):
        if not self.drawingLine:
            return

        lines = self.drawLinesHistory
        lines.append(self.drawingLine)

        if self.currentTool() == 'traceLine':
            self.setTool('line')
            lineType = 'line'
        else:
            self.setTool('traceLine')
            lineType = 'trace'

        for line in lines:
            line.setTypeLine(lineType)


    def changeSelectedLinesType(self):
        items = self.selectedGraphicsItems()
        self.resetSelectionItems()
        for item in items:
            if item.type() != LINE_TYPE:
                continue

            line = item
            if line.typeLine() == 'trace':
                line.setTypeLine('line')
            else:
                line.setTypeLine('trace')
        self.update()


    def update(self):
        QGraphicsScene.update(self)
        self.intersectionPointsShow()


    def intersectionPointsShow(self):
        if self.interceptionPoints:
            for point in self.interceptionPoints:
                if point.scene():
                    self.removeItem(point)

#        items = self.graphicsUnpackedItems()
        items = self.graphicsItems()
        if not len(items):
            return

        # accumulate lines tip intersection
        listPoints = {}
        for item in items:
            if item.type() != LINE_TYPE:
                continue

            traceLine = False
            if item.typeLine() == 'trace':
                traceLine = True

            points = item.points()
            for itemP in points:
                pointStr = "%dx%d" % (itemP.x(), itemP.y())
                if pointStr in listPoints:
                    listPoints[pointStr]['cnt'] += 1
                else:
                    listPoints[pointStr] = {'cnt': 1,
                                            'point': itemP,
                                            'item': item,
                                            'tracePoint': False}
                if traceLine:
                    listPoints[pointStr]['tracePoint'] = True

        # accumulate line to tip intersection
        showPoints = []
        for point, data in listPoints.items():
            if data['cnt'] > 2 and data['tracePoint']:
                showPoints.append(data['point'])
                continue

            for item in self.graphicsUnpackedItems():
                if item.type() != LINE_TYPE:
                    continue

                if item.typeLine() != 'trace':
                    continue

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
            pointEllipse.setPos(point - QPointF(3, 3))
            pointEllipse.setRect(QRectF(0, 0, 6, 6))
            self.addItem(pointEllipse)
            self.interceptionPoints.append(pointEllipse)


    def subComponentGroups(self, parentGroup):
        subComponents = []
        groups = self.allGraphicsItems(GROUP_TYPE)
        for group in groups:
            pGroup = group.parentComponentGroup()
            if not pGroup:
                continue
            if pGroup != parentGroup:
                continue
            subComponents.append(group)
        return subComponents


    def __str__(self):
        str = "\n--------------\n"
        str += "Scene contain:\n"
        for item in self.graphicsItems():
            str += "%s\n" % item
        return str




class RectDrawing():
    def __init__(self, scene, pen, startPoint, type="rectangle"):
        self._startPoint = startPoint
        self._scene = scene
        self._pen = pen
        self._rectGraphics = None
        self._type = type


    def setEndPoint(self, endPoint):
        self.remove()

        rect = None
        x1 = self._startPoint.x()
        y1 = self._startPoint.y()
        x2 = endPoint.x()
        y2 = endPoint.y()

        topLeft = None
        bottomRight = None
        if x1 < x2 and y1 < y2:
            topLeft = self._startPoint
            bottomRight = endPoint
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
            if self._type == "rectangle":
                self._rectGraphics = QGraphicsRectItem(None)
                self._scene.addItem(self._rectGraphics)
            elif self._type == "ellipse":
                self._rectGraphics = QGraphicsEllipseItem(None)
                self._scene.addItem(self._rectGraphics)
            else:
                return None

            self._rectGraphics.setPen(self._pen)
            rect = QRectF(topLeft, bottomRight)
            self._rectGraphics.setRect(rect)
        return rect


    def remove(self):
        if self._rectGraphics and self._rectGraphics.scene():
            self._scene.removeItem(self._rectGraphics)
        pass


    def rect(self):
        if not self._rectGraphics:
            return None
        rect = self._rectGraphics.rect()
        if not rect.width() or not rect.height():
            return None
        return rect




class MouseSelectionDrawing(RectDrawing):
    def __init__(self, scene, startPoint):
        RectDrawing.__init__(self, scene, QPen(Qt.black, 1, Qt.DashLine), startPoint)
        self._selectedItems = scene.selectedGraphicsItems()


    def setEndPoint(self, endPoint):
        rect = RectDrawing.setEndPoint(self, endPoint)
        if not rect:
            return False

        # unSelect all besides selected early
        for item in self._scene.graphicsItems():
            selected = False
            for selItem in self._selectedItems:
                if item == selItem:
                    selected = True
            if selected:
                continue
            self._scene.itemRemoveFromSelection(item)

        # Select all items in rectangle
        items = self._scene.items(rect)
        for item in items:
            if not self._scene.isGraphicsItem(item) or item == self._rectGraphics:
                continue
            item = item.root()
            self._scene.itemAddToSelection(item, True)
        return True




