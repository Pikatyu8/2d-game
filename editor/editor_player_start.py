# editor/editor_player_start.py
import pygame

class PlayerStart:
    def __init__(self, raw_data):
        self.rect = pygame.Rect(raw_data.get("start_x", 100), raw_data.get("start_y", 300), 30, 50)
        self.raw_data = raw_data