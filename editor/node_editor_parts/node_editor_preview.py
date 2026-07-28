# editor/node_editor_parts/node_editor_preview.py
import dearpygui.dearpygui as dpg
import math

# Вспомогательный хелпер для безопасного приведения типов на холсте предпросмотра
def safe_num(val, default=0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        # Игнорируем неразрешенные шаблоны
        if val.startswith("$"):
            return default
        try:
            return float(val) if "." in val else int(val)
        except (ValueError, TypeError):
            return default
    return default

class NodeEditorPreviewMixin:
    def focus_preview_window(self, sender=None, app_data=None):
        if dpg.does_item_exist("preview_window"):
            dpg.focus_item("preview_window")

    def focus_main_window(self, sender=None, app_data=None):
        if dpg.does_item_exist("main_window"):
            dpg.focus_item("main_window")

    def toggle_focus(self, sender=None, app_data=None):
        if dpg.does_item_exist("preview_window") and dpg.is_item_focused("preview_window"):
            self.focus_main_window()
        else:
            self.focus_preview_window()

    def reset_preview_pan(self, sender=None, app_data=None):
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0

    def toggle_preview_visibility(self, sender=None, app_data=None):
        if not dpg.does_item_exist("preview_window"):
            return
        is_visible = dpg.get_value("show_preview_checkbox")
        dpg.configure_item("preview_window", show=is_visible)

    def _is_mouse_over_any_node(self, mx, my):
        for node_id in self.nodes_data.keys():
            try:
                pos = dpg.get_item_pos(node_id)
                if pos[0] - 10 <= mx <= pos[0] + 250 and pos[1] - 10 <= my <= pos[1] + 220:
                    return True
            except Exception:
                pass
        return False

    def is_node_connected_to_order(self, node_id):
        node = self.nodes_data.get(node_id)
        if not node:
            return False
        order_pin = node.properties.get("order_pin")
        if not order_pin:
            return False
            
        # Проверяем, соединен ли этот pin с узлом типа Order в списке активных связей
        for lid, (p_out, p_in) in self.links_data.items():
            if p_out == order_pin:
                target_reg = self.pins_registry.get(p_in)
                if target_reg and target_reg.get("type") == "Order":
                    return True
        return False

    def get_node_shape_info(self, node, ex, ey, body_w, body_h, is_vis_box=False):
        if is_vis_box:
            if node.type == "Hitbox" and node.properties.get("vis_enabled", False):
                shape_type = node.properties.get("vis_type", "rectangle")
                w = safe_num(node.properties.get("vis_w"), 50)
                h = safe_num(node.properties.get("vis_h"), 40)
                r = safe_num(node.properties.get("vis_r"), 25)
                offset_x = safe_num(node.properties.get("vis_offset_x"), 0)
                offset_y = safe_num(node.properties.get("vis_offset_y"), 0)
                angle = 0.0
                det_type = "following"
            else:
                return None
        else:
            shape_type = None
            w, h, r = 0, 0, 0
            offset_x, offset_y = 0, 0
            angle = 0.0
            det_type = "following"
            
            if node.type == "Root":
                shape_type = node.properties.get("det_shape_type", "rectangle")
                w = safe_num(node.properties.get("det_w"), 220)
                h = safe_num(node.properties.get("det_h"), 70)
                r = safe_num(node.properties.get("det_r"), 110)
                offset_x = safe_num(node.properties.get("det_offset_x"), 0)
                offset_y = safe_num(node.properties.get("det_offset_y"), -10)
                angle = safe_num(node.properties.get("det_angle"), 0.0)
                det_type = node.properties.get("det_type", "following")
            elif node.type in ("Flow", "Sequence"):
                shape_type = node.properties.get("trig_shape_type", "rectangle")
                w = safe_num(node.properties.get("trig_w"), 90)
                h = safe_num(node.properties.get("trig_h"), 50)
                r = safe_num(node.properties.get("trig_r"), 45)
                offset_x = safe_num(node.properties.get("trig_offset_x"), 10)
                offset_y = safe_num(node.properties.get("trig_offset_y"), 0)
                angle = 0.0
                det_type = node.properties.get("trig_type", "following")
            elif node.type == "Order":
                shape_type = node.properties.get("trig_shape_type", "rectangle")
                w = safe_num(node.properties.get("trig_w"), 150)
                h = safe_num(node.properties.get("trig_h"), 60)
                r = safe_num(node.properties.get("trig_r"), 75)
                offset_x = safe_num(node.properties.get("trig_offset_x"), 0)
                offset_y = safe_num(node.properties.get("trig_offset_y"), 0)
                angle = 0.0
                det_type = node.properties.get("trig_type", "following")
            elif node.type == "Hitbox":
                shape_type = node.properties.get("shape_type", "rectangle")
                w = safe_num(node.properties.get("w"), 50)
                h = safe_num(node.properties.get("h"), 40)
                r = safe_num(node.properties.get("r"), 25)
                offset_x = safe_num(node.properties.get("offset_x"), 10)
                offset_y = safe_num(node.properties.get("offset_y"), 0)
                angle = safe_num(node.properties.get("angle"), 0.0)
                det_type = "following"
            else:
                return None
            
        rx_left = ex - safe_num(body_w, 30) / 2
        rx_right = ex + safe_num(body_w, 30) / 2
        ry_top = ey - safe_num(body_h, 50) / 2
        
        if det_type == "following":
            if shape_type == "circle":
                cx_shape = rx_right + offset_x + r
                cy_shape = ry_top + offset_y + r
            else:
                cx_shape = rx_right + offset_x + w / 2
                cy_shape = ry_top + offset_y + h / 2
        else:  # stationary
            if shape_type == "circle":
                cx_shape = rx_left + offset_x + r
                cy_shape = ry_top + offset_y + r
            else:
                cx_shape = rx_left + offset_x + w / 2
                cy_shape = ry_top + offset_y + h / 2
                
        return (shape_type, w, h, r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape)

    def draw_node_preview_shape(self, node, is_focused, ex, ey, body_w, body_h, is_vis_box=False):
        info = self.get_node_shape_info(node, ex, ey, body_w, body_h, is_vis_box=is_vis_box)
        if not info:
            return
            
        shape_type, w, h, r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape = info
        
        alpha = 140 if is_focused else 35
        border_alpha = 255 if is_focused else 70
        
        if is_vis_box:
            fill = [180, 100, 255, alpha]
            border = [180, 100, 255, border_alpha]
        elif node.type == "Root":
            fill = [255, 220, 0, alpha]
            border = [255, 220, 0, border_alpha]
        elif node.type == "Flow":
            fill = [0, 200, 255, alpha]
            border = [0, 200, 255, border_alpha]
        elif node.type == "Sequence":
            fill = [255, 100, 0, alpha]
            border = [255, 100, 0, border_alpha]
        elif node.type == "Order":
            fill = [180, 50, 255, alpha]
            border = [180, 50, 255, border_alpha]
        elif node.type == "Hitbox":
            fill = [255, 60, 60, alpha]
            border = [255, 60, 60, border_alpha]
        else:
            return
            
        thickness = 2 if is_focused else 1
        
        if shape_type == "circle":
            dpg.draw_circle(
                center=[cx_shape, cy_shape],
                radius=r,
                fill=fill,
                color=border,
                thickness=thickness,
                parent="preview_drawlist"
            )
        else:
            rad = math.radians(-angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            dx, dy = w / 2, h / 2
            corners = []
            for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                rx = px * cos_a - py * sin_a + cx_shape
                ry = px * sin_a + py * cos_a + cy_shape
                corners.append([rx, ry])
            dpg.draw_polygon(
                points=corners,
                fill=fill,
                color=border,
                thickness=thickness,
                parent="preview_drawlist"
            )

        if is_focused:
            handle_color = [0, 240, 255, 255]
            white_color = [255, 255, 255, 255]
            
            if shape_type == "rectangle":
                dpg.draw_polygon(
                    points=corners,
                    color=handle_color,
                    thickness=2,
                    parent="preview_drawlist"
                )
                for c in corners:
                    dpg.draw_circle(center=c, radius=5, fill=handle_color, color=white_color, thickness=1, parent="preview_drawlist")
                
                top_mid = [(corners[0][0]+corners[1][0])/2, (corners[0][1]+corners[1][1])/2]
                right_mid = [(corners[1][0]+corners[2][0])/2, (corners[1][1]+corners[2][1])/2]
                bottom_mid = [(corners[2][0]+corners[3][0])/2, (corners[2][1]+corners[3][1])/2]
                left_mid = [(corners[3][0]+corners[0][0])/2, (corners[3][1]+corners[0][1])/2]
                
                for m_pt in [top_mid, right_mid, bottom_mid, left_mid]:
                    dpg.draw_circle(center=m_pt, radius=4, fill=[0, 200, 255, 220], color=white_color, thickness=1, parent="preview_drawlist")
                
                dpg.draw_circle(center=[cx_shape, cy_shape], radius=3, fill=white_color, parent="preview_drawlist")
            
            elif shape_type == "circle":
                dpg.draw_circle(center=[cx_shape, cy_shape], radius=r, color=handle_color, thickness=2, parent="preview_drawlist")
                dpg.draw_circle(center=[cx_shape, cy_shape], radius=0.8 * r, color=[0, 240, 255, 120], thickness=1, parent="preview_drawlist")
                
                for ang_deg in [0, 90, 180, 270]:
                    rad_ang = math.radians(ang_deg)
                    hx = cx_shape + r * math.cos(rad_ang)
                    hy = cy_shape + r * math.sin(rad_ang)
                    dpg.draw_line(
                        p1=[cx_shape + 0.8 * r * math.cos(rad_ang), cy_shape + 0.8 * r * math.sin(rad_ang)],
                        p2=[hx, hy],
                        color=[0, 240, 255, 200],
                        thickness=1.5,
                        parent="preview_drawlist"
                    )
                    dpg.draw_circle(center=[hx, hy], radius=4, fill=handle_color, color=white_color, parent="preview_drawlist")
                
                dpg.draw_circle(center=[cx_shape, cy_shape], radius=3, fill=white_color, parent="preview_drawlist")

        if not is_vis_box and node.type == "Hitbox" and node.properties.get("vis_enabled", False):
            self.draw_node_preview_shape(node, False, ex, ey, body_w, body_h, is_vis_box=True)

    def set_node_shape_properties(self, node, updates, is_vis_box=False):
        if is_vis_box and node.type == "Hitbox":
            if "offset_x" in updates: node.properties["vis_offset_x"] = int(updates["offset_x"])
            if "offset_y" in updates: node.properties["vis_offset_y"] = int(updates["offset_y"])
            if "w" in updates: node.properties["vis_w"] = int(updates["vis_w"] if "vis_w" in updates else updates["w"])
            if "h" in updates: node.properties["vis_h"] = int(updates["vis_h"] if "vis_h" in updates else updates["h"])
            if "r" in updates: node.properties["vis_r"] = int(updates["vis_r"] if "vis_r" in updates else updates["r"])
            return

        if node.type == "Root":
            if "offset_x" in updates: node.properties["det_offset_x"] = int(updates["offset_x"])
            if "offset_y" in updates: node.properties["det_offset_y"] = int(updates["offset_y"])
            if "w" in updates: node.properties["det_w"] = int(updates["w"])
            if "h" in updates: node.properties["det_h"] = int(updates["h"])
            if "r" in updates: node.properties["det_r"] = int(updates["r"])
            if "angle" in updates: node.properties["det_angle"] = float(updates["angle"])
        elif node.type in ("Flow", "Sequence"):
            if "offset_x" in updates: node.properties["trig_offset_x"] = int(updates["offset_x"])
            if "offset_y" in updates: node.properties["trig_offset_y"] = int(updates["offset_y"])
            if "w" in updates: node.properties["trig_w"] = int(updates["w"])
            if "h" in updates: node.properties["trig_h"] = int(updates["h"])
            if "r" in updates: node.properties["trig_r"] = int(updates["r"])
        elif node.type == "Order":
            if "offset_x" in updates: node.properties["trig_offset_x"] = int(updates["offset_x"])
            if "offset_y" in updates: node.properties["trig_offset_y"] = int(updates["offset_y"])
            if "w" in updates: node.properties["trig_w"] = int(updates["w"])
            if "h" in updates: node.properties["trig_h"] = int(updates["h"])
            if "r" in updates: node.properties["trig_r"] = int(updates["r"])
        elif node.type == "Hitbox":
            if "offset_x" in updates: node.properties["offset_x"] = int(updates["offset_x"])
            if "offset_y" in updates: node.properties["offset_y"] = int(updates["offset_y"])
            if "w" in updates: node.properties["w"] = int(updates["w"])
            if "h" in updates: node.properties["h"] = int(updates["h"])
            if "r" in updates: node.properties["r"] = int(updates["r"])
            if "angle" in updates: node.properties["angle"] = float(updates["angle"])

    def _hit_test_shape(self, info, mx, my):
        shape_type, w, h, r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape = info
        
        if shape_type == "circle":
            dist = math.hypot(mx - cx_shape, my - cy_shape)
            if dist <= r + 8:
                if dist >= 0.7 * r:
                    return "resize_circle"
                else:
                    return "move"
            return None
        else:  # rectangle
            rad = math.radians(-angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            dx = mx - cx_shape
            dy = my - cy_shape
            rx_local = dx * cos_a - dy * sin_a + cx_shape
            ry_local = dx * sin_a + dy * cos_a + cy_shape
            
            half_w, half_h = w / 2, h / 2
            corners_local = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
            for cx_l, cy_l in corners_local:
                c_world_x = cx_l * cos_a - cy_l * sin_a + cx_shape
                c_world_y = cx_l * sin_a + cy_l * cos_a + cy_shape
                if math.hypot(mx - c_world_x, my - c_world_y) <= 10:
                    return "rotate"

            if (cx_shape - half_w <= rx_local <= cx_shape + half_w) and (cy_shape - half_h <= ry_local <= cy_shape + half_h):
                u = (rx_local - (cx_shape - half_w)) / w
                v = (ry_local - (cy_shape - half_h)) / h
                
                is_corner_zone = (u <= 0.25 or u >= 0.75) and (v <= 0.25 or v >= 0.75)
                if is_corner_zone:
                    return "rotate"
                elif u <= 0.25:
                    return "resize_left"
                elif u >= 0.75:
                    return "resize_right"
                elif v <= 0.25:
                    return "resize_top"
                elif v >= 0.75:
                    return "resize_bottom"
                else:
                    return "move"
            return None

    def update_preview(self):
        if not dpg.does_item_exist("preview_drawlist") or not dpg.is_item_shown("preview_window"):
            return
            
        dpg.delete_item("preview_drawlist", children_only=True)
        
        draw_w, draw_h = 360, 270
        current_win_size = dpg.get_item_rect_size("preview_window")
        if current_win_size and current_win_size[0] > 10 and current_win_size[1] > 10:
            draw_w = max(50, current_win_size[0] - 20)
            draw_h = max(50, current_win_size[1] - 70)
            if not hasattr(self, "last_preview_win_size") or self.last_preview_win_size != current_win_size:
                self.last_preview_win_size = current_win_size
                dpg.configure_item("preview_drawlist", width=draw_w, height=draw_h)

        vw = dpg.get_viewport_width()
        p_width = draw_w + 20
        target_x = max(350, vw - p_width - 30)
        target_y = 75
        dpg.set_item_pos("preview_window", [target_x, target_y])

        cx = draw_w / 2.0
        cy = draw_h / 2.0
        
        ex = cx + getattr(self, "preview_pan_x", 0.0)
        ey = cy + getattr(self, "preview_pan_y", 0.0)
        
        root_node = None
        for n in self.nodes_data.values():
            if n.type == "Root":
                root_node = n
                break
                
        body_w = safe_num(root_node.properties.get("body_w"), 30) if root_node else 30
        body_h = safe_num(root_node.properties.get("body_h"), 50) if root_node else 50
        
        floor_y = ey + body_h / 2.0
        
        dpg.draw_line(p1=[10, floor_y], p2=[draw_w - 10, floor_y], color=[100, 100, 100, 255], thickness=2, parent="preview_drawlist")
        
        dpg.draw_rectangle(
            pmin=[ex - body_w / 2.0, ey - body_h / 2.0],
            pmax=[ex + body_w / 2.0, ey + body_h / 2.0],
            fill=[110, 110, 125, 255],
            color=[80, 80, 95, 255],
            thickness=1,
            parent="preview_drawlist"
        )
        
        try:
            draw_min = dpg.get_item_rect_min("preview_drawlist")
            if draw_min and (draw_min[0] > 0 or draw_min[1] > 0):
                draw_x, draw_y = draw_min[0], draw_min[1]
            else:
                win_pos = [target_x, target_y]
                draw_x = win_pos[0] + 8
                draw_y = win_pos[1] + 48
        except Exception:
            win_pos = [target_x, target_y]
            draw_x = win_pos[0] + 8
            draw_y = win_pos[1] + 48

        mouse_pos = dpg.get_mouse_pos(local=False)
        mx = mouse_pos[0] - draw_x
        my = mouse_pos[1] - draw_y
        
        is_mouse_inside_drawlist = (0 <= mx <= draw_w and 0 <= my <= draw_h)
            
        clicked = dpg.is_mouse_button_clicked(dpg.mvMouseButton_Left) and is_mouse_inside_drawlist
        down = dpg.is_mouse_button_down(dpg.mvMouseButton_Left)
        
        active_node = self.nodes_data.get(self.active_selected_node_id) if self.active_selected_node_id else None
        
        for node in list(self.nodes_data.values()):
            # Скрываем триггерные зоны связанных с Order последовательностей и флоу, кроме выделенного в данный момент узла
            if node.type in ("Flow", "Sequence") and self.is_node_connected_to_order(node.id):
                if node != active_node:
                    continue
            if node != active_node:
                self.draw_node_preview_shape(node, False, ex, ey, body_w, body_h)
                
        if active_node:
            self.draw_node_preview_shape(active_node, True, ex, ey, body_w, body_h)

        if clicked and not self.preview_dragging and not getattr(self, "preview_canvas_panning", False):
            target_node = None
            target_mode = "move"
            target_info = None
            target_is_vis = False

            if active_node:
                info = self.get_node_shape_info(active_node, ex, ey, body_w, body_h)
                if info:
                    mode = self._hit_test_shape(info, mx, my)
                    if mode:
                        target_node = active_node
                        target_mode = mode
                        target_info = info
                if not target_node and active_node.type == "Hitbox" and active_node.properties.get("vis_enabled", False):
                    vis_info = self.get_node_shape_info(active_node, ex, ey, body_w, body_h, is_vis_box=True)
                    if_mode_found = False
                    if vis_info:
                        mode = self._hit_test_shape(vis_info, mx, my)
                        if mode:
                            target_node = active_node
                            target_mode = mode
                            target_info = vis_info
                            target_is_vis = True

            if not target_node:
                for node in reversed(list(self.nodes_data.values())):
                    # Пропускаем связанные последовательности при поиске клика для предпросмотра
                    if node.type in ("Flow", "Sequence") and self.is_node_connected_to_order(node.id):
                        continue
                    info = self.get_node_shape_info(node, ex, ey, body_w, body_h)
                    if info:
                        mode = self._hit_test_shape(info, mx, my)
                        if mode:
                            target_node = node
                            target_mode = mode
                            target_info = info
                            break

            if target_node:
                if self.active_selected_node_id != target_node.id:
                    self.active_selected_node_id = target_node.id
                    dpg.clear_selected_nodes("editor_tag")
                    self.rebuild_inspector(target_node.id)

                self.preview_dragging = True
                self.preview_drag_mode = target_mode
                self.preview_drag_is_vis = target_is_vis
                self.preview_drag_start_mouse = (mx, my)
                shape_type, w, h, r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape = target_info
                self.preview_drag_start_val = {
                    "offset_x": offset_x, "offset_y": offset_y,
                    "w": w, "h": h, "r": r, "angle": angle,
                    "cx_shape": cx_shape, "cy_shape": cy_shape
                }
            else:
                self.preview_canvas_panning = True
                self.preview_pan_start_mouse = (mx, my)
                self.preview_pan_start_val = (self.preview_pan_x, self.preview_pan_y)

        if getattr(self, "preview_canvas_panning", False) and down:
            dx = mx - self.preview_pan_start_mouse[0]
            dy = my - self.preview_pan_start_mouse[1]
            self.preview_pan_x = self.preview_pan_start_val[0] + dx
            self.preview_pan_y = self.preview_pan_start_val[1] + dy

        if getattr(self, "preview_canvas_panning", False) and not down:
            self.preview_canvas_panning = False

        if self.preview_dragging and down and active_node:
            info = self.get_node_shape_info(active_node, ex, ey, body_w, body_h, is_vis_box=getattr(self, "preview_drag_is_vis", False))
            if info:
                dx_mouse = mx - self.preview_drag_start_mouse[0]
                dy_mouse = my - self.preview_drag_start_mouse[1]
                
                start_vals = self.preview_drag_start_val
                cx_shape_start = start_vals["cx_shape"]
                cy_shape_start = start_vals["cy_shape"]
                start_offset_x = start_vals["offset_x"]
                start_offset_y = start_vals["offset_y"]
                start_w = start_vals["w"]
                start_h = start_vals["h"]
                start_r = start_vals["r"]
                start_angle = start_vals["angle"]
                
                updates = {}
                mode = self.preview_drag_mode
                
                if mode == "move":
                    updates["offset_x"] = start_offset_x + dx_mouse
                    updates["offset_y"] = start_offset_y + dy_mouse
                elif mode == "resize_right":
                    updates["w"] = max(5, int(start_w + dx_mouse))
                elif mode == "resize_left":
                    new_w = max(5, int(start_w - dx_mouse))
                    updates["w"] = new_w
                    updates["offset_x"] = int(start_offset_x + (start_w - new_w))
                elif mode == "resize_bottom":
                    updates["h"] = max(5, int(start_h + dy_mouse))
                elif mode == "resize_top":
                    new_h = max(5, int(start_h - dy_mouse))
                    updates["h"] = new_h
                    updates["offset_y"] = int(start_offset_y + (start_h - new_h))
                elif mode == "resize_circle":
                    current_dist = math.hypot(mx - cx_shape_start, my - cy_shape_start)
                    updates["r"] = max(5, int((start_r + current_dist) / 2))
                    
                self.set_node_shape_properties(active_node, updates, is_vis_box=getattr(self, "preview_drag_is_vis", False))
                self.rebuild_inspector(active_node.id)

        if self.preview_dragging and not down:
            self.preview_dragging = False
            self.preview_drag_mode = None
            self.preview_drag_is_vis = False
            self.save_preset_file(None, None)