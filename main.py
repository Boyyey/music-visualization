import os
import sys
import numpy as np
from pydub import AudioSegment
from scipy.fft import fft
import pygame
import tkinter as tk
from tkinter import filedialog

# --- CONFIG ---
FPS = 60
CHUNK_SIZE = 1024  # Number of samples per frame
NUM_BARS = 100
WIDTH, HEIGHT = 900, 600

# --- FILE PICKER ---
def pick_audio_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Audio File",
        filetypes=[("Audio/Video Files", ".mp3 .wav .aac .ogg .flac .wma .mp4 .mpeg .m4a .opus .webm .avi .mov .3gp")]
    )
    return file_path

# --- LOAD AUDIO ---
def load_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_channels(1)  # Mono
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= np.iinfo(audio.array_type).max  # Normalize to [-1, 1]
    return samples, audio.frame_rate, len(audio) / 1000

# --- MAIN VISUALIZER ---
def main():
    file_path = pick_audio_file()
    if not file_path:
        print("No file selected.")
        return
    print(f"Loading: {file_path}")
    samples, sample_rate, duration = load_audio(file_path)
    print(f"Sample rate: {sample_rate} Hz, Duration: {duration:.2f} sec")

    # --- Pygame Setup ---
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Universal Music Visualizer")
    clock = pygame.time.Clock()

    # --- Audio Playback ---
    pygame.mixer.init(frequency=sample_rate)
    # Save to temp WAV for playback
    from tempfile import NamedTemporaryFile
    temp_wav = NamedTemporaryFile(delete=False, suffix='.wav')
    AudioSegment.from_file(file_path).export(temp_wav.name, format="wav")
    temp_wav.close()  # Ensure file is closed before pygame loads it
    pygame.mixer.music.load(temp_wav.name)
    pygame.mixer.music.play()

    # --- Visualization Loop ---
    pos = 0
    running = True
    while running and pygame.mixer.music.get_busy():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Get current playback position
        ms = pygame.mixer.music.get_pos()
        pos = int((ms / 1000.0) * sample_rate)
        chunk = samples[pos:pos+CHUNK_SIZE]
        if len(chunk) < CHUNK_SIZE:
            chunk = np.pad(chunk, (0, CHUNK_SIZE - len(chunk)))

        # FFT
        spectrum = np.abs(fft(chunk))[:CHUNK_SIZE//2]
        spectrum = spectrum[:NUM_BARS]
        spectrum = np.log1p(spectrum)  # Log scale for better visuals
        spectrum /= spectrum.max() if spectrum.max() > 0 else 1

        # Draw bars
        screen.fill((10, 10, 30))
        bar_width = WIDTH // NUM_BARS
        for i in range(NUM_BARS):
            mag = int(spectrum[i] * (HEIGHT - 50))  # Ensure mag is int
            color = (100, 200 + int(55*mag/(HEIGHT-50)), 255 - int(200*mag/(HEIGHT-50)))
            pygame.draw.rect(screen, color, (i*bar_width, HEIGHT-mag, bar_width-2, mag))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.mixer.music.stop()
    pygame.quit()
    os.unlink(temp_wav.name)

if __name__ == "__main__":
    main()
