# editor/right_panel/editor_right_panel_attacks.py
import pygame
import copy
from config import BORDER_COLOR

class RightPanelAttacksTabMixin:
    def draw_enemy_attacks_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        
        # --- 1. РАЗДЕЛ АТАК БЛИЖНЕГО БОЯ ---
        lbl_title = self.font_ui.render("ATTACK TEMPLATES", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 20

        attacks = target_enemy_raw.setdefault("attacks", [])

        add_atk_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(add_atk_rect, "+ CREATE ATTACK TEMPLATE", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_atk = {
                "name": f"Atk Template {len(attacks) + 1}",
                "cooldown": 50,
                "windup": 35,
                "shapes": [{
                    "shape": {"template": "forms.rect", "w": 65, "h": 40},
                    "offset_x": 10, "offset_y": 0, "angle": 0,
                    "delay": 0, "duration": 10, "damage": 1, "kb_angle": 0, "kb_force": 12.0
                }]
            }
            attacks.append(new_atk)
            game.selected_attack_edit_idx = len(attacks) - 1
            game.selected_box_idx = 0
            game.inspector_tab = "DETAILED_ATTACK"
            game.right_panel_scroll = 0
            game.rebuild_objects()
        y_offset += 35

        for idx, att in enumerate(attacks):
            name_lbl = self.font_ui.render(f"Atk #{idx + 1}: {att.get('name', 'Attack')}", True, (255, 255, 255))
            game.screen.blit(name_lbl, (1215, y_offset))
            
            stats_txt = f"Windup: {att.get('windup', 35)} | CD: {att.get('cooldown', 45)}"
            font_stats = pygame.font.SysFont(None, 11)
            stats_lbl = font_stats.render(stats_txt, True, (160, 160, 160))
            game.screen.blit(stats_lbl, (1215, y_offset + 16))
            
            edit_btn = pygame.Rect(1215, y_offset + 32, 110, 22)
            del_btn = pygame.Rect(1330, y_offset + 32, 55, 22)
            
            if self.draw_button(edit_btn, "EDIT TEMPLATE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                game.inspector_tab = "DETAILED_ATTACK"
                game.selected_attack_edit_idx = idx
                game.selected_box_idx = 0
                game.right_panel_scroll = 0
                
            if self.draw_button(del_btn, "DEL", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                attacks.pop(idx)
                game.selected_attack_edit_idx = max(0, min(game.selected_attack_edit_idx, len(attacks) - 1))
                game.selected_box_idx = 0
                game.rebuild_objects()
                break
            y_offset += 65

        # --- ВИЗУАЛЬНЫЙ РАЗДЕЛИТЕЛЬ ---
        y_offset += 10
        pygame.draw.line(game.screen, BORDER_COLOR, (1205, y_offset), (1395, y_offset), 1)
        y_offset += 15

        # --- 2. РАЗДЕЛ ШАБЛОНОВ СНАРЯДОВ ---
        lbl_proj_title = self.font_ui.render("PROJECTILE TEMPLATES", True, (255, 180, 100))
        game.screen.blit(lbl_proj_title, (1215, y_offset))
        y_offset += 20

        projectiles = target_enemy_raw.setdefault("projectiles", [])

        add_proj_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(add_proj_rect, "+ CREATE PROJ TEMPLATE", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_proj = {
                "name": f"Proj Template {len(projectiles) + 1}",
                "speed": 10.0,
                "angle": 0.0,
                "gravity": 0.0,
                "damage": 1,
                "radius": 8,
                "aim_at_player": False,
                "homing": 0.0
            }
            projectiles.append(new_proj)
            game.selected_projectile_edit_idx = len(projectiles) - 1
            game.inspector_tab = "DETAILED_PROJECTILE"
            game.right_panel_scroll = 0
            game.rebuild_objects()
        y_offset += 35

        for idx, proj in enumerate(projectiles):
            name_lbl = self.font_ui.render(f"Proj #{idx + 1}: {proj.get('name', 'Projectile')}", True, (255, 255, 255))
            game.screen.blit(name_lbl, (1215, y_offset))
            
            stats_txt = f"Speed: {proj.get('speed', 10.0)} | Homing: {proj.get('homing', 0.0)}"
            font_stats = pygame.font.SysFont(None, 11)
            stats_lbl = font_stats.render(stats_txt, True, (160, 160, 160))
            game.screen.blit(stats_lbl, (1215, y_offset + 16))
            
            edit_btn = pygame.Rect(1215, y_offset + 32, 110, 22)
            del_btn = pygame.Rect(1330, y_offset + 32, 55, 22)
            
            if self.draw_button(edit_btn, "EDIT TEMPLATE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                game.inspector_tab = "DETAILED_PROJECTILE"
                game.selected_projectile_edit_idx = idx
                game.right_panel_scroll = 0
                
            if self.draw_button(del_btn, "DEL", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                projectiles.pop(idx)
                game.selected_projectile_edit_idx = max(0, min(getattr(game, "selected_projectile_edit_idx", 0), len(projectiles) - 1))
                game.rebuild_objects()
                break
            y_offset += 65

        return y_offset

    def draw_enemy_detailed_attack_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        attacks = target_enemy_raw.setdefault("attacks", [])
        if not attacks:
            game.inspector_tab = "ATTACKS"
            game.right_panel_scroll = 0
            return y_offset

        game.selected_attack_edit_idx = min(game.selected_attack_edit_idx, len(attacks) - 1)
        curr_att = attacks[game.selected_attack_edit_idx]
        
        shapes = curr_att.setdefault("shapes", [])
        if not shapes:
            shapes.append({
                "shape": { "template": "forms.rect", "w": 50, "h": 40 },
                "offset_x": 10, "offset_y": 0, "angle": 0, "kb_angle": 0, "kb_force": 12.0
            })
        game.selected_box_idx = min(game.selected_box_idx, len(shapes) - 1)
        curr_box = shapes[game.selected_box_idx]
        curr_box_shape = curr_box.setdefault("shape", { "template": "forms.rect", "w": 50, "h": 40 })

        back_btn_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(back_btn_rect, "<< BACK TO TEMPLATES", (100, 60, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            game.inspector_tab = "ATTACKS"
            game.right_panel_scroll = 0
        y_offset += 35
        
        rename_atk_rect = pygame.Rect(1215, y_offset, 170, 22)
        if self.draw_button(rename_atk_rect, "RENAME TEMPLATE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_name = game.prompt_text_input("Rename Attack Template", "Enter new name for the attack template:", curr_att.get("name", ""))
            if new_name and new_name.strip():
                curr_att["name"] = new_name.strip()
                game.rebuild_objects()
        y_offset += 30
            
        lbl_title = self.font_ui.render(f"EDIT TEMPLATE #{game.selected_attack_edit_idx + 1}", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 20
        
        cd_minus, cd_plus = self.draw_property_row("Cooldown", curr_att.get("cooldown", 45), y_offset)
        y_offset += 25
        wu_minus, wu_plus = self.draw_property_row("Windup", curr_att.setdefault("windup", 35), y_offset)
        y_offset += 30

        lbl_box = self.font_ui.render("DAMAGE HITBOX TIMELINE", True, (255, 180, 100))
        game.screen.blit(lbl_box, (1215, y_offset))
        y_offset += 20

        box_count_minus, box_count_plus = self.draw_property_row("Hitboxes", len(shapes), y_offset)
        y_offset += 25

        box_select_minus, box_select_plus = self.draw_property_row("Select Box", f"{game.selected_box_idx + 1}/{len(shapes)}", y_offset)
        y_offset += 25

        box_shape_type = curr_box_shape.get("type")
        if not box_shape_type:
            template_str = curr_box_shape.get("template", "")
            if "circle" in template_str or "r" in curr_box_shape:
                box_shape_type = "circle"
            else:
                box_shape_type = "rectangle"

        box_type_minus, box_type_plus = self.draw_property_row("Box Type", box_shape_type, y_offset)
        y_offset += 25

        if box_shape_type == "circle":
            box_dim1_minus, box_dim1_plus = self.draw_property_row("Box R", curr_box_shape.get("r", 25), y_offset)
            y_offset += 25
            box_dim2_minus, box_dim2_plus = None, None
        else:
            box_dim1_minus, box_dim1_plus = self.draw_property_row("Box W", curr_box_shape.get("w", 50), y_offset)
            y_offset += 25
            box_dim2_minus, box_dim2_plus = self.draw_property_row("Box H", curr_box_shape.get("h", 40), y_offset)
            y_offset += 25

        box_ox_minus, box_ox_plus = self.draw_property_row("Box OffX", curr_box.get("offset_x", 0), y_offset)
        y_offset += 25
        box_oy_minus, box_oy_plus = self.draw_property_row("Box OffY", curr_box.get("offset_y", 0), y_offset)
        y_offset += 25
        box_ang_minus, box_ang_plus = self.draw_property_row("Box Angle", curr_box.get("angle", 0), y_offset)
        y_offset += 25
        
        box_delay_minus, box_delay_plus = self.draw_property_row("Delay", curr_box.get("delay", 0), y_offset)
        y_offset += 25
        box_dur_minus, box_dur_plus = self.draw_property_row("Duration", curr_box.get("duration", 10), y_offset)
        y_offset += 25
        box_dmg_minus, box_dmg_plus = self.draw_property_row("Hit Damage", curr_box.get("damage", curr_att.get("damage", 1)), y_offset)
        y_offset += 25

        box_kb_ang_hit_minus, box_kb_ang_hit_plus = self.draw_property_row("Hit Kb Ang", curr_box.setdefault("kb_angle_hit", curr_box.get("kb_angle", 0)), y_offset)
        y_offset += 25
        box_kb_hit_minus, box_kb_hit_plus = self.draw_property_row("Hit Kb Force", curr_box.setdefault("kb_force_hit", curr_box.get("kb_force", 12.0)), y_offset)
        y_offset += 25
        box_kb_ang_parry_minus, box_kb_ang_parry_plus = self.draw_property_row("Parry Kb Ang", curr_box.setdefault("kb_angle_parry", curr_box.get("kb_angle", 0)), y_offset)
        y_offset += 25
        box_kb_parry_minus, box_kb_parry_plus = self.draw_property_row("Parry Kb Force", curr_box.setdefault("kb_force_parry", curr_box.get("kb_force", 12.0) * 0.5), y_offset)
        y_offset += 30

        sprite_dirs = ["forward", "up", "down", "to_player"]
        curr_s_dir = curr_box.setdefault("sprite_dir", "forward")
        s_dir_idx = sprite_dirs.index(curr_s_dir) if curr_s_dir in sprite_dirs else 0

        s_dir_minus, s_dir_plus = self.draw_property_row("Sprite Dir", curr_s_dir, y_offset)
        y_offset += 30

        if mouse_clicked_this_frame:
            if s_dir_minus.collidepoint(mouse_pos):
                curr_box["sprite_dir"] = sprite_dirs[(s_dir_idx - 1) % len(sprite_dirs)]
                game.rebuild_objects()
            if s_dir_plus.collidepoint(mouse_pos):
                curr_box["sprite_dir"] = sprite_dirs[(s_dir_idx + 1) % len(sprite_dirs)]
                game.rebuild_objects()

        has_vis_box = "visual_box" in curr_box
        vis_box_text = f"Custom Vis Box: {'ON' if has_vis_box else 'OFF'}"
        vis_box_rect = pygame.Rect(1215, y_offset, 170, 24)
        
        if self.draw_button(vis_box_rect, vis_box_text, (45, 45, 50), (255, 255, 255), has_vis_box, is_scrollable=True) and mouse_clicked_this_frame:
            if has_vis_box:
                curr_box.pop("visual_box", None)
            else:
                curr_box["visual_box"] = {
                    "type": box_shape_type,
                    "w": curr_box_shape.get("w", 50) if box_shape_type == "rectangle" else 0,
                    "h": curr_box_shape.get("h", 40) if box_shape_type == "rectangle" else 0,
                    "r": curr_box_shape.get("r", 25) if box_shape_type == "circle" else 0,
                    "offset_x": curr_box.get("offset_x", 0),
                    "offset_y": curr_box.get("offset_y", 0)
                }
            game.rebuild_objects()
        y_offset += 30
        
        if has_vis_box:
            v_box = curr_box["visual_box"]
            v_type = v_box.setdefault("type", "rectangle")
            
            vt_minus, vt_plus = self.draw_property_row("Vis Type", v_type, y_offset)
            y_offset += 25
            
            if mouse_clicked_this_frame:
                if vt_minus.collidepoint(mouse_pos) or vt_plus.collidepoint(mouse_pos):
                    if v_type == "rectangle":
                        v_box["type"] = "circle"
                        v_box.pop("w", None); v_box.pop("h", None)
                        v_box["r"] = v_box.get("r", 25) if v_box.get("r", 0) > 0 else 25
                    else:
                        v_box["type"] = "rectangle"
                        v_box.pop("r", None)
                        v_box["w"] = v_box.get("w", 50) if v_box.get("w", 0) > 0 else 50
                        v_box["h"] = v_box.get("h", 40) if v_box.get("h", 0) > 0 else 40
                    game.rebuild_objects()
            
            if v_type == "circle":
                vr_minus, vr_plus = self.draw_property_row("Vis R", v_box.setdefault("r", 25), y_offset)
                y_offset += 25
                vh_minus, vh_plus = None, None
            else:
                vw_minus, vw_plus = self.draw_property_row("Vis W", v_box.setdefault("w", 50), y_offset)
                y_offset += 25
                vh_minus, vh_plus = self.draw_property_row("Vis H", v_box.setdefault("h", 40), y_offset)
                y_offset += 25
                vr_minus, vr_plus = None, None
                
            vox_minus, vox_plus = self.draw_property_row("Vis OffX", v_box.setdefault("offset_x", 0), y_offset)
            y_offset += 25
            voy_minus, voy_plus = self.draw_property_row("Vis OffY", v_box.setdefault("offset_y", 0), y_offset)
            y_offset += 25
            
            if mouse_clicked_this_frame:
                if vr_minus and vr_minus.collidepoint(mouse_pos): v_box["r"] = max(5, v_box["r"] - 5)
                if vr_plus and vr_plus.collidepoint(mouse_pos):   v_box["r"] += 5
                
                if vw_minus and vw_minus.collidepoint(mouse_pos): v_box["w"] = max(5, v_box["w"] - 5)
                if vw_plus and vw_plus.collidepoint(mouse_pos):   v_box["w"] += 5
                
                if vh_minus and vh_minus.collidepoint(mouse_pos): v_box["h"] = max(5, v_box["h"] - 5)
                if vh_plus and vh_plus.collidepoint(mouse_pos):   v_box["h"] += 5
                
                if vox_minus.collidepoint(mouse_pos): v_box["offset_x"] -= 5
                if vox_plus.collidepoint(mouse_pos):  v_box["offset_x"] += 5

                if voy_minus.collidepoint(mouse_pos): v_box["offset_y"] -= 5
                if voy_plus.collidepoint(mouse_pos):  v_box["offset_y"] += 5
                
                game.rebuild_objects()

        if mouse_clicked_this_frame:
            if cd_minus.collidepoint(mouse_pos):  curr_att["cooldown"] = max(10, curr_att.get("cooldown", 45) - 5)
            if cd_plus.collidepoint(mouse_pos):   curr_att["cooldown"] += 5
            
            if wu_minus.collidepoint(mouse_pos):  curr_att["windup"] = max(5, curr_att.setdefault("windup", 35) - 5)
            if wu_plus.collidepoint(mouse_pos):   curr_att["windup"] = min(120, curr_att.setdefault("windup", 35) + 5)

            if box_count_minus.collidepoint(mouse_pos) and len(shapes) > 1:
                shapes.pop()
                game.selected_box_idx = min(game.selected_box_idx, len(shapes) - 1)
            elif box_count_plus.collidepoint(mouse_pos) and len(shapes) < 4:
                shapes.append(copy.deepcopy(shapes[-1]))
                game.selected_box_idx = len(shapes) - 1

            if box_select_minus.collidepoint(mouse_pos):
                game.selected_box_idx = max(0, game.selected_box_idx - 1)
            if box_select_plus.collidepoint(mouse_pos):
                game.selected_box_idx = min(len(shapes) - 1, game.selected_box_idx + 1)

            if box_type_minus.collidepoint(mouse_pos) or box_type_plus.collidepoint(mouse_pos):
                if box_shape_type == "rectangle":
                    curr_box_shape["type"] = "circle"
                    if "template" in curr_box_shape: curr_box_shape["template"] = "forms.circle"
                    curr_box_shape.pop("w", None); curr_box_shape.pop("h", None)
                    curr_box_shape["r"] = curr_box_shape.get("r", 25)
                else:
                    curr_box_shape["type"] = "rectangle"
                    if "template" in curr_box_shape: curr_box_shape["template"] = "forms.rect"
                    curr_box_shape.pop("r", None)
                    curr_box_shape["w"] = curr_box_shape.get("w", 50); curr_box_shape["h"] = curr_box_shape.get("h", 40)

            if box_shape_type == "circle":
                if box_dim1_minus.collidepoint(mouse_pos): curr_box_shape["r"] = max(5, curr_box_shape.get("r", 25) - 5)
                if box_dim1_plus.collidepoint(mouse_pos):  curr_box_shape["r"] += 5
            else:
                if box_dim1_minus.collidepoint(mouse_pos): curr_box_shape["w"] = max(10, curr_box_shape.get("w", 50) - 5)
                if box_dim1_plus.collidepoint(mouse_pos):  curr_box_shape["w"] += 5
                if box_dim2_minus and box_dim2_minus.collidepoint(mouse_pos): curr_box_shape["h"] = max(10, curr_box_shape.get("h", 40) - 5)
                if box_dim2_plus and box_dim2_plus.collidepoint(mouse_pos):  curr_box_shape["h"] += 5

            if box_ox_minus.collidepoint(mouse_pos): curr_box["offset_x"] = curr_box.get("offset_x", 0) - 5
            if box_ox_plus.collidepoint(mouse_pos):  curr_box["offset_x"] = curr_box.get("offset_x", 0) + 5
            if box_oy_minus.collidepoint(mouse_pos): curr_box["offset_y"] = curr_box.get("offset_y", 0) - 5
            if box_oy_plus.collidepoint(mouse_pos):  curr_box["offset_y"] = curr_box.get("offset_y", 0) + 5

            if box_ang_minus.collidepoint(mouse_pos): curr_box["angle"] = curr_box.get("angle", 0) - 15
            if box_ang_plus.collidepoint(mouse_pos):  curr_box["angle"] = curr_box.get("angle", 0) + 15
            
            if box_delay_minus.collidepoint(mouse_pos): curr_box["delay"] = max(0, curr_box.get("delay", 0) - 2)
            if box_delay_plus.collidepoint(mouse_pos):  curr_box["delay"] += 2
            
            if box_dur_minus.collidepoint(mouse_pos): curr_box["duration"] = max(2, curr_box.get("duration", 10) - 2)
            if box_dur_plus.collidepoint(mouse_pos):  curr_box["duration"] += 2
            
            if box_dmg_minus.collidepoint(mouse_pos): curr_box["damage"] = max(1, curr_box.get("damage", curr_att.get("damage", 1)) - 1)
            if box_dmg_plus.collidepoint(mouse_pos):  curr_box["damage"] += 1
            
            if box_kb_ang_hit_minus.collidepoint(mouse_pos):
                curr_box["kb_angle_hit"] = curr_box.setdefault("kb_angle_hit", 0) - 15
                game.rebuild_objects()
            if box_kb_ang_hit_plus.collidepoint(mouse_pos):
                curr_box["kb_angle_hit"] = curr_box.setdefault("kb_angle_hit", 0) + 15
                game.rebuild_objects()
            
            if box_kb_hit_minus.collidepoint(mouse_pos):
                curr_box["kb_force_hit"] = max(0.0, curr_box.setdefault("kb_force_hit", 12.0) - 1.0)
                game.rebuild_objects()
            if box_kb_hit_plus.collidepoint(mouse_pos):
                curr_box["kb_force_hit"] = min(30.0, curr_box.setdefault("kb_force_hit", 12.0) + 1.0)
                game.rebuild_objects()

            if box_kb_ang_parry_minus.collidepoint(mouse_pos):
                curr_box["kb_angle_parry"] = curr_box.setdefault("kb_angle_parry", 0) - 15
                game.rebuild_objects()
            if box_kb_ang_parry_plus.collidepoint(mouse_pos):
                curr_box["kb_angle_parry"] = curr_box.setdefault("kb_angle_parry", 0) + 15
                game.rebuild_objects()
            
            if box_kb_parry_minus.collidepoint(mouse_pos):
                curr_box["kb_force_parry"] = max(0.0, curr_box.setdefault("kb_force_parry", 6.0) - 1.0)
                game.rebuild_objects()
            if box_kb_parry_plus.collidepoint(mouse_pos):
                curr_box["kb_force_parry"] = min(30.0, curr_box.setdefault("kb_force_parry", 6.0) + 1.0)
                game.rebuild_objects()

            game.rebuild_objects()

        timeline_y = y_offset + 15
        pygame.draw.line(game.screen, BORDER_COLOR, (1205, timeline_y), (1395, timeline_y), 1)
        
        font_timeline = pygame.font.SysFont(None, 14)
        title_tl = font_timeline.render("TIMELINE PREVIEW (60 FPS)", True, (255, 180, 100))
        game.screen.blit(title_tl, (1215, timeline_y + 6))
        
        bar_x = 1215
        bar_y = timeline_y + 24
        bar_w = 170
        bar_h = 24
        
        pygame.draw.rect(game.screen, (15, 15, 20), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(game.screen, BORDER_COLOR, (bar_x, bar_y, bar_w, bar_h), 1)
        
        total_duration = max([s.get("delay", 0) + s.get("duration", 10) for s in shapes]) if shapes else 30
        scale_max = max(30, total_duration)
        
        for f in range(0, scale_max + 1, 10):
            grid_x = bar_x + int((f / scale_max) * bar_w)
            pygame.draw.line(game.screen, (40, 40, 45), (grid_x, bar_y), (grid_x, bar_y + bar_h))
            if f % 20 == 0 or f == scale_max:
                f_lbl = font_timeline.render(str(f), True, (100, 100, 100))
                game.screen.blit(f_lbl, (grid_x - f_lbl.get_width() // 2, bar_y + bar_h + 3))
        
        for s_idx, s_data in enumerate(shapes):
            delay = s_data.get("delay", 0)
            duration = s_data.get("duration", 10)
            
            hb_x = bar_x + int((delay / scale_max) * bar_w)
            hb_w = max(2, int((duration / scale_max) * bar_w))
            
            is_current = (s_idx == game.selected_box_idx)
            hb_color = (0, 200, 255) if is_current else (180, 60, 60)
            
            pygame.draw.rect(game.screen, hb_color, (hb_x, bar_y + 3, hb_w, bar_h - 6))
            pygame.draw.rect(game.screen, (255, 255, 255) if is_current else (30, 30, 30), (hb_x, bar_y + 3, hb_w, bar_h - 6), 1)
            
            if hb_w > 12:
                txt = font_timeline.render(f"H{s_idx+1}", True, (255, 255, 255))
                game.screen.blit(txt, (hb_x + hb_w//2 - txt.get_width()//2, bar_y + 6))
        
        y_offset = timeline_y + 70
        return y_offset

    def draw_enemy_detailed_projectile_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        projectiles = target_enemy_raw.setdefault("projectiles", [])
        if not projectiles:
            game.inspector_tab = "ATTACKS"
            game.right_panel_scroll = 0
            return y_offset

        game.selected_projectile_edit_idx = min(getattr(game, "selected_projectile_edit_idx", 0), len(projectiles) - 1)
        curr_proj = projectiles[game.selected_projectile_edit_idx]

        back_btn_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(back_btn_rect, "<< BACK TO TEMPLATES", (100, 60, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            game.inspector_tab = "ATTACKS"
            game.right_panel_scroll = 0
        y_offset += 35
        
        rename_proj_rect = pygame.Rect(1215, y_offset, 170, 22)
        if self.draw_button(rename_proj_rect, "RENAME TEMPLATE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_name = game.prompt_text_input("Rename Projectile Template", "Enter new name for the projectile template:", curr_proj.get("name", ""))
            if new_name and new_name.strip():
                curr_proj["name"] = new_name.strip()
                game.rebuild_objects()
        y_offset += 30
            
        lbl_title = self.font_ui.render(f"EDIT PROJ #{game.selected_projectile_edit_idx + 1}", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 20
        
        spd_minus, spd_plus = self.draw_property_row("Speed", round(curr_proj.get("speed", 10.0), 1), y_offset)
        y_offset += 25
        ang_minus, ang_plus = self.draw_property_row("Angle", round(curr_proj.get("angle", 0.0), 1), y_offset)
        y_offset += 25
        grav_minus, grav_plus = self.draw_property_row("Gravity", round(curr_proj.get("gravity", 0.0), 3), y_offset)
        y_offset += 25
        dmg_minus, dmg_plus = self.draw_property_row("Damage", curr_proj.get("damage", 1), y_offset)
        y_offset += 25
        rad_minus, rad_plus = self.draw_property_row("Radius", curr_proj.get("radius", 8), y_offset)
        y_offset += 35

        # Переключатель автонаведения на игрока
        aim_active = curr_proj.setdefault("aim_at_player", False)
        aim_rect = pygame.Rect(1215, y_offset, 170, 24)
        aim_text = f"AIM AT PLAYER: {'ON' if aim_active else 'OFF'}"
        if self.draw_button(aim_rect, aim_text, (45, 45, 50), (255, 255, 255), aim_active, is_scrollable=True) and mouse_clicked_this_frame:
            curr_proj["aim_at_player"] = not aim_active
            game.rebuild_objects()
        y_offset += 30

        # Сила активного самонаведения в полете
        homing_val = curr_proj.setdefault("homing", 0.0)
        homing_minus, homing_plus = self.draw_property_row("Homing Str", round(homing_val, 3), y_offset)
        y_offset += 35

        if mouse_clicked_this_frame:
            if spd_minus.collidepoint(mouse_pos): curr_proj["speed"] = max(1.0, round(curr_proj.get("speed", 10.0) - 0.5, 1))
            if spd_plus.collidepoint(mouse_pos):  curr_proj["speed"] = round(curr_proj.get("speed", 10.0) + 0.5, 1)
            
            if ang_minus.collidepoint(mouse_pos): curr_proj["angle"] = round(curr_proj.get("angle", 0.0) - 5.0, 1)
            if ang_plus.collidepoint(mouse_pos):  curr_proj["angle"] = round(curr_proj.get("angle", 0.0) + 5.0, 1)
            
            if grav_minus.collidepoint(mouse_pos): curr_proj["gravity"] = max(0.0, round(curr_proj.get("gravity", 0.0) - 0.005, 3))
            if grav_plus.collidepoint(mouse_pos):  curr_proj["gravity"] = round(curr_proj.get("gravity", 0.0) + 0.005, 3)
            
            if dmg_minus.collidepoint(mouse_pos): curr_proj["damage"] = max(1, curr_proj.get("damage", 1) - 1)
            if dmg_plus.collidepoint(mouse_pos):  curr_proj["damage"] = curr_proj.get("damage", 1) + 1
            
            if rad_minus.collidepoint(mouse_pos): curr_proj["radius"] = max(2, curr_proj.get("radius", 8) - 1)
            if rad_plus.collidepoint(mouse_pos):  curr_proj["radius"] = curr_proj.get("radius", 8) + 1

            if homing_minus.collidepoint(mouse_pos): curr_proj["homing"] = max(0.0, round(curr_proj.get("homing", 0.0) - 0.005, 3))
            if homing_plus.collidepoint(mouse_pos):  curr_proj["homing"] = min(0.2, round(curr_proj.get("homing", 0.0) + 0.005, 3))
            
            game.rebuild_objects()

        return y_offset
