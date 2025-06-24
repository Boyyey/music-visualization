# Universal Music Visualizer

> **Turn your music into mesmerizing visuals!**

---

## 🚀 Features
- **Universal Audio/Video Support:**
  - Play and visualize almost any audio or video file: `.mp3`, `.wav`, `.aac`, `.ogg`, `.flac`, `.wma`, `.mp4`, `.mpeg`, `.m4a`, `.opus`, `.webm`, `.avi`, `.mov`, `.3gp` and more!
- **Real-Time FFT Visualization:**
  - See your music's frequency spectrum come alive with 100 dynamic bars.
- **Modern, Responsive UI:**
  - Smooth, high-FPS (60+) animation in a beautiful window.
- **Cross-Platform:**
  - Works on Windows, macOS, and Linux (Python 3.8+).
- **No Browser Needed:**
  - 100% desktop app. No web server, no nonsense.

---

## 📦 Requirements
- Python 3.8+
- [pydub](https://github.com/jiaaro/pydub)
- [pygame](https://www.pygame.org/)
- [numpy](https://numpy.org/)
- [scipy](https://scipy.org/)
- [tkinter](https://wiki.python.org/moin/TkInter) (usually included with Python)
- ffmpeg (for full audio/video support)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## ⚡ Quick Start

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/MvizM.git
   cd MvizM
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **(Optional) Install ffmpeg:**
   - [Download ffmpeg](https://ffmpeg.org/download.html) and add it to your PATH for best compatibility.
4. **Run the visualizer:**
   ```bash
   python main.py
   ```
5. **Pick any audio/video file and enjoy the show!**

---

## 🧠 How It Works
- Uses `tkinter` to pick a file.
- Loads audio with `pydub` (and ffmpeg for universal support).
- Plays audio with `pygame.mixer`.
- Analyzes audio in real-time using FFT (`scipy.fft`).
- Renders a beautiful spectrum with `pygame`.

---

## 🎨 Customization
- Change `NUM_BARS`, `WIDTH`, `HEIGHT`, and `FPS` in `main.py` for different looks.
- Tweak color schemes and bar shapes for your own vibe.

---

## 🛠️ Troubleshooting
- **No sound or file won't load?**
  - Make sure ffmpeg is installed and in your PATH.
- **tkinter not found?**
  - On Linux: `sudo apt-get install python3-tk`
- **Weird playback or lag?**
  - Try smaller files or lower `NUM_BARS`/`FPS`.

---

## 🤩 Credits
- Inspired by classic Winamp visualizers and modern spectrum analyzers.
- Built with love using open-source Python libraries.

---

## 📜 License
MIT License. Do whatever you want, but a star ⭐️ would be awesome!

---

## 🌟 Star this repo if you like it!

[![GitHub stars](https://img.shields.io/github/stars/yourusername/MvizM?style=social)](https://github.com/yourusername/MvizM)

---

## 💬 Feedback & Contributions
- PRs, issues, and suggestions are welcome!
- Make it wilder, faster, and more beautiful!

---

## 🔗 Links
- [pydub docs](https://github.com/jiaaro/pydub)
- [pygame docs](https://www.pygame.org/docs/)
- [scipy docs](https://docs.scipy.org/doc/scipy/)
- [numpy docs](https://numpy.org/doc/)

---

**Enjoy your music like never before!** 🎶🔥
