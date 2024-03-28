import tkinter as tk
from tkinter import filedialog  

class LoopPedalUtils:
    def __init__(self, app):
        self.app = app

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
        if len(self.app.gui.recorded_tracks) > 0:
            file_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav")])
            if file_path:
                merged_track = np.zeros_like(self.app.gui.recorded_tracks[0])
                for track in self.app.gui.recorded_tracks:
                    merged_track += track
                sf.write(file_path, merged_track, self.app.audio.SAMPLE_RATE)
                tk.messagebox.showinfo("Save Recordings", "Recordings saved successfully.")
            else:
                tk.messagebox.showwarning("No Recordings", "There are no recordings to save.")
