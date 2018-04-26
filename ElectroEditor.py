from ElectroScene import *
from ElectroSceneView import *
from Color import *
from Settings import *
from LineEditValidators import *
from PyQt4.Qt import QWidget, QMainWindow, QLabel, QPoint, QTimer
import os, glob, sys, pprint, re
from shutil import copyfile
from datetime import datetime
import time


class ElectroEditor(QMainWindow):
    EDITOR_VERSION = 1

    def __init__(self, app):
        QMainWindow.__init__(self)
        self.app = app
        self.keyCTRL = False
        self.keyShift = False
        self.pages = []
        self.componentList = []
        self.connectionsList = []
        self.projectFileName = ""

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
            page.updateLinkPoints()
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
            scene = self.scene()
            if not scene:
                return
            scene.setGrid(MAX_GRID_SIZE)
            scene.setMode('select')
            self.showComponentInfo(component)
            scene.pastComponent(component.group())
            self.sceneView().setFocus()
            # self.componentListWidget.setFocus(True)
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

        self.colorDialog = QColorDialog()

        self.addPage("Undefined")
        self.setFocusPolicy(Qt.NoFocus)
        self.tabWidget.installEventFilter(self)

        # make components list
        self.loadComponents()
        self.lastSaveTime = 0
        self.settings = Settings()



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
        # remove all tabs
        cnt = self.tabWidget.count()
        while(cnt):
            for i in range(cnt):
                self.tabWidget.removeTab(i)
            cnt = self.tabWidget.count()

        # add tabs
        i = 0
        for page in self.pages:
            i += 1
            page.setNum(i)
            if page.name():
                self.tabWidget.addTab(page, "%d: %s" % (i, page.name()))
            else:
                self.tabWidget.addTab(page, "%d" % i)

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
        self.componentList.remove(component)
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


    def removePage(self, page):
        page.remove()
        self.actualizePagesTabs()


    def moveCurrentPageLeft(self):
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
        if not len(self.pages):
            return None
        return self.tabWidget.currentWidget().scene()


    def sceneView(self):
        return self.tabWidget.currentWidget().sceneView()


    def dialogColorSelect(self, currentColor, alphaChannel=False):
        if not currentColor:
            currentColor = QColor(255, 255, 255)
        whiteColorRgb = QColor(255, 255, 255).rgb()
        for index in range(self.colorDialog.customCount()):
            self.colorDialog.setCustomColor(index, whiteColorRgb)
        index = 0
        for color in Color.usedColors():
            self.colorDialog.setCustomColor(index, color.rgb())
            index += 1
        if alphaChannel:
            return self.colorDialog.getColor(currentColor,
                                             None,
                                             "",
                                             QColorDialog.ShowAlphaChannel)
        return self.colorDialog.getColor(currentColor)


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

        if not self.scene():
            return
        if self.scene().currentTool() == 'useTool':
            self.scene().abortTool()
            self.setMode('select')
            self.editor.setEditorTool(None)
            return


    def keyPressEvent(self, event):
        key = event.key()
        print key

        # detect CTRL pressed
        if key == 16777249:  # CTRL
            self.keyCTRL = True
            for page in self.pages:
                page.scene().keyCTRLPress()

        # detect Shift pressed
        if key == 16777248:  # Shift
            self.keyShift = True
            for page in self.pages:
                page.scene().keyShiftPress()

        # add new page
        if self.keyCTRL and key == 80:  # CTRL+P
            def dialogOnReturn(name):
                self.addPage(name)
            self.dialogLineEditShow("Enter new page name:", dialogOnReturn)
            return

        scene = self.scene()
        if not scene:
            return

        # cancel current operation
        if key == 16777216:  # ESC
            self.dialogLineEditHide()
            self.setTool(None)
            self.setFocus()
            self.resetSelectionItems()
            return

        # route all key pressed into scene while textEdit mode
        if scene.mode == 'textEdit':
            scene.keyPressEvent(event)
            return

        # select tool 'traceLine'
        if key == 49:  # 1
            self.setTool('traceLine')
            return


        # select tool 'line'
        if key == 50:  # 2
            self.setTool('line')
            return


        # select tool 'rectangle'
        if key == 51:  # 3
            self.setTool('rectangle')
            return

        # select tool 'ellipse'
        if key == 52:  # 4
            self.setTool('ellipse')
            return

        # select tool 'text'
        if key == 53:  # 5
            self.setTool('text')
            return

        # insert linkPoint
        if key == 76:  # l
            if scene.mode == "pastLinkPoint":
                return
            scene.setMode('pastLinkPoint')
            return

        # save project
        if self.keyCTRL and key == 83:  # CTRL+S
            file = None
            if not self.projectFileName or self.keyShift:
                lastDir = self.settings.data()['lastProjectDir']
                file = str(QFileDialog.getSaveFileName(None,
                                                       "Save project",
                                            filter="Electro schematic file (*.es)",
                                            directory=lastDir))
                if not file:
                    return
            self.saveProject(file)
            return

        # open project
        if self.keyCTRL and key == 79:  # CTRL+O
            lastDir = self.settings.data()['lastProjectDir']
            file = str(QFileDialog.getOpenFileName(None, "open schematic",
                                        filter="Electro schematic file (*.es)",
                                        directory=lastDir))
            if not file:
                return
            self.openProject(file)
            return

        # new project
        if self.keyCTRL and key == 78:  # CTRL+N
            def dialogOnReturn(answer):
                if answer != 'yes' and answer != 'y':
                    return
                self.resetEditor()
                self.addPage("Undefined")

            validator = YesNoValidator(self)
            self.dialogLineEditShow("Create new Project?:",
                                    dialogOnReturn,
                                    "no", selectAll=True,
                                    validator=validator)
            return

        # search item by indexName or id
        if self.keyCTRL and key == 70:  # CTRL+F
            def dialogOnReturn(str):
                str = str.strip()
                if str.isdigit():
                    item = self.itemById(int(str))
                else:
                    item = self.findGroupByIndexName(str)

                if not item:
                    self.showStatusBarErrorMessage("not found")
                    return
                self.resetSelectionItems()
                item.scene().itemAddToSelection(item)
                self.displayItem(item)
                item.highlight()

            self.dialogLineEditShow("Search item. Enter indexName or itemId:",
                                    dialogOnReturn)
            return

        # create connection
        if not self.keyCTRL and key == 67:  # C
            def dialogOnReturn(str):
                linkPoints = []
                w = str.split()
                for i in w:
                    point = self.itemById(int(i))
                    if not point:
                        self.showStatusBarErrorMessage("LinkPoint id:%s not found" % i)
                        return
                    linkPoints.append(point)

                if len(linkPoints) != 2:
                    self.showStatusBarErrorMessage("only two LinkPoints are allowed")
                    return

                for linkPoint in linkPoints:
                    conn = self.connectionByLinkPoint(linkPoint)
                    if conn:
                        self.removeConnection(conn)

                self.connectionCreate(linkPoints[0], linkPoints[1])

            defaultValue = ""
            linkPoints = self.selectedGraphicsItems(LINK_TYPE)
            if len(linkPoints) == 2:
                for linkPoint in linkPoints:
                    defaultValue += "%d " % linkPoint.id()
            validator = ConnectinValidator(self)
            self.dialogLineEditShow("Enter two LinkPoints IDs space separated:",
                                    dialogOnReturn,
                                    defaultValue=defaultValue,
                                    validator=validator)
            return

        # move current page left
        if self.keyCTRL and key == 16777234:  # CTRL+LEFT
            self.moveCurrentPageLeft()
            return

        # move current page right
        if self.keyCTRL and key == 16777236:  # CTRL+RIGHT
            self.moveCurrentPageRight()
            return

        # save selected items into component
        if self.keyCTRL and key == 87:  # CTRL+W
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
                    self.setUniqueComponentIndex(group)
                self.addComponent(name, group)
                self.showStatusBarMessage("added component: %s" % name)

            if not len(scene.selectedGraphicsItems()):
                self.showStatusBarErrorMessage("no selected items")
                return

            validator = ComponentNameValidator(self)
            self.dialogLineEditShow("Save selected as component. Enter new component file name and component_prefix:",
                                    dialogOnReturn, validator=validator)
            return

        # edit current page name or selected group properties
        if self.keyCTRL and key == 69:  # CTRL+E
            selectedItems = self.scene().selectedGraphicsItems()
            if len(selectedItems):
                # edit current group item
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

            # edit current page name
            name = self.currectPage().name()
            def dialogOnReturn(name):
                page = self.currectPage()
                self.renamePage(page, name)

            self.dialogLineEditShow("Edit current page name:",
                                    dialogOnReturn,
                                    name)
            return

        # remove component or current page
        if self.keyCTRL and key == 68:  # CTRL+D
            selectedComponents = self.componentListWidget.selectedItems()
            if len(selectedComponents):
                # remove selected component
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

            # remove current page
            def dialogOnRemovePage(answer):
                page = self.currectPage()
                self.dialogLineEditHide()
                if answer == 'yes' or answer == 'y':
                    self.removePage(page)

            validator = YesNoValidator(self)
            self.dialogLineEditShow("Remove current page?:",
                                    dialogOnRemovePage,
                                    "no", selectAll=True,
                                    validator=validator)
            return

        scene.keyPressEvent(event)
        return


    def keyReleaseEvent(self, event):
        key = event.key()

        if (key == 16777234 or key == 16777236 or
            key == 16777235 or key == 16777237):
            self.scene().keyReleaseEvent(event)
            return

        if key == 16777249:  # CTRL
            self.keyCTRL = False
            for page in self.pages:
                page.scene().keyCTRLRelease()

        if key == 16777248:  # Shift
            self.keyShift = False
            for page in self.pages:
                page.scene().keyShiftRelease()

        if self.scene():
            self.scene().keyReleaseEvent(event)
        return


    def showEditGroupIndexName(self, group):
        string = ""
        if group.prefixName():
            string = group.indexName()

        def dialogOnReturn(text):
            text = text.upper()
            if not len(text):
                group.setIndex(0)
                group.setPrefixName("")
                group.setParentComponentGroup(None)
                group.updateView()
                return

            unpackedName = self.unpackGroupIndexName(text)
            if not unpackedName:
                self.showStatusBarErrorMessage("Incorrect component name")
                return

            # if component not subcomponent
            if len(unpackedName) == 2:
                [prefixName, index] = unpackedName[:2]

                # change index between busyness and current index
                existGroup = self.findGroupByIndexName(text, group)
                if existGroup:
                    existGroup.setPrefixName(group.prefixName())
                    existGroup.setIndex(group.index())
                    self.updateSubComponentsView(existGroup)
                group.setPrefixName(prefixName)
                group.setIndex(index)
                group.setParentComponentGroup(None)
                self.updateSubComponentsView(group)
                return

            # if component is subcomponent
            indexName = self.packGroupIndexName(unpackedName[:-1])
            parentGroup = self.findGroupByIndexName(indexName, group)
            if not parentGroup:
                self.showStatusBarErrorMessage("Parent group %s is not exist" % indexName)
                return

            # change index between busyness and current index
            existGroup = self.findGroupByIndexName(text, group)
            if existGroup:
                existGroup.setIndex(group.index())
                self.updateSubComponentsView(existGroup)

            group.setParentComponentGroup(parentGroup)
            group.setIndex(unpackedName[-1])
            self.updateSubComponentsView(group)
            return

        validator = EditGroupValidator(self, group)
        self.dialogLineEditShow("Edit selected group. Enter component_prefix and press Space:",
                                dialogOnReturn, string,
                                validator=validator)


    def showSwitchToSubComponent(self, group):
        subGroups = self.subComponentGroups(group)
        if not len(subGroups):
            return

        def dialogOnReturn(text):
            subGroup = self.subComponentGroupByIndex(group, int(text))
            if not subGroup:
                self.showStatusBarErrorMessage("Component not found")
                return
            self.resetSelectionItems()
            scene = subGroup.scene()
            scene.itemAddToSelection(subGroup)
            self.displayItem(subGroup)
            return

        if len(subGroups) == 1:
            subGroup = subGroups[0]
            self.resetSelectionItems()
            scene = subGroup.scene()
            scene.itemAddToSelection(subGroup)
            self.displayItem(subGroup)
            return

        subIndexes = []
        promptText = "subComponents: "
        separator = ""
        for subGroup in subGroups:
            promptText += "%s%s" % (separator, subGroup.indexName())
            separator = " | "
            subIndexes.append(subGroup.index())
        promptText += ". Enter subComponent index:"

        validator = IntValidator(self, subIndexes)
        self.dialogLineEditShow(promptText, dialogOnReturn, validator=validator)


    def toClipboard(self, text):
        self.app.clipboard().setText(text)


    def fromClipboard(self):
        return self.app.clipboard().text()


    def setEditorTool(self, tool):
        if not tool:
            tool = "not selected"
        self.editorToolLabel.setText("Tool: %s" % tool)


    def setStatusCursorCoordinates(self, point):
        scene = self.scene()
        if not scene:
            return
        quadrant = scene.quadrantByPos(point)
        self.currentCursorCoordinatesLabel.setText("%s | x: %d, y: %d" %
                                                   (quadrant,
                                                    point.x(),
                                                    point.y()))


    def setStatusGraphicsItemInfo(self, item=None):
        if not item:
            self.currentGraphicsItemLabel.setText("")
            return
        text = "id: %d, type: %s" % (item.id(), item.typeName())
        if item.zIndex():
            text += ", zIndex: %d" % int(item.zIndex())
        self.currentGraphicsItemLabel.setText(text)


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
        if re.findall('\.' , indexName):
            parts = indexName.split('.')
            prefix, index = self.unpackGroupIndexName(parts[0])
            result = []
            for part in parts[1:]:
                if part.strip():
                    result.append(int(part))
            result.insert(0, int(index))
            result.insert(0, prefix)
            return result

        found = re.findall('[A-Z]+', indexName)
        if not len(found):
            return None
        prefixName = found[0]

        found = re.findall('\d+', indexName)
        if not len(found):
            return None
        index = found[0]
        return [prefixName, int(index)]


    def packGroupIndexName(self, parts):
        indexName = "%s%d" % (parts[0], parts[1])
        indexes = parts[2:]
        for index in indexes:
            indexName += ".%s" % index
        return indexName


    def findGroupByIndexName(self, indexName, excludeGroup=None):
        res = self.unpackGroupIndexName(indexName)
        if not res:
            return None

        if len(res) > 2:
            indexName = "%s%d" % (res[0], res[1])
            group = self.findGroupByIndexName(indexName)
            if not group:
                return None

            indexes = res[2:]
            for index in indexes:
                group = self.subComponentGroupByIndex(group, index)
                if not group:
                    return None
            if excludeGroup and group.id() == excludeGroup.id():
                return None
            return group

        [prefixName, index] = res[:2]
        for page in self.pages:
            groups = page.scene().graphicsItems(GROUP_TYPE)
            for group in groups:
                if excludeGroup and group.id() == excludeGroup.id():
                    continue
                if not group.prefixName():
                    continue
                if group.parentComponentGroup():
                    continue
                if group.prefixName() == prefixName and group.index() == index:
                    return group
        return None


    def findFreeComponentIndex(self, prefixName):
        listIndexes = []
        # get index list by all components
        for page in self.pages:
            groups = page.scene().allGraphicsItems(GROUP_TYPE)
            for group in groups:
                if not group.prefixName():
                    continue
                if group.prefixName() != prefixName:
                    continue
                if group.parentComponentGroup():
                    continue
                if group.index():
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


    def findFreeSubComponentIndex(self, parentComponentGroup):
        listIndexes = []
        for page in self.pages:
            groups = page.scene().allGraphicsItems(GROUP_TYPE)
            for group in groups:
                if group.parentComponentGroup() != parentComponentGroup:
                    continue
                index = group.index()
                if index:
                    listIndexes.append(index)

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


    def setUniqueComponentIndex(self, group):
        parentComponentGroup = group.parentComponentGroup()
        if not parentComponentGroup:
            prefixName = group.prefixName()
            if prefixName:
                group.setIndex(self.findFreeComponentIndex(prefixName))
            return
        freeIndex = self.findFreeSubComponentIndex(parentComponentGroup)
        group.setIndex(freeIndex)


    def subComponentGroupByIndex(self, group, index):
        subComponents = self.subComponentGroups(group)
        for subComponent in subComponents:
            if subComponent.index() == index:
                return subComponent
        return None


    def subComponentGroups(self, parentGroup):
        subComponents = []
        for page in self.pages:
            subComponents += page.scene().subComponentGroups(parentGroup)
        return subComponents


    def updateSubComponentsView(self, parentGroup):
        parentGroup.updateView()
        subComponents = self.subComponentGroups(parentGroup)
        for subComponent in subComponents:
            subComponent.updateView()
            self.updateSubComponentsView(subComponent)


    def graphicsItems(self, type=None):
        items = []
        for page in self.pages:
            items += page.scene().graphicsItems(type)
        return items


    def graphicsUnpackedItems(self):
        items = []
        for page in self.pages:
            items += page.scene().graphicsUnpackedItems()
        return items


    def graphicsUnpackedItemsById(self, id):
        items = []
        for item in self.graphicsUnpackedItems():
            if item.id() == id:
                items.append(item)
        return items


    def updateAllComponentsView(self):
        subComponents = []
        for page in self.pages:
            groups = page.scene().allGraphicsItems(GROUP_TYPE)
            for group in groups:
                group.updateView()


    def connectionCreate(self, linkPoint1, linkPoint2):
        conn = Connection(self, linkPoint1, linkPoint2)
        self.connectionsList.append(conn)


    def removeConnection(self, conn):
        conn.remove()


    def displayItem(self, item):
        scene = item.scene()
        view = scene.views()[0]
        self.tabWidget.setCurrentIndex(scene.num() - 1)
        view.setZoom(200, item.center())


    def displayRemoteLinkPoint(self, linkPoint):
        remoteLinkPoint = linkPoint.remoteLinkPoint()
        if not remoteLinkPoint:
            return False
        self.resetSelectionItems()
        remoteLinkPoint.scene().itemAddToSelection(remoteLinkPoint)
        self.displayItem(remoteLinkPoint)
        return True


    def itemById(self, id):
        for page in self.pages:
            scene = page.scene()
            item = scene.itemById(id)
            if item:
                return item
        return None


    def graphicsObjectFromJson(self, jsonText):
        try:
            ItemsProperties = json.loads(str(jsonText))
        except:
            print("Bad json data")
            return []

        listUpdateParentComponents = []
        items = []
        for itemProp in ItemsProperties:
            item = createGraphicsObjectByProperties(itemProp)
            if item:
                items.append(item)
                if item.type() == GROUP_TYPE and 'parentComponentId' in itemProp:
                    listUpdateParentComponents.append((item, itemProp['parentComponentId']))

        for (group, parentId) in listUpdateParentComponents:
            parentGroup = self.itemById(parentId)
            group.setParentComponentGroup(parentGroup)

        return items


    def connectionByLinkPoint(self, linkPoint):
        for conn in self.connectionsList:
            for point in conn.linkPoints():
                if point.id() == linkPoint.id():
                    return conn
        return None


    def selectedGraphicsItems(self, type=None):
        items = []
        for page in self.pages:
            scene = page.scene()
            items += scene.selectedGraphicsItems(type)
        return items


    def resetSelectionItems(self):
        for page in self.pages:
            scene = page.scene()
            scene.resetSelectionItems()


    def itemsAddToSelection(self, items):
        for item in items:
            for page in self.pages:
                scene = page.scene()
                if scene != item.scene():
                    continue
                scene.itemAddToSelection(item)

    def allGraphicsItems(self, type=None):
        items = []
        for page in self.pages:
            items += page.scene().unpackAllItems(self.graphicsItems(), type)
        return items


    def saveProject(self, newfileName):
        cuttentTime = int(time.time())
        if newfileName:
            if newfileName[-3:] != '.es':
                newfileName += '.es'

            fileDirName = os.path.dirname(newfileName)
            if not os.path.isdir(fileDirName):
                os.mkdir(fileDirName)
            self.projectFileName = newfileName

        if not self.projectFileName:
            return

        backupInterval = self.settings.data()['backupInterval']
        if cuttentTime > (self.lastSaveTime + backupInterval):
            self.lastSaveTime = cuttentTime
            self.backupProject()

        fileDirName = os.path.dirname(self.projectFileName)
        self.settings.set('lastProjectDir', fileDirName)
        self.saveProjectToFile(self.projectFileName)


    def saveProjectToFile(self, fileName):
        print("saveProjectToFile %s" % fileName)
        header = {"app": "Electro Schematic editor",
                  "version": self.EDITOR_VERSION}

        pagesData = []
        for page in self.pages:
            itemsData = []
            items = page.scene().graphicsItems()
            for item in items:
                itemsData.append(item.properties())
            pagesData.append({"num": page.num(),
                              "name": page.name(),
                              "items": itemsData})

        connections = []
        for connection in self.connectionsList:
            connections.append(connection.properties())

        data = {"header": header,
                "pages": pagesData,
                "connections": connections}
        jsonText = json.dumps(data, indent=2, sort_keys=True)

        file = open(fileName, "w")
        file.write(jsonText)
        file.close()
        self.showStatusBarMessage("project saved in %s" % fileName)


    def backupProject(self):
        if not self.projectFileName:
            return

        if not os.path.isfile(self.projectFileName):
            return

        baseFileName = os.path.basename(self.projectFileName)
        fileDirName = os.path.dirname(self.projectFileName)
        if fileDirName:
            fileDirName += '/'
        projectName = os.path.splitext(baseFileName)[0]
        date = datetime.now().strftime("%Y-%m-%d_%H-%M")
        newFileDir = "%s%s_backups" % (fileDirName, projectName)
        if not os.path.isdir(newFileDir):
            os.mkdir(newFileDir)
        newFileName = "%s/%s_%s.es" % (newFileDir,
                                       projectName,
                                       date)
        print("makeBackup to %s" % newFileName)
        copyfile(self.projectFileName, newFileName)


    def openProject(self, fileName):
        print("openProject from %s" % fileName)
        file = open(fileName, "r")
        fileContent = file.read()
        file.close()

        try:
            project = json.loads(str(fileContent))
        except:
            print("Incorrect file data: can't parse JSON")
            self.showStatusBarErrorMessage("Incorrect file data: can't parse JSON")
            return

        if not 'header' in project:
            print("can't find 'header' section in JSON file")
            self.showStatusBarErrorMessage("can't find 'header' section in JSON file")
            return

        if not 'pages' in project:
            print("can't find 'pages' section in JSON file")
            self.showStatusBarErrorMessage("can't find 'pages' section in JSON file")
            return

        if not 'connections' in project:
            print("can't find 'connections' section in JSON file")
            self.showStatusBarErrorMessage("can't find 'connections' section in JSON file")
            return

        self.resetEditor()

        header = project['header']
        pagesData = project['pages']
        connectionsData = project['connections']

        if header['version'] > self.EDITOR_VERSION:
            print("incompatible versions")
            self.showStatusBarErrorMessage("incompatible versions")
            return

        # create pages
        listUpdateParentComponents = []
        for pageData in pagesData:
            page = PageWidget(self, pageData['name'])
            page.setNum(pageData['num'])
            self.pages.append(page)
            itemsData = pageData['items']
            scene = page.scene()

            for itemProp in itemsData:
                item = createGraphicsObjectByProperties(itemProp, True)
                if not item:
                    continue

                if item.type() == GROUP_TYPE and 'parentComponentId' in itemProp:
                    listUpdateParentComponents.append((item,
                                                       itemProp['parentComponentId']))
                scene.addGraphicsItem(item)
            scene.update()

        # actualize parent to sub components
        for (group, parentId) in listUpdateParentComponents:
            parentGroup = self.itemById(parentId)
            group.setParentComponentGroup(parentGroup)

        self.actualizePagesTabs()


        # actualize connections
        connLastId = 0
        for connData in connectionsData:
            linkPoint1 = self.itemById(connData['p1'])
            linkPoint2 = self.itemById(connData['p2'])
            conn = Connection(self, linkPoint1, linkPoint2)
            conn._id = connData['id']
            if conn.id() > connLastId:
                connLastId = conn.id()
            self.connectionsList.append(conn)
        Connection.lastId = connLastId + 1
        self.projectFileName = fileName

        self.update()



    def resetEditor(self):
        pagesCopy = []
        for page in self.pages:
            pagesCopy.append(page)

        for page in pagesCopy:
            page.remove()
        self.pages = []
        self.connectionsList = []
        self.actualizePagesTabs()


    def focusOutEvent(self, event):
        self.keyCTRL = False
        self.keyShift = False
        for page in self.pages:
            scene = page.scene()
            scene.keyShiftRelease()
            scene.keyCTRLRelease()


def editorPath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def componentsPath():
    return "%s/components" % editorPath()





class PageWidget(QWidget):
    def __init__(self, editor, name):
        QWidget.__init__(self)
        global page_last_id
        self._name = name
        scene = ElectroScene(editor)
        self._sceneView = ElectroSceneView(editor, scene)
        layout = QVBoxLayout(self)
        layout.addWidget(self._sceneView)
        self.editor = editor
        self.setLayout(layout)


    def setNum(self, num):
        scene = self.scene()
        scene.setNum(num)
        self.pageNum = num


    def num(self):
        return self.pageNum


    def name(self):
        return unicode(self._name)


    def setName(self, name):
        self._name = name


    def scene(self):
        return self._sceneView.scene()


    def sceneView(self):
        return self._sceneView


    def remove(self):
        scene = self.scene()
        scene.removeGraphicsItems(scene.graphicsItems())
        self.editor.pages.remove(self)


    def updateLinkPoints(self):
        scene = self.scene()
        linkPoints = scene.graphicsItems(LINK_TYPE)
        if linkPoints:
            for linkPoint in linkPoints:
                linkPoint.updateView(True)



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

        jsonProp = json.dumps(self._groupProperties, indent=2, sort_keys=True)
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


