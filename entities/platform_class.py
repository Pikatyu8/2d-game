# entities/platform_class.py
import pygame
from config import CANVAS_OFFSET_X

class Platform:
    def __init__(self, resolved_data, raw_data):
        self.rect = pygame.Rect(resolved_data["x"], resolved_data["y"], resolved_data["w"], resolved_data["h"])
        self.color = resolved_data.get("color", [100, 100, 100])
        self.raw_data = raw_data

    def draw(self, surface, camera_x=0, camera_y=0, zoom=1.0):
        # Позиция и размеры масштабируются относительно точки начала координат
        sx = CANVAS_OFFSET_X + (self.rect.x - camera_x) * zoom
        sy = (self.rect.y - camera_y) * zoom
        sw = max(1.0, self.rect.width * zoom)
        sh = max(1.0, self.rect.height * zoom)
        pygame.draw.rect(surface, self.color, (sx, sy, sw, sh))