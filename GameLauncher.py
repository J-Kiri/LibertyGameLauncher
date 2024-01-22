import os
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
import pickle

class GameLauncher:
    def __init__(self, master):
        self.master = master
        self.master.title("LIberty Game Launcher")
        self.master.geometry("800x600+100+50")
        
        self.games = self.load_games()
        
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Adicionar jogo", command=self.add_game)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=self.master.destroy)
        self.menu_bar.add_cascade(label="Menu", menu=self.file_menu)
        
        self.game_frame = tk.Frame(self.master)
        self.game_frame.pack(pady=10)
        
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Remover jogo", command=self.remove_game)
        self.context_menu.add_command(label="Editar jogo", command=self.edit_game)
        
        self.game_frame.bind("<Button-3>", self.show_context_menu)
        self.display_games()

    def add_game(self):
        file_path = filedialog.askopenfilename(title="Selecione o executável do jogo", filetypes=[("Executáveis", "*.exe")])
        if file_path:
            icon_path = filedialog.askopenfilename(title="Selecione o Ícone do Jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.ico")])
            cover_path = filedialog.askopenfilename(title="Selecione a Capa do Jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
            game_name = simpledialog.askstring("Nome do Jogo", "Insira o nome do jogo:")
            
            game = {
                "game_name": game_name,
                "file_path": file_path,
                "icon_path": icon_path,
                "cover_path": cover_path
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
            
            button.bind("<Button-3>", lambda event, g=game: self.show_context_menu(event, g))

            col += 1
            if col > 5:
                col = 0
                row += 1

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

            icon_path = filedialog.askopenfilename(title="Selecionar Novo Ícone do Jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
            if icon_path:
                self.selected_game["icon_path"] = icon_path

            cover_path = filedialog.askopenfilename(title="Selecionar Nova Capa do Jogo", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
            if cover_path:
                self.selected_game["cover_path"] = cover_path

            self.games.sort(key=lambda x: x["game_name"].lower())
            self.save_games()
            self.display_games()

def main():
    root = tk.Tk()
    app = GameLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
