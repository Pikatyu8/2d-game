# editor/right_panel/editor_right_panel_level.py
import pygame
from entities.platform_class import Platform
from editor.editor_player_start import PlayerStart

class RightPanelLevelMixin:
    def draw_level_editor_properties(self, inst, y_offset, mouse_clicked_this_frame, mouse_pos):
        game = self.game
        is_plat = isinstance(inst, Platform)
        is_start = isinstance(inst, PlayerStart)
        
        if is_start:
            m_x_minus, m_x_plus = self.draw_property_row("Start X", inst.raw_data.get("start_x", 100), y_offset)
            y_offset += 26
            m_y_minus, m_y_plus = self.draw_property_row("Start Y", inst.raw_data.get("start_y", 300), y_offset)
            y_offset += 26
        else:
            m_x_minus, m_x_plus = self.draw_property_row("PosX", inst.raw_data.get("x", 0), y_offset)
            y_offset += 26
            m_y_minus, m_y_plus = self.draw_property_row("PosY", inst.raw_data.get("y", 0), y_offset)
            y_offset += 26
        
        if mouse_clicked_this_frame:
            if is_start:
                if m_x_minus.collidepoint(mouse_pos): inst.raw_data["start_x"] -= 20 if game.snap_to_grid else 5
                if m_x_plus.collidepoint(mouse_pos):  inst.raw_data["start_x"] += 20 if game.snap_to_grid else 5
                if m_y_minus.collidepoint(mouse_pos): inst.raw_data["start_y"] -= 20 if game.snap_to_grid else 5
                if m_y_plus.collidepoint(mouse_pos):  inst.raw_data["start_y"] += 20 if game.snap_to_grid else 5
            else:
                if m_x_minus.collidepoint(mouse_pos): inst.raw_data["x"] -= 20 if game.snap_to_grid else 5
                if m_x_plus.collidepoint(mouse_pos):  inst.raw_data["x"] += 20 if game.snap_to_grid else 5
                if m_y_minus.collidepoint(mouse_pos): inst.raw_data["y"] -= 20 if game.snap_to_grid else 5
                if m_y_plus.collidepoint(mouse_pos):  inst.raw_data["y"] += 20 if game.snap_to_grid else 5
            game.rebuild_objects()
        
        if is_plat:
            m_w_minus, m_w_plus = self.draw_property_row("Width", inst.raw_data.get("w", 100), y_offset)
            y_offset += 26
            m_h_minus, m_h_plus = self.draw_property_row("Height", inst.raw_data.get("h", 20), y_offset)
            y_offset += 35
            
            if mouse_clicked_this_frame:
                if m_w_minus.collidepoint(mouse_pos): inst.raw_data["w"] = max(20, inst.raw_data.get("w", 100) - 20)
                if m_w_plus.collidepoint(mouse_pos):  inst.raw_data["w"] += 20
                if m_h_minus.collidepoint(mouse_pos): inst.raw_data["h"] = max(10, inst.raw_data.get("h", 20) - 10)
                if m_h_plus.collidepoint(mouse_pos):  inst.raw_data["h"] += 10
                game.rebuild_objects()

            delete_btn_rect = pygame.Rect(1215, y_offset, 170, 26)
            if self.draw_button(delete_btn_rect, "DELETE PLATFORM", (180, 50, 50), (255, 255, 255), is_scrollable=True) and mouse_clicked_this_frame:
                if inst.raw_data in game.raw_platforms:
                    game.raw_platforms.remove(inst.raw_data)
                game.selected_instance = None
                game.rebuild_objects()
            y_offset += 35
        return y_offset