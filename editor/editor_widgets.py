# editor/editor_widgets.py
import pygame
from config import PANEL_BG_COLOR, BORDER_COLOR, SCREEN_HEIGHT, CANVAS_OFFSET_X

class EditorWidgetsMixin:
    def draw_button(self, rect, text, bg_color, text_color, is_active=False, is_scrollable=False):
        mouse_pos = pygame.mouse.get_pos()
        
        if is_scrollable:
            if rect.left < CANVAS_OFFSET_X:
                if rect.top < 10 or rect.bottom > 480:
                    is_hovered = False
                else:
                    is_hovered = rect.collidepoint(mouse_pos)
            elif rect.left >= 1200:
                if rect.top < 80 or rect.bottom > SCREEN_HEIGHT:
                    is_hovered = False
                else:
                    is_hovered = rect.collidepoint(mouse_pos)
            else:
                is_hovered = rect.collidepoint(mouse_pos)
        else:
            is_hovered = rect.collidepoint(mouse_pos)
        
        draw_color = bg_color
        if is_active:
            draw_color = (60, 110, 200)
        elif is_hovered:
            draw_color = (
                min(255, bg_color[0] + 30),
                min(255, bg_color[1] + 30),
                min(255, bg_color[2] + 30)
            )
            
        pygame.draw.rect(self.game.screen, draw_color, rect)
        pygame.draw.rect(self.game.screen, BORDER_COLOR, rect, 1)
        
        font = pygame.font.SysFont(None, 18)
        text_img = font.render(text, True, text_color)
        self.game.screen.blit(text_img, (rect.centerx - text_img.get_width()//2, rect.centery - text_img.get_height()//2))
        
        return is_hovered

    def draw_property_row(self, label, val_text, y_pos):
        font = pygame.font.SysFont(None, 18)
        lbl_img = font.render(label, True, (180, 180, 180))
        self.game.screen.blit(lbl_img, (1215, y_pos))
        
        btn_minus = pygame.Rect(1310, y_pos - 2, 20, 20)
        btn_plus = pygame.Rect(1375, y_pos - 2, 20, 20)
        
        self.draw_button(btn_minus, "-", (50, 50, 55), (255, 255, 255), is_scrollable=True)
        self.draw_button(btn_plus, "+", (50, 50, 55), (255, 255, 255), is_scrollable=True)
        
        val_img = font.render(str(val_text), True, (255, 255, 255))
        val_x = btn_minus.right + (btn_plus.left - btn_minus.right) // 2 - val_img.get_width() // 2
        self.game.screen.blit(val_img, (val_x, y_pos))
        
        return btn_minus, btn_plus