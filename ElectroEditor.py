from ElectroScene import *
from ElectroSceneView import *
from PyQt4.Qt import QWidget, QMainWindow, QLabel

last_page_id = 0

class PageWidget(QWidget):


    def __init__(self, editor, name):
        global last_page_id
        QWidget.__init__(self)
        self._name = name
        self.sceneView = ElectroSceneView(editor, ElectroScene(editor))
        layout = QVBoxLayout(self)
        layout.addWidget(self.sceneView)
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
        return self.sceneView.scene()





class ElectroEditor(QMainWindow):


    def __init__(self, app):
        QMainWindow.__init__(self)
        self.app = app
        self.keyCTRL = False
        self.pages = []

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

        self.tabWidget = QTabWidget()

        # make Line edit dialog
        self.lineEditDialog = QWidget()
        layout = QHBoxLayout(self.lineEditDialog)
        lineEdit = QLineEdit()
        lineEdit.show()
        inputMessage = QLabel()
        inputMessage.setText('bla:')
        layout.addWidget(inputMessage)
        layout.addWidget(lineEdit)
        self.lineEditDialog.hide()

        self.mainLayout.addWidget(self.tabWidget)
        self.mainLayout.addWidget(self.lineEditDialog)

        self.addPage("Page 1")
        self.addPage("Page 2")
        self.addPage("Page 3")
        self.addPage("Page 4")
        self.addPage("Page 5")
        self.setFocusPolicy(Qt.NoFocus)
        self.app.installEventFilter(self)


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

        # add new page
        if self.keyCTRL and key == 80:  # CTRL+P
            def dialogOnReturn():
                name = str(self.dialogLineEditLine.text())
                self.dialogLineEditHide()
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
                self.renamePage(page, name)

            self.dialogLineEditShow("Edit current page name:",
                                    dialogOnReturn,
                                    name)
            return

        # remove current page
        if self.keyCTRL and key == 68:  # CTRL+D
            def dialogOnReturn():
                page = self.currectPage()
                answer = str(self.dialogLineEditLine.text())
                self.dialogLineEditHide()
                if answer == 'yes' or answer == 'y':
                    self.detachPage(page)

            self.dialogLineEditShow("Remove current page?:",
                                    dialogOnReturn,
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
