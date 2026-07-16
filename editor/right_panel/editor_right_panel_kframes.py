# editor/right_panel/editor_right_panel_kframes.py
import pygame
import copy
from config import BORDER_COLOR
from core.physics import parse_hex_color, get_analogous_colors

class RightPanelKFramesTabMixin:
    def draw_enemy_kframes_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        lbl_title = self.font_ui.render("KEYFRAME SEQUENCES", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 25

        seq_list = target_enemy_raw.setdefault("sequences", [])
        
        add_seq_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(add_seq_rect, "+ ADD NEW SEQUENCE", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_seq = {
                "name": f"Seq {len(seq_list) + 1}",
                "chance": 0.5,
                "cooldown": 120,
                "trigger_zone": {
                    "shape": { "template": "forms.rect", "w": 90, "h": 50 },
                    "offset_x": 10, "offset_y": 0, "type": "following", "hold_time": 0,
                    "consecutive_limit": 3, "accumulate_hold": True
                },
                "steps": [
                    {"type": "attack", "idx": 0, "trigger": "time", "delay": 0}
                ]
            }
            seq_list.append(new_seq)
            game.selected_seq_idx = len(seq_list) - 1
            game.selected_step_idx = 0
            game.rebuild_objects()
        y_offset += 30

        if seq_list:
            game.selected_seq_idx = min(getattr(game, "selected_seq_idx", 0), len(seq_list) - 1)
            curr_seq = seq_list[game.selected_seq_idx]
            
            # Интегрированный выпадающий список выбора последовательности
            seq_options = [s.get("name", f"Seq #{i+1}") for i, s in enumerate(seq_list)]
            self.draw_dropdown("Select Seq", seq_options, game.selected_seq_idx, y_offset, "kframe_select_seq", mouse_clicked_this_frame, mouse_pos)
            y_offset += 30
            
            rename_seq_rect = pygame.Rect(1215, y_offset, 170, 22)
            if self.draw_button(rename_seq_rect, "RENAME SEQUENCE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                new_name = game.prompt_text_input("Rename Sequence", "Enter new name for the sequence:", curr_seq.get("name", ""))
                if new_name and new_name.strip():
                    curr_seq["name"] = new_name.strip()
                    game.rebuild_objects()
            y_offset += 30
            
            ch_minus, ch_plus = self.draw_property_row("Seq Chance", round(curr_seq.setdefault("chance", 0.5), 1), y_offset)
            y_offset += 25
            cd_minus, cd_plus = self.draw_property_row("Seq CD", curr_seq.setdefault("cooldown", 120), y_offset)
            y_offset += 25
            
            pcd_minus, pcd_plus = self.draw_property_row("Post CD", curr_seq.setdefault("post_cooldown", 30), y_offset)
            y_offset += 35
            
            lbl_color_sec = self.font_ui.render("TELEGRAPH TINT PALETTE", True, (255, 180, 100))
            game.screen.blit(lbl_color_sec, (1215, y_offset))
            y_offset += 20

            curr_color = curr_seq.get("color")
            color_btn_rect = pygame.Rect(1215, y_offset, 170, 22)
            color_text = "SET BASE COLOR (HEX)"
            if self.draw_button(color_btn_rect, color_text, (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                hex_input = game.prompt_text_input("Set Telegraph Base Color", "Enter Hex Color (e.g., #ff0000 or ff33aa):", "")
                parsed = parse_hex_color(hex_input)
                if parsed:
                    curr_seq["color"] = parsed
                    game.rebuild_objects()
            y_offset += 26

            base_rgb = curr_color if curr_color else [110, 110, 125]
            left_c, _, right_c = get_analogous_colors(base_rgb)

            box_w = 75
            box_h = 24
            left_rect = pygame.Rect(1215, y_offset, box_w, box_h)
            right_rect = pygame.Rect(1215 + box_w + 20, y_offset, box_w, box_h)

            pygame.draw.rect(game.screen, left_c, left_rect)
            pygame.draw.rect(game.screen, (255, 255, 255), left_rect, 1)
            font_lbl = game.get_cached_font(11)
            start_txt = font_lbl.render("START", True, (255, 255, 255) if sum(left_c)/3 < 128 else (0, 0, 0))
            game.screen.blit(start_txt, (left_rect.centerx - start_txt.get_width()//2, left_rect.centery - start_txt.get_height()//2))

            arr_txt = font_lbl.render(">", True, (150, 150, 150))
            game.screen.blit(arr_txt, (1215 + box_w + 10 - arr_txt.get_width()//2, y_offset + box_h//2 - arr_txt.get_height()//2))

            pygame.draw.rect(game.screen, right_c, right_rect)
            pygame.draw.rect(game.screen, (255, 255, 255), right_rect, 1)
            end_txt = font_lbl.render("END", True, (255, 255, 255) if sum(right_c)/3 < 128 else (0, 0, 0))
            game.screen.blit(end_txt, (right_rect.centerx - end_txt.get_width()//2, y_offset + box_h//2 - end_txt.get_height()//2))

            y_offset += 30

            if curr_color:
                clear_btn_rect = pygame.Rect(1215, y_offset, 170, 20)
                if self.draw_button(clear_btn_rect, "REMOVE CUSTOM TINT", (150, 60, 60), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                    curr_seq.pop("color", None)
                    game.rebuild_objects()
                y_offset += 25
            y_offset += 15

            if mouse_clicked_this_frame:
                if ch_minus.collidepoint(mouse_pos): curr_seq["chance"] = max(0.0, curr_seq["chance"] - 0.1)
                if ch_plus.collidepoint(mouse_pos):  curr_seq["chance"] = min(1.0, curr_seq["chance"] + 0.1)
                if cd_minus.collidepoint(mouse_pos):  curr_seq["cooldown"] = max(10, curr_seq["cooldown"] - 10)
                if cd_plus.collidepoint(mouse_pos):   curr_seq["cooldown"] += 10
                
                if pcd_minus.collidepoint(mouse_pos): curr_seq["post_cooldown"] = max(0, curr_seq.setdefault("post_cooldown", 30) - 5)
                if pcd_plus.collidepoint(mouse_pos):  curr_seq["post_cooldown"] = curr_seq.setdefault("post_cooldown", 30) + 5
                
                game.rebuild_objects()

            lbl_trig = self.font_ui.render("SEQUENCE TRIGGER ZONE", True, (255, 180, 100))
            game.screen.blit(lbl_trig, (1215, y_offset))
            y_offset += 25

            curr_trig = curr_seq.setdefault("trigger_zone", {
                "shape": { "template": "forms.rect", "w": 90, "h": 50 },
                "offset_x": 10, "offset_y": 0, "type": "following", "hold_time": 0,
                "consecutive_limit": 3, "accumulate_hold": True
            })
            curr_trig_shape = curr_trig.setdefault("shape", { "template": "forms.rect", "w": 90, "h": 50 })

            trig_shape_type = curr_trig_shape.get("type")
            if not trig_shape_type:
                template_str = curr_trig_shape.get("template", "")
                if "circle" in template_str or "r" in curr_trig_shape:
                    trig_shape_type = "circle"
                else:
                    trig_shape_type = "rectangle"

            trig_type_minus, trig_type_plus = self.draw_property_row("Trig Type", trig_shape_type, y_offset)
            y_offset += 25

            if trig_shape_type == "circle":
                trig_dim1_minus, trig_dim1_plus = self.draw_property_row("Trig R", curr_trig_shape.get("r", 45), y_offset)
                y_offset += 25
                trig_dim2_minus, trig_dim2_plus = None, None
            else:
                trig_dim1_minus, trig_dim1_plus = self.draw_property_row("Trig W", curr_trig_shape.get("w", 90), y_offset)
                y_offset += 25
                trig_dim2_minus, trig_dim2_plus = self.draw_property_row("Trig H", curr_trig_shape.get("h", 50), y_offset)
                y_offset += 25

            trig_ox_minus, trig_ox_plus = self.draw_property_row("Trig OffX", curr_trig.get("offset_x", 10), y_offset)
            y_offset += 25
            trig_oy_minus, trig_oy_plus = self.draw_property_row("Trig OffY", curr_trig.get("offset_y", 0), y_offset)
            y_offset += 25

            hold_minus, hold_plus = self.draw_property_row("Trig Hold", curr_trig.setdefault("hold_time", 0), y_offset)
            y_offset += 25

            consec_limit = curr_trig.setdefault("consecutive_limit", 3)
            consec_minus, consec_plus = self.draw_property_row("Consec Limit", consec_limit, y_offset)
            y_offset += 35

            accum_hold = curr_trig.setdefault("accumulate_hold", True)
            accum_rect = pygame.Rect(1215, y_offset, 170, 24)
            accum_text = f"ACCUMULATE HOLD: {'ON' if accum_hold else 'OFF'}"
            if self.draw_button(accum_rect, accum_text, (45, 45, 50), (255, 255, 255), accum_hold, is_scrollable=True) and mouse_clicked_this_frame:
                curr_trig["accumulate_hold"] = not accum_hold
                game.rebuild_objects()
            y_offset += 35

            if mouse_clicked_this_frame:
                if trig_type_minus.collidepoint(mouse_pos) or trig_type_plus.collidepoint(mouse_pos):
                    if trig_shape_type == "rectangle":
                        curr_trig_shape["type"] = "circle"
                        if "template" in curr_trig_shape: curr_trig_shape["template"] = "forms.circle"
                        curr_trig_shape.pop("w", None); curr_trig_shape.pop("h", None)
                        curr_trig_shape["r"] = curr_trig_shape.get("r", 45)
                    else:
                        curr_trig_shape["type"] = "rectangle"
                        if "template" in curr_trig_shape: curr_trig_shape["template"] = "forms.rect"
                        curr_trig_shape.pop("r", None)
                        curr_trig_shape["w"] = curr_trig_shape.get("w", 90); curr_trig_shape["h"] = curr_trig_shape.get("h", 50)

                if trig_shape_type == "circle":
                    if trig_dim1_minus.collidepoint(mouse_pos): curr_trig_shape["r"] = max(5, curr_trig_shape.get("r", 45) - 5)
                    if trig_dim1_plus.collidepoint(mouse_pos):  curr_trig_shape["r"] += 5
                else:
                    if trig_dim1_minus.collidepoint(mouse_pos): curr_trig_shape["w"] = max(10, curr_trig_shape.get("w", 90) - 5)
                    if trig_dim1_plus.collidepoint(mouse_pos):  curr_trig_shape["w"] += 5
                    if trig_dim2_minus and trig_dim2_minus.collidepoint(mouse_pos): curr_trig_shape["h"] = max(10, curr_trig_shape.get("h", 50) - 5)
                    if trig_dim2_plus and trig_dim2_plus.collidepoint(mouse_pos):  curr_trig_shape["h"] += 5

                if trig_ox_minus.collidepoint(mouse_pos): curr_trig["offset_x"] = curr_trig.get("offset_x", 10) - 5
                if trig_ox_plus.collidepoint(mouse_pos):  curr_trig["offset_x"] = curr_trig.get("offset_x", 10) + 5
                if trig_oy_minus.collidepoint(mouse_pos): curr_trig["offset_y"] = curr_trig.get("offset_y", 0) - 5
                if trig_oy_plus.collidepoint(mouse_pos):  curr_trig["offset_y"] = curr_trig.get("offset_y", 0) + 5
                
                if hold_minus.collidepoint(mouse_pos):
                    curr_trig["hold_time"] = max(0, curr_trig.setdefault("hold_time", 0) - 5)
                if hold_plus.collidepoint(mouse_pos):
                    curr_trig["hold_time"] = curr_trig.setdefault("hold_time", 0) + 5

                if consec_minus.collidepoint(mouse_pos):
                    curr_trig["consecutive_limit"] = max(1, consec_limit - 1)
                if consec_plus.collidepoint(mouse_pos):
                    curr_trig["consecutive_limit"] = min(10, consec_limit + 1)
                
                game.rebuild_objects()

            lbl_steps = self.font_ui.render("SEQUENCE STEPS", True, (255, 180, 100))
            game.screen.blit(lbl_steps, (1215, y_offset))
            y_offset += 20
            
            steps = curr_seq.setdefault("steps", [])
            step_add_rect = pygame.Rect(1215, y_offset, 170, 24)
            if self.draw_button(step_add_rect, "+ ADD STEP", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                steps.append({"type": "attack", "idx": 0, "trigger": "time", "delay": 0})
                game.selected_step_idx = len(steps) - 1
                game.rebuild_objects()
            y_offset += 30
            
            if steps:
                game.selected_step_idx = min(getattr(game, "selected_step_idx", 0), len(steps) - 1)
                curr_step = steps[game.selected_step_idx]
                
                # Интегрированный выпадающий список выбора шагов
                step_options = [f"Step #{i+1} ({s.get('type', 'attack').upper()})" for i, s in enumerate(steps)]
                self.draw_dropdown("Select Step", step_options, game.selected_step_idx, y_offset, "kframe_select_step", mouse_clicked_this_frame, mouse_pos)
                y_offset += 30
                
                types = ["attack", "movement", "projectile"]
                curr_type_idx = types.index(curr_step.get("type", "attack")) if curr_step.get("type", "attack") in types else 0
                type_minus, type_plus = self.draw_property_row("Step Type", curr_step.get("type", "attack"), y_offset)
                y_offset += 25
                
                delay_minus, delay_plus = self.draw_property_row("Step Delay", curr_step.setdefault("delay", 0), y_offset)
                y_offset += 25
                
                if mouse_clicked_this_frame:
                    if delay_minus.collidepoint(mouse_pos):
                        curr_step["delay"] = max(0, curr_step["delay"] - 5)
                        game.rebuild_objects()
                    if delay_plus.collidepoint(mouse_pos):
                        curr_step["delay"] = curr_step["delay"] + 5
                        game.rebuild_objects()

                    if type_minus.collidepoint(mouse_pos) or type_plus.collidepoint(mouse_pos):
                        new_type_idx = (curr_type_idx - 1 if type_minus.collidepoint(mouse_pos) else curr_type_idx + 1) % len(types)
                        curr_step["type"] = types[new_type_idx]
                        curr_delay = curr_step.get("delay", 0)
                        if curr_step["type"] == "attack":
                            curr_step.clear()
                            curr_step.update({"type": "attack", "idx": 0, "trigger": "time", "delay": curr_delay})
                        elif curr_step["type"] == "movement":
                            curr_step.clear()
                            curr_step.update({"type": "movement", "idx": 0, "delay": curr_delay})
                        elif curr_step["type"] == "projectile":
                            curr_step.clear()
                            curr_step.update({"type": "projectile", "idx": 0, "delay": curr_delay})
                        game.rebuild_objects()
                        
                # Использование выпадающего списка (dropdown) для выбора атак
                if curr_step["type"] == "attack":
                    attacks = target_enemy_raw.get("attacks", [])
                    atk_idx = curr_step.setdefault("idx", 0)
                    atk_idx = max(0, min(atk_idx, len(attacks) - 1)) if attacks else 0
                    curr_step["idx"] = atk_idx
                    
                    atk_options = [a.get("name", f"Atk #{i+1}") for i, a in enumerate(attacks)] if attacks else ["None"]
                    self.draw_dropdown("Template Atk", atk_options, atk_idx, y_offset, "step_attack_template", mouse_clicked_this_frame, mouse_pos)
                    y_offset += 30
                        
                # Использование выпадающего списка (dropdown) для выбора движений
                elif curr_step["type"] == "movement":
                    movements = target_enemy_raw.get("movements", [])
                    move_idx = curr_step.setdefault("idx", 0)
                    move_idx = max(0, min(move_idx, len(movements) - 1)) if movements else 0
                    curr_step["idx"] = move_idx
                    
                    move_options = [m.get("name", f"Move #{i+1}") for i, m in enumerate(movements)] if movements else ["None"]
                    self.draw_dropdown("Template Move", move_options, move_idx, y_offset, "step_movement_template", mouse_clicked_this_frame, mouse_pos)
                    y_offset += 30
                        
                # Использование выпадающего списка (dropdown) для выбора снарядов
                elif curr_step["type"] == "projectile":
                    proj_list = target_enemy_raw.get("projectiles", [])
                    if proj_list:
                        proj_idx = curr_step.setdefault("idx", 0)
                        proj_idx = max(0, min(proj_idx, len(proj_list) - 1))
                        curr_step["idx"] = proj_idx
                        
                        proj_options = [p.get("name", f"Proj #{i+1}") for i, p in enumerate(proj_list)]
                        self.draw_dropdown("Template Proj", proj_options, proj_idx, y_offset, "step_projectile_template", mouse_clicked_this_frame, mouse_pos)
                        y_offset += 30
                    else:
                        ps_minus, ps_plus = self.draw_property_row("Proj Speed", round(curr_step.setdefault("proj_speed", 10.0), 1), y_offset)
                        y_offset += 25
                        pa_minus, pa_plus = self.draw_property_row("Proj Ang", round(curr_step.setdefault("proj_angle", 0.0), 1), y_offset)
                        y_offset += 25
                        pg_minus, pg_plus = self.draw_property_row("Proj Grav", round(curr_step.setdefault("proj_gravity", 0.0), 2), y_offset)
                        y_offset += 30
                        
                        if mouse_clicked_this_frame:
                            if ps_minus.collidepoint(mouse_pos): curr_step["proj_speed"] = max(1.0, curr_step["proj_speed"] - 0.5)
                            if ps_plus.collidepoint(mouse_pos):  curr_step["proj_speed"] += 0.5
                            if pa_minus.collidepoint(mouse_pos): curr_step["proj_angle"] -= 5.0
                            if pa_plus.collidepoint(mouse_pos):  curr_step["proj_angle"] += 5.0
                            if pg_minus.collidepoint(mouse_pos): curr_step["proj_gravity"] = max(0.0, curr_step["proj_gravity"] - 0.02)
                            if pg_plus.collidepoint(mouse_pos):  curr_step["proj_gravity"] += 0.02
                            game.rebuild_objects()

                if len(steps) > 1:
                    step_del_rect = pygame.Rect(1215, y_offset, 170, 24)
                    if self.draw_button(step_del_rect, "DELETE STEP", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                        steps.pop(game.selected_step_idx)
                        game.selected_step_idx = max(0, game.selected_step_idx - 1)
                        game.rebuild_objects()
                    y_offset += 30
                    
            seq_del_rect = pygame.Rect(1215, y_offset, 170, 24)
            if self.draw_button(seq_del_rect, "DELETE SEQUENCE", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                seq_list.pop(game.selected_seq_idx)
                game.selected_seq_idx = max(0, game.selected_seq_idx - 1)
                game.selected_step_idx = 0
                game.rebuild_objects()
            y_offset += 35

            timeline_y = y_offset + 15
            pygame.draw.line(game.screen, BORDER_COLOR, (1205, timeline_y), (1395, timeline_y), 1)
            
            font_timeline = game.get_cached_font(14)
            title_tl = font_timeline.render("SEQUENCE TIMELINE", True, (255, 180, 100))
            game.screen.blit(title_tl, (1215, timeline_y + 6))
            
            bar_x = 1215
            bar_y = timeline_y + 24
            bar_w = 170
            bar_h = 50
            
            pygame.draw.rect(game.screen, (15, 15, 20), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(game.screen, BORDER_COLOR, (bar_x, bar_y, bar_w, bar_h), 1)
            
            def get_step_duration(step):
                stype = step.get("type", "attack")
                if stype == "attack":
                    atk_idx = step.get("idx", 0)
                    attacks = target_enemy_raw.get("attacks", [])
                    if atk_idx < len(attacks):
                        att = attacks[atk_idx]
                        shapes = att.get("shapes", [])
                        total_dur = max([s.get("delay", 0) + s.get("duration", 10) for s in shapes]) if shapes else 15
                        return att.get("windup", 35) + total_dur
                    return 40
                elif stype == "movement":
                    move_idx = step.get("idx", 0)
                    movements = target_enemy_raw.get("movements", [])
                    if move_idx < len(movements):
                        m_template = movements[move_idx]
                        phases = m_template.get("phases", [])
                        durations = []
                        for p in phases:
                            p_dur = 1 if p.get("direction") == "teleport" else p.get("duration", 15)
                            durations.append(p.get("delay", 0) + p_dur)
                        return max(durations) if durations else 15
                    return 15
                elif stype == "projectile":
                    return 8
                return 10

            total_duration = max([s.get("delay", 0) + get_step_duration(s) for s in steps]) if steps else 60
            scale_max = max(60, total_duration)
            
            for f in range(0, scale_max + 1, 20):
                grid_x = bar_x + int((f / scale_max) * bar_w)
                pygame.draw.line(game.screen, (40, 40, 45), (grid_x, bar_y), (grid_x, bar_y + bar_h))
                if f % 40 == 0 or f == scale_max:
                    f_lbl = font_timeline.render(str(f), True, (100, 100, 100))
                    game.screen.blit(f_lbl, (grid_x - f_lbl.get_width() // 2, bar_y + bar_h + 3))
            
            step_row_height = 12
            for s_idx, s_data in enumerate(steps):
                delay = s_data.get("delay", 0)
                duration = get_step_duration(s_data)
                
                row_y = bar_y + 3 + (s_idx % 3) * 15
                is_current = (s_idx == game.selected_step_idx)
                stype = s_data.get("type", "attack")
                
                if stype == "attack":
                    atk_idx = s_data.get("idx", 0)
                    attacks = target_enemy_raw.get("attacks", [])
                    if atk_idx < len(attacks):
                        att = attacks[atk_idx]
                        windup = att.get("windup", 35)
                        shapes = att.get("shapes", [])
                        total_dur = max([sh.get("delay", 0) + sh.get("duration", 10) for sh in shapes]) if shapes else 15
                    else:
                        windup = 35
                        total_dur = 15
                        
                    tx = bar_x + int((delay / scale_max) * bar_w)
                    tw = int((windup / scale_max) * bar_w)
                    
                    ax = bar_x + int(((delay + windup) / scale_max) * bar_w)
                    aw = max(2, int((total_dur / scale_max) * bar_w))
                    
                    telegraph_color = (230, 140, 30)
                    pygame.draw.rect(game.screen, telegraph_color, (tx, row_y, tw, step_row_height))
                    
                    active_color = (180, 60, 60)
                    pygame.draw.rect(game.screen, active_color, (ax, row_y, aw, step_row_height))
                    
                    hb_x = tx
                    hb_w = tw + aw
                else:
                    hb_x = bar_x + int((delay / scale_max) * bar_w)
                    hb_w = max(4, int((duration / scale_max) * bar_w))
                    
                    if is_current:
                        color = (0, 240, 255)
                    elif stype == "movement":
                        color = (60, 100, 180)
                    else:
                        color = (120, 60, 180)
                        
                    pygame.draw.rect(game.screen, color, (hb_x, row_y, hb_w, step_row_height))
                
                outline_color = (0, 240, 255) if is_current else (30, 30, 30)
                pygame.draw.rect(game.screen, outline_color, (hb_x, row_y, hb_w, step_row_height), 1)
                
                if hb_w > 15:
                    short_lbls = {"attack": f"A{s_data.get('idx', 0)+1}", "movement": f"M{s_data.get('idx', 0)+1}", "projectile": "Proj"}
                    txt = font_timeline.render(short_lbls.get(stype, "S"), True, (255, 255, 255))
                    game.screen.blit(txt, (hb_x + 2, row_y + 1))
            
            y_offset = timeline_y + 70
        return y_offset