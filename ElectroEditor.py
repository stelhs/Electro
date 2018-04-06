from ElectroScene import *
from ElectroSceneView import *
from LineEditValidators import *
from PyQt4.Qt import QWidget, QMainWindow, QLabel, QPoint, QTimer
import os, glob, sys, pprint, re



def editorPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def componentsPath():
    return "%s/components" % editorPath()


page_last_id = 0

class PageWidget(QWidget):


    def __init__(self, editor, name):
        QWidget.__init__(self)
        global page_last_id
        self._name = name
        self._sceneView = ElectroSceneView(editor, ElectroScene(editor))
        layout = QVBoxLayout(self)
        layout.addWidget(self._sceneView)
        self.editor = editor
        self.setLayout(layout)
        page_last_id += 1
        self._id = page_last_id


    def setNum(self, num):
        self.pageNum = num


    def id(self, num):
        return self._id


    def num(self):
        return self.pageNum


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
        group.setIndex(0)
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


    def name(self):
        return self._name


    def prefixName(self):
        if not 'prefixName' in self._groupProperties:
            return ""
        return self._groupProperties['prefixName']



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

        self.currentCursorCoordinatesLabel = QLabel()
        self.currentCursorCoordinatesLabel.setFrameStyle(Qt.SolidLine)

        self.currentGraphicsItemLabel = QLabel()
        self.currentGraphicsItemLabel.setFrameStyle(Qt.SolidLine)

        self.currentScaleLabel = QLabel()
        self.currentScaleLabel.setFrameStyle(Qt.SolidLine)

        self.gridSizeLabel = QLabel()
        self.gridSizeLabel.setFrameStyle(Qt.SolidLine)

        self.editorToolLabel = QLabel()
        self.editorToolLabel.setFrameStyle(Qt.SolidLine)

        self.statusBar = QStatusBar()
        self.statusBar.addPermanentWidget(self.editorToolLabel)
        self.statusBar.addPermanentWidget(self.currentCursorCoordinatesLabel)
        self.statusBar.addPermanentWidget(self.currentGraphicsItemLabel)
        self.statusBar.addPermanentWidget(self.currentScaleLabel)
        self.statusBar.addPermanentWidget(self.gridSizeLabel)
        self.setStatusBar(self.statusBar)

        # create editor tabs and components list
        self.tabWidget = QTabWidget()
        def tabChanged(index):
            if index < 0:
                return
            page = self.tabWidget.widget(index)
            self.setEditorTool(page.scene().currentTool())

        # create left panel
        leftPanel = QWidget()
        leftPanel.setFixedWidth(150)
        leftPanellayout = QVBoxLayout(leftPanel)

        # create component list
        self.tabWidget.currentChanged.connect(tabChanged)
        self.componentListWidget = QListWidget()
        leftPanellayout.addWidget(self.componentListWidget)
        def componentCliced(component):
            self.showComponentInfo(component)
            self.scene().pastComponent(component.group())
            self.sceneView().setFocus(True)
        self.componentListWidget.itemClicked.connect(componentCliced)

        # create component properties info
        self.componentInfoLabel = QLabel()
        self.componentInfoLabel.setWordWrap(True)
        self.componentInfoLabel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.componentInfoLabel.setFixedHeight(60)
        leftPanellayout.addWidget(self.componentInfoLabel)

        # create editor space
        editorSpace = QWidget()
        layout = QHBoxLayout(editorSpace)
        layout.addWidget(leftPanel)
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

        self.statusBarMessageTimer = QTimer()

        # set CSS style
        f = open("%s/listComponents.css" % editorPath(), "r")
        style = f.read()
        f.close()
        self.componentListWidget.setStyleSheet(style)


        self.mainLayout.addWidget(editorSpace)
        self.mainLayout.addWidget(self.lineEditDialog)


        self.addPage("Undefined")
        self.setFocusPolicy(Qt.NoFocus)
        self.tabWidget.installEventFilter(self)

        # make components list
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
        self.setEditorTool(page.scene().currentTool())


    def actualizePagesTabs(self, currentPage=None):
        for i in range(self.tabWidget.count()):
             self.tabWidget.removeTab(i)

        i = 0
        for page in self.pages:
            i += 1
            self.tabWidget.addTab(page, "%d: %s" % (i, page.name()))
            page.setNum(i)

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


    def dialogLineEditShow(self, message, onSuccess,
                           defaultValue="", selectAll=None, validator=None):
        lineEdit = None
        items = self.lineEditDialog.children()
        for item in items:
            if item.__class__.__name__ == 'QLineEdit':
                lineEdit = item

            if item.__class__.__name__ == 'QLabel':
                label = item

        lineEdit.setValidator(None)
        if validator:
            validator.setLineEdit(lineEdit)
            lineEdit.setValidator(validator)

        label.setText(message)
        self.dialogLineEditLine = lineEdit
        lineEdit.setText(defaultValue)

        def onReturn():
            self.dialogLineEditHide()
            onSuccess(str(lineEdit.text()))
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


    def setTool(self, tool):
        if not tool:
            self.scene().setMode('select')
            self.setEditorTool(None)
            return
        self.scene().setTool(tool)


    def mousePressEvent(self, ev):
        self.componentListWidget.clearSelection()
        self.showComponentInfo()
        QMainWindow.mousePressEvent(self, ev)
        self.dialogLineEditHide()

        if self.scene().currentTool() == 'useTool':
            self.scene().abortTool()
            self.setMode('select')
            self.editor.setEditorTool(None)
            return



    def keyPressEvent(self, event):
        key = event.key()
        print key
        scene = self.scene()

        if key == 16777216:  # ESC
            self.dialogLineEditHide()
            self.setTool(None)
            return

        if key == 49:  # 1
            self.setTool('traceLine')
            return


        if key == 50:  # 2
            self.setTool('line')
            return


        if key == 51:  # 3
            self.setTool('rectangle')
            return

        if key == 52:  # 4
            self.setTool('ellipse')
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
            def dialogOnReturn(str):
                [name, prefix] = str.split()
                items = scene.selectedGraphicsItems()
                if not len(items):
                    self.showStatusBarErrorMessage("no selected items")
                    return

                group = scene.packItemsIntoGroup(items, name)
                if not group:
                    item = items[0]
                    if item.type() != GROUP_TYPE:
                        return
                    group = item

                group.setPrefixName(prefix)
                if not group.index():
                    group.setIndex(self.findFreeComponentIndex(prefix))
                self.addComponent(name, group)
                self.showStatusBarMessage("added component: %s" % name)

            if not len(scene.selectedGraphicsItems()):
                self.showStatusBarErrorMessage("no selected items")
                return

            validator = ComponentNameValidator(self)
            self.dialogLineEditShow("Save selected as component. Enter new component file name and component_prefix:",
                                    dialogOnReturn, validator=validator)
            return

        # add new page
        if self.keyCTRL and key == 80:  # CTRL+P
            def dialogOnReturn(name):
                if not name:
                    self.showStatusBarErrorMessage("no page name entered")
                    return
                self.addPage(name)
            self.dialogLineEditShow("Enter new page name:", dialogOnReturn)
            return

        # edit page name
        if self.keyCTRL and key == 69:  # CTRL+E
            selectedItems = self.scene().selectedGraphicsItems()
            if len(selectedItems):
                groupsSelected = []
                for item in selectedItems:
                    if item.type() != GROUP_TYPE:
                        continue
                    groupsSelected.append(item)

                if len(groupsSelected) == 0:
                    self.showStatusBarErrorMessage("No group are selected")
                    return

                if len(groupsSelected) > 1:
                    self.showStatusBarErrorMessage("Too much groups are selected")
                    return

                self.showEditGroupIndexName(groupsSelected[0])
                return

            # edit page
            name = self.currectPage().name()
            def dialogOnReturn(name):
                page = self.currectPage()
                if not name:
                    self.showStatusBarErrorMessage("no page name entered")
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
                # remove component
                def dialogOnRemoveComponent(answer):
                    if answer != 'yes' and answer != 'y':
                        return
                    for component in selectedComponents:
                        self.removeComponent(component)
                validator = YesNoValidator(self)
                self.dialogLineEditShow("Remove selected components?:",
                                        dialogOnRemoveComponent,
                                        "no", selectAll=True,
                                        validator=validator)
                return

            # remove page
            def dialogOnRemovePage(answer):
                page = self.currectPage()
                self.dialogLineEditHide()
                if answer == 'yes' or answer == 'y':
                    self.detachPage(page)

            validator = YesNoValidator(self)
            self.dialogLineEditShow("Remove current page?:",
                                    dialogOnRemovePage,
                                    "no", selectAll=True,
                                    validator=validator)
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


    def showEditGroupIndexName(self, group):
        string = ""
        if group.prefixName():
            string = group.indexName()

        def dialogOnReturn(text):
            res = self.unpackGroupIndexName(text)
            if not res:
                self.showStatusBarErrorMessage("Incorrect component name")
                return
            [prefixName, index] = res
            group.setPrefixName(prefixName)
            group.setIndex(index)

        validator = EditGroupValidator(self, group)
        self.dialogLineEditShow("Edit selected group. Enter component_prefix and press Space:",
                                dialogOnReturn, string,
                                validator=validator)


    def toClipboard(self, text):
        self.app.clipboard().setText(text)


    def fromClipboard(self):
        return self.app.clipboard().text()


    def setEditorTool(self, tool):
        if not tool:
            tool = "not selected"
        self.editorToolLabel.setText("Tool: %s" % tool)


    def setStatusCursorCoordinates(self, point):
        self.currentCursorCoordinatesLabel.setText("x: %d, y: %d" % (point.x(), point.y()))


    def setStatusGraphicsItemInfo(self, item=None):
        if not item:
            self.currentGraphicsItemLabel.setText("")
            return
        self.currentGraphicsItemLabel.setText("id: %d, type: %s" % (
                                              item.id(), item.typeName()))


    def setStatusScale(self, scale):
        self.currentScaleLabel.setText("Scale: %d%%" % scale)


    def setStatusGridSize(self, gridSize):
        self.gridSizeLabel.setText("Grid: %dpx" % gridSize)


    def setTextStatusBar(self, text):
        self.statusBar.setText(text)


    def showStatusBarErrorMessage(self, message, time=5):
        self.showStatusBarMessage("Error: " + message, time, 'red')


    def showStatusBarMessage(self, message, time=5, color="black"):
        self.statusBar.showMessage(message)
        if not time:
            return

        def messageHide():
            self.statusBar.showMessage("")
            self.statusBarMessageTimer.stop()
            self.statusBar.setStyleSheet("color: Black")
        self.statusBar.setStyleSheet("color: %s" % color)
        self.statusBarMessageTimer.timeout.connect(messageHide)
        self.statusBarMessageTimer.start(time * 1000)


    def showComponentInfo(self, component=None):
        if not component:
            self.componentInfoLabel.setText("")
            return
        info = "Component\n"
        info += "file: %s\n" % component.name()
        info += "prefix: %s\n" % component.prefixName()
        self.componentInfoLabel.setText(info)


    def showGroupInfo(self, group=None):
        if not group or group.type() != GROUP_TYPE:
            self.componentInfoLabel.setText("")
            return
        info = "Group\n"
        info += "name: %s\n" % group.name()
        info += "id: %d\n" % group.id()
        info += "index: %s\n" % group.indexName()
        self.componentInfoLabel.setText(info)


    def unpackGroupIndexName(self, indexName):
        found = re.findall('[A-Za-z]+', indexName)
        if not len(found):
            return None
        prefixName = found[0]

        found = re.findall('\d+', indexName)
        if not len(found):
            return None
        index = found[0]
        return prefixName, int(index)


    def findGroupByIndexName(self, indexName, excludeGroup=None):
        print("findGroupByIndexName %s" % indexName)
        res = self.unpackGroupIndexName(indexName)
        if not res:
            return None
        [prefixName, index] = res

        for page in self.pages:
            groups = page.scene().graphicsItems(GROUP_TYPE)
            for group in groups:
                if excludeGroup and group.id() == excludeGroup.id():
                    continue
                if not group.prefixName():
                    continue
                if group.prefixName() == prefixName and group.index() == index:
                    print("group found")
                    return group
        return None


    def findFreeComponentIndex(self, prefixName):
        listIndexes = []
        # get index list by all components
        for page in self.pages:
            groups = page.scene().graphicsItems(GROUP_TYPE)
            for group in groups:
                if not group.prefixName():
                    continue
                if group.prefixName() != prefixName:
                     continue
                listIndexes.append(group.index())

        if not len(listIndexes):
            return 1

        listIndexes.sort()

        # find free index
        supposedIndex = 1
        for busyIndex in listIndexes:
            if busyIndex != supposedIndex:
                return supposedIndex
            supposedIndex += 1
        return supposedIndex




