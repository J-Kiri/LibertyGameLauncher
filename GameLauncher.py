import ctypes
import os
import sys
import pickle
import configparser
import dropbox
import webbrowser

from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import *
from ttkbootstrap.constants import *

from PIL import Image, ImageTk, ImageFilter

from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

play_button = Image.open('assets/BUTTON_play.png')
config_button = Image.open('assets/BUTTON_config.png')

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

    if "Dropbox" in config and "token" in config["Dropbox"]:
        token = config["Dropbox"]["token"]
    else:
        authorize_url = auth_flow.start()
        webbrowser.open_new_tab(authorize_url)
        
        auth_code = Querybox.get_string("Inserir TOKEN", "Insira o token do Dropbox:")
        
        try:
            oauth_result = auth_flow.finish(auth_code)
            token = oauth_result.access_token
        except Exception as e:
            print('Erro na autenticação:', e)
            sys.exit()

        config["Dropbox"] = {"token": token}
        with open(config_file_path, 'w') as config_file:
            config.write(config_file)

    class GameLauncher:
        def __init__(self, master):
            self.master = master
            self.master.title("Liberty Game Launcher")
            self.master.geometry("1000x600")

            self.games = self.load_games()

            # Main Frame
            self.main_frame = ttk.Frame(self.master)
            self.main_frame.pack(fill="both", expand=True)

            # Left Panel (Game List)
            self.left_panel = ttk.Frame(self.main_frame, width=250, relief="raised", borderwidth=2)
            self.left_panel.pack(side="left", fill="y")

            self.game_list_frame = ttk.Frame(self.left_panel)
            self.game_list_frame.pack(fill="both", expand=True)

            # Right Panel (Game Details)
            self.right_panel = ttk.Frame(self.main_frame)
            self.right_panel.pack(side="right", fill="both", expand=True)

            self.cover_image = ttk.Label(self.right_panel)
            self.cover_image.pack(pady=10, fill="x", expand=True)
            # Buttons Frame (to arrange buttons horizontally)
            self.button_frame = ttk.Frame(self.right_panel)
            self.button_frame.pack(pady=5, fill="x")

            # Play Button
            play_button_image = ImageTk.PhotoImage(play_button)
            self.play_button = ttk.Button(
                self.button_frame,
                image=play_button_image,
                command=self.launch_game,
                style="TButton"
            )
            self.play_button.pack(side="left", padx=5)
            self.play_button.image = play_button

            # Config Button
            config_button_image = ImageTk.PhotoImage(config_button)
            self.config_button = ttk.Button(
                self.button_frame,
                image=config_button_image,
                command=self.edit_game,
                style="TButton"
            )
            self.config_button.pack(side="left", padx=5)
            self.config_button.image = config_button

            # Remove button background and set size to image size
            style = ttk.Style()
            style.configure("TButton", borderwidth=0, highlightthickness=0, padding=0)

            # Menu Bar
            self.menu_bar = ttk.Menu(self.master)
            self.master.config(menu=self.menu_bar)

            self.file_menu = ttk.Menu(self.menu_bar, tearoff=0)
            self.file_menu.add_command(label="Adicionar jogo", command=self.add_game)
            self.file_menu.add_command(label="Configurar token Dropbox", command=self.add_token)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="Sair", command=self.master.destroy)
            self.menu_bar.add_cascade(label="Menu", menu=self.file_menu)

            self.context_menu = ttk.Menu(self.master, tearoff=0)
            self.context_menu.add_command(label="Remover jogo", command=self.remove_game)
            self.context_menu.add_command(label="Editar jogo", command=self.edit_game)
            self.context_menu.add_command(label="Upload save", command=self.upload_save)
            self.context_menu.add_command(label="Download save", command=self.download_save)

            self.display_games()
            self.config = configparser.ConfigParser()
            self.load_config()

        def add_game(self):
            file_path = filedialog.askopenfilename(title="Selecione o executável do jogo", filetypes=[("Executáveis", "*.exe")])
            if file_path:
                icon_path = filedialog.askopenfilename(title="Selecione o ícone do jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.ico")])
                cover_path = filedialog.askopenfilename(title="Selecione a capa do jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
                save_path = filedialog.askdirectory(title="Selecione a pasta que contém os saves do jogo")
                game_name = Querybox.get_string("Nome do Jogo", "Insira o nome do jogo:")
                
                if not game_name:
                    Messagebox.show_error(title="Erro", message="O nome do jogo não pode estar vazio.")
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

        def display_games(self):
            for widget in self.game_list_frame.winfo_children():
                widget.destroy()

            for game in self.games:
                icon = Image.open(game["icon_path"])
                icon = ImageTk.PhotoImage(icon.resize((20, 20)))

                button = ttk.Button(
                    self.game_list_frame,
                    image=icon,
                    text=game["game_name"],
                    compound="left",
                    bootstyle=("dark"),
                    command=lambda g=game: self.show_game_details(g),
                )
                button.configure()
                button.image = icon
                button.pack(pady=5, fill="x")

        def show_game_details(self, game):
            width = 600 * 3.75
            height = 900 * 3.75
            cover = Image.open(game["cover_path"])
            blur_cover = cover.filter(ImageFilter.GaussianBlur(radius=2))
            blur_cover = ImageTk.PhotoImage(blur_cover.resize((int(width), int(height))))
            self.cover_image.place(x=-300, y=-1000)
            self.cover_image.config(image=blur_cover)
            self.cover_image.image = blur_cover

            self.cover_label.config(text=game["game_name"])
            self.selected_game = game

        def launch_game(self):
            if hasattr(self, 'selected_game'):
                game = self.selected_game
                try:
                    os.chdir(os.path.dirname(game["file_path"]))
                    os.system(f'start "" "{game["file_path"]}"')
                except Exception as e:
                    Messagebox.show_error(title="Erro", message=f"Não foi possível iniciar o jogo: {e}")

        def save_games(self):
            try:
                with open("games.pickle", "wb") as file:
                    pickle.dump(self.games, file)
            except Exception as e:
                Messagebox.show_error(title="Erro", message=f"Não foi possível salvar os jogos: {e}")

        def load_games(self):
            try:
                with open("games.pickle", "rb") as file:
                    return pickle.load(file)
            except (FileNotFoundError, EOFError):
                return []

        def remove_game(self):
            if hasattr(self, 'selected_game') and self.selected_game:
                confirm = Messagebox.show_question(title="Confirmar", message=f"Tem certeza que deseja remover '{self.selected_game['game_name']}'?")
                if confirm:
                    self.games.remove(self.selected_game)
                    self.save_games()
                    self.display_games()

        def edit_game(self):
            if hasattr(self, 'selected_game') and self.selected_game:
                game_name = Querybox.get_string("Editar Nome", "Insira o novo nome do jogo:", initialvalue=self.selected_game["game_name"])
                if game_name is not None and game_name.strip() != "":
                    self.selected_game["game_name"] = game_name

                icon_path = filedialog.askopenfilename(title="Selecionar Novo Ícone do Jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.ico")])
                if icon_path:
                    self.selected_game["icon_path"] = icon_path

                cover_path = filedialog.askopenfilename(title="Selecionar Nova Capa do Jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
                if cover_path:
                    self.selected_game["cover_path"] = cover_path

                self.games.sort(key=lambda x: x["game_name"].lower())
                self.save_games()
                self.display_games()

        # Dropbox API
        def add_token(self):
            if "Dropbox" not in self.config:
                self.config["Dropbox"] = {}

            config = configparser.ConfigParser()
            config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
            config.read(config_file_path)

            authorize_url = auth_flow.start()
            webbrowser.open_new_tab(authorize_url)
            
            auth_code = Querybox.get_string("Inserir TOKEN", "Insira o token do Dropbox:")
            
            try:
                oauth_result = auth_flow.finish(auth_code)
                token = oauth_result.access_token
                self.config["Dropbox"]["token"] = token
                with open(config_file_path, 'w') as config_file:
                    self.config.write(config_file)
                Messagebox.show_info(title="Sucesso", message="Token do Dropbox atualizado com sucesso.")
            except Exception as e:
                Messagebox.show_error(title="Erro", message=f"Erro ao atualizar o token: {e}")

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
                                    Messagebox.show_error(title="Erro", message=f"Não foi possível fazer o upload: {e}")

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
                    Messagebox.show_error(title="Erro", message=f"Não foi possível fazer o download: {e}")

        def on_mousewheel(self, event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def load_config(self):
            if "Dropbox" in self.config and "token" in self.config["Dropbox"]:
                token = self.config["Dropbox"]["token"]
            else:
                Messagebox.show_info(title="Info", message="Token do Dropbox não encontrado. Configure-o.")

    root = ttk.Window(themename="darkly")
    app = GameLauncher(root)
    root.mainloop()
except Exception as e:
    Messagebox.show_error(title="Erro", message=f"Erro na inicialização do launcher: {e}")
