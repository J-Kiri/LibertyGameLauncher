import ctypes
import os
import sys
import pickle
import configparser
import dropbox
import webbrowser

from PIL import Image

from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, QDir, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QSizePolicy,
    QStatusBar, QWidget, QFileDialog, QInputDialog, QLineEdit, QMessageBox)

button_play = Image.open('assets/BUTTON_play.png')
button_config = Image.open('assets/BUTTON_config.png')

logo = Image.open('assets/LOGO.png')

favorites_icon = Image.open('assets/ICON_Favoritos.png')
recents_icon = Image.open('assets/ICON_Recentes.png')
instaled_icon = Image.open('assets/ICON_Instalados.png')
menu_icon = Image.open('assets/ICON_Menu.png')

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1282, 722)
        MainWindow.setMinimumSize(QSize(994, 564))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")

        self.Menu_Bar = (
            QWidget(self.centralwidget)
            .setObjectName(u"Menu_Bar")
            .setGeometry(QRect(-1, 0, 1920, 71))
            .setStyleSheet(u"background-color: rgb(20, 20, 20);")
        )

        self.Games_display = (
            QWidget(self.centralwidget)
            .setObjectName(u"Games_display")
            .setGeometry(QRect(0, 59, 240, 1021))
            .setAutoFillBackground(False)
            .setStyleSheet(u"background-color: rgba(0, 0, 0, 158);")
        )

        self.logo = (
            QLabel(self.Menu_Bar)
            .setObjectName(u"logo")
            .setGeometry(QRect(50, 15, 121, 41))
            .setPixmap(QPixmap(logo))
            .setScaledContents(True)
        )


    def add_game(self):
        file_path = QFileDialog.getOpenFileName(self,
            QCoreApplication.translate("MainWindow", "Selecione o executável do jogo"),
            "/Desktop",
            QCoreApplication.translate("MainWindow", "Executáveis", "*.exe")
        )

        if file_path:
            icon_path = QFileDialog.getOpenFileName(self,
                QCoreApplication.translate("MainWindow", "Selecione o ícone do jogo"),
                "/Desktop",
                QCoreApplication.translate("MainWindow", "ícone", "*.png;*.jpg;*.jpeg;*.ico")
            )

            cover_path = QFileDialog.getOpenFileName(self,
                QCoreApplication.translate("MainWindow", "Selecione a capa do jogo"),
                "/Desktop",
                QCoreApplication.translate("MainWindow", "ícone", "*.png;*.jpg;*.jpeg")
            )

            save_path = QFileDialog.getExistingDirectory(self,
                QCoreApplication.translate("MainWindow", "Selecione a pasta que contém o save do jogo"),
                (),
                "/Desktop",
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            
            game_name, ok = QInputDialog.getText(self, "QInputDialog.getText()", "Insira o nome do jogo:", QLineEdit.Normal, QDir.home().dirName())
            if ok and game_name:
                game_name.setText(game_name)
                
            if not game_name:
                Messagebox = QMessageBox()
                Messagebox.setText("O nome do jogo não pode estar vazio.")
                Messagebox.exec()
                return

            game = {
                "game_name": game_name,
                "file_path": file_path,
                "icon_path": icon_path,
                "cover_path": cover_path,
                "save_path": save_path
            }

            self.games.append(game)
            self.display_games()
            self.save_games()

        #Main Frame
        self.game_details = QLabel(self.centralwidget)
        self.game_details.setObjectName(u"game_details")
        self.game_details.setGeometry(QRect(0, 0, 1600, 900))
        self.game_details.setPixmap(QPixmap('assets/background.png'))

    # def display_games(self):

    # def show_game_info(self):

    def launch_game(self):
        if hasattr(self, 'selected_game'):
            game = self.selected_game
            try:
                os.chdir(os.path.dirname(game["file_path"]))
                os.system(f'start "" "{game["file_path"]}"')
            except Exception as e:
                Messagebox = QMessageBox()
                Messagebox.setText("Não foi possível iniciar o jogo: {e}")
                Messagebox.exec()

    def save_games(self):
        try:
            with open("games.pickle", "wb") as file:
                pickle.dump(self.games, file)
        except Exception as e:
            Messagebox = QMessageBox()
            Messagebox.setText("Não foi possível salvar o jogo: {e}")
            Messagebox.exec()

    def load_games(self):
        try:
            with open("games.pickle", "rb") as file:
                return pickle.load(file)
        except (FileNotFoundError, EOFError):
            return []

    def remove_game(self):
        if hasattr(self, 'selected_game') and self.selected_game:
            confirm = QMessageBox().setText(f"Tem certeza que deseja remover '{self.selected_game['game_name']}'?")
            confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm.setDefaultButton(QMessageBox.No)
            ret = confirm.exec()

            if ret == QMessageBox.Yes:
                self.games.remove(self.selected_game)
                self.save_games()
                self.display_games()
            elif ret == QMessageBox.No:
                return

    def edit_game(self):
        if hasattr(self, 'selected_game') and self.selected_game:
            game_name, ok = QInputDialog.getText(self, "QInputDialog.getText()", "Insira o novo nome do jogo:", QLineEdit.Normal, QDir.home().dirName())
            if ok and game_name:
                self.selected_game["game_name"] = game_name
                
            if not game_name:
                Messagebox = QMessageBox()
                Messagebox.setText("O nome do jogo não pode estar vazio.")
                Messagebox.exec()
                return

            icon_path = QFileDialog.getOpenFileName(self,
                QCoreApplication.translate("MainWindow", "Selecione o novo ícone do jogo"),
                "/Desktop",
                QCoreApplication.translate("MainWindow", "ícone", "*.png;*.jpg;*.jpeg;*.ico")
            )
            if icon_path:
                self.selected_game["icon_path"] = icon_path

            cover_path = QFileDialog.getOpenFileName(self,
                QCoreApplication.translate("MainWindow", "Selecione a nova capa do jogo"),
                "/Desktop",
                QCoreApplication.translate("MainWindow", "ícone", "*.png;*.jpg;*.jpeg")
            )
            if cover_path:
                self.selected_game["cover_path"] = cover_path

            

            self.games.sort(key=lambda x: x["game_name"].lower())
            self.save_games()
            self.display_games()

    def add_token(self):
        if "Dropbox" not in self.config:
            self.config["Dropbox"] = {}

        config = configparser.ConfigParser()
        config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
        config.read(config_file_path)

        authorize_url = auth_flow.start()
        webbrowser.open_new_tab(authorize_url)
        
        auth_code, ok = QInputDialog.getText(self, "QInputDialog.getText()", "Insira o token do Dropbox:", QLineEdit.Normal, QDir.home().dirName())
        if ok and auth_code:
            self.selected_game["game_name"] = auth_code
        
        try:
            oauth_result = auth_flow.finish(auth_code)
            token = oauth_result.access_token
            self.config["Dropbox"]["token"] = token
            with open(config_file_path, 'w') as config_file:
                self.config.write(config_file)
            Messagebox = QMessageBox()
            Messagebox.setText("Token do Dropbox atualizado com sucesso.")
            Messagebox.exec()
        except Exception as e:
            Messagebox = QMessageBox()
            Messagebox.setText(f"Erro ao atualizar o token: {e}")
            Messagebox.exec()

    def upload_save(self):
        if hasattr(self, 'selected_game') and self.selected_game:
            dbx = dropbox.Dropbox(token)
            save_path = self.selected_game["save_path"]
            if os.path.isdir(save_path):
                for file_name in os.listdir(save_path):
                    file_path = os.path.join(save_path, file_name)
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as f:
                            try:
                                dbx.files_upload(f.read(), f"/{file_name}", mode=WriteMode("overwrite"))
                            except ApiError as e:
                                Messagebox = QMessageBox()
                                Messagebox.setText(f"Não foi possível fazer o upload: {e}")
                                Messagebox.exec()

    def download_save(self):
        if hasattr(self, 'selected_game') and self.selected_game:
            dbx = dropbox.Dropbox(token)
            save_path = self.selected_game["save_path"]
            try:
                results = dbx.files_list_folder('').entries
                for entry in results:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        file_path = os.path.join(save_path, entry.name)
                        with open(file_path, 'wb') as f:
                            metadata, res = dbx.files_download(entry.path_display)
                            f.write(res.content)
            except ApiError as e:
                Messagebox = QMessageBox()
                Messagebox.setText(f"Não foi possível fazer o download: {e}")
                Messagebox.exec()

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def load_config(self):
        if "Dropbox" in self.config and "token" in self.config["Dropbox"]:
            token = self.config["Dropbox"]["token"]
        else:
            Messagebox = QMessageBox()
            Messagebox.setText("Token do Dropbox não encontrado. Configure-o.")
            Messagebox.exec()

try:
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    APP_KEY = '30cmzgdcwb3udf1'
    APP_SECRET = 'dolklifa8bdkoij'
    CONFIG_FILE = 'config.ini'

    auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

    config = configparser.ConfigParser()
    config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
    config.read(config_file_path)
    ui_main_window = Ui_MainWindow()

    if "Dropbox" in config and "token" in config["Dropbox"]:
        token = config["Dropbox"]["token"]
    else:
        authorize_url = auth_flow.start()
        webbrowser.open_new_tab(authorize_url)
        
        auth_code, ok = QInputDialog.getText(ui_main_window, "QInputDialog.getText()", "Insira o token do Dropbox:", QLineEdit.Normal, QDir.home().dirName())
        if ok and auth_code:
            auth_code.setText(auth_code)
        
        try:
            oauth_result = auth_flow.finish(auth_code)
            token = oauth_result.access_token
        except Exception as e:
            print('Erro na autenticação:', e)
            sys.exit()

        config["Dropbox"] = {"token": token}
        with open(config_file_path, 'w') as config_file:
            config.write(config_file)
except Exception as e:
    print('Erro na autenticação:', e)
