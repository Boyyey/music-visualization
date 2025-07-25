import os
import sys
import numpy as np
from pydub import AudioSegment
from scipy.fft import fft
import pygame
import tkinter as tk
from tkinter import filedialog
from tempfile import NamedTemporaryFile

# --- CONFIG ---
FPS = 60
CHUNK_SIZE = 1024  # Number of samples per frame
NUM_BARS = 100
WIDTH, HEIGHT = 1100, 700

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
    temp_wav = NamedTemporaryFile(delete=False, suffix='.wav')
    AudioSegment.from_file(file_path).export(temp_wav.name, format="wav")
    temp_wav.close()
    pygame.mixer.music.load(temp_wav.name)
    pygame.mixer.music.play()

    # --- Controls State ---
    paused = False
    running = True
    seek_drag = False
    seek_drag_start = False
    song_length = duration
    font = pygame.font.SysFont('Segoe UI', 24)
    bar_rect = pygame.Rect(50, HEIGHT-100, WIDTH-100, 20)
    seek_color = (0, 200, 255)
    seek_handle_color = (255, 255, 255)
    seek_handle_radius = 10
    skip_amount = 5  # seconds to skip forward/back
    last_btn_click = None
    playback_pos = 0  # in seconds
    stopped = False
    last_playback_pos = 0  # Track last position for resume
    dream_mode = False
    dream_trail = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dream_trail.set_alpha(80)

    # Button layout
    ctrl_bar_y = HEIGHT - 60
    btn_w = 40
    btn_h = 40
    btn_gap = 30
    btns = [
        ("play", (WIDTH//2-45, ctrl_bar_y), "Play"),
        ("pause", (WIDTH//2, ctrl_bar_y), "Pause"),
        ("stop", (WIDTH//2+45, ctrl_bar_y), "Stop"),
    ]

    # --- Animated Background State ---
    bg_particles = [
        {
            'x': np.random.uniform(0, WIDTH),
            'y': np.random.uniform(0, HEIGHT),
            'r': np.random.uniform(40, 120),
            'vx': np.random.uniform(-0.1, 0.1),
            'vy': np.random.uniform(-0.05, 0.05),
            'hue': np.random.uniform(0, 360)
        }
        for _ in range(18)
    ]

    # --- 3D Wave Function State ---
    grid_cols = 40
    grid_rows = 18
    grid_spacing_x = WIDTH // (grid_cols-2)
    grid_spacing_y = (HEIGHT-200) // (grid_rows-2)
    wave_amp = 38
    wave_speed = 1.2

    def draw_icon(label, rect, active):
        cx, cy = rect.center
        color = (180,220,255) if active else (200,200,200)
        if label == "play":
            pygame.draw.polygon(screen, color, [(cx-8, cy-12), (cx-8, cy+12), (cx+12, cy)])
        elif label == "pause":
            pygame.draw.rect(screen, color, (cx-10, cy-12, 7, 24))
            pygame.draw.rect(screen, color, (cx+3, cy-12, 7, 24))
        elif label == "stop":
            pygame.draw.rect(screen, color, (cx-12, cy-12, 24, 24))

    def draw_seek_bar(current_sec):
        pygame.draw.rect(screen, (40, 40, 60), bar_rect, border_radius=10)
        fill_width = int(bar_rect.width * (current_sec / song_length))
        pygame.draw.rect(screen, seek_color, (bar_rect.x, bar_rect.y, fill_width, bar_rect.height), border_radius=10)
        handle_x = bar_rect.x + fill_width
        pygame.draw.circle(screen, seek_handle_color, (handle_x, bar_rect.centery), seek_handle_radius)
        t1 = f"{int(current_sec//60):02}:{int(current_sec%60):02}"
        t2 = f"{int(song_length//60):02}:{int(song_length%60):02}"
        text = font.render(f"{t1} / {t2}", True, (200, 220, 255))
        screen.blit(text, (bar_rect.x, bar_rect.y-28))

    def set_song_pos(sec, play=True):
        nonlocal playback_pos, stopped, paused, last_playback_pos
        playback_pos = max(0, min(song_length-0.1, sec))
        last_playback_pos = playback_pos
        if play:
            pygame.mixer.music.play(start=playback_pos)
            paused = False
            stopped = False

    def draw_3d_bar(x, base_y, width, height, color, gap=2):
        # Face
        face_color = tuple(int(c*0.85) for c in color)
        pygame.draw.rect(screen, face_color, (x, base_y-height, width-gap, height))
        # Top (lighter)
        top_color = tuple(min(255, int(c*1.15)) for c in color)
        points = [
            (x, base_y-height),
            (x+width-gap, base_y-height),
            (x+width-gap-8, base_y-height-12),
            (x+8, base_y-height-12)
        ]
        pygame.draw.polygon(screen, top_color, points)
        # Optional: Floor reflection
        reflect_color = color + (60,)
        surf = pygame.Surface((width-gap, int(height*0.5)), pygame.SRCALPHA)
        pygame.draw.rect(surf, reflect_color, (0, 0, width-gap, int(height*0.5)))
        screen.blit(surf, (x, base_y+2))

    # --- Visualization Loop ---
    pos = 0
    btn_pressed = None
    while running:
        btn_clicked = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if paused or stopped:
                        set_song_pos(playback_pos, play=True)
                    else:
                        pygame.mixer.music.pause()
                        paused = True
                elif event.key == pygame.K_s:
                    pygame.mixer.music.stop()
                    playback_pos = 0
                    stopped = True
                    paused = False
                elif event.key == pygame.K_d:
                    dream_mode = not dream_mode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and bar_rect.collidepoint(event.pos):
                    seek_drag = True
                    seek_drag_start = True
                if event.button == 1:
                    mx, my = event.pos
                    for label, (x, y), tooltip in btns:
                        rect = pygame.Rect(x, y, btn_w, btn_h)
                        if rect.collidepoint((mx, my)):
                            btn_pressed = label
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and seek_drag:
                    seek_drag = False
                    mouse_x = event.pos[0]
                    rel = (mouse_x - bar_rect.x) / bar_rect.width
                    rel = min(max(rel, 0), 1)
                    set_song_pos(rel * song_length, play=not paused and not stopped)
                seek_drag_start = False
                if event.button == 1 and btn_pressed:
                    mx, my = event.pos
                    for label, (x, y), tooltip in btns:
                        rect = pygame.Rect(x, y, btn_w, btn_h)
                        if rect.collidepoint((mx, my)) and btn_pressed == label:
                            if label == "play":
                                set_song_pos(playback_pos, play=True)
                            elif label == "pause":
                                pygame.mixer.music.pause()
                                paused = True
                            elif label == "stop":
                                pygame.mixer.music.stop()
                                playback_pos = 0
                                stopped = True
                                paused = False
                    btn_pressed = None

        # Update playback position
        if not paused and not stopped and pygame.mixer.music.get_busy():
            ms = pygame.mixer.music.get_pos()
            playback_pos = ms / 1000.0
            last_playback_pos = playback_pos
            pos = int(playback_pos * sample_rate)
        else:
            ms = pygame.mixer.music.get_pos()
            pos = int(playback_pos * sample_rate)

        # Always compute spectrum
        chunk = samples[pos:pos+CHUNK_SIZE]
        if len(chunk) < CHUNK_SIZE:
            chunk = np.pad(chunk, (0, CHUNK_SIZE - len(chunk)))
        spectrum = np.abs(fft(chunk))[:CHUNK_SIZE//2]
        spectrum = spectrum[:NUM_BARS]
        spectrum = np.log1p(spectrum)
        spectrum /= spectrum.max() if spectrum.max() > 0 else 1

        t = pygame.time.get_ticks() / 1000.0  # Ensure t is defined before 3D wave

        # --- 3D Wave Function (drawn first, as background) ---
        wave_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for gx in range(grid_cols):
            for gy in range(grid_rows):
                # Map grid to spectrum
                spec_idx = int((gx / (grid_cols-1)) * (NUM_BARS-1))
                mag = spectrum[spec_idx]
                # Wave height modulated by spectrum and time
                z = int(wave_amp * mag * np.sin(t*wave_speed + gx*0.3 + gy*0.5))
                # Perspective projection
                px = int(gx * grid_spacing_x)
                py = int(gy * grid_spacing_y + 120 + z)
                # Color based on height
                base_hue = (t*10 + gx*8 + gy*8) % 360
                import colorsys
                color = tuple(int(c*255) for c in colorsys.hsv_to_rgb(base_hue/360, 0.18, 0.18 + 0.5*mag))
                # Draw point
                pygame.draw.circle(wave_surface, color + (90,), (px, py), 3)
                # Optionally, connect to right and down neighbors for mesh effect
                if gx < grid_cols-1:
                    spec_idx2 = int(((gx+1) / (grid_cols-1)) * (NUM_BARS-1))
                    mag2 = spectrum[spec_idx2]
                    z2 = int(wave_amp * mag2 * np.sin(t*wave_speed + (gx+1)*0.3 + gy*0.5))
                    px2 = int((gx+1) * grid_spacing_x)
                    py2 = int(gy * grid_spacing_y + 120 + z2)
                    pygame.draw.line(wave_surface, color + (60,), (px, py), (px2, py2), 2)
                if gy < grid_rows-1:
                    spec_idx2 = int((gx / (grid_cols-1)) * (NUM_BARS-1))
                    mag2 = spectrum[spec_idx2]
                    z2 = int(wave_amp * mag2 * np.sin(t*wave_speed + gx*0.3 + (gy+1)*0.5))
                    px2 = int(gx * grid_spacing_x)
                    py2 = int((gy+1) * grid_spacing_y + 120 + z2)
                    pygame.draw.line(wave_surface, color + (60,), (px, py), (px2, py2), 2)
        screen.blit(wave_surface, (0,0))

        # --- Animated Background ---
        t = pygame.time.get_ticks() / 1000.0
        # Draw gradient background to a separate surface
        bg_surface = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            hue = (t*8 + y/HEIGHT*120) % 360
            import colorsys
            rgb = tuple(int(c*255) for c in colorsys.hsv_to_rgb(hue/360, 0.35, 0.28 + 0.22*np.sin(t*0.2+y/HEIGHT*2)))
            pygame.draw.line(bg_surface, rgb, (0, y), (WIDTH, y))
        # Faint drifting particles (drawn to bg_surface)
        for p in bg_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['hue'] = (p['hue'] + 0.1) % 360
            if p['x'] < -p['r'] or p['x'] > WIDTH + p['r']:
                p['x'] = np.random.uniform(0, WIDTH)
            if p['y'] < -p['r'] or p['y'] > HEIGHT + p['r']:
                p['y'] = np.random.uniform(0, HEIGHT)
            color = tuple(int(c*255) for c in colorsys.hsv_to_rgb(p['hue']/360, 0.25, 0.45))
            surf = pygame.Surface((int(p['r']*2), int(p['r']*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, color + (60,), (int(p['r']), int(p['r'])), int(p['r']))
            bg_surface.blit(surf, (int(p['x']-p['r']), int(p['y']-p['r'])))
        # Blit the background to the main screen
        screen.blit(bg_surface, (0,0))

        if dream_mode:
            # --- DREAM MODE VISUALIZATION (as in first iteration) ---
            screen.blit(dream_trail, (0,0))
            dream_trail.fill((0,0,0,0))
            bar_width = WIDTH // NUM_BARS
            center_x, center_y = WIDTH // 2, (HEIGHT - 180) // 2 + 40
            radius = min(center_x, center_y) - 40
            t = pygame.time.get_ticks() / 1000.0
            base_hue = (t * 10) % 360
            def hsv2rgb(h, s, v):
                import colorsys
                return tuple(int(c*255) for c in colorsys.hsv_to_rgb(h/360, s, v))
            for i in range(NUM_BARS):
                angle = (2 * np.pi * i / NUM_BARS) + t * 0.15
                mag = spectrum[i]
                bar_len = int(80 + mag * (radius-80) * (1.1 + 0.7*np.sin(t+angle)))
                hue = (base_hue + i*360/NUM_BARS) % 360
                color = hsv2rgb(hue, 0.7, 1.0)
                x1 = int(center_x + np.cos(angle) * 80)
                y1 = int(center_y + np.sin(angle) * 80)
                x2 = int(center_x + np.cos(angle) * bar_len)
                y2 = int(center_y + np.sin(angle) * bar_len)
                pygame.draw.line(dream_trail, color + (120,), (x1, y1), (x2, y2), 7)
            pulse = 1.0 + 0.25*np.sin(t*2 + np.sum(spectrum))
            pygame.draw.circle(dream_trail, hsv2rgb((base_hue+180)%360, 0.5, 1.0) + (90,), (center_x, center_y), int(70*pulse))
            for i in range(NUM_BARS):
                angle = (2 * np.pi * i / NUM_BARS) + t * 0.2
                mag = spectrum[i]
                r = int(radius + 30*np.sin(t+angle+mag*2))
                hue = (base_hue + 180 + i*360/NUM_BARS) % 360
                color = hsv2rgb(hue, 0.5, 0.7)
                x = int(center_x + np.cos(angle) * r)
                y = int(center_y + np.sin(angle) * r)
                pygame.draw.circle(dream_trail, color + (110,), (x, y), 10)
            for i in range(NUM_BARS):
                mag = int(spectrum[i] * (HEIGHT - 140))
                hue = (base_hue + i*360/NUM_BARS) % 360
                color = hsv2rgb(hue, 0.7, 1.0)
                rel = abs(i - NUM_BARS/2) / (NUM_BARS/2)
                width = int(bar_width * (1.2 - 0.5*rel))
                x = int(i*bar_width + (bar_width-width)//2)
                base_y = HEIGHT-140
                draw_3d_bar(x, base_y, width, mag, color, gap=2)
            screen.blit(dream_trail, (0,0))
            dream_text = font.render("Dream Mode", True, (180, 220, 255))
            screen.blit(dream_text, (20, 20))
        else:
            # --- DEFAULT VISUALIZATION (always show when not in Dream Mode) ---
            screen.fill((10, 10, 30))
            bar_width = WIDTH // NUM_BARS
            center_x, center_y = WIDTH // 2, (HEIGHT - 180) // 2 + 40
            radius = min(center_x, center_y) - 40
            t = pygame.time.get_ticks() / 1000.0
            base_hue = (t * 30) % 360
            def hsv2rgb(h, s, v):
                import colorsys
                return tuple(int(c*255) for c in colorsys.hsv_to_rgb(h/360, s, v))
            for i in range(NUM_BARS):
                angle = (2 * np.pi * i / NUM_BARS) + t * 0.5
                mag = spectrum[i]
                bar_len = int(80 + mag * (radius-80) * (1.2 + 0.8*np.sin(t+angle)))
                hue = (base_hue + i*360/NUM_BARS) % 360
                color = hsv2rgb(hue, 0.8, 1.0)
                x1 = int(center_x + np.cos(angle) * 80)
                y1 = int(center_y + np.sin(angle) * 80)
                x2 = int(center_x + np.cos(angle) * bar_len)
                y2 = int(center_y + np.sin(angle) * bar_len)
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)
            pulse = 1.0 + 0.15*np.sin(t*4 + np.sum(spectrum))
            pygame.draw.circle(screen, hsv2rgb((base_hue+180)%360, 0.7, 1.0), (center_x, center_y), int(60*pulse))
            for i in range(NUM_BARS):
                angle = (2 * np.pi * i / NUM_BARS) + t * 0.7
                mag = spectrum[i]
                r = int(radius + 18*np.sin(t*2+angle+mag*2))
                hue = (base_hue + 180 + i*360/NUM_BARS) % 360
                color = hsv2rgb(hue, 0.6, 0.8)
                x = int(center_x + np.cos(angle) * r)
                y = int(center_y + np.sin(angle) * r)
                pygame.draw.circle(screen, color, (x, y), 6)
                mag = int(spectrum[i] * (HEIGHT - 140))
                hue = (base_hue + i*360/NUM_BARS) % 360
                color = hsv2rgb(hue, 0.7, 1.0)
                rel = abs(i - NUM_BARS/2) / (NUM_BARS/2)
                width = int(bar_width * (1.2 - 0.5*rel))
                x = int(i*bar_width + (bar_width-width)//2)
                base_y = HEIGHT-140
                draw_3d_bar(x, base_y, width, mag, color, gap=2)

        # Draw seek bar
        cur_sec = playback_pos
        draw_seek_bar(cur_sec)

        # Draw control bar and buttons
        for label, (x, y), tooltip in btns:
            rect = pygame.Rect(x, y, btn_w, btn_h)
            draw_icon(label, rect, False)
            if rect.collidepoint(pygame.mouse.get_pos()):
                tip = font.render(tooltip, True, (120,200,255))
                screen.blit(tip, (x+btn_w//2-tip.get_width()//2, y-32))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.mixer.music.stop()
    pygame.quit()
    os.unlink(temp_wav.name)

if __name__ == "__main__":
    main()
