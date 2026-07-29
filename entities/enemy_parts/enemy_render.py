# entities/enemy_parts/enemy_render.py
import pygame
import math
import os
from config import ENEMY_BODY_COLOR, ENEMY_HEAD_COLOR, CANVAS_OFFSET_X

class EnemyRenderMixin:
    def load_attack_sprite(self):
        if not self._attack_sprite_loaded:
            self._attack_sprite_loaded = True
            os.makedirs("assets", exist_ok=True)

            sprite_path = os.path.join("assets", "attack_base.png")
            if os.path.exists(sprite_path):
                try:
                    self.attack_sprite = pygame.image.load(sprite_path).convert_alpha()
                except Exception as e:
                    print(f"Error loading assets/attack_base.png: {e}")
            else:
                try:
                    temp_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
                    pygame.draw.arc(temp_surf, (200, 240, 255, 230), (10, 10, 108, 108), 0.2, 3.0, 15)
                    pygame.draw.arc(temp_surf, (100, 180, 255, 180), (5, 5, 118, 118), 0.1, 3.1, 8)
                    pygame.image.save(temp_surf, sprite_path)
                    self.attack_sprite = temp_surf
                except Exception as e:
                    print(f"Error generating procedural attack_base: {e}")

            circle_path = os.path.join("assets", "attack_base_circle.png")
            if os.path.exists(circle_path):
                try:
                    self.attack_sprite_circle = pygame.image.load(circle_path).convert_alpha()
                except Exception as e:
                    print(f"Error loading assets/attack_base_circle.png: {e}")
            else:
                try:
                    temp_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
                    pygame.draw.circle(temp_surf, (200, 240, 255, 230), (64, 64), 58, 8)
                    pygame.draw.circle(temp_surf, (100, 180, 255, 120), (64, 64), 48, 4)
                    pygame.draw.circle(temp_surf, (150, 210, 255, 80), (64, 64), 62, 2)
                    pygame.image.save(temp_surf, circle_path)
                    self.attack_sprite_circle = temp_surf
                except Exception as e:
                    print(f"Error generating procedural attack_base_circle: {e}")

    def draw(self, surface, show_debug, player_rect, camera_x=0, camera_y=0, zoom=1.0, editing_trigger_idx=None, editing_attack_idx=None, editing_box_idx=None, inspector_tab=None, selected_move_idx=None, alpha_surf=None, game=None):
        # 1. Отрисовка всех хитбоксов тела противника (Body Shapes)
        body_shapes = self.get_body_shapes()
        for b_idx, (stype, val) in enumerate(body_shapes):
            if stype == "rectangle":
                rect, angle = val
                asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
                asy = (rect.y - camera_y) * zoom
                asw = max(1.0, rect.width * zoom)
                ash = max(1.0, rect.height * zoom)

                # Главное тело или дочерний хитбокс
                draw_color = ENEMY_BODY_COLOR if b_idx == 0 else (ENEMY_BODY_COLOR[0]-20, ENEMY_BODY_COLOR[1]-20, ENEMY_BODY_COLOR[2]-20)

                if angle == 0:
                    pygame.draw.rect(surface, draw_color, (asx, asy, asw, ash))
                else:
                    cx = asx + asw / 2
                    cy = asy + ash / 2
                    rad = math.radians(-angle)
                    cos_a, sin_a = math.cos(rad), math.sin(rad)
                    dx, dy = asw / 2, ash / 2
                    corners = []
                    for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                        rx = px * cos_a - py * sin_a + cx
                        ry = px * sin_a + py * cos_a + cy
                        corners.append((int(rx), int(ry)))
                    pygame.draw.polygon(surface, draw_color, corners)
            elif stype == "circle":
                cx, cy, r = val
                scx = CANVAS_OFFSET_X + (cx - camera_x) * zoom
                scy = (cy - camera_y) * zoom
                sr = max(1.0, r * zoom)
                pygame.draw.circle(surface, ENEMY_BODY_COLOR, (int(scx), int(scy)), int(sr))

        # Отрисовка головы врага на базовом хитбоксе
        sx = CANVAS_OFFSET_X + (self.rect.x - camera_x) * zoom
        sy = (self.rect.y - camera_y) * zoom
        sw = max(1.0, self.rect.width * zoom)
        sh = max(1.0, self.rect.height * zoom)
        draw_rect = pygame.Rect(sx, sy, sw, sh)

        head_h = max(2, int(sh * 0.25))
        head_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, head_h)
        head_center_x = draw_rect.centerx
        head_center_y = draw_rect.y + head_h // 2

        def get_telegraph_color(base_color, progress):
            if base_color is None:
                return (255, int(220 * (1.0 - progress)), 0)
            r = int((base_color[0] * 0.4) + progress * (base_color[0] * 0.6))
            g = int((base_color[1] * 0.4) + progress * (base_color[1] * 0.6))
            b = int((base_color[2] * 0.4) + progress * (base_color[2] * 0.6))
            return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        active_attacks = [act for act in getattr(self, "running_actions", []) if act["type"] == "attack"]
        if active_attacks:
            first_atk = active_attacks[0]
            self.is_winding_up = first_atk["is_winding_up"]
            self.is_swinging = first_atk["is_swinging"]
            self.active_attack_idx = first_atk["idx"]
            self.attack_timeline_timer = first_atk["timeline_timer"]
            self.attack_total_duration = first_atk["total_duration"]
            self.windup_phase = first_atk.get("windup_phase", 0.0)
            self.attack_windup_timer = first_atk.get("windup_timer", 0)
            self.attack_windup_max = first_atk.get("windup_max", 35)
            self.active_execution_color = first_atk.get("execution_color")
        else:
            self.is_winding_up = False
            self.is_swinging = False
            self.attack_timeline_timer = 0
            self.attack_total_duration = 0
            self.active_execution_color = None

        if self.is_winding_up:
            is_flash_on = (int(getattr(self, "windup_phase", 0.0)) % 2 == 0)
            if is_flash_on:
                windup_max = getattr(self, "attack_windup_max", 35)
                progress = max(0.0, min(1.0, (windup_max - self.attack_windup_timer) / windup_max))
                head_color = get_telegraph_color(self.active_execution_color, progress)
            else:
                head_color = ENEMY_HEAD_COLOR
        else:
            head_color = ENEMY_HEAD_COLOR

        pygame.draw.rect(surface, head_color, head_rect)

        eye_w = max(1.0, 4 * zoom)
        eye_x = draw_rect.right - 6 * zoom if self.direction == 1 else draw_rect.left + 2 * zoom
        pygame.draw.rect(surface, (255, 255, 255), (eye_x, draw_rect.y + 6 * zoom, eye_w, eye_w))

        if self.hp > 0:
            hp_w = (sw / 5) * self.hp
            hp_draw_w = min(sw, hp_w)
            pygame.draw.rect(surface, (0, 255, 0), (draw_rect.x, draw_rect.y - 10 * zoom, hp_draw_w, max(1, int(4 * zoom))))

        font_name_size = max(8, int(12 * zoom))
        font_name = game.get_cached_font(font_name_size) if game else pygame.font.SysFont(None, font_name_size)
        name_lbl = font_name.render(self.name, True, (220, 220, 220))
        surface.blit(name_lbl, (draw_rect.x, draw_rect.y - 22 * zoom))

        if self.parry_accumulated_damage > 0:
            font_size = max(8, int(14 * zoom))
            font_parry = game.get_cached_font(font_size, bold=True) if game else pygame.font.SysFont(None, font_size, bold=True)
            parry_lbl = font_parry.render(f"+{self.parry_accumulated_damage} PARRY DMG", True, (0, 255, 255))
            surface.blit(parry_lbl, (draw_rect.x, draw_rect.y - 34 * zoom))

        if self.is_winding_up:
            windup_max = getattr(self, "attack_windup_max", 35)
            progress = max(0.0, min(1.0, (windup_max - self.attack_windup_timer) / windup_max))
            warn_color = get_telegraph_color(self.active_execution_color, progress)
            outer_r = int((22 * (1.0 - progress) + 8) * zoom)
            pygame.draw.circle(surface, warn_color, (int(head_center_x), int(head_center_y)), outer_r, max(1, int(2 * zoom)))

            if int(getattr(self, "windup_phase", 0.0)) % 2 == 0:
                font_warning = game.get_cached_font(20, bold=True) if game else pygame.font.SysFont(None, 20, bold=True)
                warn_lbl = font_warning.render("!", True, warn_color)
                lbl_x = head_center_x - warn_lbl.get_width() // 2
                surface.blit(warn_lbl, (lbl_x, draw_rect.y - 18 * zoom))

        elif self.is_swinging:
            curr_att = self.attacks[self.active_attack_idx]
            shapes = curr_att["shapes"]

            upcoming_shape = None
            min_time_to_trigger = 999

            for s_idx, s_data in enumerate(shapes):
                delay = s_data.get("delay", 0)
                time_to_trigger = delay - self.attack_timeline_timer
                if 0 < time_to_trigger <= 15:
                    if time_to_trigger < min_time_to_trigger:
                        min_time_to_trigger = time_to_trigger
                        upcoming_shape = s_data

            if upcoming_shape is not None:
                progress = (15 - min_time_to_trigger) / 15.0
                warn_color = get_telegraph_color(self.active_execution_color, progress)
                outer_r = int((22 * (1.0 - progress) + 8) * zoom)
                pygame.draw.circle(surface, warn_color, (int(head_center_x), int(head_center_y)), outer_r, max(1, int(2 * zoom)))

                blink_phase = self.attack_timeline_timer * 0.25
                if int(blink_phase) % 2 == 0:
                    font_warning = game.get_cached_font(20, bold=True) if game else pygame.font.SysFont(None, 20, bold=True)
                    warn_lbl = font_warning.render("!", True, warn_color)
                    lbl_x = head_center_x - warn_lbl.get_width() // 2
                    surface.blit(warn_lbl, (lbl_x, draw_rect.y - 18 * zoom))

            for s_idx, s_data in enumerate(shapes):
                delay = s_data.get("delay", 0)
                duration = s_data.get("duration", 10)

                if delay <= self.attack_timeline_timer <= (delay + duration):
                    vis_box = s_data.get("visual_box")
                    if vis_box:
                        v_type = vis_box.get("type", "rectangle")
                        v_ox = vis_box.get("offset_x", 0)
                        v_oy = vis_box.get("offset_y", 0)
                        if v_type == "circle":
                            v_r = vis_box.get("r", 25)
                            if self.direction == -1:
                                v_cx = self.rect.left - v_ox - v_r
                            else:
                                v_cx = self.rect.right + v_ox + v_r
                            v_cy = self.rect.y + v_oy + v_r

                            asx = CANVAS_OFFSET_X + (v_cx - v_r - camera_x) * zoom
                            asy = (v_cy - v_r - camera_y) * zoom
                            asw = v_r * 2 * zoom
                            ash = v_r * 2 * zoom
                            is_circle_visual = True
                            angle_origin_cx = v_cx
                            angle_origin_cy = v_cy
                        else:
                            v_w = vis_box.get("w", 50)
                            v_h = vis_box.get("h", 40)
                            if self.direction == -1:
                                v_abs_x = self.rect.left - v_ox - v_w
                            else:
                                v_abs_x = self.rect.right + v_ox
                            v_abs_y = self.rect.y + v_oy

                            asx = CANVAS_OFFSET_X + (v_abs_x - camera_x) * zoom
                            asy = (v_abs_y - camera_y) * zoom
                            asw = v_w * zoom
                            ash = v_h * zoom
                            is_circle_visual = False
                            angle_origin_cx = v_abs_x + v_w / 2
                            angle_origin_cy = v_abs_y + v_h / 2
                    else:
                        shape = s_data.get("shape", {"type": "rectangle", "w": 50, "h": 40})
                        stype = shape.get("type", "rectangle")
                        ox = s_data.get("offset_x", 10)
                        oy = s_data.get("offset_y", 0)
                        if stype == "rectangle":
                            w, h = shape.get("w", 50), shape.get("h", 40)
                            if self.direction == -1:
                                v_abs_x = self.rect.left - ox - w
                            else:
                                v_abs_x = self.rect.right + ox
                            v_abs_y = self.rect.y + oy

                            asx = CANVAS_OFFSET_X + (v_abs_x - camera_x) * zoom
                            asy = (v_abs_y - camera_y) * zoom
                            asw = w * zoom
                            ash = h * zoom
                            is_circle_visual = False
                            angle_origin_cx = v_abs_x + w / 2
                            angle_origin_cy = v_abs_y + h / 2
                        else:
                            r = shape.get("r", 25)
                            if self.direction == -1:
                                v_cx = self.rect.left - ox - r
                            else:
                                v_cx = self.rect.right + ox + r
                            v_cy = self.rect.y + oy + r

                            asx = CANVAS_OFFSET_X + (v_cx - r - camera_x) * zoom
                            asy = (v_cy - r - camera_y) * zoom
                            asw = r * 2 * zoom
                            ash = r * 2 * zoom
                            is_circle_visual = True
                            angle_origin_cx = v_cx
                            angle_origin_cy = v_cy

                    sprite_dir = s_data.get("sprite_dir", "forward")
                    if sprite_dir == "to_player":
                        dx = player_rect.centerx - angle_origin_cx
                        dy = player_rect.centery - angle_origin_cy
                        effective_angle = math.degrees(math.atan2(-dy, dx))
                        do_flip = False
                    elif sprite_dir == "up":
                        effective_angle = 90
                        do_flip = False
                    elif sprite_dir == "down":
                        effective_angle = -90
                        do_flip = False
                    else:
                        angle = s_data.get("angle", 0)
                        effective_angle = -angle if self.direction == -1 else angle
                        do_flip = (self.direction == -1)

                    target_sprite = self.attack_sprite_circle if is_circle_visual else self.attack_sprite

                    if target_sprite is not None:
                        scaled_img = pygame.transform.scale(target_sprite, (max(1, int(asw)), max(1, int(ash))))
                        if do_flip:
                            scaled_img = pygame.transform.flip(scaled_img, True, False)

                        rot_img = pygame.transform.rotate(scaled_img, effective_angle)
                        img_rect = rot_img.get_rect()
                        img_rect.center = (int(asx + asw / 2), int(asy + ash / 2))
                        surface.blit(rot_img, img_rect.topleft)
                    else:
                        if not is_circle_visual:
                            cx = asx + asw / 2
                            cy = asy + ash / 2
                            rad = math.radians(-effective_angle)
                            cos_a, sin_a = math.cos(rad), math.sin(rad)
                            dx, dy = asw / 2, ash / 2
                            corners = []
                            for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                                rx = px * cos_a - py * sin_a + cx
                                ry = px * sin_a + py * cos_a + cy
                                corners.append((int(rx), int(ry)))
                            pygame.draw.polygon(surface, (255, 120, 120), corners)
                        else:
                            pygame.draw.circle(surface, (255, 120, 120), (int(asx + asw/2), int(asy + ash/2)), int(asw/2))

        # Отрисовка телепортационных кривых и зон удержания в дебаг-режиме
        if show_debug:
            local_surf = alpha_surf if alpha_surf is not None else pygame.Surface(surface.get_size(), pygame.SRCALPHA)

            line_y = draw_rect.bottom
            pygame.draw.line(surface, (100, 255, 100), (CANVAS_OFFSET_X + (self.min_x - camera_x) * zoom, line_y), (CANVAS_OFFSET_X + (self.max_x - camera_x) * zoom, line_y), max(1, int(2 * zoom)))
            pygame.draw.circle(surface, (100, 255, 100), (int(CANVAS_OFFSET_X + (self.min_x - camera_x) * zoom), int(line_y)), max(1, int(4 * zoom)))
            pygame.draw.circle(surface, (100, 255, 100), (int(CANVAS_OFFSET_X + (self.max_x - camera_x) * zoom), int(line_y)), max(1, int(4 * zoom)))

            # Отрисовка зон детекции/зрения (Detection Shapes)
            det_shapes = self.get_detection_shapes()
            is_alert = self.check_player_detected(player_rect)
            color = (255, 100, 100) if is_alert else (255, 255, 100)
            for stype, val in det_shapes:
                if stype == "rectangle":
                    rect, angle = val
                    asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
                    asy = (rect.y - camera_y) * zoom
                    asw = rect.width * zoom
                    ash = rect.height * zoom
                    if angle == 0:
                        pygame.draw.rect(surface, color, (asx, asy, asw, ash), 1)
                    else:
                        cx = asx + asw / 2
                        cy = asy + ash / 2
                        rad = math.radians(-angle)
                        cos_a, sin_a = math.cos(rad), math.sin(rad)
                        dx, dy = asw / 2, ash / 2
                        corners = []
                        for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                            rx = px * cos_a - py * sin_a + cx
                            ry = px * sin_a + py * cos_a + cy
                            corners.append((int(rx), int(ry)))
                        pygame.draw.polygon(surface, color, corners, 1)
                elif stype == "circle":
                    cx, cy, r = val
                    scx = CANVAS_OFFSET_X + (cx - camera_x) * zoom
                    scy = (cy - camera_y) * zoom
                    sr = r * zoom
                    pygame.draw.circle(surface, color, (int(scx), int(scy)), int(sr), 1)

            # Отрисовка зон остановки (Root -> Stopping Shapes)
            stop_shapes = self.get_stop_shapes()
            is_stopped = self.check_player_in_stop_zone(player_rect)
            stop_color = (0, 255, 100) if is_stopped else (0, 200, 80)
            for stype, val in stop_shapes:
                if stype == "rectangle":
                    rect, angle = val
                    asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
                    asy = (rect.y - camera_y) * zoom
                    asw = rect.width * zoom
                    ash = rect.height * zoom
                    if angle == 0:
                        pygame.draw.rect(surface, stop_color, (asx, asy, asw, ash), 1)
                    else:
                        cx = asx + asw / 2
                        cy = asy + ash / 2
                        rad = math.radians(-angle)
                        cos_a, sin_a = math.cos(rad), math.sin(rad)
                        dx, dy = asw / 2, ash / 2
                        corners = []
                        for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                            rx = px * cos_a - py * sin_a + cx
                            ry = px * sin_a + py * cos_a + cy
                            corners.append((int(rx), int(ry)))
                        pygame.draw.polygon(surface, stop_color, corners, 1)
                elif stype == "circle":
                    cx, cy, r = val
                    scx = CANVAS_OFFSET_X + (cx - camera_x) * zoom
                    scy = (cy - camera_y) * zoom
                    sr = r * zoom
                    pygame.draw.circle(surface, stop_color, (int(scx), int(scy)), int(sr), 1)

            # Отрисовка триггеров Sequences
            for z_idx in range(len(self.sequences)):
                if z_idx in getattr(self, "connected_seq_indices", set()):
                    continue

                is_active_trigger_edit = (inspector_tab == "K-FRAMES" and editing_trigger_idx == z_idx)

                atk_zone_data = self.get_attack_zone_shapes_for_sequence(z_idx)
                for stype, val in atk_zone_data:
                    is_alert = self.check_player_in_zone(player_rect, z_idx)
                    base_color = (255, 60, 0) if is_alert else (255, 150, 0)

                    if not is_active_trigger_edit:
                        draw_color = (*base_color, 64)
                        target_draw_surface = local_surf
                    else:
                        draw_color = base_color
                        target_draw_surface = surface

                    draw_x, draw_y = 0, 0
                    if stype == "rectangle":
                        rect, angle = val
                        asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
                        asy = (rect.y - camera_y) * zoom
                        asw = rect.width * zoom
                        ash = rect.height * zoom
                        if angle == 0:
                            pygame.draw.rect(target_draw_surface, draw_color, (asx, asy, asw, ash), 1)
                            draw_x, draw_y = asx, asy
                        else:
                            cx = asx + asw / 2
                            cy = asy + ash / 2
                            rad = math.radians(-angle)
                            cos_a, sin_a = math.cos(rad), math.sin(rad)
                            dx, dy = asw / 2, ash / 2
                            corners = []
                            for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                                rx = px * cos_a - py * sin_a + cx
                                ry = px * sin_a + py * cos_a + cy
                                corners.append((int(rx), int(ry)))
                            pygame.draw.polygon(target_draw_surface, draw_color, corners, 1)
                            draw_x, draw_y = int(cx - asw / 2), int(cy - ash / 2)
                    elif stype == "circle":
                        cx, cy, r = val
                        scx = CANVAS_OFFSET_X + (cx - camera_x) * zoom
                        scy = (cy - camera_y) * zoom
                        sr = r * zoom
                        pygame.draw.circle(target_draw_surface, draw_color, (int(scx), int(scy)), int(sr), 1)
                        draw_x, draw_y = int(scx - sr), int(scy - sr)

            # Отрисовка триггеров Flows
            for f_idx, flow in enumerate(self.flows):
                if f_idx in getattr(self, "connected_flow_indices", set()):
                    continue

                flow_zone_data = self.get_attack_zone_shapes_for_flow(f_idx)
                for stype, val in flow_zone_data:
                    is_alert = self.check_player_in_flow_zone(player_rect, f_idx)
                    base_color = (0, 240, 255) if is_alert else (0, 150, 200)

                    is_active_flow_edit = (inspector_tab == "DETAILED_FLOW" and game is not None and game.selected_flow_idx == f_idx)

                    if not is_active_flow_edit:
                        draw_color = (*base_color, 64)
                        target_draw_surface = local_surf
                    else:
                        draw_color = base_color
                        target_draw_surface = surface

                    draw_x, draw_y = 0, 0
                    if stype == "rectangle":
                        rect, angle = val
                        asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
                        asy = (rect.y - camera_y) * zoom
                        asw = rect.width * zoom
                        ash = rect.height * zoom
                        if angle == 0:
                            pygame.draw.rect(target_draw_surface, draw_color, (asx, asy, asw, ash), 1)
                            draw_x, draw_y = asx, asy
                        else:
                            cx = asx + asw / 2
                            cy = asy + ash / 2
                            rad = math.radians(-angle)
                            cos_a, sin_a = math.cos(rad), math.sin(rad)
                            dx, dy = asw / 2, ash / 2
                            corners = []
                            for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                                rx = px * cos_a - py * sin_a + cx
                                ry = px * sin_a + py * cos_a + cy
                                corners.append((int(rx), int(ry)))
                            pygame.draw.polygon(target_draw_surface, draw_color, corners, 1)
                            draw_x, draw_y = int(cx - asw / 2), int(cy - ash / 2)
                    elif stype == "circle":
                        cx, cy, r = val
                        scx = CANVAS_OFFSET_X + (cx - camera_x) * zoom
                        scy = (cy - camera_y) * zoom
                        sr = r * zoom
                        pygame.draw.circle(target_draw_surface, draw_color, (int(scx), int(scy)), int(sr), 1)
                        draw_x, draw_y = int(scx - sr), int(scy - sr)

            # Отрисовка триггеров Orders
            editing_order_idx = game.selected_order_idx if game else None
            for o_idx, order in enumerate(getattr(self, "orders", [])):
                order_zone_data = self.get_attack_zone_shapes_for_order(o_idx)
                for stype, val in order_zone_data:
                    is_alert = self.check_player_in_order_zone(player_rect, o_idx)
                    base_color = (180, 50, 255) if is_alert else (120, 30, 200)

                    is_active_order_edit = (inspector_tab == "DETAILED_ORDER" and editing_order_idx == o_idx)

                    if not is_active_order_edit:
                        draw_color = (*base_color, 64)
                        target_draw_surface = local_surf
                    else:
                        draw_color = base_color
                        target_draw_surface = surface

                    draw_x, draw_y = 0, 0
                    if stype == "rectangle":
                        rect, angle = val
                        asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
                        asy = (rect.y - camera_y) * zoom
                        asw = rect.width * zoom
                        ash = rect.height * zoom
                        if angle == 0:
                            pygame.draw.rect(target_draw_surface, draw_color, (asx, asy, asw, ash), 1)
                            draw_x, draw_y = asx, asy
                        else:
                            cx = asx + asw / 2
                            cy = asy + ash / 2
                            rad = math.radians(-angle)
                            cos_a, sin_a = math.cos(rad), math.sin(rad)
                            dx, dy = asw / 2, ash / 2
                            corners = []
                            for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                                rx = px * cos_a - py * sin_a + cx
                                ry = px * sin_a + py * cos_a + cy
                                corners.append((int(rx), int(ry)))
                            pygame.draw.polygon(target_draw_surface, draw_color, corners, 1)
                            draw_x, draw_y = int(cx - asw / 2), int(cy - ash / 2)
                    elif stype == "circle":
                        cx, cy, r = val
                        scx = CANVAS_OFFSET_X + (cx - camera_x) * zoom
                        scy = (cy - camera_y) * zoom
                        sr = r * zoom
                        pygame.draw.circle(target_draw_surface, draw_color, (int(scx), int(scy)), int(sr), 1)
                        draw_x, draw_y = int(scx - sr), int(scy - sr)

            # Отрисовка хитбоксов атак
            for a_idx, att in enumerate(self.attacks):
                shapes_data = self.get_attack_shapes_by_index(a_idx)
                is_active_edit = (self.is_swinging and self.active_attack_idx == a_idx) or (editing_attack_idx is not None and a_idx == editing_attack_idx)

                for s_idx, (s_type, val) in enumerate(shapes_data):
                    is_selected_box = is_active_edit and (editing_box_idx is not None and s_idx == editing_box_idx)

                    if is_selected_box:
                        draw_color = (0, 240, 255)
                        thickness = 2
                        target_draw_surface = surface
                    elif not is_active_edit:
                        draw_color = (255, 50, 50, 64)
                        thickness = 1
                        target_draw_surface = local_surf
                    else:
                        draw_color = (255, 100, 100, 180)
                        thickness = 1
                        target_draw_surface = local_surf

                    if s_type == "rectangle":
                        rect, angle = val
                        asx = CANVAS_OFFSET_X + (rect.x - camera_x) * zoom
                        asy = (rect.y - camera_y) * zoom
                        asw = rect.width * zoom
                        ash = rect.height * zoom
                        if angle == 0:
                            pygame.draw.rect(target_draw_surface, draw_color, (asx, asy, asw, ash), thickness)
                            draw_x, draw_y = asx, asy
                        else:
                            cx = asx + asw / 2
                            cy = asy + ash / 2
                            rad = math.radians(-angle)
                            cos_a, sin_a = math.cos(rad), math.sin(rad)
                            dx, dy = asw / 2, ash / 2
                            corners = []
                            for px, py in [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]:
                                rx = px * cos_a - py * sin_a + cx
                                ry = px * sin_a + py * cos_a + cy
                                corners.append((int(rx), int(ry)))
                            pygame.draw.polygon(target_draw_surface, draw_color, corners, thickness)
                            draw_x, draw_y = int(cx - asw / 2), int(cy - ash / 2)
                    elif s_type == "circle":
                        cx, cy, r = val
                        scx = CANVAS_OFFSET_X + (cx - camera_x) * zoom
                        scy = (cy - camera_y) * zoom
                        sr = r * zoom
                        pygame.draw.circle(target_draw_surface, draw_color, (int(scx), int(scy)), int(sr), thickness)
                        draw_x, draw_y = int(scx - sr), int(scy - sr)

                    if is_active_edit:
                        font_size = max(8, int(12 * zoom))
                        font_att = game.get_cached_font(font_size) if game else pygame.font.SysFont(None, font_size)
                        delay = att["shapes"][s_idx].get("delay", 0)
                        dur = att["shapes"][s_idx].get("duration", 10)

                        if is_selected_box:
                            label_color = (0, 240, 255)
                            att_lbl = font_att.render(f"ACTIVE BOX #{s_idx+1} [Del:{delay} Dur:{dur}]", True, label_color)
                        else:
                            label_color = (255, 180, 180)
                            att_lbl = font_att.render(f"Box #{s_idx+1} [Del:{delay}]", True, label_color)
                        surface.blit(att_lbl, (draw_x + 3 * zoom, draw_y + 3 * zoom))

            if alpha_surf is None:
                surface.blit(local_surf, (0, 0))