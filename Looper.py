import tkinter as tk
import sounddevice as sd
import numpy as np
import asyncio
import time
from threading import Thread, Event
from tkinter import filedialog

class LoopPedalApp:
    def __init__(self, root):
        # Initialize the root window and set it as non-resizable
        self.root = root
        self.root.resizable(False, False)  

        # Initialize variables
        self.recorded_tracks = []
        self.is_recording = False
        self.is_playing = False
        self.SAMPLE_RATE = 44100
        self.duration = 5
        self.recording_count = 0
        self.recording_thread = None
        self.playback_thread = None
        self.recording_event = None
        self.playback_event = None
        self.stop_recording_event = Event()
        self.playback_during_recording_thread = None
        self.playback_stream = None
        self.playback_position = 0

        # Create the GUI
        self.create_gui()

    def create_gui(self):
        # Create the main frame for buttons
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=10)

        # Create the record button
        self.record_button = tk.Button(self.buttons_frame, text="REC", command=self.toggle_recording, font=("Arial", 14), width=15, height=2, bg="red")
        self.record_button.pack(side=tk.LEFT, padx=5)

        # Create the playback button
        self.play_button = tk.Button(self.buttons_frame, text="PLAY/STOP", command=self.toggle_playback, font=("Arial", 14), width=15, height=2, bg="green")
        self.play_button.pack(side=tk.LEFT, padx=5)

        # Create the clear button
        self.clear_button = tk.Button(self.buttons_frame, text="Clear", command=self.clear_recordings, font=("Arial", 14), width=10, height=2, bg="#4682B4")
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
        self.duration_entry.insert(0, "5")
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
                self.duration = 5
            self.is_recording = True
            self.record_button.config(text="REC")
            self.notification_label.config(text="Recording", fg="red", bg="black",  font=("Arial", 16, "bold"))
            self.recording_start_time = time.time()
            self.stop_recording_event.clear()
            self.recording_event = Thread(target=self.record_audio)
            self.recording_event.start()
            if self.playback_during_recording.get():
                self.playback_during_recording_thread = Thread(target=self.play_audio_loop)
                self.playback_during_recording_thread.start()
        else:
            self.is_recording = False
            self.record_button.config(text="REC")
            self.notification_label.config(text="", fg="black", font=("Arial", 12))
            self.stop_recording_event.set()
            self.recording_event.join()
            self.recording_event = None
            if self.playback_during_recording_thread:
                self.playback_during_recording_thread.join()
                self.playback_during_recording_thread = None

    def toggle_playback(self):
        # Toggle the playback state
        if not self.is_playing and len(self.recorded_tracks) > 0:
            self.is_playing = True
            self.play_button.config(text="PLAY/STOP")
            self.notification_label.config(text="PLAYBACK", bg="black", fg="green", font=("Arial", 20))
            self.playback_start_time = time.time()
            self.play_audio()
        elif self.is_playing:
            self.is_playing = False
            self.play_button.config(text="PLAY/STOP")
            self.notification_label.config(text="", fg="black", font=("Arial", 12))
            self.stop_playback()

    def record_audio(self):
        # Record audio for the specified duration
        new_track = sd.rec(int(self.duration * self.SAMPLE_RATE), samplerate=self.SAMPLE_RATE, channels=1, blocking=True)
        if not self.stop_recording_event.is_set():
            self.recorded_tracks.append(new_track)
            self.recording_count += 1
            self.update_recording_count_label()
        self.stop_recording()

    def play_audio(self):
        # Start playback of the recorded tracks
        if self.playback_stream is None:
            combined_track = np.zeros_like(self.recorded_tracks[0])
            for track in self.recorded_tracks:
                combined_track += track
            self.playback_position = 0
            self.playback_stream = sd.OutputStream(samplerate=self.SAMPLE_RATE, channels=1, callback=self.playback_callback, blocksize=1024)
            self.playback_stream.start()

    def playback_callback(self, outdata, frames, time, status):
        # Callback function for audio playback
        if len(self.recorded_tracks) > 0:
            combined_track = np.zeros_like(self.recorded_tracks[0])
            for track in self.recorded_tracks:
                combined_track += track
            remaining_samples = len(combined_track) - self.playback_position
            if remaining_samples >= frames:
                outdata[:] = combined_track[self.playback_position:self.playback_position + frames].reshape(-1, 1)
                self.playback_position += frames
            else:
                outdata[:remaining_samples] = combined_track[self.playback_position:]
                outdata[remaining_samples:] = 0
                self.playback_position = 0
        else:
            outdata.fill(0)

    def play_audio_loop(self):
        # Play the recorded tracks in a loop during recording
        while self.is_recording:
            self.play_audio()
            time.sleep(self.duration)

    def stop_recording(self):
        # Stop the recording process
        if self.is_recording:
            self.is_recording = False
            self.record_button.config(text="REC")
            self.notification_label.config(text="", bg="red", fg="black", font=("Arial", 12))

    def stop_playback(self):
        # Stop the playback process
        if self.playback_stream:
            self.playback_stream.stop()
            self.playback_stream = None
            self.playback_position = 0
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="PLAY/STOP")
            self.notification_label.config(text="", fg="black", font=("Arial", 12))

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

    def validate_duration(self, text):
        # Validate the duration input
        if text.isdigit():
            duration = int(text)
            if duration < 1 or duration > 30:
                return False
            else:
                return True
        else:
            return False

    def save_recordings(self):
        # Save the recorded tracks to a file
        if len(self.recorded_tracks) > 0:
            file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav")])
            if file_path:
                merged_track = np.zeros_like(self.recorded_tracks[0])
                for track in self.recorded_tracks:
                    merged_track += track
                sd.play(merged_track, self.SAMPLE_RATE, blocking=True)
                sf.write(file_path, merged_track, self.SAMPLE_RATE)
                tk.messagebox.showinfo("Save Recordings", "Recordings saved successfully.")
        else:
            tk.messagebox.showwarning("No Recordings", "There are no recordings to save.")

    def show_about_dialog(self):
            tk.messagebox.showinfo(title="About", message="Version 0.1       https://github.com/ViciousSquid/Looper")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoopPedalApp(root)
    app.run()