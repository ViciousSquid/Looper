import tkinter as tk
from looper_gui import LoopPedalGUI
from looper_audio import LoopPedalAudio
from looper_utils import LoopPedalUtils


class LoopPedalApp:
    def __init__(self, root):
        self.root = root
        self.gui = LoopPedalGUI(self)
        self.audio = LoopPedalAudio(self)
        self.utils = LoopPedalUtils(self)
        

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Looper")
    root.resizable(False, False)
    app = LoopPedalApp(root)
    app.run()
