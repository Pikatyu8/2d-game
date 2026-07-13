# editor/editor_left_panel.py
import pygame
import copy
from config import PANEL_BG_COLOR, BORDER_COLOR, SCREEN_HEIGHT, CANVAS_OFFSET_X, DEFAULT_LEVEL_DATA

class EditorLeftPanelMixin:
    def draw_left_panel(self, mouse_clicked_this_frame):
        game = self.game
        left_panel_rect = pygame.Rect(0, 0, CANVAS_OFFSET_X, SCREEN_HEIGHT)
        pygame.draw.rect(game.screen, PANEL_BG_COLOR, left_panel_rect)
        pygame.draw.line(game.screen, BORDER_COLOR, (CANVAS_OFFSET_X, 0), (CANVAS_OFFSET_X, SCREEN_HEIGHT), 1)
        
        clip_rect = pygame.Rect(0, 10, CANVAS_OFFSET_X, 470)
        game.screen.set_clip(clip_rect)
        
        y_offset = 20 - game.left_panel_scroll
        
        if game.editor_mode == "ENEMY_EDITOR":
            title_left = self.font_ui.render("ENEMY TEMPLATES", True, (255, 255, 255))
            game.screen.blit(title_left, (20, y_offset))
            y_offset += 30
            
            preset_names = sorted(list(game.presets.keys()))
            for name in preset_names:
                p_btn = pygame.Rect(15, y_offset, 170, 28)
                is_active = (game.selected_preset_name == name)
                if self.draw_button(p_btn, name, (45, 45, 50), (255, 255, 255), is_active, is_scrollable=True) and mouse_clicked_this_frame:
                    game.selected_preset_name = name
                    game.selected_trigger_idx = 0
                    game.selected_attack_edit_idx = 0
                    game.selected_box_idx = 0
                    game.inspector_tab = "MAIN"
                    game.right_panel_scroll = 0
                    game.rebuild_objects()
                y_offset += 35
        else:
            title_left = self.font_ui.render("CREATION BRUSH", True, (255, 255, 255))
            game.screen.blit(title_left, (20, y_offset))
            y_offset += 30
            
            brushes = ["Selection", "Platform"] + sorted(list(game.presets.keys()))
            for brush in brushes:
                b_rect = pygame.Rect(15, y_offset, 170, 26)
                is_active = (game.selected_brush == brush)
                if self.draw_button(b_rect, brush, (45, 45, 50), (255, 255, 255), is_active, is_scrollable=True) and mouse_clicked_this_frame:
                    if game.editor_mode == "LEVEL_EDITOR":
                        game.selected_brush = brush
                y_offset += 32
                
            y_offset += 15
            level_title = self.font_ui.render("AVAILABLE LEVELS", True, (255, 180, 100))
            game.screen.blit(level_title, (20, y_offset))
            y_offset += 25
            
            for lvl_file in game.available_levels:
                lvl_btn = pygame.Rect(15, y_offset, 170, 26)
                is_active = (game.current_level_name == lvl_file)
                display_name = lvl_file.replace(".json", "").replace("_", " ").title()
                
                if self.draw_button(lvl_btn, display_name, (40, 40, 45), (255, 255, 255), is_active, is_scrollable=True) and mouse_clicked_this_frame:
                    game.current_level_name = lvl_file
                    game.selected_instance = None
                    game.right_panel_scroll = 0
                    game.load_level()
                y_offset += 32

            new_level_rect = pygame.Rect(15, y_offset, 170, 26)
            if self.draw_button(new_level_rect, "+ NEW LEVEL", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                game.create_new_level()
            y_offset += 32

        total_height = y_offset + game.left_panel_scroll
        game.left_panel_max_scroll = max(0, total_height - 470)

        game.screen.set_clip(None)
        
        pygame.draw.line(game.screen, BORDER_COLOR, (0, 480), (CANVAS_OFFSET_X, 480), 1)
        pygame.draw.rect(game.screen, PANEL_BG_COLOR, (0, 481, CANVAS_OFFSET_X, SCREEN_HEIGHT - 481))
        
        if game.editor_mode == "ENEMY_EDITOR":
            new_preset_rect = pygame.Rect(15, 490, 170, 28)
            if self.draw_button(new_preset_rect, "+ NEW PRESET", (35, 80, 45), (255, 255, 255)) and mouse_clicked_this_frame:
                new_name = f"Custom Boss {len(game.presets) + 1}"
                game.presets[new_name] = copy.deepcopy(DEFAULT_LEVEL_DATA["presets"]["Heavy Knight"])
                game.normalize_enemy_raw(game.presets[new_name])
                game.selected_preset_name = new_name
                game.selected_trigger_idx = 0
                game.selected_attack_edit_idx = 0
                game.selected_box_idx = 0
                game.inspector_tab = "MAIN"
                game.right_panel_scroll = 0
                game.left_panel_scroll = 0
                game.rebuild_objects()
        else:
            grid_rect = pygame.Rect(15, 490, 170, 28)
            grid_text = f"GRID SNAP: {'ON' if game.snap_to_grid else 'OFF'}"
            if self.draw_button(grid_rect, grid_text, (45, 45, 50), (255, 255, 255), game.snap_to_grid) and mouse_clicked_this_frame:
                if game.editor_mode == "LEVEL_EDITOR":
                    game.snap_to_grid = not game.snap_to_grid

        save_rect = pygame.Rect(15, 525, 170, 28)
        if self.draw_button(save_rect, "SAVE ALL", (35, 80, 45), (255, 255, 255)) and mouse_clicked_this_frame:
            game.save_level()

        if game.editor_mode == "GAMEPLAY":
            mode_text, mode_color = "GAMEPLAY MODE (E)", (50, 180, 100)
        elif game.editor_mode == "LEVEL_EDITOR":
            mode_text, mode_color = "LEVEL EDITOR (E)", (180, 180, 50)
        else:
            mode_text, mode_color = "ENEMY EDITOR (E)", (220, 100, 50)
            
        mode_img = self.font_ui.render(mode_text, True, mode_color)
        game.screen.blit(mode_img, (20, SCREEN_HEIGHT - 40))