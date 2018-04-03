from ElectroScene import *
from ElectroSceneView import *
from PyQt4.Qt import QWidget, QMainWindow, QLabel, QPoint
import os, glob, sys, pprint



last_page_id = 0

def editorPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def componentsPath():
    return "%s/components" % editorPath()


class PageWidget(QWidget):


    def __init__(self, editor, name):
        global last_page_id
        QWidget.__init__(self)
        self._name = name
        self._sceneView = ElectroSceneView(editor, ElectroScene(editor))
        layout = QVBoxLayout(self)
        layout.addWidget(self._sceneView)
        self.editor = editor
        self.setLayout(layout)
        last_page_id += 1
        self.pageId = last_page_id


    def id(self):
        return self.pageId


    def name(self):
        return self._name


    def setName(self, name):
        self._name = name


    def scene(self):
        return self._sceneView.scene()


    def sceneView(self):
        return self._sceneView


class Component(QListWidgetItem):
    def __init__(self, name, group=None):
        QListWidgetItem.__init__(self)
        self._name = name
        self._groupProperties = None
        self._image = None
        if group:
            self._groupProperties = group.properties()
        pass


    def load(self):
        f = open("%s/%s.ec" % (componentsPath(), self._name), "r")
        content = f.read()
        self._groupProperties = json.loads(content)

        f.close()

        self._image = QImage()
        self._image.load("%s/%s.png" % (componentsPath(), self._name))

        pixMap = QPixmap.fromImage(self.image())
        self.setData(Qt.DecorationRole, pixMap)
        return True


    def save(self):
        group = self.group()
        rect = mapToGrid(group.boundingRect(), MAX_GRID_SIZE)
        tempScene = QGraphicsScene()
        tempScene.setSceneRect(rect)
        group.setPos(rect.topLeft())
        group.setScene(tempScene)

        self._image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        self._image.fill(Qt.transparent)
        painter = QPainter(self._image)
        tempScene.render(painter)
        painter.end()

        self._image = self._image.scaledToWidth(100, Qt.SmoothTransformation)
        self._image.save("%s/%s.png" % (componentsPath(), self._name))

        jsonProp = json.dumps(self._groupProperties)
        f = open("%s/%s.ec" % (componentsPath(), self._name), "w")
        f.write(jsonProp)
        f.close()
        pass


    def removeFiles(self):
        os.remove("%s/%s.ec" % (componentsPath(), self._name))
        os.remove("%s/%s.png" % (componentsPath(), self._name))


    def group(self):
        if not self._groupProperties:
            return False
        group = createGraphicsObjectByProperties(self._groupProperties)

        return group

    def image(self):
        return self._image


    def mousePressEvent(self, ev):
        print("bla")




class ElectroEditor(QMainWindow):


    def __init__(self, app):
        QMainWindow.__init__(self)
        self.app = app
        self.keyCTRL = False
        self.pages = []
        self.componentList = []

        self.setWindowTitle("Electro editor")

        self.mainWidwet = QWidget()
        self.setCentralWidget(self.mainWidwet)
        self.mainLayout = QVBoxLayout(self)
        self.mainWidwet.setLayout(self.mainLayout)

        self.currentCursorCoordinates = QLabel()
        self.currentCursorCoordinates.setFrameStyle(Qt.SolidLine)

        self.currentScale = QLabel()
        self.currentScale.setFrameStyle(Qt.SolidLine)

        self.gridSize = QLabel()
        self.gridSize.setFrameStyle(Qt.SolidLine)

        self.statusBar = QStatusBar()
        self.statusBar.addPermanentWidget(self.currentCursorCoordinates)
        self.statusBar.addPermanentWidget(self.currentScale)
        self.statusBar.addPermanentWidget(self.gridSize)
        self.setStatusBar(self.statusBar)

        # create editro tabs and components list
        self.tabWidget = QTabWidget()
        self.componentListWidget = QListWidget()
        self.componentListWidget.setFixedWidth(110)
        def componentCliced(component):
            self.scene().pastComponent(component.group())
            self.sceneView().setFocus(True)

        self.componentListWidget.itemClicked.connect(componentCliced)
        editorSpace = QWidget()
        layout = QHBoxLayout(editorSpace)
        layout.addWidget(self.componentListWidget)
        layout.addWidget(self.tabWidget)

        # make Line edit dialog
        self.lineEditDialog = QWidget()
        layout = QHBoxLayout(self.lineEditDialog)
        lineEdit = QLineEdit()
        lineEdit.show()
        inputMessage = QLabel()
        layout.addWidget(inputMessage)
        layout.addWidget(lineEdit)
        self.lineEditDialog.hide()

        # make components list

        # set CSS style
        f = open("%s/listComponents.css" % editorPath(), "r")
        style = f.read()
        f.close()
        self.componentListWidget.setStyleSheet(style)


        self.mainLayout.addWidget(editorSpace)
        self.mainLayout.addWidget(self.lineEditDialog)


        self.addPage("Page 1")
        self.setFocusPolicy(Qt.NoFocus)
        self.tabWidget.installEventFilter(self)

        self.loadComponents()


    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            # Redirect Left and Right buttons
            if (key == 16777234 or key == 16777236 or
                key == 16777235 or key == 16777237):
                self.keyPressEvent(event)
                return True

        if event.type() == QEvent.KeyRelease:
            key = event.key()
            # Redirect Left and Right buttons
            if (key == 16777234 or key == 16777236 or
                key == 16777235 or key == 16777237):
                self.keyReleaseEvent(event)
                return True
        return False


    def addPage(self, name):
        page = PageWidget(self, name)
        self.pages.append(page)
        self.actualizePagesTabs(page)


    def actualizePagesTabs(self, currentPage=None):
        for i in range(self.tabWidget.count()):
             self.tabWidget.removeTab(i)
        for page in self.pages:
            self.tabWidget.addTab(page, page.name())

        if not currentPage:
            return
        index = self.tabWidget.indexOf(currentPage)
        self.tabWidget.setCurrentIndex(index)


    def loadComponents(self):
        for fileName in glob.glob("%s/*.ec" % componentsPath()):
            fileName = os.path.basename(fileName)
            componentName = os.path.splitext(fileName)[0]
            component = Component(componentName)
            if not component.load():
                print("error loading component %s" % componentName)
            self.componentList.append(component)
            self.componentListWidget.addItem(component)


    def addComponent(self, name, group):
        component = Component(name, group)
        component.save()
        component.load()
        self.componentList.append(component)
        self.componentListWidget.addItem(component)


    def removeComponent(self, component):
        self.componentListWidget.takeItem(self.componentListWidget.row(component))
        component.removeFiles()
        self.scene().abortPastComponent()
        self.componentListWidget.clearSelection()


    def pageById(self, id):
        return self.tabWidget.widget(id)


    def currectPage(self):
        return self.tabWidget.currentWidget()


    def renamePage(self, page, newName):
        page.setName(newName)
        self.actualizePagesTabs(page)


    def attachPage(self, page):
       # page.attach()
        self.actualizePagesTabs(page)


    def detachPage(self, page):
        self.pages.remove(page)
        self.actualizePagesTabs()


    def moveCurrentPageLeft(self):
        print("moveCurrentPageLeft")
        def prev(index):
            if index == 0:
                return 0
            return index - 1

        currPage = self.currectPage()
        for currIndex in range(len(self.pages)):
            if self.pages[currIndex] == currPage:
                prevIndex = prev(currIndex)
                if prevIndex == currIndex:
                    break

                # exchange curr with prev
                page = self.pages[prevIndex]
                self.pages[prevIndex] = self.pages[currIndex]
                self.pages[currIndex] = page
                break
        self.actualizePagesTabs(currPage)


    def moveCurrentPageRight(self):
        print("moveCurrentPageRight")
        def next(index):
            if index == (len(self.pages) - 1):
                return len(self.pages) - 1
            return index + 1

        currPage = self.currectPage()
        for currIndex in range(len(self.pages)):
            if self.pages[currIndex] == currPage:
                nextIndex = next(currIndex)
                if nextIndex == currIndex:
                    break

                # exchange curr with next
                page = self.pages[nextIndex]
                self.pages[nextIndex] = self.pages[currIndex]
                self.pages[currIndex] = page
                break
        self.actualizePagesTabs(currPage)


    def scene(self):
        return self.tabWidget.currentWidget().scene()


    def sceneView(self):
        return self.tabWidget.currentWidget().sceneView()


    def dialogLineEditShow(self, message, onReturn,
                           defaultValue="", selectAll=None):
        lineEdit = None
        items = self.lineEditDialog.children()
        for item in items:
            if item.__class__.__name__ == 'QLineEdit':
                lineEdit = item

            if item.__class__.__name__ == 'QLabel':
                label = item

        label.setText(message)
        self.dialogLineEditLine = lineEdit
        lineEdit.setText(defaultValue)
        lineEdit.returnPressed.connect(onReturn)
        self.lineEditDialog.show()
        lineEdit.setFocus()
        if selectAll:
            lineEdit.selectAll()


    def dialogLineEditHide(self):
        if self.lineEditDialog.isHidden():
            return

        items = self.lineEditDialog.children()
        for item in items:
            if item.__class__.__name__ == 'QLineEdit':
                lineEdit = item
                break

        self.lineEditDialog.hide()
        lineEdit.returnPressed.disconnect()


    def mousePressEvent(self, ev):
        self.componentListWidget.clearSelection()
        QMainWindow.mousePressEvent(self, ev)


    def keyPressEvent(self, event):
        key = event.key()
        print key
        scene = self.scene()

        if key == 16777216:  # ESC
            self.dialogLineEditHide()
            scene.setMode('select')
            return

        if key == 49:  # 1
            scene.setMode('drawLine')
            return

        if key == 16777249:  # CTRL
            self.keyCTRL = True

        if self.keyCTRL and key == 16777234:  # CTRL+LEFT
            self.moveCurrentPageLeft()
            return

        if self.keyCTRL and key == 16777236:  # CTRL+RIGHT
            self.moveCurrentPageRight()
            return

        # add new component
        if self.keyCTRL and key == 79:  # CTRL+O
            def dialogOnReturn():
                name = str(self.dialogLineEditLine.text())
                self.dialogLineEditHide()
                if not name:
                    return

                items = scene.selectedGraphicsItems()
                if not len(items):
                    return

                group = scene.packItemsIntoGroup(items, name)
                if not group:
                    item = items[0]
                    if item.type() != GROUP_TYPE:
                        return
                    group = item

                self.addComponent(name, group)
            if not len(scene.selectedGraphicsItems()):
                return
            self.dialogLineEditShow("Save selected as component. Enter new component name:",
                                    dialogOnReturn)
            return

        # add new page
        if self.keyCTRL and key == 80:  # CTRL+P
            def dialogOnReturn():
                name = str(self.dialogLineEditLine.text())
                self.dialogLineEditHide()
                if not name:
                    return
                self.addPage(name)
            self.dialogLineEditShow("Enter new page name:", dialogOnReturn)
            return

        # edit page name
        if self.keyCTRL and key == 69:  # CTRL+E
            name = self.currectPage().name()
            def dialogOnReturn():
                page = self.currectPage()
                name = str(self.dialogLineEditLine.text())
                self.dialogLineEditHide()
                if not name:
                    return
                self.renamePage(page, name)

            self.dialogLineEditShow("Edit current page name:",
                                    dialogOnReturn,
                                    name)
            return

        # remove component or current page
        if self.keyCTRL and key == 68:  # CTRL+D
            selectedComponents = self.componentListWidget.selectedItems()
            if len(selectedComponents):
                def dialogOnRemoveComponent():
                    self.dialogLineEditHide()
                    answer = str(self.dialogLineEditLine.text())
                    if answer != 'yes' and answer != 'y':
                        return
                    for component in selectedComponents:
                        self.removeComponent(component)
                self.dialogLineEditShow("Remove selected components?:",
                                        dialogOnRemoveComponent,
                                        "no", True)
                return

            def dialogOnRemovePage():
                page = self.currectPage()
                answer = str(self.dialogLineEditLine.text())
                self.dialogLineEditHide()
                if answer == 'yes' or answer == 'y':
                    self.detachPage(page)

            self.dialogLineEditShow("Remove current page?:",
                                    dialogOnRemovePage,
                                    "no", True)
            return

        if (key == 16777234 or key == 16777236 or
            key == 16777235 or key == 16777237):
            scene.keyPressEvent(event)
            return

        scene.keyPressEvent(event)
        return
#        QWidget.keyPressEvent(self, event)


    def keyReleaseEvent(self, event):
        key = event.key()

        if (key == 16777234 or key == 16777236 or
            key == 16777235 or key == 16777237):
            self.scene().keyReleaseEvent(event)
            return

        if key == 16777249:  # CTRL
            self.keyCTRL = False

        self.scene().keyReleaseEvent(event)
        return


    def toClipboard(self, text):
        self.app.clipboard().setText(text)


    def fromClipboard(self):
        return self.app.clipboard().text()


    def setCursorCoordinates(self, point):
        self.currentCursorCoordinates.setText("x: %d, y: %d" % (point.x(), point.y()))


    def setScale(self, scale):
        self.currentScale.setText("Scale: %d%%" % scale)


    def setGridSize(self, gridSize):
        self.gridSize.setText("Grid: %dpx" % gridSize)


    def setTextStatusBar(self, text):
        self.statusBar.setText(text)


