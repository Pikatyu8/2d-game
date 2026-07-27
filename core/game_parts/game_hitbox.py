# core/game_parts/game_hitbox.py
import pygame
import math
from config import CANVAS_OFFSET_X, CANVAS_WIDTH
from core.physics import rotate_point

class GameHitboxMixin:
    def get_active_hitbox_rect_and_data(self):
        from entities.enemy import Enemy
        enemy = None
        if self.editor_mode == "ENEMY_EDITOR":
            enemy = self.dummy_enemy
        elif self.editor_mode == "LEVEL_EDITOR" and self.selected_instance and isinstance(self.selected_instance, Enemy):
            enemy = self.selected_instance
            
        if not enemy:
            return None
            
        target_enemy_raw = enemy.raw_data
        zoom = self.zoom if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") else 1.0
        camera_x = self.camera_x if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") else 0
        camera_y = self.camera_y if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") else 0
        
        shape_dict = None
        parent_dict = None
        resolved_parent_dict = None
        shape_data = None
        
        if self.inspector_tab == "MAIN":
            parent_dict = target_enemy_raw.get("detection")
            resolved_parent_dict = enemy.config.get("detection")
            if parent_dict:
                shape_dict = parent_dict.get("shape")
                shape_data = enemy.get_detection_shape()
        elif self.inspector_tab == "DETAILED_ATTACK":
            attacks = target_enemy_raw.get("attacks", [])
            if attacks and self.selected_attack_edit_idx < len(attacks):
                curr_att = attacks[self.selected_attack_edit_idx]
                shapes = curr_att.get("shapes", [])
                if shapes and self.selected_box_idx < len(shapes):
                    parent_dict = shapes[self.selected_box_idx]
                    resolved_parent_dict = enemy.attacks[self.selected_attack_edit_idx]["shapes"][self.selected_box_idx] if self.selected_attack_edit_idx < len(enemy.attacks) and self.selected_box_idx < len(enemy.attacks[self.selected_attack_edit_idx]["shapes"]) else None
                    shape_dict = parent_dict.get("shape")
                    shapes_data = enemy.get_attack_shapes_by_index(self.selected_attack_edit_idx)
                    if shapes_data and self.selected_box_idx < len(shapes_data):
                        shape_data = shapes_data[self.selected_box_idx]
        elif self.inspector_tab == "K-FRAMES":
            seq_list = target_enemy_raw.get("sequences", [])
            if seq_list and self.selected_seq_idx < len(seq_list):
                curr_seq = seq_list[self.selected_seq_idx]
                parent_dict = curr_seq.get("trigger_zone")
                if self.selected_seq_idx < len(enemy.trigger_zones):
                    resolved_parent_dict = enemy.trigger_zones[self.selected_seq_idx]
                if parent_dict:
                    shape_dict = parent_dict.get("shape")
                    shape_data = enemy.get_attack_zone_shape_for_attack_zone(self.selected_seq_idx)
        elif self.inspector_tab == "DETAILED_FLOW":
            flows = target_enemy_raw.get("flows", [])
            if flows and self.selected_flow_idx < len(flows):
                curr_flow = flows[self.selected_flow_idx]
                parent_dict = curr_flow.get("trigger_zone")
                if self.selected_flow_idx < len(enemy.flows):
                    resolved_parent_dict = enemy.flows[self.selected_flow_idx].get("trigger_zone")
                if parent_dict:
                    shape_dict = parent_dict.get("shape")
                    shape_data = enemy.get_attack_zone_shape_for_flow_zone(self.selected_flow_idx)
                    
        if not shape_dict or not parent_dict or not shape_data:
            return None
            
        stype, val = shape_data
        
        if stype == "circle":
            cx, cy, r = val
            asx = CANVAS_OFFSET_X + (cx - r - camera_x) * zoom
            asy = (cy - r - camera_y) * zoom
            asw = r * 2 * zoom
            ash = r * 2 * zoom
        else:
            rect, angle = val
            asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
            asy = (rect.y - camera_y) * zoom
            asw = rect.width * zoom
            ash = rect.height * zoom
            
        screen_rect = pygame.Rect(asx, asy, asw, ash)
        return {
            "screen_rect": screen_rect,
            "type": stype,
            "shape_dict": shape_dict,
            "parent_dict": parent_dict,
            "resolved_parent_dict": resolved_parent_dict,
            "enemy": enemy,
            "zoom": zoom,
            "shape_data_val": val
        }

    def check_hitbox_interaction(self, mouse_pos, mouse_clicked):
        if not mouse_clicked:
            return False
            
        info = self.get_active_hitbox_rect_and_data()
        if not info:
            return False
            
        screen_rect = info["screen_rect"]
        stype = info["type"]
        shape_dict = info["shape_dict"]
        parent_dict = info["parent_dict"]
        resolved_parent_dict = info.get("resolved_parent_dict")
        enemy = info["enemy"]
        val = info["shape_data_val"]
        camera_x = self.camera_x if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") else 0
        camera_y = self.camera_y if self.editor_mode in ("LEVEL_EDITOR", "ENEMY_EDITOR") else 0
        zoom = info["zoom"]
        
        mx, my = mouse_pos
        
        det_type = "following"
        if resolved_parent_dict:
            det_type = resolved_parent_dict.get("type", "following")
        else:
            det_type = parent_dict.get("type", "following") if parent_dict else "following"
            
        if stype == "circle":
            cx, cy, r = val
            scx = screen_rect.centerx
            scy = screen_rect.centery
            sr = screen_rect.width / 2
            dist = math.hypot(mx - scx, my - scy)
            
            if dist <= sr:
                self.dragging_hitbox = True
                self.hitbox_drag_start_mouse = (mx, my)
                self.hitbox_drag_start_val = {
                    "offset_x": parent_dict.get("offset_x", 0),
                    "offset_y": parent_dict.get("offset_y", 0),
                    "r": shape_dict.get("r", 25),
                    "enemy_rect_x": enemy.rect.x,
                    "enemy_rect_y": enemy.rect.y,
                    "enemy_rect_w": enemy.rect.width,
                    "enemy_rect_h": enemy.rect.height,
                    "enemy_direction": enemy.direction,
                    "det_type": det_type,
                    "is_attack": (self.inspector_tab == "DETAILED_ATTACK"),
                    "abs_x": cx - r,
                    "abs_y": cy - r,
                    "scx": scx,
                    "scy": scy
                }
                if dist >= 0.8 * sr:
                    self.hitbox_drag_mode = "resize_circle"
                else:
                    self.hitbox_drag_mode = "move"
                return True
        else:
            rect, angle = val
            cx = CANVAS_OFFSET_X + (rect.centerx - camera_x) * zoom
            cy = (rect.centery - camera_y) * zoom
            sw = rect.width * zoom
            sh = rect.height * zoom
            
            local_rect = pygame.Rect(cx - sw/2, cy - sh/2, sw, sh)
            local_mx, local_my = rotate_point((mx, my), (cx, cy), -angle)
            
            if local_rect.collidepoint(local_mx, local_my):
                self.dragging_hitbox = True
                self.hitbox_drag_start_mouse = (mx, my)
                
                self.hitbox_drag_start_val = {
                    "offset_x": parent_dict.get("offset_x", 0),
                    "offset_y": parent_dict.get("offset_y", 0),
                    "w": shape_dict.get("w", 50),
                    "h": shape_dict.get("h", 40),
                    "enemy_rect_x": enemy.rect.x,
                    "enemy_rect_y": enemy.rect.y,
                    "enemy_rect_w": enemy.rect.width,
                    "enemy_rect_h": enemy.rect.height,
                    "enemy_direction": enemy.direction,
                    "det_type": det_type,
                    "is_attack": (self.inspector_tab == "DETAILED_ATTACK"),
                    "abs_x": rect.x,
                    "abs_y": rect.y,
                    "angle": parent_dict.get("angle", shape_dict.get("angle", 0)),
                    "scx": cx,
                    "scy": cy
                }
                
                rx = (local_mx - local_rect.left) / local_rect.width
                ry = (local_my - local_rect.top) / local_rect.height
                
                is_corner = (rx <= 0.2 or rx >= 0.8) and (ry <= 0.2 or ry >= 0.8)
                
                if is_corner:
                    self.hitbox_drag_mode = "rotate"
                elif rx <= 0.2:
                    self.hitbox_drag_mode = "resize_left"
                elif rx >= 0.8:
                    self.hitbox_drag_mode = "resize_right"
                elif ry <= 0.2:
                    self.hitbox_drag_mode = "resize_top"
                elif ry >= 0.8:
                    self.hitbox_drag_mode = "resize_bottom"
                else:
                    self.hitbox_drag_mode = "move"
                return True
        return False

    def update_hitbox_drag(self, mouse_pos):
        if not self.dragging_hitbox:
            return
            
        if not pygame.mouse.get_pressed()[0]:
            self.dragging_hitbox = False
            self.hitbox_drag_mode = None
            if hasattr(self, "auto_save_current_preset"):
                self.auto_save_current_preset()
            return
            
        info = self.get_active_hitbox_rect_and_data()
        if not info:
            self.dragging_hitbox = False
            self.hitbox_drag_mode = None
            return
            
        shape_dict = info["shape_dict"]
        parent_dict = info["parent_dict"]
        zoom = info["zoom"]
        stype = info["type"]
        
        mx, my = mouse_pos
        start_mx, start_my = self.hitbox_drag_start_mouse
        
        dx_world = (mx - start_mx) / zoom
        dy_world = (my - start_my) / zoom
        
        start_vals = self.hitbox_drag_start_val
        start_abs_x = start_vals["abs_x"]
        start_abs_y = start_vals["abs_y"]
        
        new_abs_x = start_abs_x
        new_abs_y = start_abs_y
        
        if stype == "circle":
            start_r = start_vals["r"]
            new_r = start_r
            
            if self.hitbox_drag_mode == "move":
                new_abs_x = start_abs_x + dx_world
                new_abs_y = start_abs_y + dy_world
            elif self.hitbox_drag_mode == "resize_circle":
                scx = info["screen_rect"].centerx
                scy = info["screen_rect"].centery
                sr_new = math.hypot(mx - scx, my - scy)
                new_r = max(5, int(sr_new / zoom))
                start_abs_cx = start_abs_x + start_r
                start_abs_cy = start_abs_y + start_r
                new_abs_x = start_abs_cx - new_r
                new_abs_y = start_abs_cy - new_r
                
            shape_dict["r"] = int(new_r)
            
        else:
            start_w = start_vals["w"]
            start_h = start_vals["h"]
            new_w = start_w
            new_h = start_h
            
            if self.hitbox_drag_mode == "move":
                new_abs_x = start_abs_x + dx_world
                new_abs_y = start_abs_y + dy_world
            elif self.hitbox_drag_mode == "resize_right":
                new_w = max(5, start_w + dx_world)
            elif self.hitbox_drag_mode == "resize_left":
                new_w = max(5, start_w - dx_world)
                actual_dw = new_w - start_w
                new_abs_x = start_abs_x - actual_dw
            elif self.hitbox_drag_mode == "resize_bottom":
                new_h = max(5, start_h + dy_world)
            elif self.hitbox_drag_mode == "resize_top":
                new_h = max(5, start_h - dy_world)
                actual_dh = new_h - start_h
                new_abs_y = start_abs_y - actual_dh
            elif self.hitbox_drag_mode == "rotate":
                scx = start_vals["scx"]
                scy = start_vals["scy"]
                start_mouse_angle = math.atan2(start_my - scy, start_mx - scx)
                current_mouse_angle = math.atan2(my - scy, mx - scx)
                angle_diff_rad = current_mouse_angle - start_mouse_angle
                angle_diff_deg = math.degrees(angle_diff_rad)
                start_box_angle = start_vals["angle"]
                new_angle = start_box_angle - angle_diff_deg
                new_angle = (new_angle + 180) % 360 - 180
                
                parent_dict["angle"] = int(new_angle)
                
            shape_dict["w"] = int(new_w)
            shape_dict["h"] = int(new_h)
            
        enemy_rect_x = start_vals["enemy_rect_x"]
        enemy_rect_y = start_vals["enemy_rect_y"]
        enemy_rect_w = start_vals["enemy_rect_w"]
        enemy_rect_h = start_vals["enemy_rect_h"]
        enemy_direction = start_vals["enemy_direction"]
        det_type = start_vals["det_type"]
        is_attack = start_vals["is_attack"]
        
        if stype == "circle":
            new_cx = new_abs_x + new_r
            new_cy = new_abs_y + new_r
        
        if is_attack or det_type == "following":
            if enemy_direction == -1:
                if stype == "circle":
                    new_ox = enemy_rect_x - new_cx - new_r
                else:
                    new_ox = enemy_rect_x - new_abs_x - new_w
            else:
                if stype == "circle":
                    new_ox = new_cx - (enemy_rect_x + enemy_rect_w) - new_r
                else:
                    new_ox = new_abs_x - (enemy_rect_x + enemy_rect_w)
        else:
            if stype == "circle":
                new_ox = new_cx - enemy_rect_x - new_r
            else:
                new_ox = new_abs_x - enemy_rect_x
                
        if stype == "circle":
            new_oy = new_cy - enemy_rect_y - new_r
        else:
            new_oy = new_abs_y - enemy_rect_y
                
        parent_dict["offset_x"] = int(new_ox)
        parent_dict["offset_y"] = int(new_oy)
        
        self.rebuild_objects()