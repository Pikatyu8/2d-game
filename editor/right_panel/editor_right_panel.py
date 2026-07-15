# editor/right_panel/editor_right_panel.py
import pygame
from config import PANEL_BG_COLOR, BORDER_COLOR, SCREEN_HEIGHT
from entities.platform_class import Platform
from editor.editor_player_start import PlayerStart

# Импортируем суб-миксины
from editor.right_panel.editor_right_panel_level import RightPanelLevelMixin
from editor.right_panel.editor_right_panel_main import RightPanelMainTabMixin
from editor.right_panel.editor_right_panel_attacks import RightPanelAttacksTabMixin
from editor.right_panel.editor_right_panel_movement import RightPanelMovementTabMixin
from editor.right_panel.editor_right_panel_kframes import RightPanelKFramesTabMixin
from editor.right_panel.editor_right_panel_flow import RightPanelFlowTabMixin
from editor.right_panel.editor_right_panel_prob import RightPanelProbTabMixin

class EditorRightPanelMixin(
    RightPanelLevelMixin,
    RightPanelMainTabMixin,
    RightPanelAttacksTabMixin,
    RightPanelMovementTabMixin,
    RightPanelKFramesTabMixin,
    RightPanelFlowTabMixin,
    RightPanelProbTabMixin
):
    def draw_active_dropdown_overlay(self, mouse_clicked, mouse_pos):
        game = self.game
        data = game.active_dropdown_data
        options = data["options"]
        box_rect = data["rect"]
        screen_y = data["y_pos_screen"]
        
        # Блокировка закрытия списка на кадре его открытия
        if getattr(game, "dropdown_just_opened", False):
            mouse_clicked = False
            game.dropdown_just_opened = False
        
        option_height = 20
        dropdown_rect = pygame.Rect(box_rect.left, screen_y + 18, box_rect.width, len(options) * option_height)
        
        # Рисуем фон раскрытого списка
        pygame.draw.rect(game.screen, (35, 35, 40), dropdown_rect)
        pygame.draw.rect(game.screen, (100, 100, 110), dropdown_rect, 1)
        
        font = game.get_cached_font(16)
        clicked_option_idx = None
        
        for idx, opt in enumerate(options):
            opt_rect = pygame.Rect(box_rect.left, screen_y + 18 + idx * option_height, box_rect.width, option_height)
            is_hovered = opt_rect.collidepoint(mouse_pos)
            
            if is_hovered:
                pygame.draw.rect(game.screen, (60, 110, 200), opt_rect)
                
            display_text = opt
            if len(display_text) > 8:
                display_text = display_text[:6] + ".."
                
            opt_img = font.render(display_text, True, (255, 255, 255))
            game.screen.blit(opt_img, (opt_rect.left + 5, opt_rect.centery - opt_img.get_height() // 2))
            
            if mouse_clicked and is_hovered:
                clicked_option_idx = idx
                
        if mouse_clicked:
            if clicked_option_idx is not None:
                game.active_dropdown_selection = (data["id"], clicked_option_idx)
            game.active_dropdown_id = None
            game.active_dropdown_data = None

    def draw_right_panel(self, mouse_clicked_this_frame, target_enemy_raw):
        game = self.game
        mouse_pos = pygame.mouse.get_pos()
        
        right_panel_rect = pygame.Rect(1200, 0, 200, SCREEN_HEIGHT)
        pygame.draw.rect(game.screen, PANEL_BG_COLOR, right_panel_rect)
        pygame.draw.line(game.screen, BORDER_COLOR, (1200, 0), (1200, SCREEN_HEIGHT), 1)
        
        title_right = self.font_ui.render("PROPERTIES", True, (255, 255, 255))
        game.screen.blit(title_right, (1220, 15))

        if game.editor_mode == "LEVEL_EDITOR":
            game.inspector_tab = "MAIN"

        if target_enemy_raw is not None:
            attacks = target_enemy_raw.setdefault("attacks", [])
            if attacks:
                game.selected_attack_edit_idx = max(0, min(getattr(game, "selected_attack_edit_idx", 0), len(attacks) - 1))
                curr_att = attacks[game.selected_attack_edit_idx]
                shapes = curr_att.setdefault("shapes", [])
            else:
                game.selected_attack_edit_idx = 0
                shapes = []

            projectiles = target_enemy_raw.setdefault("projectiles", [])
            if projectiles:
                game.selected_projectile_edit_idx = max(0, min(getattr(game, "selected_projectile_edit_idx", 0), len(projectiles) - 1))
            else:
                game.selected_projectile_edit_idx = 0

            movements = target_enemy_raw.setdefault("movements", [])
            if movements:
                game.selected_move_edit_idx = max(0, min(getattr(game, "selected_move_edit_idx", 0), len(movements) - 1))
                curr_move = movements[game.selected_move_edit_idx]
                phases = curr_move.setdefault("phases", [])
            else:
                game.selected_move_edit_idx = 0
                phases = []

            if game.inspector_tab == "DETAILED_MOVEMENT" and phases:
                game.selected_box_idx = max(0, min(getattr(game, "selected_box_idx", 0), len(phases) - 1))
            elif game.inspector_tab == "DETAILED_ATTACK" and shapes:
                game.selected_box_idx = max(0, min(getattr(game, "selected_box_idx", 0), len(shapes) - 1))
            else:
                game.selected_box_idx = 0

            seq_list = target_enemy_raw.setdefault("sequences", [])
            if seq_list:
                game.selected_seq_idx = max(0, min(getattr(game, "selected_seq_idx", 0), len(seq_list) - 1))
                curr_seq = seq_list[game.selected_seq_idx]
                steps = curr_seq.setdefault("steps", [])
                if steps:
                    game.selected_step_idx = max(0, min(getattr(game, "selected_step_idx", 0), len(steps) - 1))
                else:
                    game.selected_step_idx = 0
            else:
                game.selected_seq_idx = 0
                game.selected_step_idx = 0

            flows = target_enemy_raw.setdefault("flows", [])
            if flows:
                game.selected_flow_idx = max(0, min(getattr(game, "selected_flow_idx", 0), len(flows) - 1))
                curr_flow = flows[game.selected_flow_idx]
                flow_steps = curr_flow.setdefault("steps", [])
                if flow_steps:
                    game.selected_flow_step_idx = max(0, min(getattr(game, "selected_flow_step_idx", 0), len(flow_steps) - 1))
                else:
                    game.selected_flow_step_idx = 0
            else:
                game.selected_flow_idx = 0
                game.selected_flow_step_idx = 0

        # Обработка выбора из выпадающего списка
        if getattr(game, "active_dropdown_selection", None) is not None:
            dropdown_id, selected_idx = game.active_dropdown_selection
            game.active_dropdown_selection = None
            
            if target_enemy_raw is not None:
                if dropdown_id == "step_attack_template":
                    seq_list = target_enemy_raw.get("sequences", [])
                    if seq_list and game.selected_seq_idx < len(seq_list):
                        curr_seq = seq_list[game.selected_seq_idx]
                        steps = curr_seq.setdefault("steps", [])
                        if steps and game.selected_step_idx < len(steps):
                            steps[game.selected_step_idx]["idx"] = selected_idx
                            game.rebuild_objects()
                elif dropdown_id == "step_movement_template":
                    seq_list = target_enemy_raw.get("sequences", [])
                    if seq_list and game.selected_seq_idx < len(seq_list):
                        curr_seq = seq_list[game.selected_seq_idx]
                        steps = curr_seq.setdefault("steps", [])
                        if steps and game.selected_step_idx < len(steps):
                            steps[game.selected_step_idx]["idx"] = selected_idx
                            game.rebuild_objects()
                elif dropdown_id == "step_projectile_template":
                    seq_list = target_enemy_raw.get("sequences", [])
                    if seq_list and game.selected_seq_idx < len(seq_list):
                        curr_seq = seq_list[game.selected_seq_idx]
                        steps = curr_seq.setdefault("steps", [])
                        if steps and game.selected_step_idx < len(steps):
                            steps[game.selected_step_idx]["idx"] = selected_idx
                            game.rebuild_objects()
                elif dropdown_id == "flow_step_sequence":
                    flows = target_enemy_raw.get("flows", [])
                    if flows and game.selected_flow_idx < len(flows):
                        curr_flow = flows[game.selected_flow_idx]
                        flow_steps = curr_flow.setdefault("steps", [])
                        if flow_steps and game.selected_flow_step_idx < len(flow_steps):
                            flow_steps[game.selected_flow_step_idx]["seq_idx"] = selected_idx
                            game.rebuild_objects()

        # Отрисовка двух строк вкладок (y = 36 и y = 59)
        if target_enemy_raw is not None and game.editor_mode == "ENEMY_EDITOR":
            tab_main_rect = pygame.Rect(1205, 36, 60, 20)
            tab_attacks_rect = pygame.Rect(1270, 36, 60, 20)
            tab_movement_rect = pygame.Rect(1335, 36, 60, 20)
            tab_kframes_rect = pygame.Rect(1205, 59, 60, 20)
            tab_flow_rect = pygame.Rect(1270, 59, 60, 20)
            tab_prob_rect = pygame.Rect(1335, 59, 60, 20)
            
            if self.draw_button(tab_main_rect, "GEN", (45, 45, 50), (255, 255, 255), game.inspector_tab == "MAIN") and mouse_clicked_this_frame:
                game.inspector_tab = "MAIN"
                game.right_panel_scroll = 0
            if self.draw_button(tab_attacks_rect, "ATK", (45, 45, 50), (255, 255, 255), game.inspector_tab in ("ATTACKS", "DETAILED_ATTACK", "DETAILED_PROJECTILE")) and mouse_clicked_this_frame:
                game.inspector_tab = "ATTACKS"
                game.right_panel_scroll = 0
            if self.draw_button(tab_movement_rect, "MOVE", (45, 45, 50), (255, 255, 255), game.inspector_tab in ("MOVEMENT", "DETAILED_MOVEMENT")) and mouse_clicked_this_frame:
                game.inspector_tab = "MOVEMENT"
                game.right_panel_scroll = 0
            if self.draw_button(tab_kframes_rect, "K-FRM", (45, 45, 50), (255, 255, 255), game.inspector_tab == "K-FRAMES") and mouse_clicked_this_frame:
                game.inspector_tab = "K-FRAMES"
                game.right_panel_scroll = 0
            if self.draw_button(tab_flow_rect, "FLOW", (45, 45, 50), (255, 255, 255), game.inspector_tab in ("FLOW", "DETAILED_FLOW")) and mouse_clicked_this_frame:
                game.inspector_tab = "FLOW"
                game.right_panel_scroll = 0
            if self.draw_button(tab_prob_rect, "PROB", (45, 45, 50), (255, 255, 255), game.inspector_tab == "PROBABILITY") and mouse_clicked_this_frame:
                game.inspector_tab = "PROBABILITY"
                game.right_panel_scroll = 0

        clip_rect = pygame.Rect(1200, 84, 200, SCREEN_HEIGHT - 84)
        game.screen.set_clip(clip_rect)
        
        y_offset = 84 - game.right_panel_scroll

        # 1. Свойства объектов в режиме Редактора Уровней
        if game.editor_mode == "LEVEL_EDITOR" and game.selected_instance and isinstance(game.selected_instance, (Platform, PlayerStart)):
            inst = game.selected_instance
            y_offset = self.draw_level_editor_properties(inst, y_offset, mouse_clicked_this_frame, mouse_pos)

        # 2. Свойства шаблона врагов (по вкладкам)
        elif target_enemy_raw is not None:
            if game.inspector_tab == "MAIN":
                y_offset = self.draw_enemy_main_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "ATTACKS":
                y_offset = self.draw_enemy_attacks_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "DETAILED_ATTACK":
                y_offset = self.draw_enemy_detailed_attack_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "DETAILED_PROJECTILE":
                y_offset = self.draw_enemy_detailed_projectile_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "MOVEMENT":
                y_offset = self.draw_enemy_movement_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "DETAILED_MOVEMENT":
                y_offset = self.draw_enemy_detailed_movement_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "K-FRAMES":
                y_offset = self.draw_enemy_kframes_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "FLOW":
                y_offset = self.draw_enemy_flow_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "DETAILED_FLOW":
                y_offset = self.draw_enemy_detailed_flow_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)
            elif game.inspector_tab == "PROBABILITY":
                y_offset = self.draw_enemy_probability_tab(target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos)

        total_height = y_offset + game.right_panel_scroll
        game.right_panel_max_scroll = max(0, total_height - (SCREEN_HEIGHT - 30))

        game.screen.set_clip(None)
        
        # Отрисовка раскрытого списка выпадающего меню поверх панелей
        if getattr(game, "active_dropdown_id", None) and getattr(game, "active_dropdown_data", None):
            self.draw_active_dropdown_overlay(mouse_clicked_this_frame, mouse_pos)