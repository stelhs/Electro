from GraphicsItems import *


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
        print("undo AddItems")
        for item in self.items:
            self.scene.removeGraphicsItemById(item.id())


    def redo(self):
        print("redo AddItems")
        self.scene.resetSelectionItems()
        for item in self.items:
            self.scene.addGraphicsItem(item)


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
        print("undo RemoveItems")
        for item in self.items:
            self.scene.addGraphicsItem(item)


    def redo(self):
        print("redo RemoveItems")
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
        print("undo ChangeItems")
        for properties in self.itemsBeforeProperties:
            for item in self.items:
                if item.id() == properties['id']:
                    item.setProperties(properties)


    def redo(self):
        print("redo ChangeItems")
        self.scene.resetSelectionItems()
        for properties in self.itemsAfterProperties:
            for item in self.items:
                if item.id() == properties['id']:
                    item.setProperties(properties)


    def __str__(self):
        str = "ActionChangeItems contains:\n"
        for item in self.items:
            str += "\t\t%s\n" % item
        return str


class ActionAddGroup(HistoryAction):


    def __init__(self, scene, group):
        self.scene = scene
        self.group = group
        self.items = group.items()


    def type(self):
        return 'addGroup'


    def undo(self):
        print("undo AddGroup")
        self.group.markPointsHide()
        self.scene.removeGraphicsItemById(self.group.id())


    def redo(self):
        print("redo AddGroup")
        self.scene.resetSelectionItems()
        self.scene.addGraphicsItem(self.group)
        self.group.addItems(self.items)


    def __str__(self):
        str = "ActionAddGroup contains:\n"
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


    def addItems(self, items, actions=None):
        if not len(items):
            return

        self.future = []

        if actions:
            actions.append(ActionAddItems(self.scene, items))
            return
        actions = []
        actions.append(ActionAddItems(self.scene, items))
        self.history.append(actions)
        return actions


    def removeItems(self, items, actions=None):
        if not len(items):
            return

        self.future = []

        if actions:
            actions.append(ActionRemoveItems(self.scene, items))
            return
        actions = []
        actions.append(ActionRemoveItems(self.scene, items))
        self.history.append(actions)
        return actions


    def changeItemsBefore(self, items):
        self.changeItemsAction = ActionChangeItems(self.scene, items)


    def changeItemsAfter(self, items, actions=None):
        if not self.changeItemsAction:
            return

        self.future = []

        self.changeItemsAction.setAfter(items)
        if actions:
            actions.append(self.changeItemsAction)
            return
        actions = []
        actions.append(self.changeItemsAction)
        self.history.append(actions)
        self.changeItemsAction = None
        return actions


    def addGroup(self, group, actions=None):
        if group.type() != GROUP_TYPE:
            return

        self.future = []

        if actions:
            actions.append(ActionAddGroup(self.scene, group))
            return
        actions = []
        actions.append(ActionAddGroup(self.scene, group))
        self.history.append(actions)
        return actions


    def undo(self):
        if not len(self.history):
            return

        actions = self.history.pop()
        self.future.append(actions)
        for action in reversed(actions):
            action.undo()


    def redo(self):
        if not len(self.future):
            return

        actions = self.future.pop()
        self.history.append(actions)
        for action in reversed(actions):
            action.redo()


    def __str__(self):
        str = "\nUndo history %d:\n" % len(self.history)
        for actions in self.history:
            str += "Action count: %d, list actions below:\n" % len(actions)
            for action in actions:
                str += "\t%s\n" % action

        str += "\nRedo history %d:\n" % len(self.future)
        for actions in self.future:
            str += "Action count: %d, list actions below:\n" % len(actions)
            for action in actions:
                str += "\t%s\n" % action

        return str
