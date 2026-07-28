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
        # Если значение является неразрешенным плейсхолдером шаблона
        if val.startswith("$"):
            return default
        try:
            # Безопасно обрабатываем строки вида "150" или "150.0"
            return int(float(val))
        except (ValueError, TypeError):
            return default
    return default


class EnemyCollisionMixin:
    def get_detection_shape(self):
        det = self.config.get("detection")
        if not det:
            return None
        shape = det["shape"]
        ox, oy = det["offset_x"], det["offset_y"]
        angle = det.get("angle", 0)
        det_type = det.get("type", "following")
        
        if shape["type"] == "rectangle":
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
            return ("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle))
            
        elif shape["type"] == "circle":
            r = shape["r"]
            if det_type == "following" and self.direction == -1:
                cx = self.rect.left - ox - r
            elif det_type == "following":
                cx = self.rect.right + ox + r
            else:
                cx = self.rect.x + ox + r
            cy = self.rect.y + oy + r
            return ("circle", (cx, cy, r))
        return None

    def check_player_detected(self, player_rect):
        if self.rect.colliderect(player_rect):
            return True
            
        for idx in range(len(self.trigger_zones)):
            # Байпас триггеров связанных последовательностей
            if idx in getattr(self, "connected_seq_indices", set()):
                continue
                
            is_in_flow = False
            for flow in self.flows:
                for step in flow.get("steps", []):
                    if step.get("is_random", False):
                        if idx in step.get("seq_pool", []):
                            is_in_flow = True
                    else:
                        if idx == step.get("seq_idx", 0):
                            is_in_flow = True
            if is_in_flow:
                continue
            if self.check_player_in_zone(player_rect, idx):
                return True

        for f_idx in range(len(self.flows)):
            # Байпас триггеров связанных потоков
            if f_idx in getattr(self, "connected_flow_indices", set()):
                continue
            if self.check_player_in_flow_zone(player_rect, f_idx):
                return True

        # Коллизия с фиолетовыми триггерами порядка (Order)
        for o_idx in range(len(self.orders)):
            if self.check_player_in_order_zone(player_rect, o_idx):
                return True

        shape_data = self.get_detection_shape()
        if not shape_data:
            return False
        stype, val = shape_data
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

    def get_attack_zone_shape_for_attack_zone(self, z_idx):
        if z_idx >= len(self.trigger_zones):
            return None
        det = self.trigger_zones[z_idx]
        shape = det["shape"]
        ox, oy = det["offset_x"], det["offset_y"]
        det_type = det.get("type", "following")
        angle = det.get("angle", 0)
        
        if shape["type"] == "rectangle":
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
            return ("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle))
            
        elif shape["type"] == "circle":
            r = shape["r"]
            if det_type == "following" and self.direction == -1:
                cx = self.rect.left - ox - r
            elif det_type == "following":
                cx = self.rect.right + ox + r
            else:
                cx = self.rect.x + ox + r
            cy = self.rect.y + oy + r
            return ("circle", (cx, cy, r))
        return None

    def check_player_in_zone(self, player_rect, z_idx):
        shape_data = self.get_attack_zone_shape_for_attack_zone(z_idx)
        if not shape_data:
            return False
        stype, val = shape_data
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

    def check_zone_vertical_overlap(self, player_rect, z_idx):
        shape_data = self.get_attack_zone_shape_for_attack_zone(z_idx)
        if not shape_data:
            return False
        stype, val = shape_data
        if stype == "rectangle":
            rect, angle = val
            if angle == 0:
                return (rect.bottom > player_rect.top) and (rect.top < player_rect.bottom)
            else:
                w, h = rect.width, rect.height
                cx, cy = rect.centerx, rect.centery
                rad = math.radians(-angle)
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                dx, dy = w / 2, h / 2
                y_coords = []
                for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                    ry = px * sin_a + py * cos_a + cy
                    y_coords.append(ry)
                min_y = min(y_coords)
                max_y = max(y_coords)
                return (max_y > player_rect.top) and (min_y < player_rect.bottom)
        elif stype == "circle":
            cx, cy, r = val
            min_y = cy - r
            max_y = cy + r
            return (max_y > player_rect.top) and (min_y < player_rect.bottom)
        return False

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
            
            closest_x = max(player.rect.left, min(cx, player.rect.right))
            closest_y = max(player.rect.top, min(cy, player.rect.bottom))
            distance_sq = (cx - closest_x)**2 + (cy - closest_y)**2
            return distance_sq <= r**2
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
            rect = pygame.Rect(abs_x, abs_y, w, h)
            
            if effective_angle == 0:
                return rect.colliderect(player.rect)
            else:
                p_rect = player.rect
                player_poly = [
                    (p_rect.left, p_rect.top),
                    (p_rect.right, p_rect.top),
                    (p_rect.right, p_rect.bottom),
                    (p_rect.left, p_rect.bottom)
                ]
                
                cx, cy = rect.centerx, rect.centery
                rad = math.radians(-effective_angle)
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                dx, dy = w / 2, h / 2
                
                rect_poly = []
                for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                    rx = px * cos_a - py * sin_a + cx
                    ry = px * sin_a + py * cos_a + cy
                    rect_poly.append((rx, ry))
                
                return collides_polygon_polygon(player_poly, rect_poly)

    def get_attack_zone_shape_for_flow_zone(self, f_idx):
        if f_idx >= len(self.flows):
            return None
        det = self.flows[f_idx]
        shape = det.setdefault("trigger_zone", {}).setdefault("shape", { "template": "forms.rect", "w": 250, "h": 80 })
        ox, oy = det["trigger_zone"].get("offset_x", 0), det["trigger_zone"].get("offset_y", 0)
        det_type = det["trigger_zone"].get("type", "following")
        angle = det["trigger_zone"].get("angle", 0)
        
        if shape["type"] == "rectangle":
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
            return ("rectangle", (pygame.Rect(abs_x, abs_y, w, h), effective_angle))
            
        elif shape["type"] == "circle":
            r = shape["r"]
            if det_type == "following" and self.direction == -1:
                cx = self.rect.left - ox - r
            elif det_type == "following":
                cx = self.rect.right + ox + r
            else:
                cx = self.rect.x + ox + r
            cy = self.rect.y + oy + r
            return ("circle", (cx, cy, r))
        return None

    def check_player_in_flow_zone(self, player_rect, f_idx):
        shape_data = self.get_attack_zone_shape_for_flow_zone(f_idx)
        if not shape_data:
            return False
        stype, val = shape_data
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

    def check_flow_zone_vertical_overlap(self, player_rect, f_idx):
        shape_data = self.get_attack_zone_shape_for_flow_zone(f_idx)
        if not shape_data:
            return False
        stype, val = shape_data
        if stype == "rectangle":
            rect, angle = val
            if angle == 0:
                return (rect.bottom > player_rect.top) and (rect.top < player_rect.bottom)
            else:
                w, h = rect.width, rect.height
                cx, cy = rect.centerx, rect.centery
                rad = math.radians(-angle)
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                dx, dy = w / 2, h / 2
                y_coords = []
                for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                    ry = px * sin_a + py * cos_a + cy
                    y_coords.append(ry)
                min_y = min(y_coords)
                max_y = max(y_coords)
                return (max_y > player_rect.top) and (min_y < player_rect.bottom)
        elif stype == "circle":
            cx, cy, r = val
            min_y = cy - r
            max_y = cy + r
            return (max_y > player_rect.top) and (min_y < player_rect.bottom)
        return False

    def get_attack_zone_shape_for_order_zone(self, o_idx):
        if o_idx >= len(self.orders):
            return None
        det = self.orders[o_idx]
        tz = det.get("trigger_zone", {})
        shape = tz.get("shape", {})
        
        stype = shape.get("type")
        if not stype:
            template_str = str(shape.get("template", ""))
            if "circle" in template_str or "r" in shape:
                stype = "circle"
            else:
                stype = "rectangle"
                
        ox = safe_int(tz.get("offset_x"), 0)
        oy = safe_int(tz.get("offset_y"), 0)
        det_type = tz.get("type", "following")
        angle = safe_int(tz.get("angle"), 0)
        
        if stype == "rectangle":
            w = safe_int(shape.get("w"), 150)
            h = safe_int(shape.get("h"), 60)
            
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
            
            return ("rectangle", (pygame.Rect(safe_int(abs_x), safe_int(abs_y), w, h), effective_angle))
            
        elif stype == "circle":
            r = safe_int(shape.get("r"), 75)
            if det_type == "following" and self.direction == -1:
                cx = self.rect.left - ox - r
            elif det_type == "following":
                cx = self.rect.right + ox + r
            else:
                cx = self.rect.x + ox + r
            cy = self.rect.y + oy + r
            return ("circle", (safe_int(cx), safe_int(cy), r))
        return None

    def check_player_in_order_zone(self, player_rect, o_idx):
        shape_data = self.get_attack_zone_shape_for_order_zone(o_idx)
        if not shape_data:
            return False
        stype, val = shape_data
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