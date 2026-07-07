# core/game_parts/game_editor_logic.py
import pygame
import copy
from entities.platform_class import Platform
from editor.editor_player_start import PlayerStart
from config import CANVAS_OFFSET_X, CANVAS_WIDTH, SCREEN_HEIGHT

class GameEditorLogicMixin:
    def handle_editor_input(self, mouse_pos, mouse_clicked, right_clicked):
        if not (CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH):
            return

        current_zoom = self.zoom
        cx = self.camera_x + (mouse_pos[0] - CANVAS_OFFSET_X) / current_zoom
        cy = self.camera_y + mouse_pos[1] / current_zoom

        if getattr(self, "is_panning", False) and pygame.mouse.get_pressed()[0]:
            dx = (mouse_pos[0] - self.pan_start_mouse_x) / self.pan_zoom_backup
            dy = (mouse_pos[1] - self.pan_start_mouse_y) / self.pan_zoom_backup
            self.camera_x = max(0, self.pan_start_cam_x - dx)
            self.camera_y = self.pan_start_cam_y - dy
        else:
            self.is_panning = False

        if self.dragging_instance:
            new_x = cx - self.drag_offset_x
            new_y = cy - self.drag_offset_y
            if self.snap_to_grid:
                new_x = (new_x // 20) * 20
                new_y = (new_y // 20) * 20
            
            if isinstance(self.dragging_instance, PlayerStart):
                self.dragging_instance.raw_data["start_x"] = new_x
                self.dragging_instance.raw_data["start_y"] = new_y
            else:
                self.dragging_instance.raw_data["x"] = new_x
                self.dragging_instance.raw_data["y"] = new_y
            self.rebuild_objects()

        elif mouse_clicked:
            clicked_obj = None
            if self.player_start_obj and self.player_start_obj.rect.collidepoint(cx, cy):
                clicked_obj = self.player_start_obj
            else:
                for enemy in self.enemies:
                    if enemy.rect.collidepoint(cx, cy):
                        clicked_obj = enemy
                        break
                if not clicked_obj:
                    for plat in self.platforms:
                        if plat.rect.collidepoint(cx, cy):
                            clicked_obj = plat
                            break
            
            if clicked_obj:
                self.selected_instance = clicked_obj
                self.dragging_instance = clicked_obj
                self.drag_offset_x = cx - clicked_obj.rect.x
                self.drag_offset_y = cy - clicked_obj.rect.y
            else:
                if self.selected_brush == "Selection":
                    self.is_panning = True
                    self.pan_start_mouse_x = mouse_pos[0]
                    self.pan_start_mouse_y = mouse_pos[1]
                    self.pan_start_cam_x = self.camera_x
                    self.pan_start_cam_y = self.camera_y
                    self.pan_zoom_backup = current_zoom
                else:
                    spawn_x = (cx // 20) * 20 if self.snap_to_grid else cx
                    spawn_y = (cy // 20) * 20 if self.snap_to_grid else cy
                    
                    if self.selected_brush == "Platform":
                        new_plat = {"x": spawn_x, "y": spawn_y, "w": 100, "h": 20, "color": [100, 150, 100]}
                        self.raw_platforms.append(new_plat)
                    else:
                        preset_data = self.presets[self.selected_brush]
                        new_enemy = copy.deepcopy(preset_data)
                        new_enemy["name"] = self.selected_brush
                        new_enemy["preset"] = self.selected_brush 
                        new_enemy["x"] = spawn_x
                        new_enemy["y"] = spawn_y
                        self.raw_enemies.append(new_enemy)
                        
                    self.rebuild_objects()
                    if self.selected_brush == "Platform":
                        self.selected_instance = self.platforms[-1]
                    else:
                        self.selected_instance = self.enemies[-1]

        elif right_clicked:
            target = None
            for enemy in self.enemies:
                if enemy.rect.collidepoint(cx, cy):
                    target = enemy
                    break
            if target:
                self.raw_enemies.remove(target.raw_data)
                if self.selected_instance == target:
                    self.selected_instance = None
                self.rebuild_objects()
            else:
                for plat in self.platforms:
                    if plat.rect.collidepoint(cx, cy):
                        target = plat
                        break
                if target:
                    self.raw_platforms.remove(target.raw_data)
                    if self.selected_instance == target:
                        self.selected_instance = None
                    self.rebuild_objects()