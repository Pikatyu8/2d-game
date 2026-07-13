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
from editor.right_panel.editor_right_panel_prob import RightPanelProbTabMixin  # Новый миксин

class EditorRightPanelMixin(
    RightPanelLevelMixin,
    RightPanelMainTabMixin,
    RightPanelAttacksTabMixin,
    RightPanelMovementTabMixin,
    RightPanelKFramesTabMixin,
    RightPanelFlowTabMixin,
    RightPanelProbTabMixin  # Добавлен миксин вероятностей
):
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

        # Отрисовка двух строк вкладок (по 3 в строке, ширина 60px каждая)
        if target_enemy_raw is not None and game.editor_mode == "ENEMY_EDITOR":
            # Строка 1 (y = 36)
            tab_main_rect = pygame.Rect(1205, 36, 60, 20)
            tab_attacks_rect = pygame.Rect(1270, 36, 60, 20)
            tab_movement_rect = pygame.Rect(1335, 36, 60, 20)
            # Строка 2 (y = 59)
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

        # Сдвиг области отрисовки ниже, так как высота вкладок увеличилась
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