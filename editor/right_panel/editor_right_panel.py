# editor/right_panel/editor_right_panel.py
import pygame
from config import PANEL_BG_COLOR, BORDER_COLOR, SCREEN_HEIGHT
from entities.platform_class import Platform
from editor.editor_player_start import PlayerStart

# Импортируем только оставшиеся необходимые суб-миксины
from editor.right_panel.editor_right_panel_level import RightPanelLevelMixin
from editor.right_panel.editor_right_panel_main import RightPanelMainTabMixin

class EditorRightPanelMixin(
    RightPanelLevelMixin,
    RightPanelMainTabMixin
):
    def draw_active_dropdown_overlay(self, mouse_pos):
        game = self.game
        data = game.active_dropdown_data
        options = data["options"]
        box_rect = data["rect"]
        screen_y = data["y_pos_screen"]
        
        option_height = 20
        dropdown_rect = pygame.Rect(box_rect.left, screen_y + 18, box_rect.width, len(options) * option_height)
        
        # Рисуем фон раскрытого списка
        pygame.draw.rect(game.screen, (35, 35, 40), dropdown_rect)
        pygame.draw.rect(game.screen, (100, 100, 110), dropdown_rect, 1)
        
        font = game.get_cached_font(16)
        
        for idx, opt in enumerate(options):
            opt_rect = pygame.Rect(box_rect.left, screen_y + 18 + idx * option_height, box_rect.width, option_height)
            is_hovered = opt_rect.collidepoint(mouse_pos)
            
            if is_hovered:
                pygame.draw.rect(game.screen, (60, 110, 200), opt_rect)
                
            # Адаптивное попиксельное сокращение текста вариантов
            available_w = box_rect.width - 10
            display_text = opt
            w, _ = font.size(display_text)
            if w > available_w:
                while len(display_text) > 0 and font.size(display_text + "..")[0] > available_w:
                    display_text = display_text[:-1]
                display_text = display_text + ".."
                
            opt_img = font.render(display_text, True, (255, 255, 255))
            game.screen.blit(opt_img, (opt_rect.left + 5, opt_rect.centery - opt_img.get_height() // 2))

    def draw_right_panel(self, mouse_clicked_this_frame, target_enemy_raw):
        game = self.game
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. Перехват, обработка и полное поглощение кликов выпадающего меню до интерфейса
        local_clicked = mouse_clicked_this_frame
        if getattr(game, "active_dropdown_id", None) and getattr(game, "active_dropdown_data", None):
            data = game.active_dropdown_data
            options = data["options"]
            box_rect = data["rect"]
            screen_y = data["y_pos_screen"]
            option_height = 20
            dropdown_rect = pygame.Rect(box_rect.left, screen_y + 18, box_rect.width, len(options) * option_height)
            
            if mouse_clicked_this_frame:
                if dropdown_rect.collidepoint(mouse_pos):
                    clicked_idx = (mouse_pos[1] - (screen_y + 18)) // option_height
                    if 0 <= clicked_idx < len(options):
                        game.active_dropdown_selection = (data["id"], clicked_idx)
                
                # Любой клик закрывает выпадающее меню
                game.active_dropdown_id = None
                game.active_dropdown_data = None
                # Сигнал клика сбрасывается для предотвращения клика сквозь панель
                local_clicked = False

        right_panel_rect = pygame.Rect(1200, 0, 200, SCREEN_HEIGHT)
        pygame.draw.rect(game.screen, PANEL_BG_COLOR, right_panel_rect)
        pygame.draw.line(game.screen, BORDER_COLOR, (1200, 0), (1200, SCREEN_HEIGHT), 1)
        
        title_right = self.font_ui.render("PROPERTIES", True, (255, 255, 255))
        game.screen.blit(title_right, (1220, 15))

        if game.editor_mode == "LEVEL_EDITOR":
            game.inspector_tab = "MAIN"

        # В режиме редактирования ИИ теперь всегда активна вкладка GENERAL PROPERTIES (с кнопкой Launch)
        if target_enemy_raw is not None and game.editor_mode == "ENEMY_EDITOR":
            game.inspector_tab = "MAIN"

        clip_rect = pygame.Rect(1200, 84, 200, SCREEN_HEIGHT - 84)
        game.screen.set_clip(clip_rect)
        
        y_offset = 84 - game.right_panel_scroll

        # 1. Свойства объектов в режиме Редактора Уровней
        if game.editor_mode == "LEVEL_EDITOR" and game.selected_instance and isinstance(game.selected_instance, (Platform, PlayerStart)):
            inst = game.selected_instance
            y_offset = self.draw_level_editor_properties(inst, y_offset, local_clicked, mouse_pos)

        # 2. Свойства шаблона врагов (вкладка GENERAL с кнопкой запуска ИИ редактора)
        elif target_enemy_raw is not None:
            if game.inspector_tab == "MAIN":
                y_offset = self.draw_enemy_main_tab(target_enemy_raw, y_offset, local_clicked, mouse_pos)

        total_height = y_offset + game.right_panel_scroll
        game.right_panel_max_scroll = max(0, total_height - (SCREEN_HEIGHT - 30))

        game.screen.set_clip(None)
        
        # Отрисовка раскрытого списка выпадающего меню поверх панелей
        if getattr(game, "active_dropdown_id", None) and getattr(game, "active_dropdown_data", None):
            self.draw_active_dropdown_overlay(mouse_pos)