from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from plyer import filechooser
import os


# -------- NEON BUTTON --------
class NeonButton(Button):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = (0, 0, 0, 1)

        with self.canvas.before:
            Color(*color)
            self.rect = RoundedRectangle(radius=[25], pos=self.pos, size=self.size)

        self.bind(pos=self.update, size=self.update)

    def update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# -------- MAIN SCREEN --------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.running = False
        self.mode = "stopwatch"
        self.time = 0
        self.sound = None
        self.alarm = None
        self.event = None  
        self.current_volume = 0.5  # Default volume 50%

        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # TIME DISPLAY
        self.label = Label(text="00:00:00", font_size=48, color=(1, 1, 1, 1))
        root.add_widget(self.label)

        # SONG & ALARM NAMES
        self.song_label = Label(text="No song selected", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.1))
        root.add_widget(self.song_label)
        
        self.alarm_label = Label(text="No alarm selected", color=(0.7, 0.7, 0.7, 1), size_hint=(1, 0.1))
        root.add_widget(self.alarm_label)

        # 🔥 COUNTDOWN INPUT (FIXED: Clear labels and hint text)
        input_row = BoxLayout(size_hint=(1, 0.15), spacing=10)
        input_row.add_widget(Label(text="Set Timer:", font_size=20, size_hint=(0.5, 1)))
        
        self.h = TextInput(hint_text="HH", font_size=24, halign="center", input_filter='int')
        self.m = TextInput(hint_text="MM", font_size=24, halign="center", input_filter='int')
        self.s = TextInput(hint_text="SS", font_size=24, halign="center", input_filter='int')

        input_row.add_widget(self.h)
        input_row.add_widget(self.m)
        input_row.add_widget(self.s)
        root.add_widget(input_row)

        # 🔥 SPOTIFY-STYLE MUSIC PROGRESS BAR
        progress_box = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.curr_time_label = Label(text="00:00", size_hint=(0.15, 1))
        self.progress = Slider(min=0, max=100, value=0, size_hint=(0.7, 1))
        self.total_time_label = Label(text="00:00", size_hint=(0.15, 1))
        
        progress_box.add_widget(self.curr_time_label)
        progress_box.add_widget(self.progress)
        progress_box.add_widget(self.total_time_label)
        root.add_widget(progress_box)

        # 🔥 SIMPLE VOLUME INCREASER/DECREASER
        vol_box = BoxLayout(size_hint=(1, 0.15), spacing=20)
        vol_box.add_widget(Label(size_hint=(0.2, 1))) # Spacer
        
        btn_vol_down = Button(text="-", font_size=30, size_hint=(0.2, 1), background_color=(0.3, 0.3, 0.3, 1))
        btn_vol_down.bind(on_press=lambda x: self.change_volume(-0.1))
        
        self.vol_label = Label(text="Volume: 50%", font_size=20, size_hint=(0.2, 1))
        
        btn_vol_up = Button(text="+", font_size=30, size_hint=(0.2, 1), background_color=(0.3, 0.3, 0.3, 1))
        btn_vol_up.bind(on_press=lambda x: self.change_volume(0.1))
        
        vol_box.add_widget(btn_vol_down)
        vol_box.add_widget(self.vol_label)
        vol_box.add_widget(btn_vol_up)
        vol_box.add_widget(Label(size_hint=(0.2, 1))) # Spacer
        
        root.add_widget(vol_box)

        # BUTTON ROW 1
        row1 = GridLayout(cols=6, size_hint=(1, 0.2))
        row1.add_widget(self.btn("Start", self.start, "#96FF1D"))
        row1.add_widget(self.btn("Pause", self.pause, "#FF9C2B"))
        row1.add_widget(self.btn("Reset", self.reset, "#DC82FF"))
        row1.add_widget(self.btn("Lap", self.lap, "#EFFF5F"))
        row1.add_widget(self.btn("SW", lambda x: self.set_mode("stopwatch"), "#52fc77"))
        row1.add_widget(self.btn("CD", lambda x: self.set_mode("countdown"), "#ff61c2"))
        root.add_widget(row1)

        # BUTTON ROW 2
        row2 = GridLayout(cols=6, size_hint=(1, 0.2))
        row2.add_widget(self.btn("Alarm", self.choose_alarm, "#5856D6"))
        row2.add_widget(self.btn("Song", self.choose_song, "#00E5FF"))
        row2.add_widget(self.btn("Play", self.play_music, "#00FF9C"))
        row2.add_widget(self.btn("Pause", self.pause_music, "#FFC300"))
        row2.add_widget(self.btn("Stop", self.stop_music, "#FF4C4C"))
        row2.add_widget(self.btn("Game", self.open_game, "#00FFAA"))
        root.add_widget(row2)

        self.add_widget(root)

        # Start a fast clock just to update the music slider smoothly
        Clock.schedule_interval(self.update_music_progress, 0.5)

    def btn(self, text, func, hex_color):
        color = tuple(int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)) + (1,)
        return NeonButton(text=text, on_press=func, color=color)

    def format_time(self, t):
        t = int(t)
        return f"{t//3600:02}:{(t//60)%60:02}:{t%60:02}"
        
    def format_music_time(self, seconds):
        seconds = int(seconds)
        return f"{(seconds//60):02}:{seconds%60:02}"

    def update(self, dt):
        if self.running:
            if self.mode == "countdown":
                if self.time > 0:
                    self.time -= 1
                else:
                    self.running = False
                    if self.alarm:
                        self.alarm.volume = self.current_volume
                        self.alarm.play()
            else:
                self.time += 1

            self.label.text = self.format_time(self.time)

    def update_music_progress(self, dt):
        if self.sound and self.sound.state == 'play':
            pos = self.sound.get_pos()
            length = self.sound.length
            
            if length > 0:
                self.progress.max = length
                self.progress.value = pos
                self.curr_time_label.text = self.format_music_time(pos)
                self.total_time_label.text = self.format_music_time(length)

    def change_volume(self, amount):
        self.current_volume += amount
        self.current_volume = max(0.0, min(1.0, self.current_volume)) # Clamp between 0 and 1
        
        self.vol_label.text = f"Volume: {int(self.current_volume * 100)}%"
        
        if self.sound:
            self.sound.volume = self.current_volume

    def start(self, x):
        if not self.running:
            if self.mode == "countdown" and self.time == 0:
                # Use "or 0" so it doesn't crash if a box is left empty
                h = int(self.h.text or "0")
                m = int(self.m.text or "0")
                s = int(self.s.text or "0")
                self.time = (h * 3600) + (m * 60) + s

            self.running = True

            if not self.event:
                self.event = Clock.schedule_interval(self.update, 1)

    def pause(self, x):
        self.running = False

    def reset(self, x):
        self.running = False
        self.time = 0
        self.label.text = "00:00:00"

    def set_mode(self, m):
        self.reset(None)
        self.mode = m

    def lap(self, x):
        print("Lap:", self.label.text)

    # FILE PICKER
    def choose_song(self, x):
        filechooser.open_file(on_selection=self.load_song)

    def load_song(self, selection):
        if selection:
            path = selection[0]
            self.sound = SoundLoader.load(path)
            self.song_label.text = os.path.basename(path)

    def choose_alarm(self, x):
        filechooser.open_file(on_selection=self.load_alarm)

    def load_alarm(self, selection):
        if selection:
            path = selection[0]
            self.alarm = SoundLoader.load(path)
            self.alarm_label.text = os.path.basename(path)

    # MUSIC
    def play_music(self, x):
        if self.sound:
            self.sound.volume = self.current_volume
            self.sound.play()

    def pause_music(self, x):
        if self.sound:
            self.sound.stop() # Kivy sound doesn't easily 'pause', stop acts as pause on some platforms

    def stop_music(self, x):
        if self.sound:
            self.sound.stop()
            self.progress.value = 0
            self.curr_time_label.text = "00:00"

    def open_game(self, x):
        self.manager.current = "game"


# -------- GAME --------
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.board = [""] * 9
        self.turn = "X"
        self.game_over = False

        root = BoxLayout(orientation='vertical')
        
        self.title_label = Label(text="Tic-Tac-Toe - Player X's Turn", font_size=32, size_hint=(1, 0.2))
        root.add_widget(self.title_label)

        grid = GridLayout(cols=3, size_hint=(1, 0.6))
        self.buttons = []

        for i in range(9):
            b = Button(text="", font_size=50)
            b.bind(on_press=lambda inst, i=i: self.click(i))
            self.buttons.append(b)
            grid.add_widget(b)

        back = Button(text="Back", font_size=24, size_hint=(1, 0.2), on_press=self.go_back)

        root.add_widget(grid)
        root.add_widget(back)

        self.add_widget(root)

    def click(self, i):
        if self.board[i] == "" and not self.game_over:
            self.board[i] = self.turn
            self.buttons[i].text = self.turn
            
            # Check for win
            if self.check_win():
                self.title_label.text = f"Player {self.turn} WINS!"
                self.game_over = True
                Clock.schedule_once(self.reset_board, 2) # Auto reset after 2 seconds
            # Check for draw
            elif "" not in self.board:
                self.title_label.text = "It's a DRAW!"
                self.game_over = True
                Clock.schedule_once(self.reset_board, 2)
            # Switch turn
            else:
                self.turn = "O" if self.turn == "X" else "X"
                self.title_label.text = f"Tic-Tac-Toe - Player {self.turn}'s Turn"

    def check_win(self):
        # All winning combinations in Tic-Tac-Toe
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8), # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8), # Columns
            (0, 4, 8), (2, 4, 6)             # Diagonals
        ]
        for a, b, c in win_conditions:
            if self.board[a] == self.board[b] == self.board[c] != "":
                return True
        return False

    def reset_board(self, dt):
        self.board = [""] * 9
        self.turn = "X"
        self.game_over = False
        self.title_label.text = "Tic-Tac-Toe - Player X's Turn"
        for b in self.buttons:
            b.text = ""

    def go_back(self, x):
        self.manager.current = "main"


# -------- APP --------
class iTimerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(GameScreen(name="game"))
        return sm


if __name__ == "__main__":
    iTimerApp().run()