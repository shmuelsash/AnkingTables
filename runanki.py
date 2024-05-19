#!/usr/bin/env python3
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
import sys
from PyQt5.QtWidgets import QApplication

try:
    import bazelfixes

    bazelfixes.fix_pywin32_in_bazel()
    bazelfixes.fix_extraneous_path_in_bazel()
except ImportError:
    pass

import aqt

def run_anki():
    app = QApplication(sys.argv)  # Create the QApplication instance

    if not os.environ.get("ANKI_IMPORT_ONLY"):
        aqt.run()

    sys.exit(app.exec_())  # Start the Qt event loop

if __name__ == "__main__":
    run_anki()