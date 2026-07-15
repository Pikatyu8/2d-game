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
        
        font = self.game.get_cached_font(18)
        text_img = font.render(text, True, text_color)
        self.game.screen.blit(text_img, (rect.centerx - text_img.get_width()//2, rect.centery - text_img.get_height()//2))
        
        return is_hovered

    def draw_property_row(self, label, val_text, y_pos):
        font = self.game.get_cached_font(18)
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

    def draw_dropdown(self, label, options, current_idx, y_pos, dropdown_id, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        font = game.get_cached_font(18)
        
        # Отрисовка названия поля
        lbl_img = font.render(label, True, (180, 180, 180))
        game.screen.blit(lbl_img, (1215, y_pos))
        
        # Отрисовка поля выпадающего списка
        box_rect = pygame.Rect(1310, y_pos - 2, 80, 20)
        is_hovered = box_rect.collidepoint(mouse_pos)
        
        bg_color = (60, 60, 65) if is_hovered else (50, 50, 55)
        pygame.draw.rect(game.screen, bg_color, box_rect)
        pygame.draw.rect(game.screen, BORDER_COLOR, box_rect, 1)
        
        current_text = options[current_idx] if 0 <= current_idx < len(options) else "None"
        display_text = current_text
        if len(display_text) > 8:
            display_text = display_text[:6] + ".."
            
        val_img = font.render(display_text, True, (255, 255, 255))
        game.screen.blit(val_img, (box_rect.left + 5, box_rect.centery - val_img.get_height() // 2))
        
        # Стрелочка индикатора выпадающего меню
        arrow_img = font.render("v", True, (150, 150, 150))
        game.screen.blit(arrow_img, (box_rect.right - 12, box_rect.centery - arrow_img.get_height() // 2))
        
        if mouse_clicked_this_frame and is_hovered:
            if getattr(game, "active_dropdown_id", None) == dropdown_id:
                game.active_dropdown_id = None
                game.active_dropdown_data = None
            else:
                game.active_dropdown_id = dropdown_id
                game.dropdown_just_opened = True  # Активируем блокировку мгновенного закрытия
                game.active_dropdown_data = {
                    "id": dropdown_id,
                    "rect": box_rect,
                    "options": options,
                    "current_idx": current_idx,
                    "y_pos_screen": y_pos  # Используем чистую Y координату
                }