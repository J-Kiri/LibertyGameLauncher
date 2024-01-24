import ctypes
import os
import tkinter as tk
import zipfile
import sys
import tempfile
import pickle
import configparser
import dropbox
import webbrowser
import sv_ttk

from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
#from pyuac import main_requires_admin

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
    
    auth_code = simpledialog.askstring("Inserir TOKEN", "Insira o token do Dropbox:")
    
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
        self.master.geometry("800x600+100+50")

        sv_ttk.set_theme("dark")

        self.games = self.load_games()

        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Adicionar jogo", command=self.add_game)
        self.file_menu.add_command(label="Configurar token Dropbox", command=self.add_token)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=self.master.destroy)
        self.menu_bar.add_cascade(label="Menu", menu=self.file_menu)

        self.canvas = tk.Canvas(self.master)
        self.scrollbar = tk.Scrollbar(self.master, command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

        self.game_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.game_frame, anchor="nw")

        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Remover jogo", command=self.remove_game)
        self.context_menu.add_command(label="Editar jogo", command=self.edit_game)
        self.context_menu.add_command(label="Upload save", command=self.upload_save)
        self.context_menu.add_command(label="Download save", command=self.download_save)
        self.game_frame.bind("<Button-3>", self.show_context_menu)

        self.display_games()
        self.config = configparser.ConfigParser()
        self.load_config()

    def add_game(self):
        file_path = filedialog.askopenfilename(title="Selecione o executável do jogo", filetypes=[("Executáveis", "*.exe")])
        if file_path:
            icon_path = filedialog.askopenfilename(title="Selecione o ícone do jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.ico")])
            cover_path = filedialog.askopenfilename(title="Selecione a capa do jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
            save_path = filedialog.askdirectory(title="Selecione a pasta que contem os saves do jogo")
            game_name = simpledialog.askstring("Nome do Jogo", "Insira o nome do jogo:")
            
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
        for widget in self.game_frame.winfo_children():
            widget.destroy()

        row = 0
        col = 0

        for game in self.games:
            cover = Image.open(game["cover_path"])
            cover = ImageTk.PhotoImage(cover.resize((150, 225)))

            button = tk.Button(self.game_frame, image=cover, text=game["game_name"], compound="top", command=lambda g=game: self.launch_game(g))
            button.image = cover
            button.grid(row=row, column=col, padx=10, pady=10)
            button.config(bd=0, highlightthickness=0)
            
            button.bind("<Button-3>", lambda event, g=game: self.show_context_menu(event, g))

            col += 1
            if col > 8:
                col = 0
                row += 1

            self.games.sort(key=lambda x: x["game_name"].lower())
            self.master.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def launch_game(self, game):
        os.chdir(os.path.dirname(game["file_path"]))
        os.system(f'start "" "{game["file_path"]}"')

    def save_games(self):
        with open("games.pickle", "wb") as file:
            pickle.dump(self.games, file)

    def load_games(self):
        try:
            with open("games.pickle", "rb") as file:
                return pickle.load(file)
        except (FileNotFoundError, EOFError):
            return []

    def show_context_menu(self, event, game):
        self.selected_game = game
        self.context_menu.post(event.x_root, event.y_root)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


    def remove_game(self):
        if self.selected_game:
            self.games.remove(self.selected_game)
            self.save_games()
            self.display_games()

    def edit_game(self):
        if self.selected_game:
            game_name = simpledialog.askstring("Editar Nome", "Insira o novo nome do jogo:", initialvalue=self.selected_game["game_name"])
            if game_name is not None:
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

    #Dropbox API
    def add_token(self):
        if "Dropbox" not in self.config:
            self.config["Dropbox"] = {}

        config = configparser.ConfigParser()
        config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE)
        config.read(config_file_path)

        authorize_url = auth_flow.start()
        webbrowser.open_new_tab(authorize_url)
        
        auth_code = simpledialog.askstring("Inserir TOKEN", "Insira o token do Dropbox:")
        
        try:
            oauth_result = auth_flow.finish(auth_code)
            new_token = oauth_result.access_token

            # Remove o token antigo, se existir
            if "Dropbox" in config and "token" in config["Dropbox"]:
                del config["Dropbox"]["token"]

            # Adiciona o novo token
            config["Dropbox"]["token"] = new_token

            with open(config_file_path, 'w') as config_file:
                config.write(config_file)
            
            self.setup_dropbox()
            print("Novo token do Dropbox configurado com sucesso.")
        except Exception as e:
            print('Erro na autenticação:', e)

    def setup_dropbox(self):
        if "Dropbox" in self.config and "token" in self.config["Dropbox"]:
            self.token = self.config["Dropbox"]["token"]
            try:
                with dropbox.Dropbox(self.token) as self.dbx:
                    self.dbx.users_get_current_account()
                print("Token do Dropbox configurado com sucesso.")
            except AuthError:
                print("ERROR: Invalid access token; try re-generating an "
                    "access token from the app console on the web.")
        else:
            print("Token do Dropbox não encontrado no arquivo de configuração.")


    def load_config(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(script_directory, CONFIG_FILE)

        if os.path.exists(config_file_path):
            self.config.read(config_file_path)

            if "Dropbox" in self.config and "token" in self.config["Dropbox"]:
                self.token = self.config["Dropbox"]["token"]
                self.setup_dropbox()
                print("Token do Dropbox carregado com sucesso.")
            else:
                print("Token do Dropbox não encontrado no arquivo de configuração.")
        else:
            print(f"Arquivo de configuração '{config_file_path}' não encontrado.")

    def save_config(self):
        with open(CONFIG_FILE, 'w') as config_file:
            self.config.write(config_file)

                
    def upload_save(self):
        if not self.token:
            print("ERROR: Nenhum Token registrado.")
            return

        if self.selected_game:
            local_folder = self.selected_game["save_path"]
            local_game_name = self.selected_game["game_name"]

            try:
                temp_zip_file = tempfile.NamedTemporaryFile(delete=False)
                temp_zip_path = temp_zip_file.name + ".zip"
                temp_zip_file.close()

                with zipfile.ZipFile(temp_zip_path, 'w') as zipf:
                    for root, dirs, files in os.walk(local_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, local_folder)
                            zipf.write(file_path, arcname)

                with open(temp_zip_path, 'rb') as f:
                    print("Uploading the save folder to Dropbox...")

                    try:
                        remote_path = f"/{local_game_name}/saves.zip"
                        self.dbx.files_upload(f.read(), remote_path, mode=WriteMode('overwrite'))
                    except ApiError as err:
                        if (err.error.is_path() and
                                err.error.get_path().reason.is_insufficient_space()):
                            sys.exit("ERROR: Cannot back up; insufficient space.")
                        elif err.user_message_text:
                            print(err.user_message_text)
                            sys.exit()
                        else:
                            print(err)
                            sys.exit()
            except FileNotFoundError:
                print(f"ERROR: Save folder not found for {local_game_name}.")
            finally:
                os.remove(temp_zip_path)

    def download_save(self):
        if not self.token:
            print("ERROR: Nenhum Token registrado.")
            return

        if self.selected_game:
            local_folder = self.selected_game["save_path"]
            local_game_name = self.selected_game["game_name"]

            try:
                temp_zip_file = tempfile.NamedTemporaryFile(delete=False)
                temp_zip_path = temp_zip_file.name + ".zip"
                temp_zip_file.close()

                remote_path = f"/{local_game_name}/saves.zip"

                try:
                    metadata, response = self.dbx.files_download(remote_path)
                    with open(temp_zip_path, "wb") as f:
                        f.write(response.content)
                except ApiError as err:
                    if err.user_message_text:
                        print(err.user_message_text)
                    else:
                        print(err)
                    return

                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(local_folder)

                print("Save sincronizado localmente com sucesso.")

            except FileNotFoundError:
                print(f"ERROR: Save folder not found for {local_game_name}.")
            finally:
                os.remove(temp_zip_path)

#@main_requires_admin
def main():
    root = tk.Tk()
    app = GameLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
