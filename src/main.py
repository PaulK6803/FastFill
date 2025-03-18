# häufig genutzte Texte wie Emails und andere, in die Zwischenablage zum einfachen einfügen, kopieren.

import webbrowser

from PyQt5.QtGui import QBrush, QColor
from plyer import notification
from pathlib import Path

import requests
import logging
from PyQt5.QtCore import QTimer, Qt, QStandardPaths, QProcess, QSize
from PyQt5.QtWidgets import QDialog, QApplication, QSystemTrayIcon, QMenu, QAction, QInputDialog, QFrame
from PyQt5 import QtCore, QtGui, QtWidgets
import configparser
import os

from PyQt5.QtWidgets import QMessageBox
from requests.auth import HTTPBasicAuth

from _internal.version import __version__

import sys

# def is_smartfill_running():
#     for proc in psutil.process_iter(['pid', 'name']):
#         try:
#             # Check if process name matches 'SmartFill.exe'
#             if proc.info['name'] == 'SmartFill.exe':
#                 # If already running, show a message box with only an OK button
#                 QMessageBox.information(None, "Already Running",
#                                          "SmartFill läuft bereits im Hintergrund.",
#                                          QMessageBox.StandardButton.Ok)
#                 logging.info("SmartFill is already running. Exiting the application.")
#                 sys.exit(0)  # Exit the program
#         except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#             pass
#     return False


# New config file path (FastFill version 2.0.0) in AppData
appData_path = Path(os.getenv("APPDATA")) / "FastFill"
config_file = appData_path / "FastFillConfig200.ini"
log_file = appData_path / "FastFill_app.log"

# Old config file path (FastFill version 1.x) in Documents
documents_path = Path.home() / "Documents"
old_config_file = documents_path / "FastFillConfig.ini"

current_section = None

# Set up logging
logging.basicConfig(
    filename=log_file,  # Log file location
    level=logging.DEBUG,
    format='%(asctime)s - %(funcName)s - Line: %(lineno)d ---- %(levelname)s - %(message)s'
)

# Log file and new config file: check if they exist (if needed)
if not log_file.exists():
    # You could open the file to create it or add initial logging if needed
    log_file.touch()  # This will create an empty log file

# write log file
try:
    with open(log_file, "w"):
        pass
except Exception as e:
    logging.error(e)

# Check if the old config file exists and delete it
if old_config_file.exists():
    try:
        old_config_file.unlink()
        logging.info(f"Deleted old config file: {old_config_file}")
    except PermissionError:
        logging.error(f"Permission denied: Cannot delete {old_config_file}")
    except Exception as e:
        logging.error(f"Error deleting {old_config_file}: {e}")
else:
    logging.info(f"Old config file not found: {old_config_file}")


# Ensure the directory exists
if not appData_path.exists():
    logging.info(f"Creating directory: {appData_path}")
    appData_path.mkdir(parents=True, exist_ok=True)

if not config_file.exists():
    logging.info(f"Config file does not exist, creating: {config_file}")
    # Optionally create the new config file with initial settings
    config_file.touch()  # This will create an empty config file

logging.info("Starting FastFill application.")


def displayNotification(title, message, timeout):
    """
    Displays a desktop notification with the specified title, message, and timeout.

    Parameters:
    title (str): Notification title.
    message (str): Notification message.
    timeout (int): Duration the notification is visible.
    """

    try:
        notification.notify(
            title=title,
            message=message,
            app_name="FastFill",
            app_icon="_internal/Icon.ico",
            timeout=timeout
        )
    except Exception as e:
        logging.error(e)


def check_for_update():
    """
    Checks for updates by fetching the latest version info from GitHub version.json.
    Notifies the user if a new version is available.
    """

    logging.info("Checking for updates...")
    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }

    try:
        response = requests.get("https://raw.githubusercontent.com/PaulK6803/FastFill/main/version.json")
        response.raise_for_status()  # Ensure we catch HTTP errors
        data = response.json()

        latest_version = data.get("version")
        new_features = data.get("new_features_de")

        if latest_version > __version__:
            logging.info(f"Current installed version: {__version__}")
            logging.info(f"New version available: {latest_version}")
            if Dialog.isVisible():
                updateWindow = QMessageBox(None)
                updateWindow.setWindowTitle("FastFill Update verfügbar")
                updateWindow.setTextFormat(Qt.RichText)
                updateWindow.setText(
                    f"<font size='4'><b>Version {latest_version} ist verfügbar.</b> <br>Möchtest du auf die Downloadseite (https://github.com) weitergeleitet werden?<br><br><br>"
                    f"<b>Was ist neu?</b> <br>"
                    f"{new_features}")
                updateWindow.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                # reply = QMessageBox.question(None, "Update verfügbar",
                #                              f"Version {latest_version} ist verfügbar. \nMöchtest du auf die Downloadseite weitergeleitet werden? \n\n\n"
                #                              f"<b>Was ist neu?</b> \n"
                #                              f"<b>{new_features}</b>",
                #                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                reply = updateWindow.exec_()


                if reply == QMessageBox.StandardButton.Yes:
                    logging.info("Opening new webbrowser tab...")
                    webbrowser.open_new_tab("https://github.com/PaulK6803/FastFill/releases")
                    logging.info("Webbrowser tab opened")
                else:
                    pass
            else:
                pass
                # displayNotification("FastFill Update", f"Version {latest_version} ist verfügbar.", 5)
        else:
            logging.info(f"Current installed version: {__version__}")
            logging.info(f"Github version: {latest_version}")
            logging.info("Already up to date.")
            return None
    except Exception as e:
        logging.error(f"Update check failed: {e}")
        return None


config = configparser.ConfigParser()
try:
    # Now read the config (whether it was just created or already existed)
    config.read(config_file)
except Exception as e:
    logging.error(e)

# Create new sections, keys and values if config is empty
try:
    if not config.sections():
        logging.info(f"Config file empty, creating sections.")
        config['Kategorie 1'] = {'item1_title': 'Beispiel Text'}
        config.set('Kategorie 1', 'item1_content', 'beispiel.mail@mail.de')
        try:
            with open(config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            logging.info(e)
    else:
        pass
except Exception as e:
    logging.error(e)

# Save any new sections back to the file
try:
    with open(config_file, 'w') as f:
        config.write(f)
except Exception as e:
    logging.info(e)


def isSectionEmpty(config, section):
    if section in config:
        return not bool(config[section])  # True if section has no keys
    else:
        raise ValueError("Section is empty")


class UiDialogMain(object):
    """
    Manages the main UI setup for the FastFill dialog.
    """

    def setupUi(self, Dialog):

        logging.info("setting up UI...")

        try:
            Dialog.closeEvent = self.closeEvent
            Dialog.setObjectName("Dialog")
            Dialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
            Dialog.resize(1000, 600)
            Dialog.setMinimumSize(QtCore.QSize(1000, 600))
            Dialog.setMaximumSize(QtCore.QSize(1000, 600))
            font = QtGui.QFont()
            font.setFamily("Arial")
            Dialog.setFont(font)
            Dialog.setFocusPolicy(QtCore.Qt.NoFocus)
            Dialog.setStyleSheet("QDialog{\n"
                                 "background-color: rgb(255, 255, 255)\n"
                                 "}\n"
                                 "\n"
                                 "QWidget {\n"
                                 "    background-color: #f5f5f5;\n"
                                 "    color: #333;\n"
                                 "}\n"
                                 "")
            self.labelHeadline = QtWidgets.QLabel(Dialog)
            self.labelHeadline.setGeometry(QtCore.QRect(0, 40, 200, 40))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(12)
            font.setBold(True)
            font.setWeight(75)
            self.labelHeadline.setFont(font)
            self.labelHeadline.setStyleSheet("color: white;\n"
                                             "background-color: #3a3a3c;\n"
                                             "border: 0px solid #bbb;\n"
                                             "border-radius: 0px;")
            self.labelHeadline.setAlignment(QtCore.Qt.AlignCenter)
            self.labelHeadline.setObjectName("labelHeadline")
            self.labelNoValuesHint = QtWidgets.QLabel(Dialog)
            self.labelNoValuesHint.setGeometry(QtCore.QRect(300, 290, 241, 61))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(11)
            self.labelNoValuesHint.setFont(font)
            self.labelNoValuesHint.setStyleSheet("color: red; background-color: white;")
            self.labelNoValuesHint.setWordWrap(True)
            self.labelNoValuesHint.setObjectName("label_2")
            self.pushButtonCopyValue = QtWidgets.QPushButton(Dialog)
            self.pushButtonCopyValue.setGeometry(QtCore.QRect(700, 550, 250, 40))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(10)
            self.pushButtonCopyValue.setFont(font)
            self.pushButtonCopyValue.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonCopyValue.setStyleSheet("QPushButton {\n"
                                                   "    background-color: #e0e0e0;\n"
                                                   "    border: 2px solid #bbb;\n"
                                                   "    border-radius: 8px;\n"
                                                   "    padding: 8px;\n"
                                                   "}\n"
                                                   "\n"
                                                   "QPushButton:hover {\n"
                                                   "    background-color: #d6d6d6;\n"
                                                   "}\n"
                                                   "\n"
                                                   "QPushButton:pressed {\n"
                                                   "    background-color: #c2c2c2;\n"
                                                   "}")
            self.pushButtonCopyValue.setIconSize(QtCore.QSize(15, 15))
            self.pushButtonCopyValue.setCheckable(False)
            self.pushButtonCopyValue.setObjectName("pushButtonCopy")
            self.listWidget = QtWidgets.QListWidget(Dialog)
            self.listWidget.setGeometry(QtCore.QRect(200, 80, 450, 520))
            self.listWidget.setMinimumSize(QtCore.QSize(450, 520))
            self.listWidget.setMaximumSize(QtCore.QSize(450, 520))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(11)
            self.listWidget.setFont(font)
            self.listWidget.setStyleSheet("background-color:rgb(255, 255, 255);\n"
                                          "border: 0px solid;\n"
                                          "border-radius: 0px;")
            self.listWidget.setFrameShadow(QtWidgets.QFrame.Raised)
            self.listWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.listWidget.setTabKeyNavigation(True)
            self.listWidget.setProperty("showDropIndicator", False)
            self.listWidget.setMovement(QtWidgets.QListView.Static)
            self.listWidget.setLayoutMode(QtWidgets.QListView.SinglePass)
            self.listWidget.setViewMode(QtWidgets.QListView.ListMode)
            self.listWidget.setBatchSize(100)
            self.listWidget.setWordWrap(False)
            self.listWidget.setSelectionRectVisible(False)
            self.listWidget.setObjectName("listWidget")

            self.listWidgetCategories = QtWidgets.QListWidget(Dialog)
            self.listWidgetCategories.setGeometry(QtCore.QRect(0, 80, 200, 520))
            self.listWidgetCategories.setMinimumSize(QtCore.QSize(200, 520))
            self.listWidgetCategories.setMaximumSize(QtCore.QSize(200, 520))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(12)
            font.setBold(True)
            self.listWidgetCategories.setFont(font)
            self.listWidgetCategories.setStyleSheet("color: white; background-color: #4c4c4c;\n"
                                          "border: 0px solid;\n"
                                          "border-radius: 0px;\n")
            self.listWidgetCategories.setFrameShadow(QtWidgets.QFrame.Raised)
            self.listWidgetCategories.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.listWidgetCategories.setTabKeyNavigation(True)
            self.listWidgetCategories.setProperty("showDropIndicator", False)
            self.listWidgetCategories.setMovement(QtWidgets.QListView.Static)
            self.listWidgetCategories.setLayoutMode(QtWidgets.QListView.SinglePass)
            self.listWidgetCategories.setViewMode(QtWidgets.QListView.ListMode)
            self.listWidgetCategories.setBatchSize(100)
            self.listWidgetCategories.setWordWrap(False)
            self.listWidgetCategories.setSelectionRectVisible(False)
            self.listWidgetCategories.setObjectName("listWidgetCategories")

            self.frame_4 = QtWidgets.QFrame(Dialog)
            self.frame_4.setGeometry(QtCore.QRect(200, 40, 800, 40))
            self.frame_4.setStyleSheet("QFrame{\n"
                                       "background-color: #3a3a3c;\n"
                                       "border: 0px solid #bbb;\n"
                                       "border-radius: 0px;\n"
                                       "}")
            self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
            self.frame_4.setObjectName("frame_4")
            self.frame_5 = QtWidgets.QFrame(Dialog)
            self.frame_5.setGeometry(QtCore.QRect(0, 0, 1000, 40))
            self.frame_5.setStyleSheet("QFrame{\n"
                                       "background-color: white;\n"
                                       "border: 0px solid #bbb;\n"
                                       "border-radius: 0px;\n"
                                       "}")
            self.frame_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.frame_5.setFrameShadow(QtWidgets.QFrame.Raised)
            self.frame_5.setObjectName("frame_5")

            self.frame_6 = QtWidgets.QFrame(Dialog)
            self.frame_6.setGeometry(QtCore.QRect(650, 80, 2, 520))
            self.frame_6.setStyleSheet("QFrame{\n"
                                       "background-color:rgb(255, 255, 255);\n"
                                       "border: 2px solid #bbb;\n"
                                       "border-radius: 8px;\n"
                                       "}")
            self.frame_6.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.frame_6.setFrameShadow(QtWidgets.QFrame.Raised)
            self.frame_6.setObjectName("frame_6")

            self.labelShowcaseTitle = QtWidgets.QLabel(Dialog)
            self.labelShowcaseTitle.setGeometry(QtCore.QRect(670, 90, 220, 40))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(12)
            self.labelShowcaseTitle.setFont(font)
            self.labelShowcaseTitle.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
            self.labelShowcaseTitle.setObjectName("labelShowcaseTitle")
            self.lineEditShowcaseTitle = QtWidgets.QLineEdit(Dialog)
            self.lineEditShowcaseTitle.setGeometry(QtCore.QRect(670, 90, 220, 40))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(10)
            self.lineEditShowcaseTitle.setFont(font)
            self.lineEditShowcaseTitle.setText("")
            self.lineEditShowcaseTitle.setObjectName("lineEditShowcaseTitle")

            self.pushButtonEdit = QtWidgets.QPushButton(Dialog)
            self.pushButtonEdit.setGeometry(QtCore.QRect(910, 90, 80, 40))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(10)
            font.setBold(True)
            font.setWeight(75)
            self.pushButtonEdit.setFont(font)
            self.pushButtonEdit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonEdit.setStyleSheet("QPushButton {\n"
                                              "    color: white;\n"
                                              "    background-color: #31b0ff;\n"
                                              "    border: 0px solid;\n"
                                              "    border-radius: 8px;\n"
                                              "}\n"
                                              "\n"
                                              "QPushButton:hover {\n"
                                              "    background-color: #05a3ff;\n"
                                              "}")
            self.pushButtonEdit.setCheckable(False)
            self.pushButtonEdit.setObjectName("pushButtonEdit")

            self.pushButtonEditConfirm = QtWidgets.QPushButton(Dialog)
            self.pushButtonEditConfirm.setGeometry(QtCore.QRect(910, 90, 80, 40))
            self.pushButtonEditConfirm.setFont(font)
            self.pushButtonEditConfirm.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonEditConfirm.setStyleSheet("QPushButton {\n"
                                              "    color: white;\n"
                                              "    background-color: #31b0ff;\n"
                                              "    border: 0px solid;\n"
                                              "    border-radius: 8px;\n"
                                              "}\n"
                                              "\n"
                                              "QPushButton:hover {\n"
                                              "    background-color: #05a3ff;\n"
                                              "}")
            self.pushButtonEditConfirm.setCheckable(False)
            self.pushButtonEditConfirm.setObjectName("pushButtonEditConfirm")
            self.pushButtonSettings = QtWidgets.QPushButton(self.frame_5)
            self.pushButtonSettings.setGeometry(QtCore.QRect(0, 0, 100, 40))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(9)
            font.setBold(False)
            font.setItalic(False)
            font.setUnderline(False)
            font.setWeight(50)
            font.setStrikeOut(False)
            self.pushButtonSettings.setFont(font)
            self.pushButtonSettings.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonSettings.setStyleSheet("QPushButton{\n"
                                                  "color: black;\n"
                                                  "background-color: transparent;\n"
                                                  "border: 0px solid;\n"
                                                  "border-radius: 0px;\n"
                                                  "}\n"
                                                  "\n"
                                                  "QPushButton:hover {\n"
                                                  "    background-color: #d6d6d6;\n"
                                                  "}")
            self.pushButtonSettings.setObjectName("pushButtonSettings")

            self.pushButtonHelp = QtWidgets.QPushButton(self.frame_5)
            self.pushButtonHelp.setGeometry(QtCore.QRect(100, 0, 51, 40))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(9)
            font.setBold(False)
            font.setItalic(False)
            font.setUnderline(False)
            font.setWeight(50)
            font.setStrikeOut(False)
            self.pushButtonHelp.setFont(font)
            self.pushButtonHelp.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonHelp.setStyleSheet("QPushButton{\n"
                                              "color: black;\n"
                                              "background-color: transparent;\n"
                                              "border: 0px solid;\n"
                                              "border-radius: 0px;\n"
                                              "}\n"
                                              "\n"
                                              "QPushButton:hover {\n"
                                              "    background-color: #d6d6d6;\n"
                                              "}")
            self.pushButtonHelp.setObjectName("pushButtonHelp")

            self.pushButtonAddCategory = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonAddCategory.setGeometry(QtCore.QRect(0, 2, 41, 41))
            self.pushButtonAddCategory.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonAddCategory.setStyleSheet("QPushButton {\n"
                                                     "    background-color: #3a3a3c;\n"
                                                     "    border: 0px solid;\n"
                                                     "    border-radius: 8px;\n"
                                                     "}")
            self.pushButtonAddCategory.setText("")
            self.pushButtonAddCategory.setIcon(QtGui.QIcon("_internal/IconAddCategory.png"))
            self.pushButtonAddCategory.setIconSize(QtCore.QSize(28, 28))
            self.pushButtonAddCategory.setCheckable(False)
            self.pushButtonAddCategory.setObjectName("pushButtonAddCategory")
            self.pushButtonRemoveCategory = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonRemoveCategory.setGeometry(QtCore.QRect(40, 2, 41, 41))
            self.pushButtonRemoveCategory.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonRemoveCategory.setStyleSheet("QPushButton {\n"
                                                        "    background-color: #3a3a3c;\n"
                                                        "    border: 0px solid;\n"
                                                        "    border-radius: 8px;\n"
                                                        "}")
            self.pushButtonRemoveCategory.setText("")
            self.pushButtonRemoveCategory.setIcon(QtGui.QIcon("_internal/IconRemoveCategory.png"))
            self.pushButtonRemoveCategory.setIconSize(QtCore.QSize(28, 28))
            self.pushButtonRemoveCategory.setCheckable(False)
            self.pushButtonRemoveCategory.setObjectName("pushButtonRemoveCategory")
            self.pushButtonAddTitle = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonAddTitle.setGeometry(QtCore.QRect(140, 2, 41, 41))
            self.pushButtonAddTitle.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonAddTitle.setStyleSheet("QPushButton {\n"
                                                  "    background-color: #3a3a3c;\n"
                                                  "    border: 0px solid;\n"
                                                  "    border-radius: 8px;\n"
                                                  "}")
            self.pushButtonAddTitle.setText("")
            self.pushButtonAddTitle.setIcon(QtGui.QIcon("_internal/IconAddTitle.png"))
            self.pushButtonAddTitle.setIconSize(QtCore.QSize(28, 28))
            self.pushButtonAddTitle.setCheckable(False)
            self.pushButtonAddTitle.setObjectName("pushButtonAddTitle")
            self.pushButtonRemoveTitle = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonRemoveTitle.setGeometry(QtCore.QRect(180, 2, 41, 41))
            self.pushButtonRemoveTitle.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonRemoveTitle.setStyleSheet("QPushButton {\n"
                                                     "    background-color: #3a3a3c;\n"
                                                     "    border: 0px solid;\n"
                                                     "    border-radius: 8px;\n"
                                                     "}")
            self.pushButtonRemoveTitle.setText("")
            self.pushButtonRemoveTitle.setIcon(QtGui.QIcon("_internal/IconRemoveTitle.png"))
            self.pushButtonRemoveTitle.setIconSize(QtCore.QSize(28, 28))
            self.pushButtonRemoveTitle.setCheckable(False)
            self.pushButtonRemoveTitle.setObjectName("pushButtonRemoveTitle")
            self.pushButtonRenameCategory = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonRenameCategory.setGeometry(QtCore.QRect(80, 2, 41, 41))
            self.pushButtonRenameCategory.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonRenameCategory.setStyleSheet("QPushButton {\n"
                                                        "    background-color: #3a3a3c;\n"
                                                        "    border: 0px solid;\n"
                                                        "    border-radius: 8px;\n"
                                                        "}")
            self.pushButtonRenameCategory.setText("")
            self.pushButtonRenameCategory.setIcon(QtGui.QIcon("_internal/IconRenameCategory.png"))
            self.pushButtonRenameCategory.setIconSize(QtCore.QSize(28, 28))
            self.pushButtonRenameCategory.setCheckable(False)
            self.pushButtonRenameCategory.setObjectName("pushButtonRenameCategory")
            self.pushButtonRenameTitle = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonRenameTitle.setGeometry(QtCore.QRect(220, 2, 41, 41))
            self.pushButtonRenameTitle.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonRenameTitle.setStyleSheet("QPushButton {\n"
                                                     "    background-color: #3a3a3c;\n"
                                                     "    border: 0px solid;\n"
                                                     "    border-radius: 8px;\n"
                                                     "}")
            self.pushButtonRenameTitle.setText("")
            self.pushButtonRenameTitle.setIcon(QtGui.QIcon("_internal/IconRenameTitle.png"))
            self.pushButtonRenameTitle.setIconSize(QtCore.QSize(28, 28))
            self.pushButtonRenameTitle.setCheckable(False)
            self.pushButtonRenameTitle.setObjectName("pushButtonRenameTitle")

            self.plainTextEdit = QtWidgets.QPlainTextEdit(Dialog)
            self.plainTextEdit.setGeometry(QtCore.QRect(668, 170, 320, 340))
            self.plainTextEdit.setMinimumSize(QtCore.QSize(320, 340))
            self.plainTextEdit.setMaximumSize(QtCore.QSize(320, 340))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(10)
            font.setBold(False)
            font.setWeight(50)
            self.plainTextEdit.setFont(font)
            self.plainTextEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.plainTextEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
            self.plainTextEdit.setReadOnly(True)
            self.plainTextEdit.setPlainText("")
            self.plainTextEdit.setCursorWidth(1)
            self.plainTextEdit.setBackgroundVisible(False)
            self.plainTextEdit.setCenterOnScroll(False)
            self.plainTextEdit.setObjectName("plainTextEdit")
            self.plainTextEdit.setPlaceholderText("Klicke auf einen Wert, um weitere Infos anzeigen zu lassen")
            self.plainTextEdit.clear()
            self.frame = QtWidgets.QFrame(Dialog)
            self.frame.setGeometry(QtCore.QRect(650, 80, 350, 520))
            self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.frame.setObjectName("frame")
            self.frame_7 = QtWidgets.QFrame(self.frame_4)
            self.frame_7.setGeometry(QtCore.QRect(130, 0, 2, 40))
            self.frame_7.setStyleSheet("QFrame{\n"
                                       "background-color:rgb(255, 255, 255);\n"
                                       "border: 2px solid #bbb;\n"
                                       "border-radius: 8px;\n"
                                       "}")
            self.frame_7.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.frame_7.setFrameShadow(QtWidgets.QFrame.Raised)
            self.frame_7.setObjectName("frame_7")

            self.frame_6.raise_()
            self.labelHeadline.raise_()
            self.pushButtonCopyValue.raise_()
            self.listWidget.raise_()
            self.pushButtonEdit.raise_()
            self.pushButtonEditConfirm.raise_()
            self.pushButtonSettings.raise_()
            self.labelShowcaseTitle.raise_()
            self.labelNoValuesHint.raise_()
            self.labelNoValuesHint.hide()
            self.plainTextEdit.raise_()

            self.retranslateUi(Dialog)

            self.pushButtonEdit.setVisible(False)
            self.pushButtonEditConfirm.setVisible(False)
            self.pushButtonCopyValue.setVisible(False)
            self.labelShowcaseTitle.setVisible(True)
            self.lineEditShowcaseTitle.setVisible(False)

            self.populate_sidebar()

            self.pushButtonSettings.clicked.connect(self.show_settings_info_box)
            self.pushButtonCopyValue.clicked.connect(self.button_copy_clicked)  # type: ignore
            self.pushButtonAddCategory.clicked.connect(self.add_category)
            self.pushButtonRemoveCategory.clicked.connect(self.remove_category)
            self.pushButtonRenameCategory.clicked.connect(self.rename_category)
            self.pushButtonAddTitle.clicked.connect(self.add_title)
            self.pushButtonRemoveTitle.clicked.connect(lambda: self.remove_title(self.listWidget.currentItem()))
            self.pushButtonRenameTitle.clicked.connect(self.rename_title)

            self.pushButtonEdit.clicked.connect(lambda: self.edit_fields(editing=True))
            self.pushButtonEditConfirm.clicked.connect(lambda: self.edit_fields(editing=False))
            self.pushButtonHelp.clicked.connect(self.show_help_contextMenu)

            self.listWidget.itemClicked.connect(self.update_fields)
            # Enable right-click context menu for the list widget
            self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
            self.listWidget.customContextMenuRequested.connect(self.show_listWidget_contextMenu)

            QtCore.QMetaObject.connectSlotsByName(Dialog)

            # Create the Tray Icon
            self.create_tray_icon(Dialog)
        except Exception as e:
            logging.error(e)
            QMessageBox.warning(None, "FastFill Error",
                                "Ein Fehler ist aufgetreten. Bitte versuche die Anwendung neu zu starten.")

        logging.info("UI initialized")

    def retranslateUi(self, Dialog):
        try:
            _translate = QtCore.QCoreApplication.translate
            Dialog.setWindowTitle(_translate("Dialog", "FastFill"))
            self.labelHeadline.setText(_translate("Dialog", "FastFill"))
            self.labelNoValuesHint.setText(_translate("Dialog", "Es wurden noch keine Elemente hinzugefügt"))
            self.pushButtonCopyValue.setText(_translate("Dialog", "Text kopieren"))
            self.pushButtonSettings.setText(_translate("Dialog", "Einstellungen"))
            self.pushButtonHelp.setText(_translate("Dialog", "Hilfe"))
            self.pushButtonEdit.setText(_translate("Dialog", "Anpassen"))
            self.pushButtonEditConfirm.setText(_translate("Dialog", "Bestätigen"))
            self.pushButtonAddCategory.setToolTip(
                _translate("Dialog", "<html><head/><body><p>Kategorie hinzufügen</p></body></html>"))
            self.pushButtonRemoveCategory.setToolTip(
                _translate("Dialog", "<html><head/><body><p>Kategorie entfernen</p></body></html>"))
            self.pushButtonAddTitle.setToolTip(
                _translate("Dialog", "<html><head/><body><p>Wert / Titel hinzufügen</p></body></html>"))
            self.pushButtonRemoveTitle.setToolTip(
                _translate("Dialog", "<html><head/><body><p>Wert / Titel entfernen</p></body></html>"))
            self.pushButtonRenameCategory.setToolTip(
                _translate("Dialog", "<html><head/><body><p>Kategorie umbenennen</p></body></html>"))
            self.pushButtonRenameTitle.setToolTip(
                _translate("Dialog", "<html><head/><body><p>Wert / Titel umbenennen</p></body></html>"))
        except Exception as e:
            logging.error(e)

    def about(self):
        """Handle 'About' action."""

        # Rich-text content for About dialog (including EULA and License)
        about_text = """
            <h2>About FastFill</h2>
            <p><strong>FastFill</strong> is a Windows application built using Python and PyQt5, designed to easily manage and copy frequently used texts - such as emails, templates, and more. It allows you to easily copy these texts to your clipboard for fast and efficient pasting, saving you time and effort.</p>
            <br>
            <h3>License</h3>
            <p>This project is licensed under the <a href="https://github.com/PaulK6803/FastFill/tree/main?tab=License-1-ov-file" target="_blank">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a> (CC BY-NC-SA 4.0).</p>
            <p> Icons by Icons8 - Icons used in this application are provided by <a href="https://icons8.com" target="_blank">Icons8</a>.</p>
            <br>
            <br>
            <h3>Version 1.4.0 coded by Paul Koch</h3>
            <p>If you have any questions or feedback, feel free to contact me:</p>
            <ul>
                <li><a href="https://github.com/PaulK6803" target="_blank">GitHub Profile: PaulK6803</a></li>
                <li>Email: <a href="mailto:paul.koch_nds@t-online.de">paul.koch_nds@t-online.de</a></li>
            </ul>
            """

        # Create a QMessageBox with rich text
        msg_box = QMessageBox(None)
        msg_box.setWindowTitle("About FastFill")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(about_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()

    def populate_sidebar(self):
        """
        Generates sidebar items dynamically for each section in the config.
        """

        global current_section

        config = configparser.ConfigParser()
        config.read(config_file)

        try:
            # Clear the existing items in listWidgetCategories to prevent duplicates
            self.listWidgetCategories.clear()

            # List to store section items for later access
            section_items = []

            for section in config.sections():
                # Dynamically create a QListWidgetItem for each section
                section_item = QtWidgets.QListWidgetItem(section)
                section_item.setSizeHint(QSize(0, 40))
                section_item.setTextAlignment(Qt.AlignCenter)

                # Add the item to the listWidgetCategories
                self.listWidgetCategories.addItem(section_item)

                # Store the item in the section_items list
                section_items.append(section_item)

                # Connect item click signal to handle category selection
                self.listWidgetCategories.itemClicked.connect(lambda item=section_item: self.on_section_item_click(item))

            # Set initial section (if needed)
            if config.sections():
                current_section = config.sections()[0]
                self.populate_list(section=current_section)
                # Find the item corresponding to the first section
                for item in section_items:
                    if item.text() == current_section:
                        item.setBackground(QBrush(QColor("orange")))  # Set the background color using QBrush
                        item.setForeground(QColor("white"))  # Set the text color to white
                        self.listWidgetCategories.setCurrentItem(item)
                        break

        except Exception as e:
            logging.error(e)

    def show_settings_info_box(self):
        QMessageBox.information(None, "Information", "Diese Funktion wird in einer späteren Version hinzugefügt.")

    def create_tray_icon(self, Dialog):
        """
        Creates the tray icon for the application.
        """
        try:
            self.tray_icon = QSystemTrayIcon(QtGui.QIcon("_internal/Icon.ico"), parent=Dialog)
            self.tray_icon.setToolTip("FastFill")

            # Tray menu
            tray_menu = QMenu()

            # Add a non-interactive text item to the tray menu
            text_item = QAction(f"FastFill (Version {__version__})", Dialog)  # You can change the text as needed
            text_item.setEnabled(False)  # Makes it non-clickable
            tray_menu.addAction(text_item)

            tray_menu.addSeparator()

            open_action = QAction("FastFill öffnen", Dialog)
            open_action.triggered.connect(self.show_dialog)
            tray_menu.addAction(open_action)

            exit_action = QAction("FastFill beenden", Dialog)
            exit_action.triggered.connect(self.exit_application)
            tray_menu.addAction(exit_action)

            tray_menu.addSeparator()

            # Restart Action
            restart_action = QAction("FastFill neu starten", Dialog)
            restart_action.triggered.connect(self.restart_app)
            tray_menu.addAction(restart_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

            # Handle double-click on the tray icon to show the dialog
            self.tray_icon.activated.connect(self.on_tray_icon_double_click)
        except Exception as e:
            logging.error(e)

    def on_tray_icon_double_click(self, reason):
        """
        Show the dialog when the tray icon is double-clicked.
        """
        try:
            if reason == QSystemTrayIcon.DoubleClick:
                self.show_dialog()
        except Exception as e:
            logging.error(e)

    def on_section_item_click(self, clicked_item):
        # Clear the text fields and hide buttons when an item is clicked
        self.plainTextEdit.clear()
        self.labelShowcaseTitle.clear()
        self.pushButtonEdit.setVisible(False)
        self.pushButtonCopyValue.setVisible(False)
        self.plainTextEdit.setPlaceholderText("Klicke auf einen Wert, um weitere Infos anzeigen zu lassen")

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            # Update the current section based on the clicked item
            global current_section
            current_section = clicked_item.text()

            if isSectionEmpty(config, current_section):
                self.listWidget.clear()
                self.labelNoValuesHint.setText(f"Es wurden noch keine Werte zu {current_section} hinzugefügt")
                self.labelNoValuesHint.show()
            else:
                self.labelNoValuesHint.hide()
                self.populate_list(section=current_section)

            # Change colors for clicked and other items
            for index in range(self.listWidgetCategories.count()):
                item = self.listWidgetCategories.item(index)
                if item == clicked_item:
                    item.setBackground(QBrush(QColor("orange")))  # Set the clicked item to orange
                    item.setForeground(QColor("white"))  # Set the text color to white
                else:
                    item.setBackground(QBrush(QColor("#4c4c4c")))  # Set other items to gray
                    item.setForeground(QColor("white"))  # Set the text color to white

        except Exception as e:
            logging.error(e)

    def button_copy_clicked(self):
        try:
            clipboard = QApplication.clipboard()

            if self.listWidget.isVisible():
                currentItem = self.listWidget.currentItem()
                if currentItem:
                    clipboard.setText(currentItem.text())

            QTimer.singleShot(10000, lambda: clipboard.clear())
        except Exception as e:
            logging.error(e)

    def populate_list(self, section):
        """
        Populates comboBoxEmails and comboBoxOther using the INI file.
        """

        try:
            self.listWidget.clear()

            config = configparser.ConfigParser()
            config.read(config_file)

            if isSectionEmpty(config, section):
                self.labelNoValuesHint.show()
                self.labelNoValuesHint.setText(f"Es wurden noch keine Werte zu {section} hinzugefügt")
            else:
                if section in config:
                    for key in config[section]:
                        if key.endswith("_title"):
                            item = QtWidgets.QListWidgetItem(config[section][key])
                            item.setSizeHint(QSize(100, 35))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.listWidget.addItem(item)
        except ValueError as e:
            logging.error(f"Error populating lists: {e}")

    def update_fields(self, item):
        """Update QLabel and QPlainTextEdit when an item is selected."""

        self.pushButtonEdit.setVisible(True)
        self.pushButtonCopyValue.setVisible(True)
        self.plainTextEdit.clear()

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if current_section not in config.sections():
                logging.warning(f"Section '{current_section}' not found in config.")
                return

            # Find the corresponding title and content in the selected section
            title = item.text()
            content = ""

            for key in config[current_section]:
                if key.endswith("_title") and config[current_section][key] == title:
                    content_key = key.replace("_title", "_content")  # Get matching content key
                    content = config[current_section].get(content_key, "").strip()  # Fetch content, default to ""

                    self.labelShowcaseTitle.setText(title)

                    if not content.strip():  # Check if content is empty or ""
                        self.plainTextEdit.setPlaceholderText(f"Klicke auf 'Anpassen', um den Inhalt von {title} zu bearbeiten")
                        return
                    else:
                        self.plainTextEdit.setPlainText(content)
                        return

        except Exception as e:
            logging.error(f"Error in update_fields: {e}")

    def edit_fields(self, editing):

        if editing:
            self.listWidget.setEnabled(False)
            self.listWidgetCategories.setEnabled(False)
            self.plainTextEdit.setReadOnly(False)
            self.pushButtonEdit.setVisible(False)
            self.pushButtonEditConfirm.setVisible(True)
            self.plainTextEdit.setFrameShape(QFrame.Box)

        else:
            self.plainTextEdit.setReadOnly(True)
            self.pushButtonEditConfirm.setVisible(False)
            self.pushButtonEdit.setVisible(True)
            self.plainTextEdit.setFrameShape(QFrame.NoFrame)
            self.listWidget.setEnabled(True)
            self.listWidgetCategories.setEnabled(True)

            self.saveFieldsContent()

    def saveFieldsContent(self):
        """
        Saves the current content of QPlainTextEdit to the correct itemX_content in the config.
        """
        try:
            # Get the current text from QPlainTextEdit
            content = self.plainTextEdit.toPlainText()

            # Get the selected item from the listWidget
            selected_item = self.listWidget.currentItem()

            if selected_item:
                item_title = selected_item.text()  # Get the title of the item

                # Get the selected category from listWidgetCategories
                selected_category_item = self.listWidgetCategories.selectedItems()

                if selected_category_item:
                    category_name = selected_category_item[0].text()  # Get the category name

                    # Load the config
                    config = configparser.ConfigParser()
                    config.read(config_file)

                    # Ensure the category exists in the config
                    if category_name in config.sections():
                        # Find the key corresponding to the title (e.g., item1_title)
                        for key in config[category_name]:
                            if key.endswith("_title") and config[category_name][key] == item_title:
                                # Create the content key
                                content_key = key.replace("_title", "_content")

                                # Update the content in the config
                                config.set(category_name, content_key, content)

                                # Save the updated config
                                with open(config_file, 'w') as cfg:
                                    config.write(cfg)
                                break

        except Exception as e:
            logging.error(e)


    def show_listWidget_contextMenu(self, pos):
        try:
            # Get the item under the cursor
            item = self.listWidget.itemAt(pos)

            # Create the context menu
            contextMenu = QMenu(self.listWidget)

            # Apply hover effects using style sheet
            contextMenu.setStyleSheet("""
                        QMenu::item {
                            background-color: transparent;
                            color: black;
                            padding: 5px 10px;
                            border: none;
                        }
                        QMenu::item:hover {
                            background-color: #31b0ff;  /* Blue background on hover */
                            color: white;  /* Text color changes to white */
                        }
                        QMenu::item:selected {
                            background-color: #31b0ff;
                            color: white;
                        }
                        QMenu::item:disabled {
                            color: grey;  /* Disabled items appear grey */
                            background-color: transparent;
                            pointer-events: none;  /* Prevent interaction */
                        }
                    """)

            # If an item is right-clicked
            if item is not None:
                action1 = QAction("Umbenennen", Dialog)  # Item-specific action
                action2 = QAction("Entfernen", Dialog)  # Item-specific action
                action3 = QAction("Hinzufügen", Dialog)
                action1.triggered.connect(self.rename_title)
                action2.triggered.connect(lambda: self.remove_title(item.text))
                action3.triggered.connect(self.add_title)
                contextMenu.addAction(action1)
                contextMenu.addAction(action2)
                contextMenu.addSeparator()
                contextMenu.addAction(action3)

            # If the list itself (no item) is right-clicked
            else:
                action3 = QAction("Hinzufügen", Dialog)  # Action for the list widget
                action3.triggered.connect(self.add_title)
                contextMenu.addAction(action3)

            # Execute the menu at the clicked position
            contextMenu.exec_(self.listWidget.mapToGlobal(pos))

        except Exception as e:
            logging.error(e)

    def show_help_contextMenu(self):
        """Display the context menu when help button is clicked."""
        try:
            # Create context menu
            context_menu = QMenu(None)

            # Create actions for the context menu
            report_bug_action = QAction("Report Bug", None)
            about_action = QAction("About", None)

            # Open the GitHub bug reporting page in the default browser
            github_url = "https://github.com/PaulK6803/FastFill/issues"  # Replace with your bug reporting page URL

            # Connect actions to functions
            report_bug_action.triggered.connect(lambda: webbrowser.open(github_url))
            about_action.triggered.connect(self.about)

            # Add actions to the context menu
            context_menu.addAction(report_bug_action)
            context_menu.addAction(about_action)

            # Show context menu at the position of the button
            context_menu.exec_(self.pushButtonHelp.mapToGlobal(self.pushButtonHelp.rect().bottomLeft()))
        except Exception as e:
            logging.error(e)

    def rename_category(self):

        """
        Renames the selected category (section) from the frame and updates the INI configuration.
        """

        global current_section

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if current_section not in config.sections():
                QMessageBox.warning(None, "Error",
                                    "Ein Fehler ist aufgetreten. Bitte versuche die Anwendung neu zu starten")
                return

            # Show input dialog to ask for a new category name
            new_category_name, ok = QInputDialog.getText(None, "Kategorie umbenennen", "Neuer Name für die Kategorie:",
                                                         text=current_section)

            if ok and new_category_name:  # If user confirmed and entered a name
                # Check if the new name already exists
                if new_category_name in config.sections():
                    QMessageBox.warning(None, "Category Exists", "Kategorie mit diesem Namen existiert bereits.")
                    return

                # Rename the category in the config
                config.add_section(new_category_name)  # Add new section
                for key, value in config[current_section].items():
                    config[new_category_name][key] = value  # Copy the items to the new section

                # Remove the old section
                config.remove_section(current_section)

                # Save the updated config file
                with open(config_file, 'w') as cfg:
                    config.write(cfg)

                # Update the category button in listWidgetCategories
                for index in range(self.listWidgetCategories.count()):
                    item = self.listWidgetCategories.item(index)
                    if item.text() == current_section:
                        item.setText(new_category_name)
                        break

                self.populate_sidebar()
                self.labelNoValuesHint.hide()

        except Exception as e:
            logging.error(e)

    def remove_category(self):
        try:
            # Zuerst die ausgewählte Kategorie aus dem listWidget ermitteln
            selected_item = self.listWidgetCategories.selectedItems()

            if not selected_item:
                # Zeige eine Warnung an, wenn keine Kategorie ausgewählt wurde
                QMessageBox.warning(None, "Input Error", "Bitte wähle eine Kategorie zum Entfernen aus.")
                return

            # Den Text der ausgewählten Kategorie extrahieren
            category_to_remove = selected_item[0].text()

            # Konfiguration laden
            config = configparser.ConfigParser()
            config.read(config_file)

            # Prevent removing the last category
            if len(config.sections()) == 1:
                QMessageBox.warning(None, "Error", "Die Kategorie kann nicht entfernt werden. Es muss mindestens eine Kategorie vorhanden sein.")
                return

            # Überprüfen, ob die Kategorie existiert
            if category_to_remove not in config.sections():
                QMessageBox.warning(None, "Error", f"Ein Fehler ist aufgetreten. Bitte versuche die Anwendung neu zu starten")
                return

            # Show a confirmation dialog
            reply = QtWidgets.QMessageBox.question(
                None,
                "Kategorie löschen?",
                f"Möchtest du die Kategorie '{category_to_remove}' wirklich entfernen?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )

            # If the user chooses 'No', exit the function
            if reply == QtWidgets.QMessageBox.No:
                return

            # Die Kategorie aus der Konfiguration entfernen
            config.remove_section(category_to_remove)

            # Die aktualisierte Konfiguration zurück in die Datei schreiben
            with open(config_file, 'w') as cfg:
                config.write(cfg)

            self.populate_sidebar()
            self.labelNoValuesHint.hide()
        except Exception as e:
            logging.error(e)

    def add_category(self):
        try:
            # Load the existing configuration
            config = configparser.ConfigParser()
            config.read(config_file)

            # Open a QInputDialog to get the new category name
            new_category, ok = QInputDialog.getText(None, "Neue Kategorie", "Name der neuen Kategorie:")

            # If user clicked OK and entered a valid name
            if ok and new_category:
                new_category = new_category.strip()  # Remove leading/trailing spaces

                # Check if category already exists
                if new_category in config.sections():
                    QMessageBox.warning(None, "Category Exists", "Eine Kategorie mit diesem Namen existiert bereits.")
                    return

                # Add the new section to the config
                config.add_section(new_category)

                # Save the updated config to the file
                with open(config_file, 'w') as cfg:
                    config.write(cfg)

                self.populate_sidebar()
        except Exception as e:
            logging.error(e)

    def rename_title(self):
        """
            Renames the selected item in listWidget and updates the INI configuration.
            """
        global current_section

        # Get the selected item from the list
        selected_item = self.listWidget.currentItem()
        if not selected_item:
            QtWidgets.QMessageBox.warning(None, "Fehler", "Bitte wähle zuerst einen Wert aus der Liste.")
            return

        old_title = selected_item.text()  # Get the current title

        # Ask the user for a new name
        new_title, ok = QtWidgets.QInputDialog.getText(None, "Umbenennen", "Neuer Name für den Wert:", text=old_title)

        if not ok or not new_title.strip():  # If cancelled or empty input
            return

        new_title = new_title.strip()  # Trim spaces

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if current_section not in config.sections():
                QtWidgets.QMessageBox.warning(None, "Fehler", "Die aktuelle Kategorie wurde nicht gefunden.")
                return

            # Find the key for the selected title
            key_to_rename = None
            for key, value in config[current_section].items():
                if key.endswith("_title") and value == old_title:
                    key_to_rename = key
                    break

            if not key_to_rename:
                QtWidgets.QMessageBox.warning(None, "Fehler", "Fehler beim Umbenennen des Wertes.")
                return

            # Check if the new title already exists
            existing_titles = [config[current_section][k] for k in config[current_section] if k.endswith("_title")]
            if new_title in existing_titles:
                QtWidgets.QMessageBox.warning(None, "Fehler", "Ein Wert mit diesem Namen existiert bereits.")
                return

            # Rename the title in the config
            config[current_section][key_to_rename] = new_title

            # Save changes
            with open(config_file, 'w') as cfg:
                config.write(cfg)

            # Update the item in listWidget
            selected_item.setText(new_title)

        except Exception as e:
            logging.error(f"Error in action1 (rename title): {e}")
            QtWidgets.QMessageBox.warning(None, "Fehler", "Ein Fehler ist aufgetreten. Bitte versuche die Anwendung neu zu starten")

    def remove_title(self, key):
        """
        Removes the selected item from listWidget and updates the INI configuration.
        """
        global current_section

        # Get the selected item from listWidget
        selected_item = self.listWidget.currentItem()
        if not selected_item:
            QtWidgets.QMessageBox.warning(None, "Selection Error", "Bitte wähle zuerst einen Wert aus der Liste.")
            return

        item_title = selected_item.text()  # Get the title of the selected item

        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(
            None,
            "Wert entfernen",
            f"Möchtest du '{item_title}' wirklich entfernen?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.No:
            return  # Cancel deletion if user selects "No"

        # Load the config file
        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            # Ensure the section exists in the config
            if current_section not in config.sections():
                QtWidgets.QMessageBox.warning(None, "Error", "Kategorie nicht gefunden.")
                return

            # Find the key index for the selected title
            key_index_to_remove = None
            for key, value in config[current_section].items():
                if key.endswith("_title") and value == item_title:
                    key_index_to_remove = int(key.replace("item", "").replace("_title", ""))
                    break

            if key_index_to_remove is not None:
                # Remove the title and its corresponding content
                config.remove_option(current_section, f"item{key_index_to_remove}_title")
                config.remove_option(current_section, f"item{key_index_to_remove}_content")

                # Collect remaining titles and contents in order
                items = []
                for key, value in config[current_section].items():
                    if key.endswith("_title"):
                        index = int(key.replace("item", "").replace("_title", ""))
                        content_key = f"item{index}_content"
                        content_value = config[current_section].get(content_key,
                                                                    "")  # Get content (default to empty string)
                        items.append((index, value, content_value))

                # Sort by original index to maintain order
                items.sort()

                # Clear the section
                for key in list(config[current_section].keys()):
                    config.remove_option(current_section, key)

                # Rewrite the keys with updated numbering
                for new_index, (_, title_value, content_value) in enumerate(items, start=1):
                    config.set(current_section, f"item{new_index}_title", title_value)
                    config.set(current_section, f"item{new_index}_content", content_value)

                # Save changes to the config file
                with open(config_file, 'w') as cfg:
                    config.write(cfg)

                # Remove item from listWidget
                self.listWidget.takeItem(self.listWidget.row(selected_item))

                logging.info(f"Removed Key / Title: {item_title} from {current_section}.")

            else:
                QtWidgets.QMessageBox.warning(None, "Error",
                                              "Ein Fehler ist aufgetreten. Versuche die Anwendung neu zu starten.")
        except Exception as e:
            logging.error(e)

    def add_title(self):
        global current_section
        # Load the existing configuration
        config = configparser.ConfigParser()
        config.read(config_file)

        # Ensure the selected section exists
        if current_section not in config.sections():
            QMessageBox.warning(None, "Error",
                                "Ein Fehler ist aufgetreten. Bitte versuche die Anwendung neu zu starten.")
            return

        # Open a QInputDialog to get the new item's title
        new_title, ok = QInputDialog.getText(None, "Neuer Wert", "Gebe den Namen des neuen Wertes ein:")

        # If user clicked OK and entered a valid title
        if ok and new_title:
            new_title = new_title.strip()  # Remove leading/trailing spaces

            # Check if the title already exists in the selected section
            existing_titles = [config[current_section][key] for key in config[current_section] if
                               key.endswith("_title")]

            if new_title in existing_titles:
                QMessageBox.warning(None, "Wert existiert bereits",
                                    f"Dieser Wert existiert bereits in der Kategorie ({current_section}).")
                return

            # Add the title to the QListWidget
            item = QtWidgets.QListWidgetItem(new_title)
            item.setSizeHint(QSize(100, 35))
            item.setTextAlignment(Qt.AlignCenter)
            self.listWidget.addItem(item)

            # Generate a unique index
            existing_keys = [key for key in config[current_section] if key.endswith("_title")]
            new_index = len(existing_keys) + 1  # Example: item1, item2, item3...

            # Define keys for title and content
            title_key = f"item{new_index}_title"
            content_key = f"item{new_index}_content"

            # Save title and leave content empty
            config[current_section][title_key] = new_title
            config[current_section][content_key] = " "  # Default empty content

            # Save the updated configuration
            with open(config_file, 'w') as cfg:
                config.write(cfg)

            self.labelNoValuesHint.hide()

            logging.info(f"Added new Key / Title: {new_title} to {current_section}")

    def show_dialog(self):
        """
        Show the dialog if it's not visible, or bring it to the front if it is.
        """

        try:
            if not Dialog.isVisible():
                Dialog.show()
            else:
                Dialog.raise_()
        except Exception as e:
            logging.error(e)

    def exit_application(self):
        """
        Exit the application when the tray icon's exit action is triggered.
        """

        try:
            clipboard = QApplication.clipboard()

            clipboard.clear()
            logging.info("Exiting application via Tray Icon")
            QApplication.quit()
        except Exception as e:
            logging.error(e)

    def closeEvent(self, event):
        """
        Prevents the dialog from closing and hides it instead.
        """
        try:
            event.ignore()  # Prevent the dialog from closing
            Dialog.hide()  # Hide the dialog
            # displayNotification(title="FastFill", message="FastFill läuft im Hintergrund", timeout=4)
        except Exception as e:
            logging.error(e)

    def restart_app(self):
        """
        Restarts the application by relaunching the .exe file.
        """
        try:
            logging.info("restarting Application...")
            logging.info("opening new exe...")
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            logging.error(e)


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)

        # is_smartfill_running()

        Dialog = QDialog()
        ui = UiDialogMain()
        ui.setupUi(Dialog)
        ui.dialog = Dialog  # Speichert das Dialog-Objekt
        Dialog.show()
        logging.info("FastFill application started.")  #
        check_for_update()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(e)

