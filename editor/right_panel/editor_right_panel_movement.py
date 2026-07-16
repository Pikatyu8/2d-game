# editor/right_panel/editor_right_panel_movement.py
import pygame
import copy
from config import BORDER_COLOR

class RightPanelMovementTabMixin:
    def draw_enemy_movement_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        lbl_title = self.font_ui.render("MOVEMENT CONFIG", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 25
        
        move_cfg = target_enemy_raw.setdefault("movement_config", {})
        type_move = move_cfg.setdefault("type_move", "walking")
        
        type_minus, type_plus = self.draw_property_row("Move Type", type_move, y_offset)
        y_offset += 26
        
        spd_minus, spd_plus = self.draw_property_row("Base Spd", round(move_cfg.setdefault("speed", 1.2), 1), y_offset)
        y_offset += 26
        
        rng_minus, rng_plus = self.draw_property_row("Patrol Rng", move_cfg.setdefault("range_x", 120), y_offset)
        y_offset += 26
        
        stop_minus, stop_plus = self.draw_property_row("Stop Dist", move_cfg.setdefault("stop_dist", 60), y_offset)
        y_offset += 35
        
        patrol_plat = move_cfg.setdefault("patrol_on_platform", False)
        patrol_plat_btn = pygame.Rect(1215, y_offset, 170, 24)
        patrol_plat_text = f"PATROL PLATFORM: {'ON' if patrol_plat else 'OFF'}"
        
        if self.draw_button(patrol_plat_btn, patrol_plat_text, (45, 45, 50), (255, 255, 255), patrol_plat, is_scrollable=True) and mouse_clicked_this_frame:
            move_cfg["patrol_on_platform"] = not patrol_plat
            game.rebuild_objects()
        y_offset += 32

        if mouse_clicked_this_frame:
            if type_minus.collidepoint(mouse_pos) or type_plus.collidepoint(mouse_pos):
                move_cfg["type_move"] = "flying" if type_move == "walking" else "walking"
                game.rebuild_objects()
            
            if spd_minus.collidepoint(mouse_pos):
                move_cfg["speed"] = max(0.1, round(move_cfg.get("speed", 1.2) - 0.1, 1))
                game.rebuild_objects()
            if spd_plus.collidepoint(mouse_pos):
                move_cfg["speed"] = round(move_cfg.get("speed", 1.2) + 0.1, 1)
                game.rebuild_objects()
            
            if rng_minus.collidepoint(mouse_pos):
                move_cfg["range_x"] = max(0, move_cfg.get("range_x", 120) - 10)
                game.rebuild_objects()
            if rng_plus.collidepoint(mouse_pos):
                move_cfg["range_x"] = move_cfg.get("range_x", 120) + 10
                game.rebuild_objects()

            if stop_minus.collidepoint(mouse_pos):
                move_cfg["stop_dist"] = max(0, move_cfg.get("stop_dist", 60) - 10)
                game.rebuild_objects()
            if stop_plus.collidepoint(mouse_pos):
                move_cfg["stop_dist"] = move_cfg.get("stop_dist", 60) + 10
                game.rebuild_objects()

        lbl_post = self.font_ui.render("MOVEMENT TEMPLATES", True, (255, 180, 100))
        game.screen.blit(lbl_post, (1215, y_offset))
        y_offset += 25
        
        movements = target_enemy_raw.setdefault("movements", [])
        
        add_move_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(add_move_rect, "+ CREATE MOVE PRESET", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_move = {
                "name": f"Move Pres {len(movements) + 1}",
                "stop_dist": 0,
                "phases": [{
                    "direction": "forward",
                    "curve": "fade_out",
                    "force_x": 8.0,
                    "force_y": 0.0,
                    "delay": 0,
                    "duration": 15
                }]
            }
            movements.append(new_move)
            game.selected_move_edit_idx = len(movements) - 1
            game.selected_box_idx = 0
            game.inspector_tab = "DETAILED_MOVEMENT"
            game.right_panel_scroll = 0
            game.rebuild_objects()
        y_offset += 35

        for idx, move in enumerate(movements):
            name_lbl = self.font_ui.render(f"Move #{idx + 1}: {move.get('name', 'Movement')}", True, (255, 255, 255))
            game.screen.blit(name_lbl, (1215, y_offset))
            
            phases = move.setdefault("phases", [])
            total_dur = max([p.get("delay", 0) + p.get("duration", 15) for p in phases]) if phases else 0
            stats_txt = f"Phases: {len(phases)} | Total Dur: {total_dur}"
            font_stats = pygame.font.SysFont(None, 11)
            stats_lbl = font_stats.render(stats_txt, True, (160, 160, 160))
            game.screen.blit(stats_lbl, (1215, y_offset + 16))
            
            edit_btn = pygame.Rect(1215, y_offset + 32, 110, 22)
            del_btn = pygame.Rect(1330, y_offset + 32, 55, 22)
            
            if self.draw_button(edit_btn, "EDIT TEMPLATE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                game.inspector_tab = "DETAILED_MOVEMENT"
                game.selected_move_edit_idx = idx
                game.selected_box_idx = 0
                game.right_panel_scroll = 0
                
            if self.draw_button(del_btn, "DEL", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                movements.pop(idx)
                game.selected_move_edit_idx = max(0, min(game.selected_move_edit_idx, len(movements) - 1))
                game.selected_box_idx = 0
                game.rebuild_objects()
                break
            y_offset += 65
        return y_offset

    def draw_enemy_detailed_movement_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        movements = target_enemy_raw.setdefault("movements", [])
        if not movements:
            game.inspector_tab = "MOVEMENT"
            game.right_panel_scroll = 0
            return y_offset

        game.selected_move_edit_idx = min(game.selected_move_edit_idx, len(movements) - 1)
        curr_move = movements[game.selected_move_edit_idx]
        
        phases = curr_move.setdefault("phases", [])
        if not phases:
            phases.append({
                "direction": "forward",
                "curve": "fade_out",
                "force_x": 8.0,
                "force_y": 0.0,
                "delay": 0,
                "duration": 15
            })
        game.selected_box_idx = min(game.selected_box_idx, len(phases) - 1)
        curr_phase = phases[game.selected_box_idx]

        back_btn_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(back_btn_rect, "<< BACK TO TEMPLATES", (100, 60, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            game.inspector_tab = "MOVEMENT"
            game.right_panel_scroll = 0
        y_offset += 35
        
        rename_move_rect = pygame.Rect(1215, y_offset, 170, 22)
        if self.draw_button(rename_move_rect, "RENAME TEMPLATE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_name = game.prompt_text_input("Rename Movement Template", "Enter new name for the movement template:", curr_move.get("name", ""))
            if new_name and new_name.strip():
                curr_move["name"] = new_name.strip()
                game.rebuild_objects()
        y_offset += 30
            
        lbl_title = self.font_ui.render(f"EDIT TEMPLATE #{game.selected_move_edit_idx + 1}", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 20
        
        # Интегрированный выпадающий список выбора шаблона движения
        move_options = [m.get("name", f"Move #{i+1}") for i, m in enumerate(movements)]
        self.draw_dropdown("Select Move", move_options, game.selected_move_edit_idx, y_offset, "movement_select_active_move", mouse_clicked_this_frame, mouse_pos)
        y_offset += 30
        
        m_stop_minus, m_stop_plus = self.draw_property_row("Stop Dist", curr_move.setdefault("stop_dist", 0), y_offset)
        y_offset += 25
        
        phase_count_minus, phase_count_plus = self.draw_property_row("Phases", len(phases), y_offset)
        y_offset += 25

        # Интегрированный выпадающий список выбора фазы движения
        phase_options = [f"Phase #{i+1} ({p.get('direction', 'forward').upper()})" for i, p in enumerate(phases)]
        self.draw_dropdown("Select Phase", phase_options, game.selected_box_idx, y_offset, "movement_select_phase", mouse_clicked_this_frame, mouse_pos)
        y_offset += 30

        directions = ["forward", "backward", "to_player", "away_from_player", "teleport"]
        curr_dir = curr_phase.get("direction", "forward")
        dir_idx = directions.index(curr_dir) if curr_dir in directions else 0
        dir_minus, dir_plus = self.draw_property_row("Direction", curr_dir, y_offset)
        y_offset += 25

        curves = ["fade_out", "fade_in", "constant", "ease_in_out"]
        curr_curve = curr_phase.get("curve", "fade_out")
        curve_idx = curves.index(curr_curve) if curr_curve in curves else 0
        
        if curr_dir != "teleport":
            curve_minus, curve_plus = self.draw_property_row("Curve", curr_curve, y_offset)
            y_offset += 25
        else:
            curve_minus, curve_plus = None, None

        label_x = "Teleport DX" if curr_dir == "teleport" else "Force X"
        label_y = "Teleport DY" if curr_dir == "teleport" else "Force Y"
        
        fx_minus, fx_plus = self.draw_property_row(label_x, round(curr_phase.get("force_x", 8.0), 1), y_offset)
        y_offset += 25
        fy_minus, fy_plus = self.draw_property_row(label_y, round(curr_phase.get("force_y", 0.0), 1), y_offset)
        y_offset += 25
        
        delay_minus, delay_plus = self.draw_property_row("Delay", curr_phase.setdefault("delay", 0), y_offset)
        y_offset += 25
        
        if curr_dir != "teleport":
            dur_minus, dur_plus = self.draw_property_row("Duration", curr_phase.get("duration", 15), y_offset)
            y_offset += 30
        else:
            dur_minus, dur_plus = None, None
            y_offset += 10
        
        if mouse_clicked_this_frame:
            if m_stop_minus.collidepoint(mouse_pos):
                curr_move["stop_dist"] = max(0, curr_move.get("stop_dist", 0) - 10)
                game.rebuild_objects()
            if m_stop_plus.collidepoint(mouse_pos):
                curr_move["stop_dist"] = curr_move.get("stop_dist", 0) + 10
                game.rebuild_objects()

            if phase_count_minus.collidepoint(mouse_pos) and len(phases) > 1:
                phases.pop()
                game.selected_box_idx = min(game.selected_box_idx, len(phases) - 1)
                game.rebuild_objects()
            elif phase_count_plus.collidepoint(mouse_pos) and len(phases) < 4:
                phases.append(copy.deepcopy(phases[-1]))
                game.selected_box_idx = len(phases) - 1
                game.rebuild_objects()
            
            if dir_minus.collidepoint(mouse_pos):
                curr_phase["direction"] = directions[(dir_idx - 1) % len(directions)]
                game.rebuild_objects()
            if dir_plus.collidepoint(mouse_pos):
                curr_phase["direction"] = directions[(dir_idx + 1) % len(directions)]
                game.rebuild_objects()

            if curve_minus and curve_minus.collidepoint(mouse_pos):
                curr_phase["curve"] = curves[(curve_idx - 1) % len(curves)]
                game.rebuild_objects()
            if curve_plus and curve_plus.collidepoint(mouse_pos):
                curr_phase["curve"] = curves[(curve_idx + 1) % len(curves)]
                game.rebuild_objects()
                
            if fx_minus.collidepoint(mouse_pos):
                step_val = 10.0 if curr_dir == "teleport" else 0.5
                curr_phase["force_x"] = round(curr_phase.get("force_x", 8.0) - step_val, 1)
                if curr_dir != "teleport":
                    curr_phase["force_x"] = max(0.0, curr_phase["force_x"])
                game.rebuild_objects()
            if fx_plus.collidepoint(mouse_pos):
                step_val = 10.0 if curr_dir == "teleport" else 0.5
                curr_phase["force_x"] = round(curr_phase.get("force_x", 8.0) + step_val, 1)
                game.rebuild_objects()
                
            if fy_minus.collidepoint(mouse_pos):
                step_val = 10.0 if curr_dir == "teleport" else 0.5
                curr_phase["force_y"] = round(curr_phase.get("force_y", 0.0) - step_val, 1)
                if curr_dir != "teleport":
                    curr_phase["force_y"] = max(0.0, curr_phase["force_y"])
                game.rebuild_objects()
            if fy_plus.collidepoint(mouse_pos):
                step_val = 10.0 if curr_dir == "teleport" else 0.5
                curr_phase["force_y"] = round(curr_phase.get("force_y", 0.0) + step_val, 1)
                game.rebuild_objects()
                
            if delay_minus.collidepoint(mouse_pos):
                curr_phase["delay"] = max(0, curr_phase.setdefault("delay", 0) - 2)
                game.rebuild_objects()
            if delay_plus.collidepoint(mouse_pos):
                curr_phase["delay"] = curr_phase.setdefault("delay", 0) + 2
                game.rebuild_objects()

            if dur_minus and dur_minus.collidepoint(mouse_pos):
                curr_phase["duration"] = max(1, curr_phase.get("duration", 15) - 1)
                game.rebuild_objects()
            if dur_plus and dur_plus.collidepoint(mouse_pos):
                curr_phase["duration"] = curr_phase.get("duration", 15) + 1
                game.rebuild_objects()

        # --- Отрисовка таймлайна движения ---
        timeline_y = y_offset + 15
        pygame.draw.line(game.screen, BORDER_COLOR, (1205, timeline_y), (1395, timeline_y), 1)
        
        font_timeline = pygame.font.SysFont(None, 14)
        title_tl = font_timeline.render("MOVEMENT TIMELINE (60 FPS)", True, (255, 180, 100))
        game.screen.blit(title_tl, (1215, timeline_y + 6))
        
        bar_x = 1215
        bar_y = timeline_y + 24
        bar_w = 170
        bar_h = 24
        
        pygame.draw.rect(game.screen, (15, 15, 20), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(game.screen, BORDER_COLOR, (bar_x, bar_y, bar_w, bar_h), 1)
        
        total_duration = max([p.get("delay", 0) + p.get("duration", 15) for p in phases]) if phases else 30
        scale_max = max(30, total_duration)
        
        for f in range(0, scale_max + 1, 10):
            grid_x = bar_x + int((f / scale_max) * bar_w)
            pygame.draw.line(game.screen, (40, 40, 45), (grid_x, bar_y), (grid_x, bar_y + bar_h))
            if f % 20 == 0 or f == scale_max:
                f_lbl = font_timeline.render(str(f), True, (100, 100, 100))
                game.screen.blit(f_lbl, (grid_x - f_lbl.get_width() // 2, bar_y + bar_h + 3))
        
        for p_idx, p_data in enumerate(phases):
            delay = p_data.get("delay", 0)
            duration = p_data.get("duration", 15)
            
            hb_x = bar_x + int((delay / scale_max) * bar_w)
            hb_w = max(2, int((duration / scale_max) * bar_w))
            
            is_current = (p_idx == game.selected_box_idx)
            is_teleport = (p_data.get("direction") == "teleport")
            hb_color = (0, 200, 255) if is_current else ((180, 80, 255) if is_teleport else (60, 100, 180))
            
            pygame.draw.rect(game.screen, hb_color, (hb_x, bar_y + 3, hb_w, bar_h - 6))
            pygame.draw.rect(game.screen, (255, 255, 255) if is_current else (30, 30, 30), (hb_x, bar_y + 3, hb_w, bar_h - 6), 1)
            
            if hb_w > 12:
                lbl_text = f"T{p_idx+1}" if is_teleport else f"P{p_idx+1}"
                txt = font_timeline.render(lbl_text, True, (255, 255, 255))
                game.screen.blit(txt, (hb_x + hb_w//2 - txt.get_width()//2, bar_y + 6))
        
        y_offset = timeline_y + 70
        return y_offset