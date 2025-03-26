# FastFill is a Windows application built using Python and PyQt5,
# designed to easily manage and copy frequently used texts - such as emails, templates, and more.
# It allows you to easily copy these texts to your clipboard for fast and efficient pasting, saving you time and effort.
import subprocess
import tempfile
import webbrowser
import winreg

from plyer import notification
from pathlib import Path
import configparser
import os
import sys

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

from PyQt5.QtGui import QBrush, QColor, QIcon
from PyQt5.QtCore import QTimer, Qt, QSize, QPoint, QCoreApplication, QTranslator, QSettings
from PyQt5.QtWidgets import QDialog, QApplication, QSystemTrayIcon, QMenu, QAction, QInputDialog, QFrame, QLineEdit, \
    QVBoxLayout, QLabel, QProgressBar, QPushButton, QProgressDialog, QAbstractItemView
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox

from pyqttoast import Toast, ToastPreset, ToastPosition

import requests
import logging

from _internal.version import __version__


# New config file path in AppData
appData_path = Path(os.getenv("APPDATA")) / "FastFill"
config_file = appData_path / "FastFillConfig.ini"
settings_file = appData_path / "settings.ini"
log_file = appData_path / "FastFill_app.log"

# Old config file path (FastFill version 1.x) in Documents
documents_path = Path.home() / "Documents"
old_config_file = documents_path / "FastFillConfig.ini"

current_section = None

# Ensure the directory exists
if not appData_path.exists():
    logging.info(f"Creating directory: {appData_path}")
    appData_path.mkdir(parents=True, exist_ok=True)

if not log_file.exists():
    # You could open the file to create it or add initial logging if needed
    log_file.touch()  # This will create an empty log file

# Set up logging
logging.basicConfig(
    filename=log_file,  # Log file location
    level=logging.DEBUG,
    format='%(asctime)s - %(funcName)s - Line: %(lineno)d ---- %(levelname)s - %(message)s'
)

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

if not config_file.exists():
    logging.info(f"Config file does not exist, creating: {config_file}")
    config_file.touch()  # This will create an empty config file

if not settings_file.exists():
    logging.info(f"Config file does not exist, creating: {settings_file}")
    settings_file.touch()  # This will create an empty config file

config = configparser.ConfigParser()

try:
    # Now read the config (whether it was just created or already existed)
    config.read(config_file)
except Exception as e:
    logging.error(e)

# Save any new sections back to the file
try:
    with open(config_file, 'w') as f:
        config.write(f)
except Exception as e:
    logging.info(e)

logging.info("Starting FastFill application.")


def check_for_update():
    """
    Checks for updates by fetching the latest version info from GitHub version.json.
    Notifies the user if a new version is available.
    """

    settings_config = configparser.ConfigParser()
    settings_config.read(settings_file)

    logging.info("Checking for updates...")

    try:
        response = requests.get("https://raw.githubusercontent.com/PaulK6803/FastFill/main/version.json")
        response.raise_for_status()  # Ensure we catch HTTP errors
        data = response.json()

        latest_version = data.get("version")

        new_features = None

        # Check if the 'user' section exists and get the language value
        language_code = settings_config.get("User", "language",
                                            fallback="en")  # Default to 'en' if 'language' is not set
        # Determine the active language and get new features based on the language
        if language_code == "de":  # If the language is German
            new_features = data.get("new_features_de")
        elif language_code == "en":  # If the language is English
            new_features = data.get("new_features_en")

        if latest_version > __version__:
            logging.info(f"Current installed version: {__version__}")
            logging.info(f"New version available: {latest_version}")
            if Dialog.isVisible():
                updateWindow = QMessageBox(None)
                updateWindow.setWindowTitle(QCoreApplication.translate("UpdateWindow", "FastFill Update available"))
                updateWindow.setTextFormat(Qt.RichText)
                updateWindow.setText(QCoreApplication.translate("UpdateWindow",
                                                                f"<font size='4'><b>Version") + f" {latest_version} " + QCoreApplication.translate(
                    "UpdateWindow",
                    "is available.</b> <br>Would you like to download the update now?<br><br><br>"f"<b>What's new?</b> <br>") + f"{new_features}")

                updateWindow.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                reply = updateWindow.exec_()

                if reply == QMessageBox.StandardButton.Yes:
                    download_update()

                    # logging.info("Opening new webbrowser tab...")
                    # webbrowser.open_new_tab("https://github.com/PaulK6803/FastFill/releases")
                    # logging.info("Webbrowser tab opened")
                else:
                    pass
            else:
                pass
                # displayNotification("FastFill Update", f"Version {latest_version} is available.", 5)
        else:
            logging.info(f"Current installed version: {__version__}")
            logging.info(f"Github version: {latest_version}")
            logging.info("Already up to date.")
            return None
    except Exception as e:
        logging.error(f"Update check failed: {e}")
        return None


def download_update():
    """
        Downloads FastFillSetup.exe and installs it.
        """
    url = "https://github.com/PaulK6803/FastFill/releases/latest/download/FastFillSetup.exe"
    temp_dir = tempfile.gettempdir()
    setup_path = os.path.join(temp_dir, "FastFillSetup.exe")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024  # 1 KB
        downloaded_size = 0

        progress = QProgressDialog("Downloading update...", "Cancel", 0, total_size)
        progress.setWindowIcon(QIcon("_internal/Icon.ico"))
        progress.setWindowTitle("FastFill Update")

        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        with open(setup_path, "wb") as file:
            for chunk in response.iter_content(block_size):
                if progress.wasCanceled():
                    logging.info("Update download canceled.")
                    return

                file.write(chunk)
                downloaded_size += len(chunk)
                progress.setValue(downloaded_size)

        progress.close()

        logging.info(f"Downloaded FastFillSetup.exe to {setup_path}")

        # Execute the installer
        subprocess.Popen([setup_path], shell=True)
        sys.exit(0)  # Exit the application after launching the installer

    except Exception as e:
        logging.error(f"Failed to download update: {e}")


def install_update(installer_path):
    subprocess.Popen([installer_path], shell=True)  # Run installer
    sys.exit()  # Exit application


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

        config = configparser.ConfigParser()
        config.read(config_file)

        self.current_toast = None # Store the toast object of show_toast_notification function
        self.clear_clipboard_timer = None  # Store the QTimer object of button_copy_clicked function

        self.current_field_content = ""

        logging.info("setting up UI...")

        # Use QSettings with INI format
        self.settings = QSettings(str(settings_file), QSettings.IniFormat)

        # Check if it's the first run
        if self.settings.value("App/first_run", True, type=bool):  # Check if 'first_run' is True
            logging.info("Starting first time configuration")  # Log first-time run
            self.show_language_selection()  # Prompt user to select language
            self.settings.setValue("App/first_run", False)  # Mark first run as complete
            self.settings.sync()

        # Initialize the translator
        self.translator = QTranslator()  # Create translator object

        # Get saved language from QSettings
        lang_code = self.settings.value("User/language", "en")

        # Load translation based on saved language
        if lang_code == "de":  # If language is German
            self.translator.load("_internal/fastfill_de.qm")  # Load German translation
            logging.info("fastFill_de.qm language file loaded successfully")

            try:
                if not config.sections():  # If config is empty, initialize German sections
                    config.add_section("Kategorie 1")
                    config.set('Kategorie 1', 'item1_title', 'Beispiel Text')
                    config.set('Kategorie 1', 'item1_content', 'beispiel.mail@mail.de')

                    with open(config_file, 'w') as cfg:
                        config.write(cfg)
            except Exception as e:
                logging.error(f"Error with config: {e}")

        else:  # If language is English
            try:
                if not config.sections():  # If config is empty, initialize English sections
                    config.add_section("Category 1")
                    config.set('Category 1', 'item1_title', 'Example Text')
                    config.set('Category 1', 'item1_content', 'example.mail@mail.com')

                    with open(config_file, 'w') as cfg:
                        config.write(cfg)
            except Exception as e:
                logging.error(f"Error with config: {e}")

        # Install the translator to apply language
        app.installTranslator(self.translator)

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
            Dialog.setWindowIcon(QIcon("_internal/Icon.ico"))
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
            self.pushButtonAddEncTitle = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonAddEncTitle.setGeometry(QtCore.QRect(180, 2, 41, 41))
            self.pushButtonAddEncTitle.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonAddEncTitle.setStyleSheet("QPushButton {\n"
                                                  "    background-color: #3a3a3c;\n"
                                                  "    border: 0px solid;\n"
                                                  "    border-radius: 8px;\n"
                                                  "}")
            self.pushButtonAddEncTitle.setText("")
            self.pushButtonAddEncTitle.setIcon(QtGui.QIcon("_internal/IconAddEnctitle.png"))
            self.pushButtonAddEncTitle.setIconSize(QtCore.QSize(28, 28))
            self.pushButtonAddEncTitle.setCheckable(False)
            self.pushButtonAddEncTitle.setObjectName("pushButtonAddEncTitle")
            self.pushButtonRemoveTitle = QtWidgets.QPushButton(self.frame_4)
            self.pushButtonRemoveTitle.setGeometry(QtCore.QRect(220, 2, 41, 41))
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
            self.pushButtonRenameTitle.setGeometry(QtCore.QRect(260, 2, 41, 41))
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

            self.pushButtonEdit.setVisible(False)
            self.pushButtonEditConfirm.setVisible(False)
            self.pushButtonCopyValue.setVisible(False)
            self.labelShowcaseTitle.setVisible(True)
            self.lineEditShowcaseTitle.setVisible(False)

            self.populate_sidebar()

            self.pushButtonSettings.clicked.connect(lambda: self.show_settings_ContextMenu(
                self.pushButtonSettings.mapToGlobal(QPoint(0, self.pushButtonSettings.height()))))

            self.pushButtonCopyValue.clicked.connect(self.button_copy_clicked)  # type: ignore

            self.pushButtonAddCategory.clicked.connect(self.add_category)
            self.pushButtonRemoveCategory.clicked.connect(self.remove_category)
            self.pushButtonRenameCategory.clicked.connect(self.rename_category)
            self.pushButtonAddTitle.clicked.connect(self.add_title)
            self.pushButtonAddEncTitle.clicked.connect(self.add_encrypted_title)
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

            self.retranslateUi(Dialog)

            # Create the Tray Icon
            self.create_tray_icon(Dialog)

            self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
            self.listWidget.setDefaultDropAction(Qt.MoveAction)
            self.listWidget.setDragEnabled(True)
            self.listWidget.setAcceptDrops(True)

            self.listWidgetCategories.setDragDropMode(QAbstractItemView.InternalMove)
            self.listWidgetCategories.setDefaultDropAction(Qt.MoveAction)
            self.listWidgetCategories.setDragEnabled(True)
            self.listWidgetCategories.setAcceptDrops(True)

            self.listWidget.model().rowsMoved.connect(self.save_title_order)
            self.listWidgetCategories.model().rowsMoved.connect(self.save_category_order)
        except Exception as e:
            logging.error(e)
            QMessageBox.warning(Dialog, "FastFill Error",
                                QApplication.translate("setupUI", "An error occurred. Try restarting the application."))

        logging.info("UI initialized")

    def retranslateUi(self, Dialog):
        try:
            _translate = QtCore.QCoreApplication.translate
            Dialog.setWindowTitle(_translate("Dialog", "FastFill"))
            self.plainTextEdit.setPlaceholderText(
                _translate("Dialog", "Click on a value to display more information"))
            self.labelHeadline.setText(_translate("Dialog", "FastFill"))
            self.labelNoValuesHint.setText(_translate("Dialog", "No elements have been added yet"))
            self.pushButtonCopyValue.setText(_translate("Dialog", "Copy text"))
            self.pushButtonSettings.setText(_translate("Dialog", "Settings"))
            self.pushButtonHelp.setText(_translate("Dialog", "Help"))
            self.pushButtonEdit.setText(_translate("Dialog", "Edit"))
            self.pushButtonEditConfirm.setText(_translate("Dialog", "Confirm"))
            self.pushButtonAddCategory.setToolTip(
                _translate("Dialog", "Add category"))
            self.pushButtonRemoveCategory.setToolTip(
                _translate("Dialog", "Remove category"))
            self.pushButtonAddTitle.setToolTip(
                _translate("Dialog", "Add value/title"))
            self.pushButtonRemoveTitle.setToolTip(
                _translate("Dialog", "Remove value/title"))
            self.pushButtonRenameCategory.setToolTip(
                _translate("Dialog", "Rename category"))
            self.pushButtonRenameTitle.setToolTip(
                _translate("Dialog", "Rename value/title"))
            self.pushButtonAddEncTitle.setToolTip(
                _translate("Dialog", "Add encrypted value/title"))

        except Exception as e:
            logging.error(e)


    def show_language_selection(self):
        """ Show a message box asking the user to select a language. """
        try:
            msg = QMessageBox(None)
            msg.setWindowTitle("Welcome to FastFill!")
            msg.setIcon(QMessageBox.Information)
            msg.setTextFormat(Qt.RichText)  # Enables rich text
            msg.setText(
                "<b>Seems like you are running FastFill for the first time.</b><br> Please select your preferred language:")

            # Add buttons for language selection
            german_button = msg.addButton("German", QMessageBox.AcceptRole)
            english_button = msg.addButton("English", QMessageBox.AcceptRole)

            # Show the message box
            msg.exec_()

            # Determine which button was clicked and save the language
            if msg.clickedButton() == german_button:
                self.settings.setValue("User/language", "de")
                self.settings.sync()
            elif msg.clickedButton() == english_button:
                self.settings.setValue("User/language", "en")
                self.settings.sync()


        except Exception as e:
            logging.error(e)

    def setLanguage(self, lang_code):
        """Switch between different languages using QSettings."""
        try:
            # Store the selected language in QSettings
            self.settings.setValue("User/language", lang_code)
            self.settings.sync()

            # Load the appropriate translation file
            if lang_code == "de":
                self.translator.load("./_internal/fastfill_de.qm")
            # Add more languages as needed

            # Install the translator so that the app uses the selected language
            app.installTranslator(self.translator)

            # Restart the app to apply changes
            self.restart_app()

        except Exception as e:
            logging.error(f"Error setting language: {e}")

    def about(self):
        """Handle 'About' action."""

        # Rich-text content for About dialog (including EULA and License)
        about_text = """
            <h2>About FastFill</h2>
            <p><strong>FastFill</strong> is a Windows application built using Python and PyQt5, designed to easily manage and copy frequently used texts - such as emails, templates, and more. It allows you to easily copy these texts to your clipboard for fast and efficient pasting, saving you time and effort.</p>
            <br>
            <h3>License</h3>
            <p>This project is licensed under the <a href="https://github.com/PaulK6803/FastFill/tree/main?tab=License-1-ov-file" target="_blank">GNU GENERAL PUBLIC LICENSE</a><br>Copyright © 2007 Free Software Foundation (GPLv3).</p>
            <p> Icons by Icons8 - Icons used in this application are provided by <a href="https://icons8.com" target="_blank">Icons8</a>.</p>
            <br>
            <br>
            <h3>Privacy Policy and Disclaimer</h3>
            <p><a href="https://github.com/PaulK6803/FastFill/blob/main/Privacy_Policy_and_Disclaimer.md" target="_blank">https://github.com/PaulK6803/FastFill/blob/main/Privacy_Policy_and_Disclaimer.md</a></p>
            <br>
            <br>
            <h3>Version 1.5.0 coded by Paul Koch</h3>
            <p>If you have any questions or feedback, feel free to contact me:</p>
            <ul>
            <li><a href="https://github.com/PaulK6803" target="_blank">GitHub Profile: PaulK6803</a></li>
            <li><a href="https://github.com/PaulK6803/FastFill/discussions" target="_blank">GitHub Discussions: FastFill</a></li>
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
                self.listWidgetCategories.itemClicked.connect(
                    lambda item=section_item: self.on_section_item_click(item))

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

            open_action = QAction(QCoreApplication.translate("TrayIcon", "Open FastFill"), Dialog)
            open_action.triggered.connect(self.show_dialog)
            tray_menu.addAction(open_action)

            exit_action = QAction(QCoreApplication.translate("TrayIcon", "Exit FastFill"), Dialog)
            exit_action.triggered.connect(self.exit_application)
            tray_menu.addAction(exit_action)

            tray_menu.addSeparator()

            # Restart Action
            restart_action = QAction(QCoreApplication.translate("TrayIcon", "Restart FastFill"), Dialog)

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
        self.plainTextEdit.setPlaceholderText(QCoreApplication.translate("on_section_item_click",
                                                                         "Click on a value to display more information"))

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            # Update the current section based on the clicked item
            global current_section
            current_section = clicked_item.text()

            if isSectionEmpty(config, current_section):
                self.listWidget.clear()
                self.labelNoValuesHint.setText(QCoreApplication.translate("on_section_item_click",
                                                                          f"No values have been added to the selected category yet"))

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

            # Copy the content from QPlainTextEdit
            clipboard.setText(self.plainTextEdit.toPlainText())

            # Cancel the previous timer if it exists
            if self.clear_clipboard_timer:
                self.clear_clipboard_timer.stop()

            # Create a new QTimer that will clear the clipboard after 10 seconds
            self.clear_clipboard_timer = QTimer()
            self.clear_clipboard_timer.setSingleShot(True)
            self.clear_clipboard_timer.timeout.connect(lambda: clipboard.clear())
            self.clear_clipboard_timer.start(10000)  # 10 seconds

            if self.settings.value("User/show_copy_notification", True, type=bool):
                self.show_toast_notification(title="FastFill", text=QApplication.translate("ToastNotification", "The text has been copied to the clipboard"), duration=10000)
        except Exception as e:
            logging.error(e)

    def populate_list(self, section):

        try:
            self.listWidget.clear()

            config = configparser.ConfigParser()
            config.read(config_file)

            if isSectionEmpty(config, section):
                self.labelNoValuesHint.show()
                self.labelNoValuesHint.setText(
                    QCoreApplication.translate("populate_list", f"No values have been added to") + f" {section}")
            else:
                if section in config:
                    for key in config[section]:
                        if key.endswith("_title"):
                            config_value = config[section][key]
                            if config_value.endswith("_encrypted"):
                                config_value = config_value.replace("_encrypted", "")
                                config_value = config_value + " 🔒"
                            item = QtWidgets.QListWidgetItem(config_value)
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
            title = title.replace(" 🔒", "")
            content = ""
            is_encrypted = False  # to check if the content was originally encrypted

            for key in config[current_section]:
                config_value = config[current_section][key]  # The original value from config

                if key.endswith("_title") and config_value.replace("_encrypted", "") == title:
                    content_key = key.replace("_title", "_content")  # Get matching content key
                    content = config[current_section].get(content_key, "").strip()  # Fetch content, default to ""

                    self.labelShowcaseTitle.setText(title)

                    # Check if the original config value (before _encrypted removal) was encrypted
                    if config_value.endswith("_encrypted"):
                        is_encrypted = True

                    if not content.strip():  # Check if content is empty or ""
                        self.plainTextEdit.setPlaceholderText(
                            QCoreApplication.translate("update_fields", f"Click on 'Edit' to modify the content"))
                        return
                    else:
                        # If needed, decrypt content here
                        if is_encrypted:
                            self.pushButtonEdit.hide()
                            self.plainTextEdit.setPlaceholderText(
                                QCoreApplication.translate("update_fields",
                                                           f""))
                            # Ask for password
                            password, ok = QInputDialog.getText(Dialog, "Encryption Password",
                                                                QCoreApplication.translate("update_fields", "Enter the password to access this content:"),
                                                                QLineEdit.Password)
                            if not ok or not password.strip():
                                self.plainTextEdit.setPlaceholderText(
                                    QCoreApplication.translate("update_fields",
                                                               f"Click on the title again and enter the password to unlock the content"))
                                return
                            content = self.decrypt_data(password, content)  # Decrypt config value
                            if not content:
                                QMessageBox.critical(Dialog, "Wrong Password", QCoreApplication.translate("update_fields", "Wrong password for this content"))
                                self.plainTextEdit.setPlaceholderText(
                                    QCoreApplication.translate("update_fields",
                                                               f"Click on the title again and enter the password to unlock the content"))
                                return

                        self.plainTextEdit.setPlainText(content)
                        self.pushButtonEdit.show()
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
            self.plainTextEdit.setStyleSheet("border: 2px solid red;")
            self.current_field_content = self.plainTextEdit.toPlainText()

        else:
            self.plainTextEdit.setReadOnly(True)
            self.pushButtonEditConfirm.setVisible(False)
            self.pushButtonEdit.setVisible(True)
            self.plainTextEdit.setFrameShape(QFrame.NoFrame)
            self.plainTextEdit.setStyleSheet("")
            self.listWidget.setEnabled(True)
            self.listWidgetCategories.setEnabled(True)

            self.save_fields_content()

    def save_fields_content(self):
        """
        Saves the current content of QPlainTextEdit to the correct itemX_content in the config.
        Ensures that encrypted content remains encrypted and non-encrypted remains non-encrypted.
        """
        try:
            # Get the current text from QPlainTextEdit
            content = self.plainTextEdit.toPlainText()

            if content == self.current_field_content:
                return

            # Get the selected item from the listWidget
            selected_item = self.listWidget.currentItem()
            if not selected_item:
                return  # No item selected, nothing to save

            item_title = selected_item.text().replace("🔒", "").strip()  # Remove lock emoji if present

            # Get the selected category from listWidgetCategories
            selected_category_item = self.listWidgetCategories.selectedItems()
            if not selected_category_item:
                return  # No category selected, nothing to save

            category_name = selected_category_item[0].text().strip()  # Get the category name

            # Load the config
            config = configparser.ConfigParser()
            config.read(config_file)

            if category_name not in config.sections():
                return  # Category not found in config

            # Find the key corresponding to the title
            content_key = None
            is_encrypted = False  # Track if original content was encrypted

            for key, value in config[category_name].items():
                if key.endswith("_title"):
                    # Check for exact match (non-encrypted)
                    if value == item_title:
                        content_key = key.replace("_title", "_content")
                        break
                    # Check for encrypted match
                    elif value == item_title + "_encrypted":
                        if not content:
                            return
                        content_key = key.replace("_title", "_content")
                        is_encrypted = True
                        break

            if not content_key:
                return  # Content key not found, nothing to save

            # Encrypt if originally encrypted, otherwise save as plain text
            if is_encrypted:
                # Ask for password to encrypt the content
                password, ok = QtWidgets.QInputDialog.getText(
                    Dialog, "Encryption Password",
                    QCoreApplication.translate("saveFieldsContent", "Enter the same or a new password to secure this content:"),
                    QtWidgets.QLineEdit.Password
                )
                if not ok or not password.strip():
                    return  # User canceled encryption, do not save

                encrypted_content = self.encrypt_data(password, content)
                config.set(category_name, content_key, encrypted_content)
                # Save the updated config
                with open(config_file, 'w') as cfg:
                    config.write(cfg)
            else:
                # Save plain text
                config.set(category_name, content_key, content)
                # Save the updated config
                with open(config_file, 'w') as cfg:
                    config.write(cfg)

        except Exception as e:
            logging.error(f"Error saving content: {e}")


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
                action1 = QAction(QCoreApplication.translate("listWidget_ContextMenu", "Rename"),
                                  Dialog)  # Item-specific action
                action2 = QAction(QCoreApplication.translate("listWidget_ContextMenu", "Remove"),
                                  Dialog)  # Item-specific action
                action3 = QAction(QCoreApplication.translate("listWidget_ContextMenu", "Add"),
                                  Dialog)  # Item-specific action
                action1.triggered.connect(self.rename_title)
                action2.triggered.connect(lambda: self.remove_title(item.text))
                action3.triggered.connect(self.add_title)
                contextMenu.addAction(action1)
                contextMenu.addAction(action2)
                contextMenu.addSeparator()
                contextMenu.addAction(action3)

            # If the list itself (no item) is right-clicked
            else:
                action3 = QAction(QCoreApplication.translate("listWidget_ContextMenu", "Add"),
                                  Dialog)  # Action for the list widget
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
            report_bug_action = QAction(QCoreApplication.translate("help_ContextMenu", "Report Bug"), None)
            about_action = QAction(QCoreApplication.translate("help_ContextMenu", "About"), None)

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

    def show_settings_ContextMenu(self, pos):
        """Display the settings context menu."""
        try:

            menu = QMenu(None)

            # Language submenu
            language_menu = QMenu(QCoreApplication.translate("settings_ContextMenu", "Language"), None)

            # Add language options

            action_de = QAction(QCoreApplication.translate("settings_ContextMenu", "German"), None)
            action_de.setCheckable(True)
            action_de.triggered.connect(lambda: self.setLanguage("de"))
            action_en = QAction(QCoreApplication.translate("settings_ContextMenu", "English"), None)
            action_en.setCheckable(True)
            action_en.triggered.connect(lambda: self.setLanguage("en"))

            if self.settings.value("User/language", "en") == "de":
                action_de.setChecked(True)
            else:
                action_en.setChecked(True)

            language_menu.addAction(action_de)
            language_menu.addAction(action_en)

            # Other settings options
            start_with_windows_action = QAction(
                QCoreApplication.translate("settings_ContextMenu", "Start FastFill with Windows"), None)
            start_with_windows_action.setCheckable(True)

            # Load saved setting
            start_with_windows_action.setChecked(self.settings.value("App/start_with_windows", False, type=bool))

            # Connect toggle signal
            start_with_windows_action.triggered.connect(lambda checked: self.start_with_windows(checked, self.settings))

            start_minimized_action = QAction(
                QCoreApplication.translate("settings_ContextMenu", "Start FastFill Minimized"), None)
            start_minimized_action.setCheckable(True)
            start_minimized_action.setChecked(self.settings.value("App/start_minimized", False, type=bool))

            # Connect toggle signal
            start_minimized_action.triggered.connect(lambda checked: self.toggle_start_minimized(checked, self.settings))

            show_copy_notification_action = QAction(
                QCoreApplication.translate("settings_ContextMenu", "Show text copied Notification"), None)
            show_copy_notification_action.setCheckable(True)
            show_copy_notification_action.setChecked(self.settings.value("User/show_copy_notification", True, type=bool))

            if self.settings.value("User/show_copy_notification", True, type=bool):
                show_copy_notification_action.triggered.connect(lambda checked: self.settings.setValue("User/show_copy_notification", False))
            else:
                show_copy_notification_action.triggered.connect(lambda checked: self.settings.setValue("User/show_copy_notification", True))


            # Add actions to menu
            menu.addMenu(language_menu)
            menu.addAction(start_with_windows_action)
            menu.addAction(start_minimized_action)
            menu.addAction(show_copy_notification_action)

            # Show menu at the button's position
            menu.exec_(pos)
        except Exception as e:
            logging.error(e)

    def start_with_windows(self, enable, settings):
        """Enable or disable starting FastFill with Windows."""
        try:
            exe_path = os.path.abspath(sys.argv[0])  # Get the path of the running FastFill.exe
            registry_key = r"Software\Microsoft\Windows\CurrentVersion\Run"

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_key, 0, winreg.KEY_ALL_ACCESS) as key:
                if enable:
                    winreg.SetValueEx(key, "FastFill", 0, winreg.REG_SZ, exe_path)
                else:
                    try:
                        winreg.DeleteValue(key, "FastFill")
                    except FileNotFoundError:
                        pass  # If it doesn't exist, ignore it

            # Save setting
            settings.setValue("App/start_with_windows", enable)
            settings.sync()

        except Exception as e:
            logging.error(f"Failed to modify startup setting: {e}")

    def toggle_start_minimized(self, checked, settings):
        """Enable or disable starting FastFill minimized."""
        settings.setValue("App/start_minimized", checked)
        settings.sync()

    def rename_category(self):

        """
        Renames the selected category (section) and updates the INI configuration.
        """

        global current_section

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if current_section not in config.sections():
                QMessageBox.warning(Dialog, "Error",
                                    QCoreApplication.translate("rename_category",
                                                               "An error occurred. Please try restarting the application"))
                return

            # Show input dialog to ask for a new category name
            new_category_name, ok = QInputDialog.getText(Dialog, "FastFill",
                                                         QCoreApplication.translate("rename_category",
                                                                                    "New name for the category:"),
                                                         text=current_section)

            if ok and new_category_name:  # If user confirmed and entered a name
                # Check if the new name already exists
                if new_category_name in config.sections():
                    QMessageBox.warning(Dialog, "Error", QCoreApplication.translate("rename_category",
                                                                                    "A category with this name already exists."))

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
                QMessageBox.warning(Dialog, "Input Error", QCoreApplication.translate("remove_category",
                                                                                      "Please select a category to remove."))
                return

            # Den Text der ausgewählten Kategorie extrahieren
            category_to_remove = selected_item[0].text()

            # Konfiguration laden
            config = configparser.ConfigParser()
            config.read(config_file)

            # Prevent removing the last category
            if len(config.sections()) == 1:
                QMessageBox.warning(Dialog, "Error",
                                    QCoreApplication.translate("remove_category",
                                                               "The category cannot be removed. There must be at least one category present."))
                return

            # Überprüfen, ob die Kategorie existiert
            if category_to_remove not in config.sections():
                QMessageBox.warning(Dialog, "Error",
                                    QCoreApplication.translate("remove_category",
                                                               f"An error occurred. Please try restarting the application."))
                return

            # Show a confirmation dialog
            reply = QtWidgets.QMessageBox.question(
                Dialog, "Delete category?", QCoreApplication.translate("remove_category",
                                                                       f"Are you sure you want to remove the category") + f" \n\n{category_to_remove}",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)

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
            new_category, ok = QInputDialog.getText(Dialog, "New category", QCoreApplication.translate("add_category",
                                                                                                       "Name of the new category:"))

            # If user clicked OK and entered a valid name
            if ok and new_category:
                new_category = new_category.strip()  # Remove leading/trailing spaces

                # Check if category already exists
                if new_category in config.sections():
                    QMessageBox.warning(Dialog, "Category Exists", QCoreApplication.translate("add_category",
                                                                                              "A category with this name already exists."))
                    return

                # Add the new section to the config
                config.add_section(new_category)

                # Save the updated config to the file
                with open(config_file, 'w') as cfg:
                    config.write(cfg)

                self.populate_sidebar()
        except Exception as e:
            logging.error(e)

    def save_category_order(self):
        """ Saves the new order of categories (sections) to the INI file. """
        config = configparser.ConfigParser()
        config.read(config_file)

        # Get new category order from listWidget_2
        new_order = [self.listWidgetCategories.item(i).text() for i in range(self.listWidgetCategories.count())]

        # Recreate the config with new order
        new_config = configparser.ConfigParser()
        for section in new_order:
            new_config.add_section(section)
            for key, value in config[section].items():
                new_config.set(section, key, value)

        # Write back to file
        with open(config_file, 'w') as cfg:
            new_config.write(cfg)

    def save_title_order(self):
        """Saves the new order of items in the selected category to the INI file."""

        try:
            global current_section
            config = configparser.ConfigParser()
            config.read(config_file)

            keys = []
            for i in range(self.listWidget.count()):
                item_title = self.listWidget.item(i).text()

                # Check if the title ends with the lock emoji
                if item_title.endswith("🔒"):
                    item_title = item_title.replace(" 🔒", "_encrypted")  # Replace lock emoji with _encrypted

                keys.append(item_title)  # Add modified title to the list

            # Create a new ordered dictionary to store the updated key-value pairs
            new_section_data = {}

            # Iterate through the reordered keys from the QListWidget
            for index, key in enumerate(keys, 1):  # Start enumeration from 1 for consistency with item numbering
                # Generate new title and content keys based on their new positions
                title_key = f"item{index}_title"
                content_key = f"item{index}_content"

                # Find the original key that matches the current key value and ends with "_title"
                old_title_key = [
                    k for k in config[current_section]
                    if config[current_section][k] == key and k.endswith("_title")
                ]

                if old_title_key:  # If a matching key is found
                    # Find the corresponding content key by replacing "_title" with "_content"
                    old_content_key = old_title_key[0].replace("_title", "_content")

                    # Store the reordered keys and their values in the new dictionary
                    new_section_data[title_key] = config[current_section][old_title_key[0]]
                    new_section_data[content_key] = config[current_section][old_content_key]

            # At the end of the loop, new_section_data will contain the reordered key-value pairs

            # Update the section in the config with the new ordered dictionary
            config[current_section] = new_section_data

            # Save the updated config back to the file
            with open(config_file, "w") as cfg:
                config.write(cfg)

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
            QtWidgets.QMessageBox.warning(
                Dialog, "Error",
                QCoreApplication.translate("rename_title", "Please select a title from the list first.")
            )
            return

        old_title = selected_item.text().replace(" 🔒", "")  # Remove lock emoji if present
        is_encrypted = False  # To track if the content is encrypted

        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if current_section not in config.sections():
                QtWidgets.QMessageBox.warning(
                    Dialog, "Error",
                    QCoreApplication.translate("rename_title", "The current category was not found.")
                )
                return

            # Find the key for the selected title
            key_to_rename = None
            content_key = None
            original_config_value = None

            for key, value in config[current_section].items():
                if key.endswith("_title") and value.replace("_encrypted", "") == old_title:
                    key_to_rename = key
                    original_config_value = value  # Store the original config value
                    content_key = key.replace("_title", "_content")  # The corresponding content key
                    break

            if not key_to_rename:
                QtWidgets.QMessageBox.warning(
                    Dialog, "Error",
                    QCoreApplication.translate("rename_title", "Error renaming the title.")
                )
                return

            # Check if the original content is encrypted
            if original_config_value.endswith("_encrypted"):
                is_encrypted = True

            # Ask the user for a new name
            new_title, ok = QtWidgets.QInputDialog.getText(
                Dialog, "Rename",
                QCoreApplication.translate("rename_title", "New name for the title:"),
                text=old_title
            )

            if not ok or not new_title.strip():  # If cancelled or empty input
                return

            new_title = new_title.strip()  # Trim spaces

            # Check if the new title already exists
            existing_titles = [
                config[current_section][k].replace("_encrypted", "")
                for k in config[current_section] if k.endswith("_title")
            ]

            if new_title in existing_titles:
                QtWidgets.QMessageBox.warning(
                    Dialog, "Error",
                    QCoreApplication.translate("rename_title", "A title with this name already exists.")
                )
                return

            # Preserve encryption status: if the original title had encrypted content, keep _encrypted
            if is_encrypted:
                new_title += "_encrypted"

            # Rename the title in the config
            config[current_section][key_to_rename] = new_title

            # Save changes to the config
            with open(config_file, 'w') as cfg:
                config.write(cfg)

            # Update the GUI (list widget and showcase title)
            display_title = new_title.replace("_encrypted", "")  # Show title without "_encrypted" in the UI
            selected_item.setText(display_title + (" 🔒" if is_encrypted else ""))  # Add lock icon if encrypted
            self.labelShowcaseTitle.setText(display_title)

        except Exception as e:
            logging.error(f"Error in (rename title): {e}")
            QtWidgets.QMessageBox.warning(Dialog, "Error",
                                          QCoreApplication.translate("rename_title",
                                                                     "An error occurred. Please try restarting the application."))

    def remove_title(self, key):
        """
        Removes the selected item from listWidget and updates the INI configuration.
        """
        global current_section

        # Get the selected item from listWidget
        selected_item = self.listWidget.currentItem()
        if not selected_item:
            QtWidgets.QMessageBox.warning(Dialog, "Selection Error", QCoreApplication.translate("remove_title",
                                                                                                "Please select a value from the list first."))
            return

        item_title = selected_item.text()  # Get the title of the selected item
        if item_title.endswith("🔒"):
            item_title = item_title.replace(" 🔒", "")  # Remove lock emoji if present

        # Confirm deletion
        reply = QtWidgets.QMessageBox.question(Dialog, "remove value", QCoreApplication.translate("remove_title",
                                                                                                  "Are you sure you want to remove") + f" \n\n{item_title}",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            return  # Cancel deletion if user selects "No"

        # Load the config file
        try:
            config = configparser.ConfigParser()
            config.read(config_file)

            if current_section not in config.sections():
                QtWidgets.QMessageBox.warning(
                    Dialog, "Error",
                    QCoreApplication.translate("remove_title", "The current category was not found.")
                )
                return

            # Find the key index for the selected title
            key_index_to_remove = None
            for key, value in config[current_section].items():
                if key.endswith("_title") and value == item_title + "_encrypted":
                    key_index_to_remove = int(key.replace("item", "").replace("_title", ""))
                    break
                elif key.endswith("_title") and value == item_title:
                    key_index_to_remove = int(key.replace("item", "").replace("_title", ""))
                    break

            if key_index_to_remove is None:
                QtWidgets.QMessageBox.warning(
                    Dialog, "Error",
                    QCoreApplication.translate("remove_title", "Title not found.")
                )
                return

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
                # Preserve _encrypted suffix if needed for the title and content
                if content_value.endswith("_encrypted"):
                    config.set(current_section, f"item{new_index}_title", title_value + "_encrypted")
                else:
                    config.set(current_section, f"item{new_index}_title", title_value)

                # Save content with or without _encrypted as needed
                if content_value.endswith("_encrypted"):
                    config.set(current_section, f"item{new_index}_content", content_value)
                else:
                    config.set(current_section, f"item{new_index}_content", content_value)

            # Save changes to the config file
            with open(config_file, 'w') as cfg:
                config.write(cfg)

            # Remove item from listWidget
            self.listWidget.takeItem(self.listWidget.row(selected_item))

            logging.info(f"Removed Key / Title: {item_title} from {current_section}.")
        except Exception as e:
            logging.error(e)

    def add_title(self):
        global current_section
        # Load the existing configuration
        config = configparser.ConfigParser()
        config.read(config_file)

        # Ensure the selected section exists
        if current_section not in config.sections():
            QMessageBox.warning(Dialog, "Error",
                                QCoreApplication.translate("add_title",
                                                           "An error occurred. Try restarting the application."))
            return

        # Open a QInputDialog to get the new item's title
        new_title, ok = QInputDialog.getText(Dialog, "New value", QCoreApplication.translate("add_title",
                                                                                             "Name of the new title:"))

        # If user clicked OK and entered a valid title
        if ok and new_title:
            new_title = new_title.strip()  # Remove leading/trailing spaces

            # Check if the title already exists in the selected section
            existing_titles = [config[current_section][key] for key in config[current_section] if
                               key.endswith("_title")]

            if new_title in existing_titles:
                QMessageBox.warning(Dialog, "Value already exists",
                                    QCoreApplication.translate("add_title",
                                                               f"This title already exists in the category") + f"\n\n{current_section}.")
                return
            if new_title + "_encrypted" in existing_titles:
                QMessageBox.warning(Dialog, "Value already exists",
                                    QCoreApplication.translate("add_title",
                                                               f"This title already exists in the category") + f"\n\n{current_section}.")
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

    def add_encrypted_title(self):
        global current_section
        config = configparser.ConfigParser()
        config.read(config_file)

        if current_section not in config.sections():
            QMessageBox.warning(Dialog, "Error",
                                QCoreApplication.translate("add_encrypted_title", "An error occurred. Try restarting the application."))
            return

        # Get the new title
        new_title, ok = QInputDialog.getText(Dialog, "New Encrypted Value",
                                             QCoreApplication.translate("add_encrypted_title", "Name of the new encrypted title:"))
        if not ok or not new_title.strip():
            return

        new_title = new_title.strip()
        existing_titles = [config[current_section][key] for key in config[current_section] if key.endswith("_title")]

        if new_title in existing_titles:
            QMessageBox.warning(Dialog, "Value already exists",
                                QCoreApplication.translate("add_encrypted_title", "This title already exists in the currently selected category.") + f"\n\n{current_section}.")
            return

        if new_title + "_encrypted" in existing_titles:
            QMessageBox.warning(Dialog, "Value already exists",
                                QCoreApplication.translate("add_encrypted_title",
                                                           f"This title already exists in the currently selected category") + f"\n\n{current_section}.")
            return

        # Get the new content
        new_content, ok = QInputDialog.getText(Dialog, "New Encrypted Content",
                                               QCoreApplication.translate("add_encrypted_title", "Enter the content of") + f"\n\n{new_title}")
        if not ok or not new_content.strip():
            return

        # Ask for password
        password, ok = QInputDialog.getText(Dialog, "Encryption Password",
                                            QCoreApplication.translate("add_encrypted_title", "Enter a password to secure this content:"),
                                            QLineEdit.Password)
        if not ok or not password.strip():
            return

        item = QtWidgets.QListWidgetItem(new_title + " 🔒")  # Indicate encrypted item
        item.setSizeHint(QSize(100, 35))
        item.setTextAlignment(Qt.AlignCenter)
        self.listWidget.addItem(item)

        existing_keys = [key for key in config[current_section] if key.endswith("_title")]
        new_index = len(existing_keys) + 1

        title_key = f"item{new_index}_title"
        content_key = f"item{new_index}_content"

        # Encrypt content
        encrypted_content = self.encrypt_data(password, new_content)

        new_title = new_title + "_encrypted"
        config[current_section][title_key] = new_title
        config[current_section][content_key] = encrypted_content

        with open(config_file, 'w') as cfg:
            config.write(cfg)

        self.labelNoValuesHint.hide()
        logging.info(f"Added new encrypted Key / Title: {new_title} to {current_section}")

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
            sys.exit()
        except Exception as e:
            logging.error(e)

    def closeEvent(self, event):
        """
        Prevents the dialog from closing and hides it instead.
        """
        try:
            event.ignore()  # Prevent the dialog from closing
            Dialog.hide()  # Hide the dialog
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

    def show_toast_notification(self, title, text, duration):

        # If a toast is already showing, hide it before creating a new one
        if self.current_toast:
            self.current_toast.hide()  # Hide the existing toast


        self.current_toast = Toast(Dialog)
        self.current_toast.setDuration(duration=duration)  # in ms (5000 = 5 s)
        self.current_toast.setTitle(title=title) # title
        self.current_toast.setText(text=text) # text

        self.current_toast.setPosition(ToastPosition.BOTTOM_RIGHT) # position of toast notification on screen
        self.current_toast.setMaximumOnScreen(1) # maximum toast notifications shown at once
        self.current_toast.setResetDurationOnHover(False) # If duration bar resets on hover

        self.current_toast.applyPreset(ToastPreset.SUCCESS)  # Apply style preset
        self.current_toast.setBorderRadius(4)
        self.current_toast.setBackgroundColor(QColor('#ffffff'))
        self.current_toast.setDurationBarColor(QColor('#31b0ff'))

        self.current_toast.show()

    # Generate a strong encryption key from a password
    def derive_key(self, password: str, salt: bytes) -> bytes:
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            return kdf.derive(password.encode())
        except Exception as e:
            logging.error(e)

    # Encrypt datc
    def encrypt_data(self, password: str, plaintext: str) -> str:
        try:
            salt = os.urandom(16)  # Generate a new salt
            key = self.derive_key(password, salt)
            iv = os.urandom(16)  # Generate a random IV

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # Pad plaintext to be a multiple of 16 bytes (AES block size)
            padding_length = 16 - (len(plaintext) % 16)
            padded_plaintext = plaintext + chr(padding_length) * padding_length

            ciphertext = encryptor.update(padded_plaintext.encode()) + encryptor.finalize()

            return base64.b64encode(salt + iv + ciphertext).decode()  # Store salt, iv, and ciphertext together
        except Exception as e:
            logging.error(e)

    # Decrypt data
    def decrypt_data(self, password: str, encrypted_data: str) -> str:
        try:
            data = base64.b64decode(encrypted_data)
            salt, iv, ciphertext = data[:16], data[16:32], data[32:]

            key = self.derive_key(password, salt)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove padding
            padding_length = decrypted_padded[-1]
            return decrypted_padded[:-padding_length].decode()
        except Exception as e:
            logging.error(e)


class UpdateProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Updating FastFill")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)

        self.label = QLabel("Downloading update...", self)
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)

        settings = QSettings(str(settings_file), QSettings.IniFormat)
        start_minimized = settings.value("App/start_minimized", False, type=bool)

        Dialog = QDialog()
        ui = UiDialogMain()
        ui.setupUi(Dialog)
        ui.dialog = Dialog  # saves the Dialog-Object
        if not start_minimized:
            Dialog.show()
        logging.info("FastFill application started.")  #
        check_for_update()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(e)



