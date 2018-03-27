from ElectroScene import *
from ElectroSceneView import *
from PyQt4.Qt import QWidget


class ElectroEditor(QWidget):


    def __init__(self, app):
        QWidget.__init__(self)
        self.app = app
        self.scene = ElectroScene(self)
        self.statusBar = QLabel()
        self.sceneView = ElectroSceneView(self, self.scene)
        self.sceneView.setMouseTracking(True)
        self.sceneView.setFixedSize(QSize(800, 400))
        self.scene.setSceneRect(0, 0, 1600, 1600)

        self.setWindowTitle("Electro editor")

        self.layout = QGridLayout(self)
        self.layout.addWidget(self.sceneView)
        self.layout.addWidget(self.statusBar)
        self.show()

        self.matrixStep = 10


    def keyPressEvent(self, event):
        key = event.key()
        print key
        if key == 16777216:  # ESC
            self.scene.setMode('select')
            return

        if key == 49:  # 1
            self.scene.setMode('drawLine')
            return

        self.scene.keyPressEvent(event)
        return
#        QWidget.keyPressEvent(self, event)


    def keyReleaseEvent(self, event):
        self.scene.keyReleaseEvent(event)
        return


    def toClipboard(self, text):
        self.app.clipboard().setText(text)


    def fromClipboard(self):
        return self.app.clipboard().text()


    def setCursorCoordinates(self, point):
        self.setTextStatusBar("x: %d, y: %d" % (point.x(), point.y()))


    def setTextStatusBar(self, text):
        self.statusBar.setText(text)
