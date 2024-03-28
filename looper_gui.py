import tkinter as tk
import time
from tkinter import filedialog
from threading import Thread

class LoopPedalGUI:
    def __init__(self, app):
        self.app = app
        self.root = app.root

        # Initialize variables
        self.recorded_tracks = []
        self.is_recording = False
        self.is_playing = False
        self.duration = 4
        self.recording_count = 0

        # Create the GUI
        self.create_gui()

    def create_gui(self):
        # Create the main frame for buttons
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=10)

        # Create the record button
        self.record_button = tk.Button(self.buttons_frame, text="REC", command=self.toggle_recording, font=("Arial", 14), width=12, height=2, bg="red")
        self.record_button.pack(side=tk.LEFT, padx=5)

        # Create the playback button
        self.play_button = tk.Button(self.buttons_frame, text="PLAY", command=self.toggle_playback, font=("Arial", 14), width=12, height=2, bg="green")
        self.play_button.pack(side=tk.LEFT, padx=5)

        # Create the clear button
        self.clear_button = tk.Button(self.buttons_frame, text="Clear", command=self.clear_recordings, font=("Arial", 14), width=8, height=2, bg="#4682B4")
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Create a frame for duration entry and playback during recording checkbox
        self.duration_playback_frame = tk.Frame(self.root)
        self.duration_playback_frame.pack(pady=5)

        # Create a checkbox for playback during recording
        self.playback_during_recording = tk.BooleanVar()
        self.playback_checkbox = tk.Checkbutton(self.duration_playback_frame, text="Playback during Recording", variable=self.playback_during_recording, font=("Arial", 12))
        self.playback_checkbox.pack(side=tk.LEFT, padx=60, pady=1)

        # Create a label and entry for duration
        self.duration_label = tk.Label(self.duration_playback_frame, text="Duration (sec):", font=("Arial", 12))
        self.duration_label.pack(side=tk.LEFT, padx=5)
        self.duration_entry = tk.Entry(self.duration_playback_frame, font=("Arial", 12), width=5)
        self.duration_entry.insert(0, "4")
        self.duration_entry.pack(side=tk.LEFT, padx=2)

        # Create a notification label
        self.notification_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.notification_label.pack(pady=10)

        # Create a timer label
        self.timer_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.timer_label.pack(pady=10)

        # Create a label for displaying the number of recordings
        self.recording_count_label = tk.Label(self.root, text="Tracks: 0", font=("Arial", 16))
        self.recording_count_label.pack(pady=10)

        # Create a menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Create a File menu
        self.file_menu = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save Recordings", command=self.save_recordings)

        # Create a Help menu
        self.help_menu = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="About", command=self.show_about_dialog)

        # Start the timer
        self.root.after(100, self.update_timer)

    def toggle_recording(self):
        # Toggle the recording state
        if not self.is_recording:
            try:
                self.duration = float(self.duration_entry.get())
            except ValueError:
                self.duration = 4
            self.is_recording = True
            self.record_button.config(text="REC")
            self.notification_label.config(text="Recording", fg="red", bg="black",  font=("Arial", 16, "bold"))
            self.recording_start_time = time.time()
            self.app.audio.stop_recording_event.clear()
            self.app.audio.recording_event = Thread(target=self.app.audio.record_audio)
            self.app.audio.recording_event.start()
            if self.playback_during_recording.get():
                self.app.audio.playback_during_recording_thread = Thread(target=self.app.audio.play_audio_loop)
                self.app.audio.playback_during_recording_thread.start()
        else:
            self.is_recording = False
            self.record_button.config(text="REC")
            self.notification_label.config(text="", fg="black", font=("Arial", 12))
            self.app.audio.stop_recording_event.set()
            self.app.audio.recording_event.join()
            self.app.audio.recording_event = None
            if self.app.audio.playback_during_recording_thread:
                self.app.audio.playback_during_recording_thread.join()
                self.app.audio.playback_during_recording_thread = None

    def toggle_playback(self):
        # Toggle the playback state
        if not self.is_playing and len(self.app.audio.recorded_tracks) > 0:
            self.is_playing = True
            self.play_button.config(text="PLAY", bg="#90EE90")
            self.notification_label.config(text="PLAYBACK", bg="black", fg="green", font=("Arial", 20))
            self.playback_start_time = time.time()
            self.app.audio.play_audio()
        elif self.is_playing:
            self.is_playing = False
            self.play_button.config(text="PLAY")
            self.notification_label.config(text="", fg="black", font=("Arial", 12))
            self.app.audio.stop_playback()

    def record_audio(self):
        pass

    def play_audio(self):
        pass

    def playback_callback(self, outdata, frames, time, status):
        pass

    def play_audio_loop(self):
        pass

    def stop_recording(self):
        pass

    def stop_playback(self):
        pass

    def update_timer(self):
        # Update the timer label with the elapsed time for recording or playback
        if self.is_recording:
            elapsed_time = time.time() - self.recording_start_time
            minutes, seconds = divmod(int(elapsed_time), 60)
            milliseconds = int((elapsed_time - int(elapsed_time)) * 1000)
            self.timer_label.config(text=f"Recording: {minutes:02d}:{seconds:02d}:{milliseconds:03d}")
        elif self.is_playing:
            elapsed_time = time.time() - self.playback_start_time
            self.timer_label.config(text=f"Playback: {int(elapsed_time)}")
        else:
            self.timer_label.config(text="[ READY ]")
        self.root.after(100, self.update_timer)

    def clear_recordings(self):
        # Clear all recorded tracks
        if len(self.recorded_tracks) > 0:
            confirm = tk.messagebox.askyesno("Clear Recordings", "Are you sure?")
            if confirm:
                self.recorded_tracks.clear()
                self.recording_count = 0
                self.update_recording_count_label()

    def update_recording_count_label(self):
        # Update the label displaying the number of recordings
        self.recording_count_label.config(text=f"Tracks: {self.recording_count}")

    def save_recordings(self):
        self.app.utils.save_recordings()

    def show_about_dialog(self):
        tk.messagebox.showinfo(title="About", message="Version 0.11\nhttps://github.com/ViciousSquid/Looper")
