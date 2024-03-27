import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QFileDialog, QSplitter, QHBoxLayout
from PySide6.QtGui import QAction
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument
from PySide6.QtCore import QBuffer, QByteArray, QIODeviceBase
from PySide6.QtCore import Qt, Signal
import PySide6
import renderer
import tempfile

import os

dark_stylesheet = """
        QWidget {
            background-color: #333;
            color: #FFF;
        }
        QPushButton {
            background-color: #555;
            border: none;
            padding: 10px 20px;
        }
        QPushButton:hover {
            background-color: #777;
        }
    """


import sys
from PySide6.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QVBoxLayout, QMenu, QTabWidget

import logging
logging.basicConfig(level=logging.INFO)

from datetime import datetime

class Console(QTabWidget, logging.Handler):
  def __init__(self):
    super().__init__()
    super(logging.Handler, self).__init__()
    logging.getLogger().addHandler(self)
    self._console = CmdWidget()
    self._logs = QTextEdit()
    self._logs.setReadOnly(True)
    self.addTab(self._console, "Terminal")
    self.addTab(self._logs, "Logs")
  
  def emit(self, record):
    msg = self.format(record)
    self._logs.append(f"{datetime.now().strftime('%H:%M:%S')} [{record.levelname}] {record.message}")


import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit
from PySide6.QtCore import QProcess, QByteArray, QObject

import subprocess
import select

from queue import Queue, Empty
from threading import Thread

from collections import deque



# class LogHandler(logging.Handler, QObject):
#   log = Signal(str)
#   def __init__(self):
#     super(logging.Handler, self).__init__()
#     super(QObject, self).__init__()

#   def emit(self, record):
#     msg = self.format(record)
#     self.log.emit(msg)


class CmdWidget(QWidget):
  def __init__(self):
    super().__init__()
    self.initUI()

  def initUI(self):
    layout = QVBoxLayout(self)

    # TextEdit to display command output
    self._output = QTextEdit(self)
    self._output.setReadOnly(True)
    layout.addWidget(self._output)

    # LineEdit for entering commands
    self._input = QLineEdit(self)
    self._input.returnPressed.connect(self._command)
    layout.addWidget(self._input)
    self._process = subprocess.Popen(["cmd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True)
    self._process.stdin.write("echo\n")
    self._process.stdin.flush()

  def _command(self):
    command = self._input.text()
    self._input.clear()
    self._output.append(f"$ {command}")

    try:
      # self._process.stdin.write(bytes(command + "\n", encoding="UTF-8"))
      self._process.stdin.write(f"{command} & echo END_OF_COMMAND\n")
      self._process.stdin.flush()
      
      output = ""
      while line := self._process.stdout.readline(-1):
        if line == "END_OF_COMMAND\n":
          break
        output += line
      self._output.append(output)
    except Exception as e:
      print(f"Failed to send command: {e}")

  def _log(self, message):
    ...


class CustomFileSystemModel(QFileSystemModel):
  def __init__(self):
    super().__init__()

  def flags(self, index):
    default_flags = super().flags(index)
    return default_flags | Qt.ItemIsEditable

class FileExplorer(QTreeView):
  def __init__(self):
    super().__init__()
  
    self._model = CustomFileSystemModel()
    self.setModel(self._model)
    self.header().hide()
    for i in range(1, 4):
      self.hideColumn(i)
    self.customContextMenuRequested.connect(self.showContextMenu)
  
  def setFolder(self, folderPath: str):
    self._model.setRootPath(folderPath)
    self.setRootIndex(self._model.index(folderPath))
  
  def showContextMenu(self, position):
    index = self.indexAt(position)
    if index.isValid():
      menu = QMenu()
      createFileAction = QAction("Create File", self)
      createFileAction.triggered.connect(print("hello"))
      menu.addAction(createFileAction)
      menu.exec_(self.mapToGlobal(position))



class TextEdit(QTextEdit):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setUndoRedoEnabled(True)

  def keyPressEvent(self, event):
    if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
      if event.key() == Qt.Key.Key_V:
        self._pasteEvent(event)
        return
    super().keyPressEvent(event)

  def _pasteEvent(self, event):
    clipboard = QApplication.clipboard()
    mimeData = clipboard.mimeData()
    if mimeData.hasText():
      super().keyPressEvent(event)
    elif mimeData.hasImage():
      pixmap = clipboard.pixmap()
      imagePath = os.path.join("data", f"{hash(pixmap)}.png")
      if pixmap.save(imagePath):
        self.textCursor().insertText(f"[{imagePath}]")


class GUI(QMainWindow):
  def __init__(self, workdir: str=None):
    super().__init__()
    self._initUI()
    self._workdir = "workdir"
    self._filePath = None
    self._openFile(os.path.join("workdir", "main.txt"))
    self._explorer.setFolder(self._workdir)

  def _initUI(self):  
    self._explorer = FileExplorer()
    self._textEditor = TextEdit()
    self._pdfView = QPdfView()
    self._pdfView.setPageMode(self._pdfView.PageMode.MultiPage)
    self._pdfView.setZoomMode(self._pdfView.ZoomMode.FitToWidth)
    self._pdfDocument = QPdfDocument()
    self._pdfView.setDocument(self._pdfDocument)

    vSplitter = QSplitter()
    vSplitter.addWidget(self._explorer)
    vSplitter.addWidget(self._textEditor)
    vSplitter.addWidget(self._pdfView)
    vSplitter.setSizes([100, 400, 400])

    self._console = Console()

    hSplitter = QSplitter()
    hSplitter.setOrientation(Qt.Orientation.Vertical)
    hSplitter.addWidget(vSplitter)
    hSplitter.addWidget(self._console)
    hSplitter.setSizes([600, 200])

    self.setCentralWidget(hSplitter)

    self._createActions()
    self._createMenu()

    self.setWindowTitle("PaxillinWriter 0.0.1")
    self.setWindowState(Qt.WindowState.WindowMaximized)

    self._explorer.clicked.connect(lambda x: self._openFile(os.path.join(self._workdir, x.data())))

  def _createActions(self):
    self._newFileAction = QAction("&New", self)
    self._newFileAction.setShortcut("Ctrl+N")
    self._newFileAction.triggered.connect(self._newFile)

    self._openFileAction = QAction("&Open", self)
    self._openFileAction.setShortcut("Ctrl+O")
    self._openFileAction.triggered.connect(self._selectFile)

    self._saveFileAction = QAction("&Save", self)
    self._saveFileAction.setShortcut("Ctrl+S")
    self._saveFileAction.triggered.connect(self._saveFile)

    self._savePdfAction = QAction("&Save as PDF", self)
    self._savePdfAction.setShortcut("Ctrl+Shift+S")
    self._savePdfAction.triggered.connect(self._savePdf)

    self._renderFileAction = QAction("&Render", self)
    self._renderFileAction.setShortcut("Ctrl+Return")
    self._renderFileAction.triggered.connect(self._renderFile)

    self._openFolderAction = QAction("&OpenFolder", self)
    self._openFolderAction.setShortcut("Ctrl+Shift+O")
    self._openFolderAction.triggered.connect(self._openFolder)

  def _createMenu(self):
    menuBar = self.menuBar()
    fileMenu = menuBar.addMenu("&File")
    fileMenu.addAction(self._newFileAction)
    fileMenu.addAction(self._openFileAction)
    fileMenu.addAction(self._saveFileAction)
    fileMenu.addAction(self._savePdfAction)
    fileMenu.addAction(self._renderFileAction)
    fileMenu.addAction(self._openFolderAction)

    viewMenu = menuBar.addMenu("&View")
    action = QAction("&ShowExplorer", self)
    action.setShortcut("Ctrl+B")
    action.triggered.connect(lambda: self._showHideWidget(self._explorer))
    viewMenu.addAction(action)

    action = QAction("&ShowConsole", self)
    action.setShortcut("Ctrl+J")
    action.triggered.connect(lambda: self._showHideWidget(self._console))
    viewMenu.addAction(action)

  def _showHideWidget(self, widget):
    if widget.isVisible():
      widget.hide()
    else:
      widget.show()

  def _newFile(self):
    if self._filePath is not None:
      self._saveFile()
    self._filePath = None
    self._textEditor.clear()

  def _selectFile(self):
    filePath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*)")
    self._openFile(filePath)

  def _openFile(self, filePath: str):
    if os.path.exists(filePath) and os.path.isfile(filePath):
      if self._filePath is not None:
        self._saveFile()
      with open(filePath, "r") as file:
        self._textEditor.setPlainText(file.read())
      self._filePath = filePath
  
  def _openFolder(self):
    folderPath = QFileDialog.getExistingDirectory(self, "Open Folder", "")
    if folderPath:
      self._explorer.setFolder(folderPath)

  def _saveFile(self):
    if self._filePath is None:
      filePath, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*)")
    else:
      filePath = self._filePath
    if filePath:
      self._filePath = filePath
      with open(filePath, "w") as f:
        f.write(self._textEditor.toPlainText())
  
  def _savePdf(self):
    if self._filePath is not None:
      report = renderer.generate_pdf(self._textEditor.toPlainText())
      with open(os.path.splitext(self._filePath)[0] + ".pdf", "wb") as f:
        f.write(report)
  
  def _renderFile(self):
    self._saveFile()
    varPath = os.path.splitext(self._filePath)[0] + ".var"
    if os.path.exists(varPath):
      with open(varPath) as f:
        varFile = f.read()
      var = eval(varFile)
    report = renderer.generate_pdf(self._workdir, self._textEditor.toPlainText(), var)
    with open(os.path.join(self._workdir, "tmp.pdf"), "wb") as f:
      f.write(report)
    self._pdfDocument.load(os.path.join(self._workdir, "tmp.pdf"))


def main():
  app = QApplication(sys.argv)
  editor = GUI()
  editor.show()
  editor._renderFile()
  sys.exit(app.exec())


if __name__ == "__main__":
  main()
