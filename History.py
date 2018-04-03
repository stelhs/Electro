from GraphicsItem import *
from pprint import *


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


class ActionAddRemoveItems(HistoryAction):


    def __init__(self, scene, type, items):
        self.scene = scene
        self.items = items
        self.type = type


    def type(self):
        return 'addRemoveItems'


    def remove(self):
        self.scene.removeGraphicsItems(self.items)


    def add(self):
        self.scene.resetSelectionItems()
        for item in self.items:
            self.scene.addGraphicsItem(item)


    def undo(self):
        if self.type == 'add':
            print("undo AddItems")
            self.remove()
            return
        print("undo RemoveItems")
        self.add()


    def redo(self):
        if self.type == 'add':
            print("redo AddItems")
            self.add()
            return
        print("redo RemoveItems")
        self.remove()


    def __str__(self):
        if self.type == 'add':
            str = "ActionAddItems contains:\n"
        else:
            str = "ActionRemoveItems contains:\n"

        for item in self.items:
            str += "\t\t%s\n" % item
        return str


class ActionChangeItems(HistoryAction):


    def __init__(self, scene, items):
        self.scene = scene
        self.items = items
        print(len(self.items))
        self.itemsBeforeProperties = self.copyProperties(items)
        self.itemsAfterProperties = []


    def finish(self):
        changed = False
        for item in self.items:
            for prop in self.itemsBeforeProperties:
                if prop['id'] != item.id():
                    continue

                if not item.compareProperties(prop):
                    changed = True

        if not changed:
            print("not changed")
            return

        self.itemsAfterProperties = self.copyProperties(self.items)
        return True


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


class ActionPackUnpackGroup(HistoryAction):


    def __init__(self, scene, type, group):
        self.scene = scene
        self.type = type
        self.group = group


    def type(self):
        return 'addGroup'


    def pack(self):
        print("pack")
        self.scene.resetSelectionItems()
        self.scene.removeGraphicsItems(self.group.items())
        self.scene.addGraphicsItem(self.group)
        self.scene.itemAddToSelection(self.group)


    def unpack(self):
        self.group.markPointsHide()
        unpackedItems = self.scene.unpackGroup(self.group)
        self.scene.itemsAddToSelection(unpackedItems)


    def undo(self):
        if self.type == 'pack':
            print("undo packGroup")
            self.unpack()
            return
        print("undo unpackGroup")
        self.pack()


    def redo(self):
        if self.type == 'pack':
            print("redo packGroup")
            self.pack()
            return
        print("redo unpackGroup")
        self.unpack()


    def __str__(self):
        if self.type == 'pack':
            str = "ActionPackGroup id: %d contains:\n" % self.group.id()
        else:
            str = "ActionUnpackGroup id %d contains:\n" % self.group.id()
        for item in self.group.items():
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

        action = ActionAddRemoveItems(self.scene, 'add', items)
        if actions:
            actions.append(action)
            return

        actions = []
        actions.append(action)
        self.history.append(actions)
        return actions


    def removeItems(self, items, actions=None):
        if not len(items):
            return

        self.future = []

        action = ActionAddRemoveItems(self.scene, 'remove', items)
        if actions:
            actions.append(action)
            return

        actions = []
        actions.append(action)
        self.history.append(actions)
        return actions


    def changeItemsStart(self, items):
        self.changeItemsAction = ActionChangeItems(self.scene, items)


    def changeItemsFinish(self, actions=None):
        if not self.changeItemsAction:
            return

        if not self.changeItemsAction.finish():
            return

        self.future = []

        if actions:
            actions.append(self.changeItemsAction)
            return
        actions = []
        actions.append(self.changeItemsAction)
        self.history.append(actions)
        self.changeItemsAction = None
        return actions


    def packGroup(self, group, actions=None):
        if group.type() != GROUP_TYPE:
            return

        self.future = []

        action = ActionPackUnpackGroup(self.scene, 'pack', group)
        if actions:
            actions.append(action)
            return

        actions = []
        actions.append(action)
        self.history.append(actions)
        return actions


    def unpackGroup(self, group, actions=None):
        if group.type() != GROUP_TYPE:
            return

        self.future = []

        action = ActionPackUnpackGroup(self.scene, 'unpack', group)
        if actions:
            actions.append(action)
            return

        actions = []
        actions.append(action)
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
