"""
 * This class organized Undo/Redo functionality
 *
 * Copyright (c) 2018 Michail Kurochkin
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 """

from ElectroEditor import *

class NavigationHistory():
    TIMEOUT = 600

    def __init__(self, editor):
        self.editor = editor
        self.history = []
        self.timer = QTimer()
        self.idx = 0

        def timeout():
            pos = editor.pos()
            if len(self.history) and pos == self.history[self.idx - 1]:
                return
            print("push new view position")

            if self.idx < len(self.history):
                self.history = self.history[:self.idx]
                self.idx = len(self.history)

            self.history.append(pos)
            self.idx += 1

        self.timer.timeout.connect(timeout)
        self.timer.start(self.TIMEOUT)


    def undo(self):
        if self.idx <= 1:
            return
        self.idx -= 1
        self.editor.setPos(self.history[self.idx - 1])


    def redo(self):
        if self.idx >= len(self.history):
            return
        self.idx += 1
        self.editor.setPos(self.history[self.idx - 1])


    def resetTimer(self):
        pass
        self.timer.start(self.TIMEOUT)


    def reset(self):
        self.history = []
        self.idx = 0


    def __str__(self):
        str = "\nNavigation history %d, idx = %d:\n" % (len(self.history), self.idx)
        for item in self.history:
            str += "%s\n" % item
        return str


