# -*- coding: utf-8 -*-

import rlcompleter, readline
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from ElectroEditor import *

readline.parse_and_bind('tab:complete')

app = QApplication(sys.argv)

electro = ElectroEditor(app)
electro.show()


