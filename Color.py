from PyQt4.QtGui import *
from PyQt4.Qt import QPoint


class Color (QColor):
    usedColorsList = []
    def __init__(self, arg1, arg2=None, arg3=None, arg4=None):
        argType = arg1.__class__.__name__
        if argType == 'QColor':
            red = arg1.red()
            green = arg1.green()
            blue = arg1.blue()
            alpha = arg1.alpha()
        else:
            red = arg1
            green = arg2
            blue = arg3
            alpha = arg4 if arg4 else 255
        QColor.__init__(self, red, green, blue, alpha)
        Color.storeColor(self)


    @staticmethod
    def storeColor(color):
        exist = False
        for row in Color.usedColorsList:
            existColor, counter = row.items()[0]
            if existColor == color:
                exist = True
                break
        if exist:
            row[existColor] += 1
            return
        Color.usedColorsList.append({color: 1})


    @staticmethod
    def usedColorsPrint():
        for row in Color.usedColorsList:
            color, counter = row.items()[0]
            print("%s - %d" % (color, counter))


    @staticmethod
    def usedColors():
        colors = []
        for row in Color.usedColorsList:
            color, counter = row.items()[0]
            colors.append(color)
        return colors


    def __eq__(self, other):
        return (self.red() == other.red() and
                self.green() == other.green() and
                self.blue() == other.blue())


    def __str__(self):
        return "RGB: %d:%d:%d" % (self.red(),
                                  self.green(),
                                  self.blue())


    def remove(self):
        for row in Color.usedColorsList:
            color, counter = row.items()[0]
            if color == self:
                row[color] -= 1
                if not row[color]:
                    Color.usedColorsList.remove(row)
                    return


    def setColor(self, arg1, arg2=None, arg3=None, arg4=None):
        argType = arg1.__class__.__name__
        if argType == 'QColor':
            red = arg1.red()
            green = arg1.green()
            blue = arg1.blue()
            alpha = arg1.alpha()
        else:
            red = arg1
            green = arg2
            blue = arg3
            alpha = arg4 if arg4 else 255

        self.remove()
        QColor.setRed(self, red)
        QColor.setGreen(self, green)
        QColor.setBlue(self, blue)
        QColor.setAlpha(self, alpha)
        Color.storeColor(self)


