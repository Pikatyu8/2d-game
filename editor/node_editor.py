# editor/node_editor.py
import sys
import os
import time
import json
import math
import copy

# Динамически добавляем корневую директорию проекта в sys.path.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import dearpygui.dearpygui as dpg
except ImportError as e:
    with open("node_editor_error.log", "a", encoding="utf-8") as f:
        f.write(f"\n[Ошибка] Не удалось импортировать Dear PyGui: {e}\n")
        f.write("[Решение] Пожалуйста, убедитесь, что библиотека установлена в используемом Python-окружении:\n")
        f.write(f"          Сделайте запуск: {sys.executable} -m pip install dearpygui\n")
    raise

from editor.node_editor_parts.node_editor_state import NodeEditorStateMixin
from editor.node_editor_parts.node_editor_nodes import NodeEditorNodesMixin
from editor.node_editor_parts.node_editor_io import NodeEditorIOMixin
from editor.node_editor_parts.node_editor_inspector import NodeEditorInspectorMixin

class NodeEditor(
    NodeEditorStateMixin,
    NodeEditorNodesMixin,
    NodeEditorIOMixin,
    NodeEditorInspectorMixin
):
    def __init__(self):
        dpg.create_context()
        self.init_state()
        self.init_themes()

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

    def setup_ui(self):
        with dpg.window(
            label="AI Behavior Node Visual Graph Designer",
            tag="main_window",
            width=1400,
            height=800,
            no_bring_to_front_on_focus=True
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("Target Preset:")
                presets = self.find_all_presets()
                default_val = presets[0] if presets else ""
                dpg.add_combo(items=presets, default_value=default_val, tag="preset_combo", width=300)
                dpg.add_button(label="Load Graph", callback=self.load_preset_file)
                dpg.add_button(label="Save (Live-Reload)", callback=self.save_preset_file)
                dpg.add_button(label="Auto-Arrange", callback=self.auto_arrange)
                dpg.add_checkbox(label="Show Preview [P]", default_value=True, tag="show_preview_checkbox", callback=self.toggle_preview_visibility)
                dpg.add_button(label="Focus Preview [F]", callback=self.toggle_focus)
                
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                with dpg.child_window(tag="left_panel_window", width=320, height=720):
                    with dpg.collapsing_header(label="Create Graph Nodes", default_open=True):
                        dpg.add_button(label="Add AI Flow Node", width=290, callback=self.spawn_flow_btn)
                        dpg.add_button(label="Add Action Sequence Node", width=290, callback=self.spawn_sequence_btn)
                        dpg.add_button(label="Add Attack Action Node", width=290, callback=self.spawn_attack_btn)
                        dpg.add_button(label="Add Hitbox Component Node", width=290, callback=self.spawn_hitbox_btn)
                        dpg.add_button(label="Add Movement Action Node", width=290, callback=self.spawn_movement_btn)
                        dpg.add_button(label="Add Phase Component Node", width=290, callback=self.spawn_phase_btn)
                        dpg.add_button(label="Add Projectile Action Node", width=290, callback=self.spawn_projectile_btn)
                        
                    dpg.add_separator()
                    
                    with dpg.child_window(tag="properties_panel", width=300, height=330):
                        dpg.add_text("Select a node on the canvas to inspect its properties.")
                        
                    dpg.add_separator()
                    
                    # Интегрированная панель таймлайна последовательностей в левой части экрана
                    with dpg.collapsing_header(label="Sequence Timeline", default_open=True, tag="timeline_header"):
                        dpg.add_drawlist(width=300, height=120, tag="timeline_drawlist")
                        
                with dpg.child_window(tag="right_panel_window", width=1050, height=720):
                    dpg.add_node_editor(tag="editor_tag", callback=self.link_callback, delink_callback=self.delink_callback, minimap=True)

        self.setup_preview_window()
        
        # Регистрация динамического изменения размера под вьюпорт и клавиатурного ввода
        dpg.set_viewport_resize_callback(self.resize_callback)
        with dpg.handler_registry():
            dpg.add_key_press_handler(callback=self.global_key_handler)

    def setup_preview_window(self):
        # Окно предпросмотра сделано ресайзабельным, но закрепленным по позиции (no_move=True)
        with dpg.window(label="Interactive Preview Panel", tag="preview_window", width=380, height=340, pos=[950, 150], no_close=True, no_move=True):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Reset View", callback=self.reset_preview_pan)
                dpg.add_text("RMB: Pan | Drag to resize")
            dpg.add_drawlist(width=360, height=270, tag="preview_drawlist")

    def resize_callback(self, sender, app_data):
        if not dpg.does_item_exist("main_window"):
            return
        
        vw = dpg.get_viewport_width()
        vh = dpg.get_viewport_height()
        
        # Масштабируем главное контейнерное окно под текущие границы экрана
        dpg.configure_item("main_window", width=vw, height=vh)
        dpg.set_item_pos("main_window", [0, 0])
        
        left_w = 320
        child_h = max(100, vh - 90)
        right_w = max(100, vw - left_w - 40)
        
        if dpg.does_item_exist("left_panel_window"):
            dpg.configure_item("left_panel_window", width=left_w, height=child_h)
        if dpg.does_item_exist("right_panel_window"):
            dpg.configure_item("right_panel_window", width=right_w, height=child_h)
        if dpg.does_item_exist("properties_panel"):
            # Вычисляем высоту с учетом свободного места под заголовок создания нод и таймлайн
            dpg.configure_item("properties_panel", width=left_w - 20, height=max(100, child_h - 410))

    def global_key_handler(self, sender, app_data):
        # 122 — F11, 27 — Escape для выхода/входа в полноэкранный режим
        if app_data == 122 or app_data == 27:
            dpg.toggle_viewport_fullscreen()
        # 70 — Клавиша 'F' для переключения фокуса на окно симуляции
        elif app_data == 70:
            self.toggle_focus()
        # 80 — Клавиша 'P' для временного скрытия/показа окна предпросмотра
        elif app_data == 80:
            if dpg.does_item_exist("show_preview_checkbox"):
                current_val = dpg.get_value("show_preview_checkbox")
                dpg.set_value("show_preview_checkbox", not current_val)
                self.toggle_preview_visibility()

    def _is_mouse_over_any_node(self, mx, my):
        for node_id in self.nodes_data.keys():
            try:
                pos = dpg.get_item_pos(node_id)
                if pos[0] - 10 <= mx <= pos[0] + 250 and pos[1] - 10 <= my <= pos[1] + 220:
                    return True
            except Exception:
                pass
        return False

    def get_node_shape_info(self, node, ex, ey, body_w, body_h, is_vis_box=False):
        if is_vis_box:
            if node.type == "Hitbox" and node.properties.get("vis_enabled", False):
                shape_type = node.properties.get("vis_type", "rectangle")
                w = node.properties.get("vis_w", 50)
                h = node.properties.get("vis_h", 40)
                r = node.properties.get("vis_r", 25)
                offset_x = node.properties.get("vis_offset_x", 0)
                offset_y = node.properties.get("vis_offset_y", 0)
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
                w = node.properties.get("det_w", 220)
                h = node.properties.get("det_h", 70)
                r = node.properties.get("det_r", 110)
                offset_x = node.properties.get("det_offset_x", 0)
                offset_y = node.properties.get("det_offset_y", -10)
                angle = node.properties.get("det_angle", 0.0)
                det_type = node.properties.get("det_type", "following")
            elif node.type in ("Flow", "Sequence"):
                shape_type = node.properties.get("trig_shape_type", "rectangle")
                w = node.properties.get("trig_w", 90)
                h = node.properties.get("trig_h", 50)
                r = node.properties.get("trig_r", 45)
                offset_x = node.properties.get("trig_offset_x", 10)
                offset_y = node.properties.get("trig_offset_y", 0)
                angle = 0.0
                det_type = node.properties.get("trig_type", "following")
            elif node.type == "Hitbox":
                shape_type = node.properties.get("shape_type", "rectangle")
                w = node.properties.get("w", 50)
                h = node.properties.get("h", 40)
                r = node.properties.get("r", 25)
                offset_x = node.properties.get("offset_x", 10)
                offset_y = node.properties.get("offset_y", 0)
                angle = node.properties.get("angle", 0.0)
                det_type = "following"
            else:
                return None
            
        rx_left = ex - body_w / 2
        rx_right = ex + body_w / 2
        ry_top = ey - body_h / 2
        
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
        
        # Получаем реальные размеры встроенной панели, чтобы подстроить холст рисования
        draw_w, draw_h = 360, 270
        current_win_size = dpg.get_item_rect_size("preview_window")
        if current_win_size and current_win_size[0] > 10 and current_win_size[1] > 10:
            draw_w = max(50, current_win_size[0] - 20)
            draw_h = max(50, current_win_size[1] - 70)
            if not hasattr(self, "last_preview_win_size") or self.last_preview_win_size != current_win_size:
                self.last_preview_win_size = current_win_size
                dpg.configure_item("preview_drawlist", width=draw_w, height=draw_h)

        # Вычисляем якорные координаты для прижатия к правому верхнему углу холста
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
                
        body_w = root_node.properties.get("body_w", 30) if root_node else 30
        body_h = root_node.properties.get("body_h", 50) if root_node else 50
        
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
                    if vis_info:
                        mode = self._hit_test_shape(vis_info, mx, my)
                        if mode:
                            target_node = active_node
                            target_mode = mode
                            target_info = vis_info
                            target_is_vis = True

            if not target_node:
                for node in reversed(list(self.nodes_data.values())):
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

    def update_timeline(self):
        if not dpg.does_item_exist("timeline_drawlist"):
            return
            
        dpg.delete_item("timeline_drawlist", children_only=True)
        
        # Получаем активный выделенный узел
        node = self.nodes_data.get(self.active_selected_node_id) if self.active_selected_node_id else None
        
        # Если выделен хитбокс, находим родительскую атаку
        if node and node.type == "Hitbox":
            p_in_hitbox = list(node.input_pins.keys())[0] if node.input_pins else None
            for lid, (p_out, p_in) in self.links_data.items():
                if p_in == p_in_hitbox:
                    atk_id = self.pin_to_node.get(p_out)
                    if atk_id and self.nodes_data.get(atk_id) and self.nodes_data[atk_id].type == "Attack":
                        # Находим последовательность, к которой прилинкована эта атака
                        p_atk_in = list(self.nodes_data[atk_id].input_pins.keys())[0]
                        for lid2, (p_out2, p_in2) in self.links_data.items():
                            if p_in2 == p_atk_in:
                                seq_id = self.pin_to_node.get(p_out2)
                                if seq_id and self.nodes_data.get(seq_id) and self.nodes_data[seq_id].type == "Sequence":
                                    node = self.nodes_data[seq_id]
                                    break
                        break

        # Отрисовка пустого состояния, если не выделена последовательность
        if not node or node.type != "Sequence":
            dpg.draw_text(
                pos=[15, 45], 
                text="Select any Sequence node\nto view its frame timeline.", 
                color=[140, 140, 150, 200], 
                size=12, 
                parent="timeline_drawlist"
            )
            return

        # Находим и группируем все шаги Sequence на основе линков ее выходящих пинов
        steps = []
        for pin_id in node.properties.get("steps_pins", []):
            pin_prop = node.output_pins[pin_id].properties
            step_delay = pin_prop["delay"]
            step_index = pin_prop["index"]
            
            linked_act = None
            for _, (p_out, p_in) in self.links_data.items():
                if p_out == pin_id:
                    act_id = self.pin_to_node.get(p_in)
                    if act_id and self.nodes_data.get(act_id) and self.nodes_data[act_id].type in ("Attack", "Movement", "Projectile"):
                        linked_act = self.nodes_data[act_id]
                        break
            steps.append({
                "pin_id": pin_id,
                "index": step_index,
                "delay": step_delay,
                "node": linked_act
            })

        # Вспомогательная функция вычисления длительности действия
        def get_step_duration(step_node):
            if not step_node:
                return 10
            stype = step_node.type
            if stype == "Attack":
                windup = step_node.properties.get("windup", 35)
                p_hitboxes_out = list(step_node.output_pins.keys())[0]
                connected_hitboxes = []
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == p_hitboxes_out:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id) and self.nodes_data[hb_id].type == "Hitbox":
                            connected_hitboxes.append(self.nodes_data[hb_id])
                total_dur = max([hb.properties.get("delay", 0) + hb.properties.get("duration", 10) for hb in connected_hitboxes]) if connected_hitboxes else 15
                return windup + total_dur
            elif stype == "Movement":
                p_phases_out = list(step_node.output_pins.keys())[0]
                connected_phases = []
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == p_phases_out:
                        ph_id = self.pin_to_node.get(p_in)
                        if ph_id and self.nodes_data.get(ph_id) and self.nodes_data[ph_id].type == "Phase":
                            connected_phases.append(self.nodes_data[ph_id])
                durations = []
                for ph in connected_phases:
                    p_dur = 1 if ph.properties.get("direction") == "teleport" else ph.properties.get("duration", 15)
                    durations.append(ph.properties.get("delay", 0) + p_dur)
                return max(durations) if durations else 15
            elif stype == "Projectile":
                return 8
            return 10

        # Рассчитываем общую длину шкалы времени
        total_duration = max([s["delay"] + get_step_duration(s["node"]) for s in steps]) if steps else 60
        scale_max = max(60, total_duration)

        bar_x = 10
        bar_y = 10
        bar_w = 280
        bar_h = 75

        # Фон сетки таймлайна
        dpg.draw_rectangle(pmin=[bar_x, bar_y], pmax=[bar_x + bar_w, bar_y + bar_h], fill=[15, 15, 20, 255], color=[50, 50, 60, 255], parent="timeline_drawlist")

        # Отрисовка временной шкалы и разметки кадров
        for f in range(0, scale_max + 1, 20):
            grid_x = bar_x + (f / scale_max) * bar_w
            dpg.draw_line(p1=[grid_x, bar_y], p2=[grid_x, bar_y + bar_h], color=[35, 35, 40, 255], thickness=1, parent="timeline_drawlist")
            if f % 40 == 0 or f == scale_max:
                dpg.draw_text(pos=[grid_x - 6, bar_y + bar_h + 3], text=str(f), color=[100, 100, 100, 255], size=9, parent="timeline_drawlist")

        # Отрисовка полос шагов
        step_row_height = 12
        for s_idx, s in enumerate(steps):
            delay = s["delay"]
            step_node = s["node"]
            duration = get_step_duration(step_node)
            
            row_y = bar_y + 4 + (s_idx % 4) * 17
            is_current = (self.active_selected_node_id == (step_node.id if step_node else None))
            
            if step_node and step_node.type == "Attack":
                windup = step_node.properties.get("windup", 35)
                p_hitboxes_out = list(step_node.output_pins.keys())[0]
                connected_hitboxes = []
                for _, (p_out, p_in) in self.links_data.items():
                    if p_out == p_hitboxes_out:
                        hb_id = self.pin_to_node.get(p_in)
                        if hb_id and self.nodes_data.get(hb_id) and self.nodes_data[hb_id].type == "Hitbox":
                            connected_hitboxes.append(self.nodes_data[hb_id])
                total_dur = max([hb.properties.get("delay", 0) + hb.properties.get("duration", 10) for hb in connected_hitboxes]) if connected_hitboxes else 15
                
                tx = bar_x + (delay / scale_max) * bar_w
                tw = (windup / scale_max) * bar_w
                
                ax = bar_x + ((delay + windup) / scale_max) * bar_w
                aw = (total_dur / scale_max) * bar_w
                
                # Подготовка атаки (windup) - оранжевый
                dpg.draw_rectangle(pmin=[tx, row_y], pmax=[tx + tw, row_y + step_row_height], fill=[255, 140, 0, 150], color=[255, 140, 0, 255] if is_current else [150, 80, 0, 200], parent="timeline_drawlist")
                # Активная фаза действия (хитбоксы) - красный
                dpg.draw_rectangle(pmin=[ax, row_y], pmax=[ax + aw, row_y + step_row_height], fill=[255, 60, 60, 180], color=[255, 60, 60, 255] if is_current else [180, 40, 40, 200], parent="timeline_drawlist")
                
                label = f"{step_node.properties.get('name', 'Attack')} (Step {s['index']})"
                dpg.draw_text(pos=[tx + 5, row_y - 1], text=label, color=[255, 255, 255, 220], size=10, parent="timeline_drawlist")
                
            elif step_node and step_node.type == "Movement":
                mx_start = bar_x + (delay / scale_max) * bar_w
                mw = (duration / scale_max) * bar_w
                
                # Фаза перемещения - синий
                dpg.draw_rectangle(pmin=[mx_start, row_y], pmax=[mx_start + mw, row_y + step_row_height], fill=[45, 85, 140, 150], color=[75, 130, 160, 255] if is_current else [45, 85, 140, 200], parent="timeline_drawlist")
                
                label = f"{step_node.properties.get('name', 'Movement')} (Step {s['index']})"
                dpg.draw_text(pos=[mx_start + 5, row_y - 1], text=label, color=[255, 255, 255, 220], size=10, parent="timeline_drawlist")
                
            elif step_node and step_node.type == "Projectile":
                px_start = bar_x + (delay / scale_max) * bar_w
                pw = (duration / scale_max) * bar_w
                
                # Фаза стрельбы снарядом - фиолетовый
                dpg.draw_rectangle(pmin=[px_start, row_y], pmax=[px_start + pw, row_y + step_row_height], fill=[105, 55, 140, 150], color=[105, 55, 140, 255] if is_current else [80, 40, 110, 200], parent="timeline_drawlist")
                
                label = f"{step_node.properties.get('name', 'Projectile')} (Step {s['index']})"
                dpg.draw_text(pos=[px_start + 5, row_y - 1], text=label, color=[255, 255, 255, 220], size=10, parent="timeline_drawlist")
            else:
                # Слот шага без связи
                ux_start = bar_x + (delay / scale_max) * bar_w
                uw = (10 / scale_max) * bar_w
                dpg.draw_rectangle(pmin=[ux_start, row_y], pmax=[ux_start + uw, row_y + step_row_height], fill=[40, 40, 45, 100], color=[80, 80, 85, 120], parent="timeline_drawlist")
                label = f"Unlinked (Step {s['index']})"
                dpg.draw_text(pos=[ux_start + 5, row_y - 1], text=label, color=[150, 150, 150, 180], size=10, parent="timeline_drawlist")

    def run(self, arg_name=None):
        dpg.create_viewport(title="AI Visual Graph Editor", width=1410, height=810)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        # Переводим вьюпорт в полноэкранный режим при запуске
        dpg.toggle_viewport_fullscreen()

        last_checked_selection = None
        while dpg.is_dearpygui_running():
            self.update_preview()
            self.update_timeline()
            
            mouse_down_r = dpg.is_mouse_button_down(dpg.mvMouseButton_Right)
            mouse_clicked_r = dpg.is_mouse_button_clicked(dpg.mvMouseButton_Right)

            m_pos = dpg.get_mouse_pos(local=False)
            
            is_mouse_over_preview = False
            try:
                p_min = dpg.get_item_rect_min("preview_window")
                p_size = dpg.get_item_rect_size("preview_window")
                if p_min[0] <= m_pos[0] <= p_min[0] + p_size[0] and p_min[1] <= m_pos[1] <= p_min[1] + p_size[1]:
                    is_mouse_over_preview = True
            except Exception:
                pass

            if not is_mouse_over_preview and 330 <= m_pos[0] <= 1380 and 40 <= m_pos[1] <= 760:
                if mouse_clicked_r and not getattr(self, "graph_canvas_panning", False):
                    self.graph_canvas_panning = True
                    self.graph_pan_last_mouse = m_pos
                
                if getattr(self, "graph_canvas_panning", False) and mouse_down_r:
                    dx = m_pos[0] - self.graph_pan_last_mouse[0]
                    dy = m_pos[1] - self.graph_pan_last_mouse[1]
                    if dx != 0 or dy != 0:
                        for node_id in list(self.nodes_data.keys()):
                            try:
                                cur_p = dpg.get_item_pos(node_id)
                                dpg.set_item_pos(node_id, [cur_p[0] + dx, cur_p[1] + dy])
                            except Exception:
                                pass
                        self.graph_pan_last_mouse = m_pos

            if not mouse_down_r:
                self.graph_canvas_panning = False

            if self.current_loaded_file_path and os.path.exists(self.current_loaded_file_path):
                try:
                    mtime = os.path.getmtime(self.current_loaded_file_path)
                    if not hasattr(self, "last_file_mod_time"):
                        self.last_file_mod_time = mtime
                    if mtime > self.last_file_mod_time:
                        self.last_file_mod_time = mtime
                        print(f"[Live-Reload] Пресет изменен извне (Pygame). Перезагрузка графа...")
                        self.load_preset_file(None, None)
                except Exception:
                    pass

            selected = dpg.get_selected_nodes("editor_tag")
            if selected:
                active_sel = selected[0]
                if active_sel != last_checked_selection:
                    last_checked_selection = active_sel
                    self.rebuild_inspector(active_sel)
                    
                    node = self.nodes_data.get(active_sel)
                    if node:
                        print(f"[Node Editor Log] Selected node: id={node.id}, type={node.type}, label='{node.label}'")
                        selection_info = None
                        
                        if node.type == "Hitbox":
                            atk_node = None
                            p_in_hitbox = list(node.input_pins.keys())[0] if node.input_pins else None
                            if p_in_hitbox:
                                for lid, (p_out, p_in) in self.links_data.items():
                                    if p_in == p_in_hitbox:
                                        atk_node_id = self.pin_to_node.get(p_out)
                                        if atk_node_id and self.nodes_data.get(atk_node_id) and self.nodes_data[atk_node_id].type == "Attack":
                                            atk_node = self.nodes_data[atk_node_id]
                                            break
                            if atk_node:
                                sorted_attacks = sorted([n for n in self.nodes_data.values() if n.type == "Attack"], key=lambda x: dpg.get_item_pos(x.id)[1])
                                try:
                                    atk_idx = sorted_attacks.index(atk_node)
                                    p_hitboxes_out = list(atk_node.output_pins.keys())[0]
                                    connected_hitboxes = []
                                    for _, (p_out, p_in) in self.links_data.items():
                                        if p_out == p_hitboxes_out:
                                            hb_node_id = self.pin_to_node.get(p_in)
                                            if hb_node_id and self.nodes_data.get(hb_node_id) and self.nodes_data[hb_node_id].type == "Hitbox":
                                                connected_hitboxes.append(self.nodes_data[hb_node_id])
                                    connected_hitboxes.sort(key=lambda x: x.properties.get("delay", 0))
                                    hb_idx = connected_hitboxes.index(node)
                                    
                                    selection_info = {
                                        "preset_name": dpg.get_value("preset_combo"),
                                        "inspector_tab": "DETAILED_ATTACK",
                                        "attack_idx": atk_idx,
                                        "box_idx": hb_idx
                                    }
                                except ValueError as ve:
                                    print(f"[Node Editor Error] Failed to resolve index in lists: {ve}")
                                    
                        elif node.type == "Sequence":
                            sorted_sequences = sorted([n for n in self.nodes_data.values() if n.type == "Sequence"], key=lambda x: dpg.get_item_pos(x.id)[1])
                            if node in sorted_sequences:
                                seq_idx = sorted_sequences.index(node)
                                selection_info = {
                                    "preset_name": dpg.get_value("preset_combo"),
                                    "inspector_tab": "K-FRAMES",
                                    "seq_idx": seq_idx
                                }
                                
                        elif node.type == "Flow":
                            sorted_flows = sorted([n for n in self.nodes_data.values() if n.type == "Flow"], key=lambda x: dpg.get_item_pos(x.id)[1])
                            if node in sorted_flows:
                                flow_idx = sorted_flows.index(node)
                                selection_info = {
                                    "preset_name": dpg.get_value("preset_combo"),
                                    "inspector_tab": "DETAILED_FLOW",
                                    "flow_idx": flow_idx
                                }
                                
                        elif node.type == "Root":
                            selection_info = {
                                "preset_name": dpg.get_value("preset_combo"),
                                "inspector_tab": "MAIN"
                            }
                            
                        if selection_info:
                            try:
                                with open(".editor_selection.json", "w", encoding="utf-8") as sf:
                                    json.dump(selection_info, sf, indent=4)
                            except Exception as ex:
                                print(f"[Node Editor Error] Failed to write .editor_selection.json: {ex}")
            dpg.render_dearpygui_frame()
            time.sleep(0.016)

        dpg.destroy_context()

if __name__ == "__main__":
    editor = NodeEditor()
    editor.setup_ui()
    
    start_arg = sys.argv[1].strip() if len(sys.argv) > 1 else None
    editor.run(start_arg)