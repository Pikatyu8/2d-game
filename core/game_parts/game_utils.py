# core/game_parts/game_utils.py
import pygame
import os
import array
import math

class GameUtilsMixin:
    def get_cached_font(self, size, bold=False):
        size = max(6, int(size))
        key = (size, bold)
        if key not in self.font_cache:
            self.font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
        return self.font_cache[key]

    def play_sound(self, sound_name):
        if not pygame.mixer or not pygame.mixer.get_init():
            return
            
        if sound_name not in self.sounds:
            os.makedirs("assets", exist_ok=True)
            sound_file = os.path.join("assets", f"{sound_name}.wav")
            
            if os.path.exists(sound_file):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_file)
                except Exception as e:
                    print(f"Error loading sound {sound_file}: {e}")
                    self.sounds[sound_name] = None
            else:
                sample_rate = 44100
                audio_data = array.array('h')
                
                if sound_name == "parry":
                    duration_ms = 150
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-15 * t)
                        freq = 900 + 400 * (1.0 - t)
                        val = int(25000 * math.sin(2 * math.pi * freq * t) * decay)
                        audio_data.append(val)
                elif sound_name == "damage":
                    duration_ms = 200
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-12 * t)
                        freq = 150 - 60 * t
                        val = int(22000 * math.sin(2 * math.pi * freq * t) * decay)
                        audio_data.append(val)
                else:
                    duration_ms = 100
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-10 * t)
                        val = int(15000 * math.sin(2 * math.pi * 440 * t) * decay)
                        audio_data.append(val)
                        
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(buffer=bytes(audio_data))
                except Exception as e:
                    print(f"Error creating procedural sound {sound_name}: {e}")
                    self.sounds[sound_name] = None
                    
        sound_obj = self.sounds.get(sound_name)
        if sound_obj:
            try:
                sound_obj.play()
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")

    def spawn_projectile(self, x, y, vx, vy, damage=1, radius=8, gravity=0.0, homing=0.0):
        from entities.projectile import Projectile
        self.projectiles.append(Projectile(x, y, vx, vy, damage, radius, gravity, homing))

    def prompt_text_input(self, title, prompt, initial_value=""):
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        result = simpledialog.askstring(title, prompt, initialvalue=initial_value)
        root.destroy()
        return result