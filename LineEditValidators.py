from PyQt4.QtGui import *
from ElectroEditor import *
from GraphicsItem import *


class DialogLineEditValidator(QValidator):
    invalidSymbols = "~!@#$%^&*()=+{}[]\/,"
    def __init__(self, editor, lineEdit=None):
        QValidator.__init__(self)
        if lineEdit:
            self.lineEdit = lineEdit
        self.editor = editor


    def setLineEdit(self, lineEdit):
        self.lineEdit = lineEdit


    def stringIsValid(self, string):
        for sym in string:
            if self.invalidSymbols.find(sym) >= 0:
                return False
        return True


    def sendOkMessage(self, message):
        self.lineEdit.setStyleSheet("color: green")
        self.editor.showStatusBarMessage(message)


    def sendError(self, message):
        self.lineEdit.setStyleSheet("color: red")
        self.editor.showStatusBarErrorMessage(message)


    def fixup(self, string):
        pass




class ComponentNameValidator(DialogLineEditValidator):
    def __init__(self, editor, lineEdit=None):
        DialogLineEditValidator.__init__(self, editor, lineEdit)


    def validate(self, string, pos):
        string = str(string)
        if not self.stringIsValid(string):
            return QValidator.Invalid, pos

        words = string.split()
        if len(words) != 2:
            self.sendError("Please enter component_name and component_prefix through a space")

        if len(words) > 1:
            prefix = words[1]
        else:
            prefix = ""
        name = words[0]

        for component in self.editor.componentList:
            if component.name() == name:
                self.sendError("component with name '%s' already exists" % name)
                return QValidator.Intermediate, pos

        self.sendOkMessage("OK! Component name:'%s' and prefix:'%s'" %
                           (name, prefix))
        return QValidator.Acceptable, pos




class YesNoValidator(DialogLineEditValidator):
    def __init__(self, editor, lineEdit=None):
        DialogLineEditValidator.__init__(self, editor, lineEdit)


    def validate(self, string, pos):
        string = str(string).lower()
        if (string != 'yes' and string != 'y' and
            string != 'no' and string != 'n'):
            self.sendError("Enrer Yes or No")
            return QValidator.Intermediate, pos

        self.sendOkMessage("OK")
        return QValidator.Acceptable, pos




class EditGroupValidator(DialogLineEditValidator):
    def __init__(self, editor, group):
        DialogLineEditValidator.__init__(self, editor)
        self.group = group


    def validate(self, string, pos):
        string = str(string).upper()
        if not self.stringIsValid(string):
            return QValidator.Invalid, pos

        if not len(string):
            return QValidator.Acceptable, pos

        # string can not begin with digit
        if string.isdigit():
            return QValidator.Invalid, pos

        unpackedName = self.editor.unpackGroupIndexName(string)

        # space for after complete
        if string[-1] == ' ':
            if len(string) == 1:
                return QValidator.Invalid, pos

            if string[-2].isdigit():
                return QValidator.Invalid, pos

            if string[-2] == '.':
                indexName = self.editor.packGroupIndexName(unpackedName)
                parentGroup = self.editor.findGroupByIndexName(indexName, self.group)
                if not parentGroup:
                    self.sendError("parent component '%s' not exists" % indexName)
                    return QValidator.Invalid, pos
                prefix = "%s." % parentGroup.indexName()
                index = self.editor.findFreeSubComponentIndex(parentGroup)
            else:
                prefix = string[:-1]
                index = self.editor.findFreeComponentIndex(string[:-1])

            self.lineEdit.setText("%s%d" % (prefix, index))
            return QValidator.Invalid, pos

        # check for multiple name
        if string[-1].find('.') > 0:
            if not unpackedName[2]:
                self.sendError("Not complete")
                return QValidator.Intermediate, pos

            indexName = self.editor.packGroupIndexName(unpackedName[:-1])
            group = self.editor.findGroupByIndexName(indexName, self.group)
            if not group:
                self.sendError("Parent component '%s' not exists" % indexName)
                return QValidator.Intermediate, pos
            self.sendOkMessage("OK")
            return QValidator.Acceptable, pos

        # check for name's busyness
        group = self.editor.findGroupByIndexName(string, self.group)
        if group:
            self.sendOkMessage("component '%s' already exists! Compnent will be overwritten!" % string)
            return QValidator.Acceptable, pos

        self.sendOkMessage("OK")
        return QValidator.Acceptable, pos




class ConnectinValidator(DialogLineEditValidator):
    def __init__(self, editor):
        DialogLineEditValidator.__init__(self, editor)


    def validate(self, string, pos):
        validsymbols = "0123456789 "
        string = str(string)
        if not self.stringIsValid(string):
            return QValidator.Invalid, pos

        self.editor.resetSelectionItems()

        if not len(string):
            return QValidator.Intermediate, pos

        for i in range(len(string)):
            sym = string[i]
            if validsymbols.find(sym) < 0:
                 return QValidator.Invalid, i

        words = string.split()
        if len(words) != 2:
            self.sendError("Only two LinkPoints allowed")
            return QValidator.Intermediate, pos

        if words[0] == words[1]:
            self.sendError("LinkPoints is equal")
            return QValidator.Intermediate, pos

        linkPoints = []
        warning = False
        for w in words:
            itemId = int(w)
            item = self.editor.itemById(itemId)
            if not item:
                self.sendError("Item id:%d is not exist" % itemId)
                return QValidator.Intermediate, pos

            if item.type() != LINK_TYPE:
                self.sendError("Item id:%d is not LinkPoint" % itemId)
                return QValidator.Intermediate, pos
            linkPoint = item
            linkPoints.append(linkPoint)

            conn = self.editor.connectionByLinkPoint(linkPoint)
            if conn:
                warning = True
                self.sendOkMessage("LinkPoint id:%d already in connection %d" %
                                    (linkPoint.id(), conn.id()))


        if not warning:
            self.sendOkMessage("OK")

        self.editor.itemsAddToSelection(linkPoints)
        return QValidator.Acceptable, pos



class IntValidator(DialogLineEditValidator):
    def __init__(self, editor, range=None):
        DialogLineEditValidator.__init__(self, editor)
        QIntValidator.__init__(self)
        self._range = range


    def validate(self, string, pos):
        validsymbols = "0123456789"
        string = str(string)
        if not self.stringIsValid(string):
            return QValidator.Invalid, pos

        if not len(string):
            return QValidator.Intermediate, pos

        enteredInt = int(string)
        for i in self._range:
            if i == enteredInt:
                self.sendOkMessage("OK")
                return QValidator.Acceptable, pos

        self.sendError("Incorrect number")
        return QValidator.Intermediate, pos




