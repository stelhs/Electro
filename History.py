

class HistoryAction():


    def __init__(self):
        pass


    def type(self):
        return 'undefine'


    def copyProperties(self, items):
        ItemsProperties = []
        for item in items:
             ItemsProperties.append(item.properties())
        return ItemsProperties


class ActionAddItems(HistoryAction):


    def __init__(self, scene, items):
        self.scene = scene
        self.items = items


    def type(self):
        return 'addItems'


    def undo(self):
        for item in self.items:
            self.scene.removeGraphicsItemById(item.id())


    def redo(self):
        for item in self.items:
            self.scene.addItem(item)


    def __str__(self):
        str = "ActionAddItems contains:\n"
        for item in self.items:
            str += "\t\t%s\n" % item
        return str


class ActionRemoveItems(HistoryAction):


    def __init__(self, scene, items):
        self.scene = scene
        self.items = items


    def type(self):
        return 'removeItems'


    def undo(self):
        for item in self.items:
            self.scene.addItem(item)


    def redo(self):
        for item in self.items:
            self.scene.removeGraphicsItemById(item.id())


    def __str__(self):
        str = "ActionRemoveItems contains:\n"
        for item in self.items:
            str += "\t\t%s\n" % item
        return str


class ActionChangeItems(HistoryAction):


    def __init__(self, scene, items):
        self.scene = scene
        self.items = items
        self.itemsBeforeProperties = self.copyProperties(items)
        self.itemsAfterProperties = []


    def setAfter(self, items):
        self.itemsAfterProperties = self.copyProperties(items)


    def type(self):
        return 'changeItems'


    def undo(self):
        for properties in self.itemsBeforeProperties:
            item = self.scene.itemById(properties['id'])
            item.setProperties(properties)


    def redo(self):
        for properties in self.itemsAfterProperties:
            item = self.scene.itemById(properties['id'])
            item.setProperties(properties)


    def __str__(self):
        str = "ActionChangeItems\n\tcontains:\n\t"
        for item in self.items:
            str += "\t\t%s\n" % item
        return str


class History():


    def __init__(self, scene):
        self.scene = scene
        self.history = []
        self.future = []

        self.changeItemsAction = None
        pass


    def addItems(self, items):
        if not len(items):
            return

        self.future = []

        self.history.append(ActionAddItems(self.scene, items))
        pass


    def removeItems(self, items):
        if not len(items):
            return

        self.future = []

        self.history.append(ActionRemoveItems(self.scene, items))
        pass


    def changeItemsBefore(self, items):
        self.changeItemsAction = ActionChangeItems(self.scene, items)


    def changeItemsAfter(self, items):
        if not self.changeItemsAction:
            return

        self.future = []

        self.changeItemsAction.setAfter(items)
        self.history.append(self.changeItemsAction)
        self.changeItemsAction = None


    def undo(self):
        if not len(self.history):
            return

        action = self.history.pop()
        self.future.append(action)
        action.undo()


    def redo(self):
        if not len(self.future):
            return

        action = self.future.pop()
        self.history.append(action)
        action.redo()


    def __str__(self):
        str = "\nUndo history %d:\n" % len(self.history)
        for item in self.history:
            str += "%s\n" % item

        str += "\nRedo history %d:\n" % len(self.future)
        for item in self.future:
            str += "%s\n" % item

        return str
