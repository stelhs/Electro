# -*- coding: utf-8 -*-

import rlcompleter, readline
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ElectroEditor import *

readline.parse_and_bind('tab:complete')


app = QApplication(sys.argv)
electro = ElectroEditor(app)
electro.show()

if not (len(sys.argv) > 1 and sys.argv[1] == '-i'):
    sys.exit(app.exec_())
