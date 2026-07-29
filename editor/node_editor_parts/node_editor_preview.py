# editor/node_editor_parts/node_editor_preview.py
import dearpygui.dearpygui as dpg
import math

def safe_num(val, default=0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
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

        for lid, (p_out, p_in) in self.links_data.items():
            if p_out == order_pin:
                target_reg = self.pins_registry.get(p_in)
                if target_reg and target_reg.get("type") == "Order":
                    return True
        return False

    def is_hitbox_connected_to_node(self, hb_id, parent_id):
        if hb_id == parent_id:
            return True
        hb_node = self.nodes_data.get(hb_id)
        if not hb_node or not hb_node.input_pins:
            return False
        p_in = list(hb_node.input_pins.keys())[0]
        for _, (p_out, p_in_link) in self.links_data.items():
            if p_in_link == p_in:
                src_node_id = self.pin_to_node.get(p_out)
                if src_node_id == parent_id:
                    return True
        return False

    def is_hitbox_linked_to_any_parent(self, hb_id):
        hb_node = self.nodes_data.get(hb_id)
        if not hb_node or not hb_node.input_pins:
            return False
        p_in_hb = list(hb_node.input_pins.keys())[0]
        for _, (p_out, p_in) in self.links_data.items():
            if p_in == p_in_hb:
                return True
        return False

    def get_node_shapes_info(self, node, ex, ey, body_w, body_h, zoom):
        shapes_info = []

        if node.type == "Root":
            # хитбоксы тела врага
            body_pin = node.properties.get("body_pin")
            if body_pin:
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == body_pin:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id):
                            shapes_info.append(self._get_hitbox_geom(self.nodes_data[hb_id], ex, ey, body_w, body_h, zoom, "body"))

            # хитбоксы детекции (зрения)
            det_pin = node.properties.get("det_pin")
            if det_pin:
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == det_pin:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id):
                            shapes_info.append(self._get_hitbox_geom(self.nodes_data[hb_id], ex, ey, body_w, body_h, zoom, "detection"))

            # универсальные хитбоксы остановки (stopping shapes)
            stop_pin = node.properties.get("stop_pin")
            if stop_pin:
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == stop_pin:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id):
                            shapes_info.append(self._get_hitbox_geom(self.nodes_data[hb_id], ex, ey, body_w, body_h, zoom, "movement_stop"))

        elif node.type in ("Flow", "Sequence", "Order"):
            trig_pin = node.properties.get("trig_pin")
            category_map = {"Flow": "flow_trigger", "Sequence": "sequence_trigger", "Order": "order_trigger"}
            category = category_map.get(node.type, "trigger")
            if trig_pin:
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == trig_pin:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id):
                            shapes_info.append(self._get_hitbox_geom(self.nodes_data[hb_id], ex, ey, body_w, body_h, zoom, category))

        elif node.type == "Projectile":
            hitbox_pin = node.properties.get("hitbox_pin")
            if hitbox_pin:
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == hitbox_pin:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id):
                            shapes_info.append(self._get_hitbox_geom(self.nodes_data[hb_id], ex, ey, body_w, body_h, zoom, "projectile"))

        elif node.type == "Movement":
            stop_pin = node.properties.get("stop_pin")
            if stop_pin:
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == stop_pin:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id):
                            shapes_info.append(self._get_hitbox_geom(self.nodes_data[hb_id], ex, ey, body_w, body_h, zoom, "movement_stop"))

        elif node.type == "Attack":
            p_out_atk = list(node.output_pins.keys())[0] if node.output_pins else None
            if p_out_atk:
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == p_out_atk:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id) and self.nodes_data[hb_id].type == "Hitbox":
                            shapes_info.append(self._get_hitbox_geom(self.nodes_data[hb_id], ex, ey, body_w, body_h, zoom, "attack"))

        elif node.type == "Hitbox":
            if not self.is_hitbox_linked_to_any_parent(node.id):
                shapes_info.append(self._get_hitbox_geom(node, ex, ey, body_w, body_h, zoom, "attack"))

        return [s for s in shapes_info if s is not None]

    def _get_hitbox_geom(self, hb, ex, ey, body_w, body_h, zoom, category):
        shape_type = hb.properties.get("shape_type", "rectangle")
        w = safe_num(hb.properties.get("w"), 50)
        h = safe_num(hb.properties.get("h"), 40)
        r = safe_num(hb.properties.get("r"), 25)
        offset_x = safe_num(hb.properties.get("offset_x"), 0)
        offset_y = safe_num(hb.properties.get("offset_y"), 0)
        angle = safe_num(hb.properties.get("angle"), 0.0)

        if category in ("attack", "projectile"):
            det_type = "following"
        elif category in ("body", "movement_stop"):
            det_type = "stationary"
        else:
            det_type = hb.properties.get("sprite_dir", "following")

        rx_left = ex - (safe_num(body_w, 30) * zoom) / 2.0
        rx_right = ex + (safe_num(body_w, 30) * zoom) / 2.0
        ry_top = ey - (safe_num(body_h, 50) * zoom) / 2.0

        scaled_offset_x = offset_x * zoom
        scaled_offset_y = offset_y * zoom
        scaled_r = r * zoom
        scaled_w = w * zoom
        scaled_h = h * zoom

        if det_type == "following":
            if shape_type == "circle":
                cx_shape = rx_right + scaled_offset_x + scaled_r
                cy_shape = ry_top + scaled_offset_y + scaled_r
            else:
                cx_shape = rx_right + scaled_offset_x + scaled_w / 2.0
                cy_shape = ry_top + scaled_offset_y + scaled_h / 2.0
        else: # stationary
            if shape_type == "circle":
                cx_shape = rx_left + scaled_offset_x + scaled_r
                cy_shape = ry_top + scaled_offset_y + scaled_r
            else:
                cx_shape = rx_left + scaled_offset_x + scaled_w / 2.0
                cy_shape = ry_top + scaled_offset_y + scaled_h / 2.0

        return (shape_type, scaled_w, scaled_h, scaled_r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape, hb, category)

    def draw_node_preview_shape(self, shape_info, is_focused):
        shape_type, scaled_w, scaled_h, scaled_r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape = shape_info[:10]
        hb_node = shape_info[10] if len(shape_info) > 10 else None
        category = shape_info[11] if len(shape_info) > 11 else "attack"

        alpha = 140 if is_focused else 20
        border_alpha = 255 if is_focused else 90

        if category == "body":
            fill = [110, 110, 125, alpha]
            border = [80, 80, 95, border_alpha]
        elif category == "detection":
            fill = [255, 220, 0, min(alpha, 15)]
            border = [255, 220, 0, border_alpha]
        elif category == "sequence_trigger":
            fill = [255, 100, 0, min(alpha, 15)]
            border = [255, 100, 0, border_alpha]
        elif category == "flow_trigger":
            fill = [0, 200, 255, min(alpha, 15)]
            border = [0, 200, 255, border_alpha]
        elif category == "order_trigger":
            fill = [180, 50, 255, min(alpha, 15)]
            border = [180, 50, 255, border_alpha]
        elif category == "projectile":
            fill = [105, 55, 140, min(alpha, 25)]
            border = [105, 55, 140, border_alpha]
        elif category == "movement_stop":
            # Хитбоксы остановки отрисовываем зелеными тонами
            fill = [0, 255, 100, min(alpha, 15)]
            border = [0, 200, 80, border_alpha]
        else: # attack
            fill = [255, 60, 60, min(alpha, 30)]
            border = [255, 60, 60, border_alpha]

        thickness = 2 if is_focused else 1

        if shape_type == "circle":
            dpg.draw_circle(
                center=[cx_shape, cy_shape],
                radius=scaled_r,
                fill=fill,
                color=border,
                thickness=thickness,
                parent="preview_drawlist"
            )
        else:
            rad = math.radians(-angle)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            dx, dy = scaled_w / 2.0, scaled_h / 2.0
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
                dpg.draw_circle(center=[cx_shape, cy_shape], radius=scaled_r, color=handle_color, thickness=2, parent="preview_drawlist")
                dpg.draw_circle(center=[cx_shape, cy_shape], radius=0.8 * scaled_r, color=[0, 240, 255, 120], thickness=1, parent="preview_drawlist")

                for ang_deg in [0, 90, 180, 270]:
                    rad_ang = math.radians(ang_deg)
                    hx = cx_shape + scaled_r * math.cos(rad_ang)
                    hy = cy_shape + scaled_r * math.sin(rad_ang)
                    dpg.draw_line(
                        p1=[cx_shape + 0.8 * scaled_r * math.cos(rad_ang), cy_shape + 0.8 * scaled_r * math.sin(rad_ang)],
                        p2=[hx, hy],
                        color=[0, 240, 255, 200],
                        thickness=1.5,
                        parent="preview_drawlist"
                    )
                    dpg.draw_circle(center=[hx, hy], radius=4, fill=handle_color, color=white_color, parent="preview_drawlist")

                dpg.draw_circle(center=[cx_shape, cy_shape], radius=3, fill=white_color, parent="preview_drawlist")

    def _hit_test_shape(self, info, mx, my):
        shape_type, scaled_w, scaled_h, scaled_r, offset_x, offset_y, angle, det_type, cx_shape, cy_shape = info[:10]

        if shape_type == "circle":
            dist = math.hypot(mx - cx_shape, my - cy_shape)
            if dist <= scaled_r + 8:
                if dist >= 0.75 * scaled_r:
                    return "resize_circle"
                else:
                    return "move"
            return None
        else: # rectangle
            rad = math.radians(angle)
            dx = mx - cx_shape
            dy = my - cy_shape
            rx_local = dx * math.cos(rad) - dy * math.sin(rad) + cx_shape
            ry_local = dx * math.sin(rad) + dy * math.cos(rad) + cy_shape

            half_w, half_h = scaled_w / 2.0, scaled_h / 2.0
            rad_fwd = math.radians(-angle)
            cos_fwd, sin_fwd = math.cos(rad_fwd), math.sin(rad_fwd)
            corners_local = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
            for cx_l, cy_l in corners_local:
                c_world_x = cx_l * cos_fwd - cy_l * sin_fwd + cx_shape
                c_world_y = cx_l * sin_fwd + cy_l * cos_fwd + cy_shape
                if math.hypot(mx - c_world_x, my - c_world_y) <= 10:
                    return "rotate"

            if (cx_shape - half_w <= rx_local <= cx_shape + half_w) and (cy_shape - half_h <= ry_local <= cy_shape + half_h):
                u = (rx_local - (cx_shape - half_w)) / scaled_w if scaled_w > 0 else 0.5
                v = (ry_local - (cy_shape - half_h)) / scaled_h if scaled_h > 0 else 0.5

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

        win_size = dpg.get_item_rect_size("preview_window")
        win_w = win_size[0] if win_size and win_size[0] > 10 else 380
        win_h = win_size[1] if win_size and win_size[1] > 10 else 340

        draw_w = win_w - 20
        draw_h = win_h - 80

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

        zoom = dpg.get_value("preview_zoom") if dpg.does_item_exist("preview_zoom") else 0.5

        root_node = None
        for n in self.nodes_data.values():
            if n.type == "Root":
                root_node = n
                break

        body_w = safe_num(root_node.properties.get("body_w"), 30) if root_node else 30
        body_h = safe_num(root_node.properties.get("body_h"), 50) if root_node else 50

        bw = body_w * zoom
        bh = body_h * zoom

        floor_y = ey + bh / 2.0

        # Линия пола
        dpg.draw_line(p1=[10, floor_y], p2=[draw_w - 10, floor_y], color=[100, 100, 100, 255], thickness=2, parent="preview_drawlist")

        # Базовое тело врага
        dpg.draw_rectangle(
            pmin=[ex - bw / 2.0, ey - bh / 2.0],
            pmax=[ex + bw / 2.0, ey + bh / 2.0],
            fill=[110, 110, 125, 255],
            color=[80, 80, 95, 255],
            thickness=1,
            parent="preview_drawlist"
        )

        # Голова врага
        head_h = max(2.0, bh * 0.25)
        dpg.draw_rectangle(
            pmin=[ex - bw / 2.0, ey - bh / 2.0],
            pmax=[ex + bw / 2.0, ey - bh / 2.0 + head_h],
            fill=[80, 80, 95, 255],
            color=[60, 60, 75, 255],
            thickness=1,
            parent="preview_drawlist"
        )

        # Глаз врага
        eye_w = max(2.0, 4.0 * zoom)
        eye_x = ex + bw / 2.0 - 6.0 * zoom
        eye_y = ey - bh / 2.0 + 6.0 * zoom
        dpg.draw_rectangle(
            pmin=[eye_x, eye_y],
            pmax=[eye_x + eye_w, eye_y + eye_w],
            fill=[255, 255, 255, 255],
            color=[255, 255, 255, 255],
            parent="preview_drawlist"
        )

        # Полоска HP
        dpg.draw_rectangle(
            pmin=[ex - bw / 2.0, ey - bh / 2.0 - 8.0 * zoom],
            pmax=[ex + bw / 2.0, ey - bh / 2.0 - 4.0 * zoom],
            fill=[0, 255, 0, 255],
            parent="preview_drawlist"
        )

        # Имя врага
        enemy_name = root_node.properties.get("name", "Enemy") if root_node else "Enemy"
        dpg.draw_text(
            pos=[ex - bw / 2.0, ey - bh / 2.0 - 22.0 * zoom],
            text=enemy_name,
            color=[220, 220, 220, 255],
            size=max(10, int(12 * zoom)),
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

        # Собираем хитбоксы всех нод
        all_shapes = []
        for node in self.nodes_data.values():
            all_shapes.extend(self.get_node_shapes_info(node, ex, ey, body_w, body_h, zoom))

        focused_shapes = []
        for s in all_shapes:
            hb_node = s[10]
            is_focused = False
            if active_node:
                if hb_node == active_node or hb_node.id == active_node.id:
                    is_focused = True
                elif self.is_hitbox_connected_to_node(hb_node.id, active_node.id):
                    is_focused = True

            if is_focused:
                focused_shapes.append(s)
            else:
                self.draw_node_preview_shape(s, False)

        for s in focused_shapes:
            self.draw_node_preview_shape(s, True)

        if clicked and not self.preview_dragging and not getattr(self, "preview_canvas_panning", False):
            target_shape = None
            target_mode = None

            for s in focused_shapes:
                mode = self._hit_test_shape(s, mx, my)
                if mode:
                    target_shape = s
                    target_mode = mode
                    break

            if not target_shape:
                for s in reversed(all_shapes):
                    mode = self._hit_test_shape(s, mx, my)
                    if mode:
                        target_shape = s
                        target_mode = mode
                        break

            if target_shape:
                hb_node = target_shape[10]
                if self.active_selected_node_id != hb_node.id:
                    self.active_selected_node_id = hb_node.id
                    dpg.clear_selected_nodes("editor_tag")
                    self.rebuild_inspector(hb_node.id)

                self.preview_dragging = True
                self.preview_drag_mode = target_mode
                self.preview_drag_start_mouse = (mx, my)

                hb = target_shape[10]
                self.preview_drag_start_val = {
                    "offset_x": safe_num(hb.properties.get("offset_x"), 0),
                    "offset_y": safe_num(hb.properties.get("offset_y"), 0),
                    "w": safe_num(hb.properties.get("w"), 50),
                    "h": safe_num(hb.properties.get("h"), 40),
                    "r": safe_num(hb.properties.get("r"), 25),
                    "angle": safe_num(hb.properties.get("angle"), 0.0),
                    "cx_shape": target_shape[8],
                    "cy_shape": target_shape[9]
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

        if self.preview_dragging and down and active_node and active_node.type == "Hitbox":
            dx_mouse = mx - self.preview_drag_start_mouse[0]
            dy_mouse = my - self.preview_drag_start_mouse[1]

            dx_world = dx_mouse / zoom
            dy_world = dy_mouse / zoom

            start_vals = self.preview_drag_start_val
            updates = {}
            mode = self.preview_drag_mode

            if mode == "move":
                updates["offset_x"] = int(start_vals["offset_x"] + dx_world)
                updates["offset_y"] = int(start_vals["offset_y"] + dy_world)
            elif mode == "resize_right":
                updates["w"] = max(5, int(start_vals["w"] + dx_world))
            elif mode == "resize_left":
                new_w = max(5, int(start_vals["w"] - dx_world))
                updates["w"] = new_w
                updates["offset_x"] = int(start_vals["offset_x"] + (start_vals["w"] - new_w))
            elif mode == "resize_bottom":
                updates["h"] = max(5, int(start_vals["h"] + dy_world))
            elif mode == "resize_top":
                new_h = max(5, int(start_vals["h"] - dy_world))
                updates["h"] = new_h
                updates["offset_y"] = int(start_vals["offset_y"] + (start_vals["h"] - new_h))
            elif mode == "resize_circle":
                cx_shape_start = start_vals["cx_shape"]
                cy_shape_start = start_vals["cy_shape"]
                current_dist = math.hypot(mx - cx_shape_start, my - cy_shape_start)
                updates["r"] = max(5, int(current_dist / zoom))
            elif mode == "rotate":
                cx_shape_start = start_vals["cx_shape"]
                cy_shape_start = start_vals["cy_shape"]
                start_mouse_angle = math.atan2(self.preview_drag_start_mouse[1] - cy_shape_start, self.preview_drag_start_mouse[0] - cx_shape_start)
                current_mouse_angle = math.atan2(my - cy_shape_start, mx - cx_shape_start)
                angle_diff_rad = current_mouse_angle - start_mouse_angle
                angle_diff_deg = math.degrees(angle_diff_rad)
                updates["angle"] = float(start_vals["angle"] - angle_diff_deg)

            for k, v in updates.items():
                active_node.properties[k] = v
            self.rebuild_inspector(active_node.id)

        if self.preview_dragging and not down:
            self.preview_dragging = False
            self.preview_drag_mode = None
            self.save_preset_file(None, None)