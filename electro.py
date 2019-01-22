#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 * Main executable file of editor.
 *     option '-i' provide python console after run editor.
 *     Example: python3 -i electro.py -i
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

import rlcompleter, readline
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ElectroEditor import *

readline.parse_and_bind('tab:complete')


app = QApplication(sys.argv)
electro = ElectroEditor(app)
electro.show()

if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    electro.openProject(sys.argv[1])

if not (len(sys.argv) > 1 and sys.argv[1] == '-i'):
    sys.exit(app.exec_())
