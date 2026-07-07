# editor/right_panel/editor_right_panel_main.py
import pygame

class RightPanelMainTabMixin:
    def draw_enemy_main_tab(self, target_enemy_raw, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        det = target_enemy_raw.setdefault("detection", {
            "template": "detections.front_view",
            "shape": { "template": "forms.rect", "w": 220, "h": 70 },
            "offset_x": 0, "offset_y": -10, "type": "following"
        })
        det_shape = det.setdefault("shape", { "template": "forms.rect", "w": 220, "h": 70 })

        lbl_title = self.font_ui.render("GENERAL PROPERTIES", True, (255, 180, 100))
        game.screen.blit(lbl_title, (1215, y_offset))
        y_offset += 25
        
        if game.editor_mode == "LEVEL_EDITOR":
            name_lbl = self.font_ui.render(f"Name: {target_enemy_raw.get('name', 'Enemy')}", True, (255, 180, 100))
            game.screen.blit(name_lbl, (1215, y_offset))
            y_offset += 20
            
            rename_inst_rect = pygame.Rect(1215, y_offset, 170, 22)
            if self.draw_button(rename_inst_rect, "RENAME INSTANCE", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                game.rename_selected_instance()
            y_offset += 30

            m_x_minus, m_x_plus = self.draw_property_row("PosX", target_enemy_raw.get("x", 0), y_offset)
            y_offset += 26
            m_y_minus, m_y_plus = self.draw_property_row("PosY", target_enemy_raw.get("y", 0), y_offset)
            y_offset += 26
            
            if mouse_clicked_this_frame:
                if m_x_minus.collidepoint(mouse_pos): target_enemy_raw["x"] -= 20 if game.snap_to_grid else 5
                if m_x_plus.collidepoint(mouse_pos):  target_enemy_raw["x"] += 20 if game.snap_to_grid else 5
                if m_y_minus.collidepoint(mouse_pos): target_enemy_raw["y"] -= 20 if game.snap_to_grid else 5
                if m_y_plus.collidepoint(mouse_pos):  target_enemy_raw["y"] += 20 if game.snap_to_grid else 5
                game.rebuild_objects()
            y_offset += 35

            delete_btn_rect = pygame.Rect(1215, y_offset, 170, 26)
            if self.draw_button(delete_btn_rect, "DELETE OBJECT", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                if game.selected_instance.raw_data in game.raw_enemies:
                    game.raw_enemies.remove(game.selected_instance.raw_data)
                game.selected_instance = None
                game.rebuild_objects()
            y_offset += 35
        else:
            name_lbl = self.font_ui.render(f"Preset: {game.selected_preset_name}", True, (255, 180, 100))
            game.screen.blit(name_lbl, (1215, y_offset))
            y_offset += 20
            
            rename_btn_rect = pygame.Rect(1215, y_offset, 170, 22)
            if self.draw_button(rename_btn_rect, "RENAME PRESET", (60, 100, 150), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                game.rename_current_preset()
            y_offset += 30

            hp_minus, hp_plus = self.draw_property_row("Base HP", target_enemy_raw.get("hp", 3), y_offset)
            y_offset += 26
            
            if "body" not in target_enemy_raw:
                target_enemy_raw["body"] = {"template": "forms.rect", "w": 30, "h": 50}
            body_w_minus, body_w_plus = self.draw_property_row("Body W", target_enemy_raw["body"].get("w", 30), y_offset)
            y_offset += 26
            body_h_minus, body_h_plus = self.draw_property_row("Body H", target_enemy_raw["body"].get("h", 50), y_offset)
            y_offset += 35

            lbl_det = self.font_ui.render("CHASE TRIGGER (VISION)", True, (255, 180, 100))
            game.screen.blit(lbl_det, (1215, y_offset))
            y_offset += 25

            # Безопасное определение типа фигуры
            vis_shape_type = det_shape.get("type")
            if not vis_shape_type:
                template_str = det_shape.get("template", "")
                if "circle" in template_str or "r" in det_shape:
                    vis_shape_type = "circle"
                else:
                    vis_shape_type = "rectangle"

            vis_type_minus, vis_type_plus = self.draw_property_row("Type", vis_shape_type, y_offset)
            y_offset += 26

            if vis_shape_type == "circle":
                vis_dim1_minus, vis_dim1_plus = self.draw_property_row("Vision R", det_shape.get("r", 110), y_offset)
                y_offset += 26
                vis_dim2_minus, vis_dim2_plus = None, None
            else:
                vis_dim1_minus, vis_dim1_plus = self.draw_property_row("Vision W", det_shape.get("w", 220), y_offset)
                y_offset += 26
                vis_dim2_minus, vis_dim2_plus = self.draw_property_row("Vision H", det_shape.get("h", 70), y_offset)
                y_offset += 26

            vis_ox_minus, vis_ox_plus = self.draw_property_row("Offset X", det.get("offset_x", 0), y_offset)
            y_offset += 26
            vis_oy_minus, vis_oy_plus = self.draw_property_row("Offset Y", det.get("offset_y", -10), y_offset)
            y_offset += 35

            if mouse_clicked_this_frame:
                if hp_minus.collidepoint(mouse_pos): target_enemy_raw["hp"] = max(1, target_enemy_raw.get("hp", 3) - 1)
                if hp_plus.collidepoint(mouse_pos):  target_enemy_raw["hp"] = target_enemy_raw.get("hp", 3) + 1
                
                if body_w_minus.collidepoint(mouse_pos): target_enemy_raw["body"]["w"] = max(15, target_enemy_raw["body"].get("w", 30) - 5)
                if body_w_plus.collidepoint(mouse_pos):  target_enemy_raw["body"]["w"] += 5
                if body_h_minus.collidepoint(mouse_pos): target_enemy_raw["body"]["h"] = max(15, target_enemy_raw["body"].get("h", 50) - 5)
                if body_h_plus.collidepoint(mouse_pos):  target_enemy_raw["body"]["h"] += 5

                if vis_type_minus.collidepoint(mouse_pos) or vis_type_plus.collidepoint(mouse_pos):
                    if vis_shape_type == "rectangle":
                        det_shape["type"] = "circle"
                        if "template" in det_shape: det_shape["template"] = "forms.circle"
                        det_shape.pop("w", None); det_shape.pop("h", None)
                        det_shape["r"] = det_shape.get("r", 110)
                    else:
                        det_shape["type"] = "rectangle"
                        if "template" in det_shape: det_shape["template"] = "forms.rect"
                        det_shape.pop("r", None)
                        det_shape["w"] = det_shape.get("w", 220); det_shape["h"] = det_shape.get("h", 70)

                if vis_shape_type == "circle":
                    if vis_dim1_minus.collidepoint(mouse_pos): det_shape["r"] = max(10, det_shape.get("r", 110) - 5)
                    if vis_dim1_plus.collidepoint(mouse_pos):  det_shape["r"] += 5
                else:
                    if vis_dim1_minus.collidepoint(mouse_pos): det_shape["w"] = max(10, det_shape.get("w", 220) - 10)
                    if vis_dim1_plus.collidepoint(mouse_pos):  det_shape["w"] += 10
                    if vis_dim2_minus and vis_dim2_minus.collidepoint(mouse_pos): det_shape["h"] = max(10, det_shape.get("h", 70) - 5)
                    if vis_dim2_plus and vis_dim2_plus.collidepoint(mouse_pos):  det_shape["h"] += 5

                if vis_ox_minus.collidepoint(mouse_pos): det["offset_x"] = det.get("offset_x", 0) - 5
                if vis_ox_plus.collidepoint(mouse_pos):  det["offset_x"] = det.get("offset_x", 0) + 5
                if vis_oy_minus.collidepoint(mouse_pos): det["offset_y"] = det.get("offset_y", -10) - 5
                if vis_oy_plus.collidepoint(mouse_pos):  det["offset_y"] = det.get("offset_y", -10) + 5

                game.rebuild_objects()

            if len(game.presets) > 1:
                delete_preset_rect = pygame.Rect(1215, y_offset, 170, 26)
                if self.draw_button(delete_preset_rect, "DELETE PRESET", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                    preset_to_delete = game.selected_preset_name
                    if preset_to_delete in game.presets:
                        game.delete_preset(preset_to_delete)
                y_offset += 35
        return y_offset