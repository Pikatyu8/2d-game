# entities/enemy_parts/enemy_collision.py
import pygame
import math
from core.physics import collides_polygon_polygon

def safe_int(val, default=0):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        if val.startswith("$"):
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default
    return default

class EnemyCollisionMixin:
    # --- Одиночные методы-обертки для совместимости с редактором Pygame ---
    def get_detection_shape(self):
        shapes = self.get_detection_shapes()
        return shapes[0] if shapes else None

    def get_attack_zone_shape_for_attack_zone(self, z_idx):
        shapes = self.get_attack_zone_shapes_for_sequence(z_idx)
        return shapes[0] if shapes else None

    def get_attack_zone_shape_for_flow_zone(self, f_idx):
        shapes = self.get_attack_zone_shapes_for_flow(f_idx)
        return shapes[0] if shapes else None

    def get_attack_zone_shape_for_order_zone(self, o_idx):
        shapes = self.get_attack_zone_shapes_for_order(o_idx)
        return shapes[0] if shapes else None

    # --- Множественные хитбоксы тела противника (Root -> Body Shapes) ---
    def get_body_shapes(self):
        shapes_list = self.config.get("body_shapes", [])
        if not shapes_list and "body" in self.config:
            b = self.config["body"]
            shapes_list = [{
                "shape": {"type": "rectangle", "w": b.get("w", 30), "h": b.get("h", 50)},
                "offset_x": 0, "offset_y": 0, "angle": 0
            }]

        resolved_shapes = []
        for s in shapes_list:
            shape = s["shape"]
            ox, oy = s.get("offset_x", 0), s.get("offset_y", 0)
            angle = s.get("angle", 0)
            stype = shape.get("type", "rectangle")

            if stype == "rectangle":
                w, h = shape["w"], shape["h"]
                abs_x = self.rect.x + ox
                abs_y = self.rect.y + oy
                resolved_shapes.append(("rectangle", (pygame.Rect(abs_x, abs_y, w, h), angle)))
            elif stype == "circle":
                r = shape["r"]
                cx = self.rect.centerx + ox
                cy = self.rect.centery + oy
                resolved_shapes.append(("circle", (cx, cy, r)))
        return resolved_shapes

    # --- Множественные зоны зрения (Root -> Detection Shapes) ---
    def get_detection_shapes(self):
        shapes_list = self.config.get("detection_shapes", [])
        if not shapes_list and "detection" in self.config:
            det = self.config["detection"]
            shapes_list = [{
                "shape": det.get("shape", {"type": "rectangle", "w": 220, "h": 70}),
                "offset_x": det.get("offset_x", 0),
                "offset_y": det.get("offset_y", -10),
                "angle": det.get("angle", 0),
                "type": det.get("type", "following")
            }]

        resolved_shapes = []
        for s in shapes_list:
            shape = s["shape"]
            ox, oy = s.get("offset_x", 0), s.get("offset_y", 0)
            angle = s.get("angle", 0)
            det_type = s.get("type", "following")
            stype = shape.get("type", "rectangle")

            if stype == "rectangle":
                w, h = shape["w"], shape["h"]
                if det_type == "following" and self.direction == -1:
                    abs_x = self.rect.left - ox - w
                    effective_angle = -angle
                elif det_type == "following":
                    abs_x = self.rect.right + ox
                    effective_angle = angle
                else:
                    abs_x = self.rect.x + ox
                    effective_angle = angle
                abs_y = self.rect.y + oy
                resolved_shapes.append(("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle)))
            elif stype == "circle":
                r = shape["r"]
                if det_type == "following" and self.direction == -1:
                    cx = self.rect.left - ox - r
                elif det_type == "following":
                    cx = self.rect.right + ox + r
                else:
                    cx = self.rect.x + ox + r
                cy = self.rect.y + oy + r
                resolved_shapes.append(("circle", (cx, cy, r)))
        return resolved_shapes

    # --- Множественные зоны остановки (Root -> Stopping Shapes) ---
    def get_stop_shapes(self):
        shapes_list = self.config.get("stop_shapes", [])
        if not shapes_list:
            # Резервный хитбокс на основе старого stop_dist для обратной совместимости
            move_cfg = self.config.get("movement_config", {})
            stop_dist = move_cfg.get("stop_dist", 60)
            shapes_list = [{
                "shape": {"type": "rectangle", "w": stop_dist * 2, "h": self.rect.height + 40},
                "offset_x": -stop_dist + self.rect.width // 2, "offset_y": -20,
                "angle": 0, "type": "stationary"
            }]

        resolved_shapes = []
        for s in shapes_list:
            shape = s["shape"]
            ox, oy = s.get("offset_x", 0), s.get("offset_y", 0)
            angle = s.get("angle", 0)
            det_type = s.get("type", "stationary")
            stype = shape.get("type", "rectangle")

            if stype == "rectangle":
                w, h = shape["w"], shape["h"]
                if det_type == "following" and self.direction == -1:
                    abs_x = self.rect.left - ox - w
                    effective_angle = -angle
                elif det_type == "following":
                    abs_x = self.rect.right + ox
                    effective_angle = angle
                else:
                    abs_x = self.rect.x + ox
                    effective_angle = angle
                abs_y = self.rect.y + oy
                resolved_shapes.append(("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle)))
            elif stype == "circle":
                r = shape["r"]
                if det_type == "following" and self.direction == -1:
                    cx = self.rect.left - ox - r
                elif det_type == "following":
                    cx = self.rect.right + ox + r
                else:
                    cx = self.rect.x + ox + r
                cy = self.rect.y + oy + r
                resolved_shapes.append(("circle", (cx, cy, r)))
        return resolved_shapes

    def check_player_in_stop_zone(self, player_rect):
        for stype, val in self.get_stop_shapes():
            if self._check_single_shape_collision(player_rect, stype, val):
                return True
        return False

    def check_player_detected(self, player_rect):
        if self.rect.colliderect(player_rect):
            return True

        for stype, val in self.get_detection_shapes():
            if self._check_single_shape_collision(player_rect, stype, val):
                return True

        for idx in range(len(self.sequences)):
            if idx in getattr(self, "connected_seq_indices", set()):
                continue
            if self.check_player_in_zone(player_rect, idx):
                return True

        for f_idx in range(len(self.flows)):
            if f_idx in getattr(self, "connected_flow_indices", set()):
                continue
            if self.check_player_in_flow_zone(player_rect, f_idx):
                return True

        for o_idx in range(len(self.orders)):
            if self.check_player_in_order_zone(player_rect, o_idx):
                return True

        return False

    # --- Множественные хитбоксы триггера Sequence ---
    def get_attack_zone_shapes_for_sequence(self, z_idx):
        if z_idx >= len(self.sequences):
            return []
        seq = self.sequences[z_idx]
        shapes_list = seq.get("trigger_shapes", [])
        if not shapes_list and "trigger_zone" in seq:
            tz = seq["trigger_zone"]
            shapes_list = [{
                "shape": tz.get("shape", {"type": "rectangle", "w": 90, "h": 50}),
                "offset_x": tz.get("offset_x", 10),
                "offset_y": tz.get("offset_y", 0),
                "angle": tz.get("angle", 0),
                "type": tz.get("type", "following")
            }]

        resolved_shapes = []
        for s in shapes_list:
            shape = s["shape"]
            ox, oy = s.get("offset_x", 0), s.get("offset_y", 0)
            angle = s.get("angle", 0)
            det_type = s.get("type", "following")
            stype = shape.get("type", "rectangle")

            if stype == "rectangle":
                w, h = shape["w"], shape["h"]
                if det_type == "following" and self.direction == -1:
                    abs_x = self.rect.left - ox - w
                    effective_angle = -angle
                elif det_type == "following":
                    abs_x = self.rect.right + ox
                    effective_angle = angle
                else:
                    abs_x = self.rect.x + ox
                    effective_angle = angle
                abs_y = self.rect.y + oy
                resolved_shapes.append(("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle)))
            elif stype == "circle":
                r = shape["r"]
                if det_type == "following" and self.direction == -1:
                    cx = self.rect.left - ox - r
                elif det_type == "following":
                    cx = self.rect.right + ox + r
                else:
                    cx = self.rect.x + ox + r
                cy = self.rect.y + oy + r
                resolved_shapes.append(("circle", (cx, cy, r)))
        return resolved_shapes

    def check_player_in_zone(self, player_rect, z_idx):
        for stype, val in self.get_attack_zone_shapes_for_sequence(z_idx):
            if self._check_single_shape_collision(player_rect, stype, val):
                return True
        return False

    def check_zone_vertical_overlap(self, player_rect, z_idx):
        for stype, val in self.get_attack_zone_shapes_for_sequence(z_idx):
            if stype == "rectangle":
                rect, angle = val
                if angle == 0:
                    if (rect.bottom > player_rect.top) and (rect.top < player_rect.bottom):
                        return True
                else:
                    y_coords = self._get_rotated_rect_y_coords(rect, angle)
                    if max(y_coords) > player_rect.top and min(y_coords) < player_rect.bottom:
                        return True
            elif stype == "circle":
                cx, cy, r = val
                if (cy + r > player_rect.top) and (cy - r < player_rect.bottom):
                    return True
        return False

    # --- Множественные хитбоксы триггера Flow ---
    def get_attack_zone_shapes_for_flow(self, f_idx):
        if f_idx >= len(self.flows):
            return []
        flow = self.flows[f_idx]
        shapes_list = flow.get("trigger_shapes", [])
        if not shapes_list and "trigger_zone" in flow:
            tz = flow["trigger_zone"]
            shapes_list = [{
                "shape": tz.get("shape", {"type": "rectangle", "w": 250, "h": 80}),
                "offset_x": tz.get("offset_x", 0),
                "offset_y": tz.get("offset_y", 0),
                "angle": tz.get("angle", 0),
                "type": tz.get("type", "following")
            }]

        resolved_shapes = []
        for s in shapes_list:
            shape = s["shape"]
            ox, oy = s.get("offset_x", 0), s.get("offset_y", 0)
            angle = s.get("angle", 0)
            det_type = s.get("type", "following")
            stype = shape.get("type", "rectangle")

            if stype == "rectangle":
                w, h = shape["w"], shape["h"]
                if det_type == "following" and self.direction == -1:
                    abs_x = self.rect.left - ox - w
                    effective_angle = -angle
                elif det_type == "following":
                    abs_x = self.rect.right + ox
                    effective_angle = angle
                else:
                    abs_x = self.rect.x + ox
                    effective_angle = angle
                abs_y = self.rect.y + oy
                resolved_shapes.append(("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle)))
            elif stype == "circle":
                r = shape["r"]
                if det_type == "following" and self.direction == -1:
                    cx = self.rect.left - ox - r
                elif det_type == "following":
                    cx = self.rect.right + ox + r
                else:
                    cx = self.rect.x + ox + r
                cy = self.rect.y + oy + r
                resolved_shapes.append(("circle", (cx, cy, r)))
        return resolved_shapes

    def check_player_in_flow_zone(self, player_rect, f_idx):
        for stype, val in self.get_attack_zone_shapes_for_flow(f_idx):
            if self._check_single_shape_collision(player_rect, stype, val):
                return True
        return False

    def check_flow_zone_vertical_overlap(self, player_rect, f_idx):
        for stype, val in self.get_attack_zone_shapes_for_flow(f_idx):
            if stype == "rectangle":
                rect, angle = val
                if angle == 0:
                    if (rect.bottom > player_rect.top) and (rect.top < player_rect.bottom):
                        return True
                else:
                    y_coords = self._get_rotated_rect_y_coords(rect, angle)
                    if max(y_coords) > player_rect.top and min(y_coords) < player_rect.bottom:
                        return True
            elif stype == "circle":
                cx, cy, r = val
                if (cy + r > player_rect.top) and (cy - r < player_rect.bottom):
                    return True
        return False

    # --- Множественные хитбоксы триггера Order ---
    def get_attack_zone_shapes_for_order(self, o_idx):
        if o_idx >= len(self.orders):
            return []
        order = self.orders[o_idx]
        shapes_list = order.get("trigger_shapes", [])
        if not shapes_list and "trigger_zone" in order:
            tz = order["trigger_zone"]
            shapes_list = [{
                "shape": tz.get("shape", {"type": "rectangle", "w": 150, "h": 60}),
                "offset_x": tz.get("offset_x", 0),
                "offset_y": tz.get("offset_y", 0),
                "angle": tz.get("angle", 0),
                "type": tz.get("type", "following")
            }]

        resolved_shapes = []
        for s in shapes_list:
            shape = s["shape"]
            ox, oy = s.get("offset_x", 0), s.get("offset_y", 0)
            angle = s.get("angle", 0)
            det_type = s.get("type", "following")
            stype = shape.get("type", "rectangle")

            if stype == "rectangle":
                w, h = shape["w"], shape["h"]
                if det_type == "following" and self.direction == -1:
                    abs_x = self.rect.left - ox - w
                    effective_angle = -angle
                elif det_type == "following":
                    abs_x = self.rect.right + ox
                    effective_angle = angle
                else:
                    abs_x = self.rect.x + ox
                    effective_angle = angle
                abs_y = self.rect.y + oy
                resolved_shapes.append(("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle)))
            elif stype == "circle":
                r = shape["r"]
                if det_type == "following" and self.direction == -1:
                    cx = self.rect.left - ox - r
                elif det_type == "following":
                    cx = self.rect.right + ox + r
                else:
                    cx = self.rect.x + ox + r
                cy = self.rect.y + oy + r
                resolved_shapes.append(("circle", (cx, cy, r)))
        return resolved_shapes

    def check_player_in_order_zone(self, player_rect, o_idx):
        for stype, val in self.get_attack_zone_shapes_for_order(o_idx):
            if self._check_single_shape_collision(player_rect, stype, val):
                return True
        return False

    # --- Хитбоксы атак ---
    def get_attack_shapes_by_index(self, a_idx):
        if a_idx >= len(self.attacks):
            return []
        att = self.attacks[a_idx]
        shapes_data = []
        shapes = att.get("shapes", [])
        for s_data in shapes:
            shape = s_data.get("shape", {"type": "rectangle", "w": 50, "h": 40})
            stype = shape.get("type", "rectangle")
            ox = s_data.get("offset_x", 10)
            oy = s_data.get("offset_y", 0)
            angle = s_data.get("angle", 0)

            if stype == "circle":
                r = shape.get("r", 25)
                if self.direction == -1:
                    cx = self.rect.left - ox - r
                else:
                    cx = self.rect.right + ox + r
                cy = self.rect.y + oy + r
                shapes_data.append(("circle", (cx, cy, r)))
            else:
                w = shape.get("w", 50)
                h = shape.get("h", 40)
                if self.direction == -1:
                    abs_x = self.rect.left - ox - w
                    effective_angle = -angle
                else:
                    abs_x = self.rect.right + ox
                    effective_angle = angle
                abs_y = self.rect.y + oy
                shapes_data.append(("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle)))
        return shapes_data

    def check_specific_hitbox_collision(self, player, s_data):
        shape = s_data.get("shape", {"type": "rectangle", "w": 50, "h": 40})
        stype = shape.get("type", "rectangle")
        ox = s_data.get("offset_x", 10)
        oy = s_data.get("offset_y", 0)
        angle = s_data.get("angle", 0)

        if stype == "circle":
            r = shape.get("r", 25)
            if self.direction == -1:
                cx = self.rect.left - ox - r
            else:
                cx = self.rect.right + ox + r
            cy = self.rect.y + oy + r
            return self._check_single_shape_collision(player.rect, "circle", (cx, cy, r))
        else:
            w = shape.get("w", 50)
            h = shape.get("h", 40)
            if self.direction == -1:
                abs_x = self.rect.left - ox - w
                effective_angle = -angle
            else:
                abs_x = self.rect.right + ox
                effective_angle = angle
            abs_y = self.rect.y + oy
            return self._check_single_shape_collision(player.rect, "rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle))

    # --- Универсальный физический расчет пересечений ---
    def _check_single_shape_collision(self, player_rect, stype, val):
        if stype == "rectangle":
            rect, angle = val
            if angle == 0:
                return rect.colliderect(player_rect)
            else:
                player_poly = [
                    (player_rect.left, player_rect.top),
                    (player_rect.right, player_rect.top),
                    (player_rect.right, player_rect.bottom),
                    (player_rect.left, player_rect.bottom)
                ]
                w, h = rect.width, rect.height
                cx, cy = rect.centerx, rect.centery
                rad = math.radians(-angle)
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                dx, dy = w / 2, h / 2
                rect_poly = []
                for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                    rx = px * cos_a - py * sin_a + cx
                    ry = px * sin_a + py * cos_a + cy
                    rect_poly.append((rx, ry))
                return collides_polygon_polygon(player_poly, rect_poly)
        elif stype == "circle":
            cx, cy, r = val
            closest_x = max(player_rect.left, min(cx, player_rect.right))
            closest_y = max(player_rect.top, min(cy, player_rect.bottom))
            distance_sq = (cx - closest_x)**2 + (cy - closest_y)**2
            return distance_sq <= r**2
        return False

    def _get_rotated_rect_y_coords(self, rect, angle):
        w, h = rect.width, rect.height
        cx, cy = rect.centerx, rect.centery
        rad = math.radians(-angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        dx, dy = w / 2, h / 2
        y_coords = []
        for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
            ry = px * sin_a + py * cos_a + cy
            y_coords.append(ry)
        return y_coords