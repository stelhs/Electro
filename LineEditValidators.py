from PyQt4.QtGui import *
from ElectroEditor import *


class DialogLineEditValidator(QValidator):
    invalidSymbols = "~!@#$%^&*()=+{}[]\/,"
    def __init__(self, editor, lineEdit=None):
        QValidator.__init__(self)
        if lineEdit:
            self.lineEdit = lineEdit
        self.editor = editor


    def setLineEdit(self, lineEdit):
        self.lineEdit = lineEdit


    def symIsValid(self, sym):
        if len(sym) != 1:
            return False
        for invalidSym in self.invalidSymbols:
            if sym == invalidSym:
                return False
        return True


    def stringIsValid(self, string):
        for sym in string:
            if not self.symIsValid(sym):
                return False
        return True


    def sendOkMessage(self, message):
        self.lineEdit.setStyleSheet("color: green")
        self.editor.showStatusBarMessage(message)


    def sendError(self, message):
        self.lineEdit.setStyleSheet("color: red")
        self.editor.showStatusBarErrorMessage(message)




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
            return QValidator.Intermediate, pos

        name = words[0]
        prefix = words[1]
        for component in self.editor.componentList:
            if component.name() == name:
                self.sendError("component with name '%s' already exists" % name)
                return QValidator.Intermediate, pos

        self.sendOkMessage("OK! Component name:'%s' and prefix:'%s'" %
                           (name, prefix))
        return QValidator.Acceptable, pos


    def fixup(self, string):
        pass



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


    def fixup(self, string):
        pass



class EditGroupValidator(DialogLineEditValidator):
    def __init__(self, editor, group):
        DialogLineEditValidator.__init__(self, editor)
        self.group = group


    def validate(self, string, pos):
        string = str(string).upper()
        if not self.stringIsValid(string):
            return QValidator.Invalid, pos

        if not len(string):
            return QValidator.Intermediate, pos

        # string can not begin with digit
        if string.isdigit():
            return QValidator.Invalid, pos

        # string can not end with letters
        if len(string) > 1 and not string[-1].isdigit() and string[-2].isdigit():
                return QValidator.Invalid, pos

        # space for after complete
        if string[-1] == ' ':
            if len(string) == 1:
                return QValidator.Invalid, pos

            if string[-2].isdigit():
                return QValidator.Invalid, pos

            self.lineEdit.setText("%s%d" % (
                                  string[:-1],
                                  self.editor.findFreeComponentIndex(string[:-1])))
            return QValidator.Invalid, pos

        # check for completely entered name
        if not self.editor.unpackGroupIndexName(string):
            self.sendError("Not complete")
            return QValidator.Intermediate, pos

        # check for name's busyness
        res = self.editor.findGroupByIndexName(string, self.group)
        if res:
            self.sendError("component with name '%s' already exists" % string)
            return QValidator.Intermediate, pos

        self.sendOkMessage("OK")
        return QValidator.Acceptable, pos


    def fixup(self, string):
        pass






