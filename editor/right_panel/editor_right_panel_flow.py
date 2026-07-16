# editor/right_panel/editor_right_panel_flow.py
import pygame
import copy
from config import BORDER_COLOR
from core.physics import parse_hex_color, get_analogous_colors

class RightPanelFlowTabMixin:
    def draw_enemy_flow_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        lbl_title = self.font_ui.render("AI FLOW DESIGNER", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 25

        flows = target_enemy_raw.setdefault("flows", [])
        
        add_flow_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(add_flow_rect, "+ CREATE NEW FLOW", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_flow = {
                "name": f"Combo Flow {len(flows) + 1}",
                "chance": 0.5,
                "cooldown": 180,
                "trigger_zone": {
                    "shape": { "template": "forms.rect", "w": 250, "h": 80 },
                    "offset_x": 0, "offset_y": 0, "type": "following",
                    "hold_time": 0, "consecutive_limit": 3, "accumulate_hold": True
                },
                "steps": [
                    { "seq_idx": 0, "delay": 0, "is_random": False, "seq_pool": [0] }
                ]
            }
            flows.append(new_flow)
            game.selected_flow_idx = len(flows) - 1
            game.selected_flow_step_idx = 0
            game.inspector_tab = "DETAILED_FLOW"
            game.right_panel_scroll = 0
            game.rebuild_objects()
        y_offset += 30

        for idx, flow in enumerate(flows):
            name_lbl = self.font_ui.render(f"Flow #{idx + 1}: {flow.get('name', 'Combo')}", True, (255, 255, 255))
            game.screen.blit(name_lbl, (1215, y_offset))
            
            steps = flow.setdefault("steps", [])
            stats_txt = f"Steps: {len(steps)} | CD: {flow.get('cooldown', 180)}"
            font_stats = game.get_cached_font(11)
            stats_lbl = font_stats.render(stats_txt, True, (160, 160, 160))
            game.screen.blit(stats_lbl, (1215, y_offset + 16))
            
            edit_btn = pygame.Rect(1215, y_offset + 32, 110, 22)
            del_btn = pygame.Rect(1330, y_offset + 32, 55, 22)
            
            if self.draw_button(edit_btn, "EDIT FLOW", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                game.inspector_tab = "DETAILED_FLOW"
                game.selected_flow_idx = idx
                game.selected_flow_step_idx = 0
                game.right_panel_scroll = 0
                
            if self.draw_button(del_btn, "DEL", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                flows.pop(idx)
                game.selected_flow_idx = max(0, min(getattr(game, "selected_flow_idx", 0), len(flows) - 1))
                game.selected_flow_step_idx = 0
                game.rebuild_objects()
                break
            y_offset += 65
        return y_offset

    def draw_enemy_detailed_flow_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        flows = target_enemy_raw.setdefault("flows", [])
        if not flows:
            game.inspector_tab = "FLOW"
            game.right_panel_scroll = 0
            return y_offset

        game.selected_flow_idx = min(getattr(game, "selected_flow_idx", 0), len(flows) - 1)
        curr_flow = flows[game.selected_flow_idx]
        
        steps = curr_flow.setdefault("steps", [])
        if not steps:
            steps.append({ "seq_idx": 0, "delay": 0, "is_random": False, "seq_pool": [0] })
        game.selected_flow_step_idx = min(getattr(game, "selected_flow_step_idx", 0), len(steps) - 1)
        curr_step = steps[game.selected_flow_step_idx]

        back_btn_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(back_btn_rect, "<< BACK TO FLOWS", (100, 60, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            game.inspector_tab = "FLOW"
            game.right_panel_scroll = 0
        y_offset += 35
        
        rename_flow_rect = pygame.Rect(1215, y_offset, 170, 22)
        if self.draw_button(rename_flow_rect, "RENAME FLOW", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            new_name = game.prompt_text_input("Rename Flow", "Enter new name for the behavior flow:", curr_flow.get("name", ""))
            if new_name and new_name.strip():
                curr_flow["name"] = new_name.strip()
                game.rebuild_objects()
        y_offset += 30
            
        lbl_title = self.font_ui.render(f"EDIT FLOW #{game.selected_flow_idx + 1}", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 20
        
        # Интегрированный выпадающий список выбора активного потока
        flow_options = [f.get("name", f"Flow #{i+1}") for i, f in enumerate(flows)]
        self.draw_dropdown("Select Flow", flow_options, game.selected_flow_idx, y_offset, "flow_select_active_flow", mouse_clicked_this_frame, mouse_pos)
        y_offset += 30
        
        ch_minus, ch_plus = self.draw_property_row("Flow Chance", round(curr_flow.setdefault("chance", 0.5), 1), y_offset)
        y_offset += 25
        cd_minus, cd_plus = self.draw_property_row("Flow CD", curr_flow.setdefault("cooldown", 180), y_offset)
        y_offset += 25
        
        pcd_minus, pcd_plus = self.draw_property_row("Post CD", curr_flow.setdefault("post_cooldown", 30), y_offset)
        y_offset += 35
        
        lbl_color_sec = self.font_ui.render("TELEGRAPH TINT PALETTE", True, (255, 180, 100))
        game.screen.blit(lbl_color_sec, (1215, y_offset))
        y_offset += 20

        curr_color = curr_flow.get("color")
        color_btn_rect = pygame.Rect(1215, y_offset, 170, 22)
        color_text = "SET BASE COLOR (HEX)"
        if self.draw_button(color_btn_rect, color_text, (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            hex_input = game.prompt_text_input("Set Execution Color", "Enter Hex Color (e.g., #ff0000 or ff33aa):", "")
            parsed = parse_hex_color(hex_input)
            if parsed:
                curr_flow["color"] = parsed
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
                curr_flow.pop("color", None)
                game.rebuild_objects()
            y_offset += 25
        y_offset += 15
        
        if mouse_clicked_this_frame:
            if ch_minus.collidepoint(mouse_pos): curr_flow["chance"] = max(0.0, curr_flow["chance"] - 0.1)
            if ch_plus.collidepoint(mouse_pos):  curr_flow["chance"] = min(1.0, curr_flow["chance"] + 0.1)
            if cd_minus.collidepoint(mouse_pos):  curr_flow["cooldown"] = max(10, curr_flow["cooldown"] - 10)
            if cd_plus.collidepoint(mouse_pos):   curr_flow["cooldown"] += 10
            
            if pcd_minus.collidepoint(mouse_pos): curr_flow["post_cooldown"] = max(0, curr_flow.setdefault("post_cooldown", 30) - 5)
            if pcd_plus.collidepoint(mouse_pos):  curr_flow["post_cooldown"] = curr_flow.setdefault("post_cooldown", 30) + 5
            
            game.rebuild_objects()

        lbl_trig = self.font_ui.render("FLOW TRIGGER ZONE", True, (255, 180, 100))
        game.screen.blit(lbl_trig, (1215, y_offset))
        y_offset += 25

        curr_trig = curr_flow.setdefault("trigger_zone", {
            "shape": { "template": "forms.rect", "w": 250, "h": 80 },
            "offset_x": 0, "offset_y": 0, "type": "following",
            "hold_time": 0, "consecutive_limit": 3, "accumulate_hold": True
        })
        curr_trig_shape = curr_trig.setdefault("shape", { "template": "forms.rect", "w": 250, "h": 80 })

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
            trig_dim1_minus, trig_dim1_plus = self.draw_property_row("Trig R", curr_trig_shape.get("r", 80), y_offset)
            y_offset += 25
            trig_dim2_minus, trig_dim2_plus = None, None
        else:
            trig_dim1_minus, trig_dim1_plus = self.draw_property_row("Trig W", curr_trig_shape.get("w", 250), y_offset)
            y_offset += 25
            trig_dim2_minus, trig_dim2_plus = self.draw_property_row("Trig H", curr_trig_shape.get("h", 80), y_offset)
            y_offset += 25

        trig_ox_minus, trig_ox_plus = self.draw_property_row("Trig OffX", curr_trig.get("offset_x", 0), y_offset)
        y_offset += 25
        trig_oy_minus, trig_oy_plus = self.draw_property_row("Trig OffY", curr_trig.get("offset_y", 0), y_offset)
        y_offset += 35

        flow_hold = curr_trig.setdefault("hold_time", 0)
        hold_minus, hold_plus = self.draw_property_row("Trig Hold", flow_hold, y_offset)
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
                    curr_trig_shape["r"] = curr_trig_shape.get("r", 80)
                else:
                    curr_trig_shape["type"] = "rectangle"
                    if "template" in curr_trig_shape: curr_trig_shape["template"] = "forms.rect"
                    curr_trig_shape.pop("r", None)
                    curr_trig_shape["w"] = curr_trig_shape.get("w", 250); curr_trig_shape["h"] = curr_trig_shape.get("h", 80)

            if trig_shape_type == "circle":
                if trig_dim1_minus.collidepoint(mouse_pos): curr_trig_shape["r"] = max(5, curr_trig_shape.get("r", 80) - 5)
                if trig_dim1_plus.collidepoint(mouse_pos):  curr_trig_shape["r"] += 5
            else:
                if trig_dim1_minus.collidepoint(mouse_pos): curr_trig_shape["w"] = max(10, curr_trig_shape.get("w", 250) - 10)
                if trig_dim1_plus.collidepoint(mouse_pos):  curr_trig_shape["w"] += 10
                if trig_dim2_minus and trig_dim2_minus.collidepoint(mouse_pos): curr_trig_shape["h"] = max(10, curr_trig_shape.get("h", 80) - 5)
                if trig_dim2_plus and trig_dim2_plus.collidepoint(mouse_pos):  curr_trig_shape["h"] += 5

            if trig_ox_minus.collidepoint(mouse_pos): curr_trig["offset_x"] = curr_trig.get("offset_x", 0) - 5
            if trig_ox_plus.collidepoint(mouse_pos):  curr_trig["offset_x"] = curr_trig.get("offset_x", 0) + 5
            if trig_oy_minus.collidepoint(mouse_pos): curr_trig["offset_y"] = curr_trig.get("offset_y", 0) - 5
            if trig_oy_plus.collidepoint(mouse_pos):  curr_trig["offset_y"] = curr_trig.get("offset_y", 0) + 5
            
            if hold_minus.collidepoint(mouse_pos):
                curr_trig["hold_time"] = max(0, flow_hold - 5)
                game.rebuild_objects()
            if hold_plus.collidepoint(mouse_pos):
                curr_trig["hold_time"] = flow_hold + 5
                game.rebuild_objects()
            if consec_minus.collidepoint(mouse_pos):
                curr_trig["consecutive_limit"] = max(1, consec_limit - 1)
                game.rebuild_objects()
            if consec_plus.collidepoint(mouse_pos):
                curr_trig["consecutive_limit"] = min(10, consec_limit + 1)

            game.rebuild_objects()

        lbl_steps = self.font_ui.render("FLOW TIMELINE STEPS", True, (255, 180, 100))
        game.screen.blit(lbl_steps, (1215, y_offset))
        y_offset += 20
        
        step_add_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(step_add_rect, "+ ADD SEQ TO TIMELINE", (35, 80, 45), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            steps.append({ "seq_idx": 0, "delay": max([s.get("delay", 0) for s in steps] or [0]) + 30, "is_random": False, "seq_pool": [0] })
            game.selected_flow_step_idx = len(steps) - 1
            game.rebuild_objects()
        y_offset += 30
        
        if steps:
            # Интегрированный выпадающий список выбора шагов
            sequences = target_enemy_raw.get("sequences", [])
            step_options = []
            for i, s in enumerate(steps):
                if s.get("is_random", False):
                    step_options.append(f"Step #{i+1} (RANDOM)")
                else:
                    seq_name = sequences[s.get("seq_idx", 0)].get("name", f"Seq {s.get('seq_idx', 0)+1}") if s.get("seq_idx", 0) < len(sequences) else "None"
                    step_options.append(f"Step #{i+1} ({seq_name})")
            self.draw_dropdown("Select Step", step_options, game.selected_flow_step_idx, y_offset, "flow_select_step", mouse_clicked_this_frame, mouse_pos)
            y_offset += 30

            is_random = curr_step.setdefault("is_random", False)
            mode_text = f"Step Mode: {'RANDOM POOL' if is_random else 'SINGLE'}"
            mode_btn_rect = pygame.Rect(1215, y_offset, 170, 24)
            if self.draw_button(mode_btn_rect, mode_text, (45, 45, 50), (255, 255, 255), is_random, is_scrollable=True) and mouse_clicked_this_frame:
                curr_step["is_random"] = not is_random
                if curr_step["is_random"]:
                    curr_step["seq_pool"] = [curr_step.get("seq_idx", 0)]
                else:
                    curr_step["seq_idx"] = curr_step.get("seq_pool", [0])[0] if curr_step.get("seq_pool") else 0
                game.rebuild_objects()
            y_offset += 30

            # Использование выпадающего списка (dropdown) для выбора Sequence
            if not is_random:
                seq_idx = curr_step.setdefault("seq_idx", 0)
                seq_idx = max(0, min(seq_idx, len(sequences) - 1)) if sequences else 0
                curr_step["seq_idx"] = seq_idx
                
                seq_options_list = [s.get("name", f"Seq #{i+1}") for i, s in enumerate(sequences)] if sequences else ["None"]
                self.draw_dropdown("Sequence", seq_options_list, seq_idx, y_offset, "flow_step_sequence", mouse_clicked_this_frame, mouse_pos)
                y_offset += 30
            else:
                lbl_pool = self.font_ui.render("RANDOM POOL SELECTION:", True, (255, 180, 100))
                game.screen.blit(lbl_pool, (1215, y_offset))
                y_offset += 20
                
                seq_pool = curr_step.setdefault("seq_pool", [0])
                seq_pool = [idx for idx in seq_pool if idx < len(sequences)]
                if not seq_pool and sequences:
                    seq_pool = [0]
                curr_step["seq_pool"] = seq_pool
                
                for s_idx, seq_item in enumerate(sequences):
                    in_pool = s_idx in seq_pool
                    state_text = f"[X] {seq_item.get('name', f'Seq {s_idx+1}')}" if in_pool else f"[ ] {seq_item.get('name', f'Seq {s_idx+1}')}"
                    pool_btn_rect = pygame.Rect(1215, y_offset, 170, 22)
                    btn_color = (45, 90, 60) if in_pool else (45, 45, 50)
                    
                    if self.draw_button(pool_btn_rect, state_text, btn_color, (255, 255, 255), in_pool, is_scrollable=True) and mouse_clicked_this_frame:
                        if in_pool:
                            if len(seq_pool) > 1:
                                seq_pool.remove(s_idx)
                        else:
                            seq_pool.append(s_idx)
                        curr_step["seq_pool"] = sorted(list(set(seq_pool)))
                        game.rebuild_objects()
                    y_offset += 25
                y_offset += 5

            delay_minus, delay_plus = self.draw_property_row("Trigger Delay", curr_step.setdefault("delay", 0), y_offset)
            y_offset += 30
            
            if mouse_clicked_this_frame:
                if delay_minus.collidepoint(mouse_pos):
                    curr_step["delay"] = max(0, curr_step["delay"] - 10)
                    game.rebuild_objects()
                if delay_plus.collidepoint(mouse_pos):
                    curr_step["delay"] = curr_step["delay"] + 10
                    game.rebuild_objects()

            if len(steps) > 1:
                step_del_rect = pygame.Rect(1215, y_offset, 170, 24)
                if self.draw_button(step_del_rect, "DELETE STEP", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                    steps.pop(game.selected_flow_step_idx)
                    game.selected_flow_step_idx = max(0, game.selected_flow_step_idx - 1)
                    game.rebuild_objects()
                y_offset += 30
                
        seq_del_rect = pygame.Rect(1215, y_offset, 170, 24)
        if self.draw_button(seq_del_rect, "DELETE FLOW", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
            flows.pop(game.selected_flow_idx)
            game.selected_flow_idx = max(0, game.selected_flow_idx - 1)
            game.selected_flow_step_idx = 0
            game.rebuild_objects()
        y_offset += 35

        timeline_y = y_offset + 15
        pygame.draw.line(game.screen, BORDER_COLOR, (1205, timeline_y), (1395, timeline_y), 1)
        
        font_timeline = game.get_cached_font(14)
        title_tl = font_timeline.render("FLOW MASTER TIMELINE", True, (255, 180, 100))
        game.screen.blit(title_tl, (1215, timeline_y + 6))
        
        bar_x = 1215
        bar_y = timeline_y + 24
        bar_w = 170
        bar_h = 50
        
        pygame.draw.rect(game.screen, (15, 15, 20), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(game.screen, BORDER_COLOR, (bar_x, bar_y, bar_w, bar_h), 1)
        
        def get_step_duration(step):
            sequences = target_enemy_raw.get("sequences", [])
            if step.get("is_random", False) and step.get("seq_pool"):
                durations = []
                for s_idx in step["seq_pool"]:
                    if s_idx < len(sequences):
                        steps_data = sequences[s_idx].get("steps", [])
                        d = max([s.get("delay", 0) + 15 for s in steps_data]) if steps_data else 30
                        durations.append(d)
                return max(durations) if durations else 30
            else:
                s_idx = step.get("seq_idx", 0)
                if s_idx < len(sequences):
                    steps_data = sequences[s_idx].get("steps", [])
                    return max([s.get("delay", 0) + 15 for s in steps_data]) if steps_data else 30
                return 30

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
            is_current = (s_idx == game.selected_flow_step_idx)
            
            hb_x = bar_x + int((delay / scale_max) * bar_w)
            hb_w = max(4, int((duration / scale_max) * bar_w))
            
            color = (0, 240, 255) if is_current else (180, 100, 255)
            pygame.draw.rect(game.screen, color, (hb_x, row_y, hb_w, step_row_height))
            
            outline_color = (0, 240, 255) if is_current else (30, 30, 30)
            pygame.draw.rect(game.screen, outline_color, (hb_x, row_y, hb_w, step_row_height), 1)
            
            if hb_w > 15:
                if s_data.get("is_random", False):
                    pool_str = ",".join(str(idx + 1) for idx in s_data.get("seq_pool", []))
                    txt_str = f"S[{pool_str}]"
                    if len(txt_str) > 6:
                        txt_str = "SRND"
                else:
                    txt_str = f"S{s_data.get('seq_idx', 0)+1}"
                    
                txt = font_timeline.render(txt_str, True, (255, 255, 255))
                game.screen.blit(txt, (hb_x + 2, row_y + 1))
        
        y_offset = timeline_y + 70
        return y_offset