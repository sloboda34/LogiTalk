
import socket
import threading
import queue

from urllib.parse import urlparse
from urllib.request import getproxies

import websocket
import customtkinter as ctk

SERVER_URL = 'wss://corncob-greasily-semifinal.ngrok-free.dev'

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def proxy_settings():
    proxy = getproxies().get('https') or getproxies().get('http')

    if not proxy:
        return {}

    p = urlparse(proxy if '://' in proxy else 'http://' + proxy)

    return {
        'http_proxy_host': p.hostname,
        'http_proxy_port': p.port or 8080,
        'proxy_type': 'http'
    }


def where_is_server():
    try:
        return socket.gethostbyname(urlparse(SERVER_URL).hostname)
    except Exception as e:
        return f"Не вдалося знайти адресу: {e}"


class MainWindow(ctk.CTk):


    def __init__(self):
        super().__init__()

        self.geometry("850x600")
        self.minsize(600, 450)
        self.title("LogiTalk")

        self.username = "Artem"

        self.sock = None
        self.messages_queue = queue.Queue()

        self.emoji_list = [
            "😀", "😂", "🤣", "😊", "😍",
            "🥰", "😎", "😭", "😡", "👍",
            "👎", "❤️", "🔥", "🎉", "👏",
            "🤔", "😴", "💀", "💯", "🚀",
            "😇", "😉", "🙃", "🤩"
        ]

        self.create_interface()
        self.connect_to_server()

        self.after(100, self.process_incoming)

    # Головний інтерфейс
    def create_interface(self):

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Бокове меню
        self.menu_frame = ctk.CTkFrame(
            self,
            width=180,
            corner_radius=0
        )
        self.menu_frame.grid(row=0, column=0, sticky="ns")
        self.menu_frame.grid_propagate(False)

        ctk.CTkLabel(
            self.menu_frame,
            text="LogiTalk",
            font=("Arial", 25, "bold")
        ).pack(pady=25)




        ctk.CTkLabel(
            self.menu_frame,
            text="Налаштування",
            font=("Arial", 17, "bold")
        ).pack(pady=15)

        self.name_entry = ctk.CTkEntry(
            self.menu_frame,
            placeholder_text="Ваше ім'я"
        )
        self.name_entry.pack(padx=10, pady=5)
        self.name_entry.insert(0, self.username)

        ctk.CTkButton(
            self.menu_frame,
            text="Змінити ім'я",
            command=self.change_username
        ).pack(padx=10, pady=5)


        # Основна частина
        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=0
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Верхня панель
        self.top_frame = ctk.CTkFrame(
            self.main_frame,
            height=55,
            corner_radius=0
        )
        self.top_frame.grid(
            row=0, column=0, sticky="ew"
        )

        self.menu_button = ctk.CTkButton(
            self.top_frame,
            text="☰",
            width=45,
            command=self.toggle_menu
        )
        self.menu_button.pack(side="left", padx=10, pady=8)

        ctk.CTkLabel(
            self.top_frame,
            text="Загальний чат",
            font=("Arial", 20, "bold")
        ).pack(side="left", padx=10)

        # Область повідомлень
        self.chat_scroll = ctk.CTkScrollableFrame(
            self.main_frame,
            corner_radius=10
        )
        self.chat_scroll.grid(
            row=1, column=0,
            sticky="nsew",
            padx=15, pady=10
        )

        # Нижня панель
        self.bottom_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        self.bottom_frame.grid(
            row=2, column=0,
            sticky="ew",
            padx=15, pady=15
        )

        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkEntry(
            self.bottom_frame,
            placeholder_text="Напишіть повідомлення...",
            height=42,
            font=("Arial", 14)
        )
        self.message_entry.grid(
            row=0, column=0,
            sticky="ew",
            padx=(0, 8)
        )

        self.message_entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )

        # Кнопка емодзі
        ctk.CTkButton(
            self.bottom_frame,
            text="😀",
            width=45,
            height=42,
            command=self.open_emoji_picker
        ).grid(row=0, column=1, padx=4)

        # Кнопка відправлення
        ctk.CTkButton(
            self.bottom_frame,
            text="➤",
            width=50,
            height=42,
            command=self.send_message
        ).grid(row=0, column=2)

    # Бокове меню
    def toggle_menu(self):

        if self.menu_frame.winfo_manager():
            self.menu_frame.grid_remove()
        else:
            self.menu_frame.grid()

    # Зміна імені
    def change_username(self):

        name = self.name_entry.get().strip()

        if name:
            self.username = name
            self.add_message(
                "[SYSTEM] Тепер ваше ім'я: " + name,
                "[SYSTEM]"
            )

    # Вибір емодзі
    def open_emoji_picker(self):

        window = ctk.CTkToplevel(self)
        window.title("Емодзі")
        window.geometry("300x280")
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()

        ctk.CTkLabel(
            window,
            text="Виберіть емодзі",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        emoji_frame = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )
        emoji_frame.pack(padx=10, pady=5)

        for i, emoji in enumerate(self.emoji_list):

            button = ctk.CTkButton(
                emoji_frame,
                text=emoji,
                width=48,
                height=43,
                font=("Segoe UI Emoji", 25),
                fg_color="#D6E8FA",
                hover_color="#A9D2F5",
                text_color="#222222",
                corner_radius=10,
                command=lambda e=emoji: self.insert_emoji(e, window)
            )

            button.grid(
                row=i // 5,
                column=i % 5,
                padx=2,
                pady=2
            )

    def insert_emoji(self, emoji, window):

        self.message_entry.insert("insert", emoji)
        window.destroy()
        self.message_entry.focus()

    # Підключення до сервера
    def connect_to_server(self):

        try:
            self.sock = websocket.create_connection(
                SERVER_URL,
                header=["ngrok-skip-browser-warning: true"],
                timeout=5,
                **proxy_settings()
            )
            self.sock.settimeout(None)

            hello = (
                f"TEXT@{self.username}@"
                f"[SYSTEM] {self.username} приєднався(лась) до чату!"
            )

            self.sock.send(hello)

            threading.Thread(
                target=self.recv_message,
                daemon=True
            ).start()

            self.add_message(
                "[SYSTEM] Ви підключилися до сервера!",
                "[SYSTEM]"
            )

        except Exception as e:

            self.sock = None

            self.add_message(
                f"[SYSTEM] Помилка підключення: {e}",
                "[SYSTEM]"
            )

            self.add_message(
                f"IP сервера: {where_is_server()}",
                "[SYSTEM]"
            )

    # Отримання повідомлень
    def recv_message(self):

        while True:
            try:
                data = self.sock.recv()

                if not data:
                    break

                self.messages_queue.put(data.strip())

            except Exception:
                break

        self.messages_queue.put(None)

    # Обробка отриманих повідомлень
    def process_incoming(self):

        while not self.messages_queue.empty():

            data = self.messages_queue.get()

            if data is None:
                self.add_message(
                    "[SYSTEM] З'єднання з сервером розірвано",
                    "[SYSTEM]"
                )
                self.sock = None
                continue

            self.handle_line(data)

        self.after(100, self.process_incoming)

    def handle_line(self, line):

        if not line:
            return

        parts = line.split("@", 2)

        if parts[0] == "TEXT" and len(parts) >= 3:

            author = parts[1]
            message = parts[2]

            # Не показуємо повторно власне повідомлення
            if author != self.username:
                self.add_message(message, author)

        elif parts[0] == "IMAGE" and len(parts) >= 3:

            author = parts[1]
            filename = parts[2]

            self.add_message(
                f"Надіслано зображення: {filename}",
                author
            )

        else:
            self.add_message(line, "[SYSTEM]")

    # Створення аватарки та бульбашки
    def add_message(self, text, author):

        if author == "[SYSTEM]":
            color = "#E5E5E5"
            avatar_color = "#BDBDBD"
            initials = "S"
            own_message = False

        else:
            own_message = author == self.username

            if own_message:
                color = "#D6E4F0"
                avatar_color = "#A9C7E2"
            else:
                color = "#E5E5E5"
                avatar_color = "#BDBDBD"

            initials = author[:2].upper()

        # Рядок повідомлення
        row = ctk.CTkFrame(
            self.chat_scroll,
            fg_color="transparent"
        )
        row.pack(fill="x", padx=8, pady=5)

        group = ctk.CTkFrame(
            row,
            fg_color="transparent"
        )

        if own_message:
            group.pack(side="right", padx=5)
        else:
            group.pack(side="left", padx=5)
        # Аватарка
        avatar = ctk.CTkLabel(
            group,
            text=initials,
            width=36,
            height=36,
            corner_radius=20,
            fg_color=avatar_color,
            font=("Arial", 12, "bold")
        )

        # Бульбашка
        bubble = ctk.CTkFrame(
            group,
            fg_color=color,
            corner_radius=15
        )

        name_label = ctk.CTkLabel(
            bubble,
            text=author,
            font=("Arial", 11, "bold"),
            text_color="#333333"
        )
        name_label.pack(
            anchor="w",
            padx=10,
            pady=(6, 0)
        )

        message_label = ctk.CTkLabel(
            bubble,
            text=text,
            font=("Arial", 14),
            justify="left",
            wraplength=400
        )
        message_label.pack(
            anchor="w",
            padx=10,
            pady=(2, 8)
        )

        if own_message:
            bubble.pack(side="left", padx=7)
            avatar.pack(side="left", padx=3)
        else:
            avatar.pack(side="left", padx=3)
            bubble.pack(side="left", padx=7)

        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    # Надсилання повідомлень
    def send_message(self):

        message = self.message_entry.get().strip()

        if not message:
            return

        if self.sock is None:
            self.add_message(
                "[SYSTEM] Немає підключення до сервера",
                "[SYSTEM]"
            )
            return

        try:
            data = f"TEXT@{self.username}@{message}"
            self.sock.send(data)

            self.add_message(message, self.username)

            self.message_entry.delete(0, "end")

        except Exception as e:

            self.add_message(
                f"[SYSTEM] Помилка надсилання: {e}",
                "[SYSTEM]"
            )

    def on_close(self):

        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

        self.destroy()


win = MainWindow()
win.protocol("WM_DELETE_WINDOW", win.on_close)
win.mainloop()
