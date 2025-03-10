import webbrowser
from plyer import notification

import requests
import logging
from PyQt5.QtCore import QTimer, Qt, QStandardPaths, QProcess
from PyQt5.QtWidgets import QDialog, QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5 import QtCore, QtGui, QtWidgets
import configparser
import os

from PyQt5.QtWidgets import QMessageBox
from requests.auth import HTTPBasicAuth

from _internal.FastFill_addRemove import UiDialogAddRemove as DialogAddRemove
from _internal.version import __version__

import sys


isDialogShown = True

documents_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
config_file = os.path.join(documents_path, "FastFillConfig.ini")
log_file = os.path.join(documents_path, "FastFill_app.log")

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
            app_icon="_internal/Icon.ico",  # Optional: Use your app icon
            timeout=timeout  # Notification disappears after 5 seconds
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
        response = requests.get("https://raw.githubusercontent.com/PaulK6803/FastFill/main/version.json",
                                auth=HTTPBasicAuth("PaulK6803",
                                                   "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"),
                                headers=headers)
        response.raise_for_status()  # Ensure we catch HTTP errors
        data = response.json()

        latest_version = data.get("version")
        new_features = data.get("new_features")

        if latest_version > __version__:
            logging.info(f"Current installed version: {__version__}")
            logging.info(f"New version available: {latest_version}")
            if Dialog.isVisible():
                reply = QMessageBox.question(None, "Update verfügbar",
                                             f"Version {latest_version} ist verfügbar. \nMöchtest du auf die Downloadseite weitergeleitet werden? \n\n\n"
                                             f"Was ist neu? \n"
                                             f"{new_features}",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                if reply == QMessageBox.StandardButton.Yes:
                    logging.info("Opening new webbrowser tab...")
                    webbrowser.open_new_tab("https://github.com/PaulK6803/FastFill/releases")
                    logging.info("Webbrowser tab opened")
                else:
                    pass
            else:
                displayNotification("FastFill Update", f"Version {latest_version} ist verfügbar.", 5)
        else:
            logging.info("Already up to date.")
            return None
    except Exception as e:
        logging.error(f"Update check failed: {e}")
        return None



try:
    config = configparser.ConfigParser()

    # Check if the config file exists
    if not os.path.exists(config_file):
        logging.info(f"Config file {config_file} not found, creating a new one.")
        config['Kategorie 1'] = {'item1': 'beispiel.mail@mail.de'}
        config['Kategorie 2'] = {'item1': 'Beispiel Text'}

        # Write the initial config to the file
        try:
            with open(config_file, 'w') as file:
                config.write(file)
            logging.info("New Config file created")
        except Exception as e:
            logging.error(e)

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

        self.firstSection = None
        self.firstSectionButton = None
        self.currentSectionButtonText = None

        self.buttons = []


        try:
            if not config.sections():
                logging.info(f"Config file empty, creating sections.")
                config['Kategorie 1'] = {'item1': 'beispiel.mail@mail.de'}
                config['Kategorie 2'] = {'item1': 'Beispiel Text'}
                try:
                    with open(config_file, 'w') as f:
                        config.write(f)
                except Exception as e:
                    logging.info(e)
            else:
                pass
        except Exception as e:
            logging.error(e)


        logging.info("setting up UI...")

        try:
            Dialog.closeEvent = self.closeEvent
            Dialog.setObjectName("Dialog")
            Dialog.setWindowIcon(QtGui.QIcon("_internal/Icon.ico"))
            Dialog.resize(550, 552)
            Dialog.setMinimumSize(QtCore.QSize(550, 552))
            Dialog.setMaximumSize(QtCore.QSize(550, 552))
            Dialog.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
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
            self.labelHeadline.setGeometry(QtCore.QRect(160, 10, 381, 51))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(14)
            font.setBold(True)
            font.setWeight(75)
            self.labelHeadline.setFont(font)
            self.labelHeadline.setStyleSheet("background-color:rgb(255, 255, 255);\n"
                                     "border: 2px solid #bbb;\n"
                                     "border-radius: 8px;")
            self.labelHeadline.setAlignment(QtCore.Qt.AlignCenter)
            self.labelHeadline.setObjectName("label")
            self.checkBox = QtWidgets.QCheckBox(Dialog)
            self.checkBox.setGeometry(QtCore.QRect(170, 380, 221, 17))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(11)
            self.checkBox.setFont(font)
            self.checkBox.setObjectName("checkBox")
            self.checkBox.hide()
            self.labelRestartHint = QtWidgets.QLabel(Dialog)
            self.labelRestartHint.setGeometry(QtCore.QRect(220, 210, 241, 61))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(11)
            self.labelRestartHint.setFont(font)
            self.labelRestartHint.setStyleSheet("color: red; background-color: rgb(255, 255, 255)")
            self.labelRestartHint.setWordWrap(True)
            self.labelRestartHint.setObjectName("label_2")
            self.pushButtonCopyValue = QtWidgets.QPushButton(Dialog)
            self.pushButtonCopyValue.setGeometry(QtCore.QRect(210, 500, 251, 41))
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
            self.pushButtonCopyValue.setObjectName("pushButton_5")
            self.listWidget = QtWidgets.QListWidget(Dialog)
            self.listWidget.setGeometry(QtCore.QRect(160, 70, 381, 291))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(10)
            self.listWidget.setFont(font)
            self.listWidget.setStyleSheet("background-color:rgb(255, 255, 255);\n"
                                                "border: 2px solid #bbb;\n"
                                                "border-radius: 8px;")
            self.listWidget.setTabKeyNavigation(True)
            self.listWidget.setProperty("showDropIndicator", False)
            self.listWidget.setMovement(QtWidgets.QListView.Static)
            self.listWidget.setLayoutMode(QtWidgets.QListView.SinglePass)
            self.listWidget.setViewMode(QtWidgets.QListView.ListMode)
            self.listWidget.setBatchSize(100)
            self.listWidget.setSelectionRectVisible(False)
            self.listWidget.setObjectName("listWidget")

            self.frameCategories = QtWidgets.QFrame(Dialog)
            self.frameCategories.setGeometry(QtCore.QRect(4, 70, 145, 421))
            self.frameCategories.setStyleSheet("QFrame{\n"
                                       "background-color:rgb(255, 255, 255);\n"
                                       "border: 2px solid #bbb;\n"
                                       "border-radius: 8px;\n"
                                       "}")
            self.frameCategories.setFrameShape(QtWidgets.QFrame.StyledPanel)
            self.frameCategories.setFrameShadow(QtWidgets.QFrame.Raised)
            self.frameCategories.setObjectName("frame_3")
            self.pushButtonEdit = QtWidgets.QPushButton(Dialog)
            self.pushButtonEdit.setGeometry(QtCore.QRect(4, 10, 145, 51))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(9)
            font.setBold(False)
            font.setItalic(True)
            font.setUnderline(False)
            font.setWeight(50)
            font.setStrikeOut(False)
            self.pushButtonEdit.setFont(font)
            self.pushButtonEdit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonEdit.setStyleSheet("QPushButton{\n"
                                            "background-color:rgb(255, 255, 255);\n"
                                            "border: 2px solid #bbb;\n"
                                            "border-radius: 8px;\n"
                                            "}\n"
                                            "\n"
                                            "QPushButton:hover {\n"
                                            "    background-color: #d6d6d6;\n"
                                            "}")
            self.pushButtonEdit.setObjectName("pushButton_6")
            self.pushButtonSettings = QtWidgets.QPushButton(Dialog)
            self.pushButtonSettings.setGeometry(QtCore.QRect(4, 500, 145, 41))
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(10)
            font.setBold(True)
            font.setWeight(75)
            self.pushButtonSettings.setFont(font)
            self.pushButtonSettings.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.pushButtonSettings.setStyleSheet("QPushButton{\n"
                                            "background-color:rgb(255, 255, 255);\n"
                                            "border: 2px solid #bbb;\n"
                                            "border-radius: 8px;\n"
                                            "}\n"
                                            "\n"
                                            "QPushButton:hover {\n"
                                            "    background-color: #d6d6d6;\n"
                                            "}\n"
                                            "\n"
                                            "QPushButton:pressed {\n"
                                            "    background-color: #c2c2c2;\n"
                                            "}")
            self.pushButtonSettings.setIconSize(QtCore.QSize(15, 15))
            self.pushButtonSettings.setCheckable(False)
            self.pushButtonSettings.setObjectName("pushButton_4")
            self.labelHeadline.raise_()
            self.checkBox.raise_()
            self.pushButtonCopyValue.raise_()
            self.listWidget.raise_()
            self.pushButtonEdit.raise_()
            self.pushButtonSettings.raise_()
            self.labelRestartHint.raise_()
            self.labelRestartHint.hide()

            self.retranslateUi(Dialog)

            self.populate_sidebar()

            self.pushButtonSettings.clicked.connect(self.show_settings_info_box)
            self.pushButtonCopyValue.clicked.connect(self.button_copy_clicked)  # type: ignore

            self.pushButtonEdit.clicked.connect(self.show_add_remove_dialog)

            QtCore.QMetaObject.connectSlotsByName(Dialog)

            # Create the Tray Icon
            self.create_tray_icon(Dialog)
        except Exception as e:
            logging.error(e)

        logging.info("UI initialized")

    def populate_sidebar(self):
        """
        Generates sidebar buttons dynamically for each section in the config.
        """

        try:
            # Durchlaufe alle Sections und erstelle einen Button für jede Section
            # Startposition für den ersten Button
            y_position = 10  # Initiale Y-Position
            button_width = 131  # Breite des Buttons
            button_height = 41  # Höhe des Buttons
            x_position = 7  # Feste X-Position

            for index, section in enumerate(config.sections()):
                # Dynamisch einen Button für jede Section erstellen
                section_button = QtWidgets.QPushButton(self.frameCategories)
                font = QtGui.QFont()
                font.setFamily("Arial")
                font.setPointSize(10)
                font.setBold(True)
                font.setWeight(75)
                section_button.setFont(font)
                if index == 0:
                    section_button.setStyleSheet("QPushButton{\n"
                                                 "background-color: rgb(255, 173, 78);\n"
                                                 "border: 2px solid #e69c46;\n"
                                                 "border-radius: 8px;\n"
                                                 "padding: 8px;\n"
                                                 "}")
                    self.populate_list(section=section)
                    self.firstSection = section
                    self.firstSectionButton = section_button
                else:
                    section_button.setStyleSheet("QPushButton{\n"
                                                 "background-color: #e0e0e0;\n"
                                                 "border: 2px solid #bbb;\n"
                                                 "border-radius: 8px;\n"
                                                 "}")
                section_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                section_button.setText(section)
                section_button.setGeometry(QtCore.QRect(x_position, y_position, button_width, button_height))
                self.buttons.append(section_button)
                section_button.clicked.connect(
                    lambda checked, s=section, btn=section_button: self.on_section_button_click(s, btn))
                y_position += button_height + 10  # Verschiebung nach unten (Höhe des Buttons + Abstand)
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
                global isDialogShown
                isDialogShown = True
        except Exception as e:
            logging.error(e)

    def show_dialog(self):
        """
        Show the dialog if it's not visible, or bring it to the front if it is.
        """

        try:
            if not Dialog.isVisible():
                Dialog.show()
                global isDialogShown
                isDialogShown = True
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
            global isDialogShown
            isDialogShown = False
        except Exception as e:
            logging.error(e)

    def on_section_button_click(self, section, clicked_button):
        try:
            self.currentSectionButtonText = clicked_button.text()
            config = configparser.ConfigParser()
            config.read(config_file)
            # Alle Buttons auf grau setzen
            for button in self.buttons:
                button.setStyleSheet("QPushButton{\n"
                                     "background-color: #e0e0e0;\n"
                                     "border: 2px solid #bbb;\n"
                                     "border-radius: 8px;\n"
                                     "}")
            # Den angeklickten Button auf orange setzen
            clicked_button.setStyleSheet("QPushButton{\n"
                                         "background-color: rgb(255, 173, 78);\n"
                                         "border: 2px solid #e69c46;\n"
                                         "border-radius: 8px;\n"
                                         "padding: 8px;\n"
                                         "}")

            logging.info(f"Button of section '{section}' was clicked.")

            if isSectionEmpty(config, section):
                self.listWidget.clear()
                self.labelRestartHint.setText(f"Es wurden noch keine Werte zu {section} hinzugefügt")
                self.labelRestartHint.show()
            else:
                self.labelRestartHint.hide()
                self.populate_list(clicked_button.text())
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

    def show_add_remove_dialog(self):
        # Create an instance of the first dialog and show it
        try:
            addRemoveDialog = QDialog()  # Create the dialog instance
            first_ui = DialogAddRemove()  # Create the UI from the first code
            first_ui.setupUi(addRemoveDialog)  # Set up the UI for the dialog
            Dialog.hide()
            addRemoveDialog.exec_()  # Show the dialog as a modal dialog and block execution of code until Dialog is closed

            config = configparser.ConfigParser()
            config.read(config_file)

            self.populate_sidebar()
            Dialog.show()
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
                self.labelRestartHint.show()
                self.labelRestartHint.setText(f"Es wurden noch keine Werte zu {section} hinzugefügt")
            else:
                if section in config:
                    for key in config[section]:
                        item = QtWidgets.QListWidgetItem(config[section][key])
                        self.listWidget.addItem(item)
                # # Populate listWidgetOther
                # if 'Sonstige' in config:
                #     for key in config['Sonstige']:
                #         self.listWidgetOther.addItem(config['Sonstige'][key])
        except ValueError as e:
            logging.error(f"Error populating lists: {e}")

    def retranslateUi(self, Dialog):
        try:
            _translate = QtCore.QCoreApplication.translate
            Dialog.setWindowTitle(_translate("Dialog", "FastFill"))
            self.labelHeadline.setText(_translate("Dialog", "FastFill"))
            self.checkBox.setText(_translate("Dialog", "Automatisches ausfüllen"))
            self.labelRestartHint.setText(_translate("Dialog", "Es wurden noch keine Werte hinzugefügt"))
            self.pushButtonCopyValue.setText(_translate("Dialog", "Text kopieren"))
            __sortingEnabled = self.listWidget.isSortingEnabled()
            self.listWidget.setSortingEnabled(False)
            self.listWidget.setSortingEnabled(__sortingEnabled)
            self.pushButtonEdit.setText(_translate("Dialog", "Editieren / Anpassen"))
            self.pushButtonSettings.setText(_translate("Dialog", "Einstellungen"))
        except Exception as e:
            logging.error(e)

    def restart_app(self):
        """
        Restarts the application by relaunching the .exe file.
        """
        try:
            logging.info("restarting Application via TrayIcon...")
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
        # Setting up the QTimer to call check_for_update every 60 seconds (1 minute)
        timer = QTimer()
        timer.timeout.connect(check_for_update)
        timer.start(3600000)  # 1 Hour
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(e)
