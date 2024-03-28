import sounddevice as sd
import numpy as np
import asyncio
import time
import soundfile as sf
from threading import Thread, Event

class LoopPedalAudio:
    def __init__(self, app):
        self.app = app

        # Initialize audio-related variables
        self.SAMPLE_RATE = 44100
        self.recording_thread = None
        self.playback_thread = None
        self.recording_event = None
        self.playback_event = None
        self.stop_recording_event = Event()
        self.playback_during_recording_thread = None
        self.playback_stream = None
        self.playback_position = 0
        self.recording_stream = None  # Initialize the recording_stream attribute

    def record_callback(self, indata, frames, time, status):
        if status:
            print("Recording callback error:", status)
        else:
            # Append the incoming audio data to the recorded tracks
            self.app.gui.recorded_tracks.append(indata.copy())
            self.app.gui.recording_count += 1
            self.app.gui.update_recording_count_label()

    def record_audio(self):
        # Start non-blocking recording
        if not self.recording_stream or not self.recording_stream.active:
            self.recording_stream = sd.InputStream(samplerate=self.SAMPLE_RATE, channels=1, callback=self.record_callback, blocksize=1024)
            self.recording_stream.start()

    def play_audio(self):
        # Start playback of the recorded tracks
        if self.playback_stream is None:
            combined_track = np.zeros_like(self.app.gui.recorded_tracks[0])
            for track in self.app.gui.recorded_tracks:
                combined_track += track
            self.playback_position = 0
            self.playback_stream = sd.OutputStream(samplerate=self.SAMPLE_RATE, channels=1, callback=self.playback_callback, blocksize=1024)
            self.playback_stream.start()

            # Fill the initial buffer with data
            while True:
                data = self.playback_callback(None, 1024, None, None)
                if data is not None:
                    self.playback_stream.write(data)
                else:
                    break

    def playback_callback(self, outdata, frames, time, status):
        if outdata is None:
            return

        if len(self.app.gui.recorded_tracks) > 0:
            combined_track = np.zeros_like(self.app.gui.recorded_tracks[0])
            for track in self.app.gui.recorded_tracks:
                combined_track += track

            while True:
                remaining_samples = len(combined_track) - self.playback_position
                if remaining_samples >= frames:
                    outdata[:] = combined_track[self.playback_position:self.playback_position + frames].reshape(-1, 1)
                    self.playback_position += frames
                    break
                else:
                    # Fill the remaining buffer with the end of the combined track
                    outdata[:remaining_samples] = combined_track[self.playback_position:]
                    self.playback_position = 0
                    # Fill the rest of the buffer with the beginning of the combined track
                    outdata[remaining_samples:] = combined_track[:frames - remaining_samples].reshape(-1, 1)
                    self.playback_position += frames - remaining_samples
        else:
            outdata.fill(0)

    def play_audio_loop(self):
        # Play the recorded tracks in a loop during recording
        while self.app.gui.is_recording:
            self.play_audio()
            time.sleep(self.app.gui.duration)

    def stop_recording(self):
        # Stop the recording process
        if self.app.gui.is_recording:
            self.app.gui.is_recording = False
            self.app.gui.record_button.config(text="REC")
            self.app.gui.notification_label.config(text="", bg="red", fg="black", font=("Arial", 12))

            if self.recording_stream and self.recording_stream.active:
                self.recording_stream.stop()
                self.recording_stream.close()
                self.recording_stream = None

    def stop_playback(self):
        # Stop the playback process
        if self.playback_stream:
            self.playback_stream.stop()
            self.playback_stream = None
            self.playback_position = 0
            if self.app.gui.is_playing:
                self.app.gui.is_playing = False
                self.app.gui.play_button.config(text="PLAY/STOP")
                self.app.gui.notification_label.config(text="", fg="black", font=("Arial", 12))