# core/game.py
import pygame
import os
import copy
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CANVAS_OFFSET_X, CANVAS_WIDTH, ensure_level_file
)
from core.game_parts.game_io import GameIOMixin
from core.game_parts.game_editor_logic import GameEditorLogicMixin
from entities.platform_class import Platform
from editor.editor_ui import EditorUI, PlayerStart

class Game(GameIOMixin, GameEditorLogicMixin):
    def __init__(self):
        pygame.init()
        
        # Безопасная инициализация звукового микшера
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        except Exception as e:
            print(f"Mixer init error: {e}")
            
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
        ensure_level_file()
        self.platforms = []
        self.enemies = []
        self.projectiles = []  
        self.player = None
        self.gravity = 0.5
        self.flash_timer = 0
        self.show_debug = True
        
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0  
        
        self.left_panel_scroll = 0
        self.left_panel_max_scroll = 400
        self.right_panel_scroll = 0
        self.right_panel_max_scroll = 400
        
        self.editor_mode = "GAMEPLAY"   
        self.snap_to_grid = True        
        self.selected_brush = "Selection"  
        self.selected_instance = None   
        self.dragging_instance = None   
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
        self.available_levels = []
        self.current_level_name = "level_1.json"  
        
        self.inspector_tab = "MAIN"     
        self.selected_preset_name = None
        
        self.selected_trigger_idx = 0   
        self.selected_attack_edit_idx = 0 
        self.selected_box_idx = 0       
        self.selected_move_edit_idx = 0
        self.selected_projectile_edit_idx = 0  
        
        self.selected_seq_idx = 0
        self.selected_step_idx = 0
        
        self.dummy_platform = Platform({"x": 200, "y": 400, "w": CANVAS_WIDTH, "h": 20}, None)
        self.dummy_enemy = None
        self.player_start_obj = None
        
        self.raw_platforms = []
        self.raw_enemies = []
        self.raw_player_cfg = {}
        self.templates = {}
        self.presets = {}
        self.preset_filepaths = {}  
        
        self.hitstop_timer = 0
        self.sounds = {}
        
        # Оптимизация: динамический кэш шрифтов и выделение единого буфера прозрачности
        self.font_cache = {}
        self.debug_alpha_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        self.ui = EditorUI(self)
        self.load_level()

    def get_cached_font(self, size, bold=False):
        size = max(6, int(size))
        key = (size, bold)
        if key not in self.font_cache:
            self.font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
        return self.font_cache[key]

    def play_sound(self, sound_name):
        if not pygame.mixer or not pygame.mixer.get_init():
            return
            
        if sound_name not in self.sounds:
            os.makedirs("assets", exist_ok=True)
            sound_file = os.path.join("assets", f"{sound_name}.wav")
            
            if os.path.exists(sound_file):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_file)
                except Exception as e:
                    print(f"Error loading sound {sound_file}: {e}")
                    self.sounds[sound_name] = None
            else:
                # Синтез процедурного звука, если физического файла нет на диске
                import array
                import math
                sample_rate = 44100
                audio_data = array.array('h')
                
                if sound_name == "parry":
                    # Высокий металлический "дзынь" (частотный свип с быстрым затуханием)
                    duration_ms = 150
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-15 * t)
                        freq = 900 + 400 * (1.0 - t)
                        val = int(25000 * math.sin(2 * math.pi * freq * t) * decay)
                        audio_data.append(val)
                elif sound_name == "damage":
                    # Глухой низкочастотный удар
                    duration_ms = 200
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-12 * t)
                        freq = 150 - 60 * t
                        val = int(22000 * math.sin(2 * math.pi * freq * t) * decay)
                        audio_data.append(val)
                else:
                    duration_ms = 100
                    num_samples = int(sample_rate * (duration_ms / 1000.0))
                    for i in range(num_samples):
                        t = i / sample_rate
                        decay = math.exp(-10 * t)
                        val = int(15000 * math.sin(2 * math.pi * 440 * t) * decay)
                        audio_data.append(val)
                        
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(buffer=bytes(audio_data))
                except Exception as e:
                    print(f"Error creating procedural sound {sound_name}: {e}")
                    self.sounds[sound_name] = None
                    
        sound_obj = self.sounds.get(sound_name)
        if sound_obj:
            try:
                sound_obj.play()
            except Exception as e:
                print(f"Error playing sound {sound_name}: {e}")

    def spawn_projectile(self, x, y, vx, vy, damage=1, radius=8, gravity=0.0, homing=0.0):
        from entities.projectile import Projectile
        self.projectiles.append(Projectile(x, y, vx, vy, damage, radius, gravity, homing))

    def prompt_text_input(self, title, prompt, initial_value=""):
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        result = simpledialog.askstring(title, prompt, initialvalue=initial_value)
        root.destroy()
        return result

    def run(self):
        running = True
        while running:
            self.clock.tick(60)  
            mouse_clicked_this_frame = False
            right_clicked_this_frame = False
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_clicked_this_frame = True
                    elif event.button == 3:
                        right_clicked_this_frame = True
                    elif event.button == 4:
                        if 0 <= mouse_pos[0] < CANVAS_OFFSET_X:
                            self.left_panel_scroll = max(0, self.left_panel_scroll - 30)
                        elif 1200 <= mouse_pos[0] <= 1400:
                            self.right_panel_scroll = max(0, self.right_panel_scroll - 30)
                        elif self.editor_mode == "LEVEL_EDITOR" and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                            self.zoom = min(3.0, self.zoom + 0.1)
                    elif event.button == 5:
                        if 0 <= mouse_pos[0] < CANVAS_OFFSET_X:
                            max_scroll_l = getattr(self, "left_panel_max_scroll", 400)
                            self.left_panel_scroll = min(max_scroll_l, self.left_panel_scroll + 30)
                        elif 1200 <= mouse_pos[0] <= 1400:
                            max_scroll_r = getattr(self, "right_panel_max_scroll", 400)
                            self.right_panel_scroll = min(max_scroll_r, self.right_panel_scroll + 30)
                        elif self.editor_mode == "LEVEL_EDITOR" and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                            self.zoom = max(0.3, self.zoom - 0.1)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging_instance = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        self.left_panel_scroll = 0
                        self.right_panel_scroll = 0
                        if self.editor_mode == "GAMEPLAY":
                            self.editor_mode = "LEVEL_EDITOR"
                        elif self.editor_mode == "LEVEL_EDITOR":
                            self.editor_mode = "ENEMY_EDITOR"
                            self.zoom = 1.0  
                            self.selected_attack_edit_idx = 0
                            self.selected_box_idx = 0
                        else:
                            # Возвращение в GAMEPLAY
                            self.editor_mode = "GAMEPLAY"
                            self.zoom = 1.0
                            if self.player:
                                self.player.respawn(self)
                        self.rebuild_objects()
                    elif event.key == pygame.K_r:
                        # Проверяем зажатый Shift
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_SHIFT:
                            self.load_level()
                        else:
                            if self.player:
                                self.player.respawn(self)
                    # Фикс: обработка клавиши TAB для переключения режима отображения отладки
                    elif event.key == pygame.K_TAB:
                        self.show_debug = not self.show_debug

            if self.editor_mode == "GAMEPLAY" and self.player:
                # Если таймер хитстопа активен, мы замораживаем логику, но продолжаем рендеринг
                if self.hitstop_timer > 0:
                    self.hitstop_timer -= 1
                else:
                    self.player.handle_input()
                    self.player.update(self.platforms, self.enemies, self)
                    
                    self.projectiles = [p for p in self.projectiles if not p.update(self.platforms, self.player, self)]
                    
                    for enemy in self.enemies:
                        enemy.update(self.platforms, self.gravity, self.player, self)
                    
                    self.enemies = [e for e in self.enemies if e.hp > 0]
                
                target_cam_x = self.player.rect.centerx - CANVAS_WIDTH // 2
                target_cam_y = self.player.rect.centery - SCREEN_HEIGHT // 2
                
                self.camera_x += (target_cam_x - self.camera_x) * 0.1
                self.camera_y += (target_cam_y - self.camera_y) * 0.1
                self.camera_x = max(0, self.camera_x)

            if self.flash_timer > 0:
                self.screen.fill((40, 70, 40))
                self.flash_timer -= 1
            else:
                self.screen.fill((20, 20, 25))
            
            game_canvas_rect = pygame.Rect(CANVAS_OFFSET_X, 0, CANVAS_WIDTH, SCREEN_HEIGHT)
            pygame.draw.rect(self.screen, (30, 30, 30), game_canvas_rect)
            
            # Очистка общей прозрачной поверхности перед отрисовкой отладочной графики
            self.debug_alpha_surf.fill((0, 0, 0, 0))

            editing_trig_idx = None
            editing_atk_idx = None
            editing_box_idx = None
            target_enemy_raw = None
            if self.editor_mode == "ENEMY_EDITOR" and self.selected_preset_name:
                target_enemy_raw = self.presets.get(self.selected_preset_name)
            elif self.editor_mode == "LEVEL_EDITOR" and self.selected_instance:
                if not isinstance(self.selected_instance, (Platform, PlayerStart)):
                    target_enemy_raw = self.selected_instance.raw_data

            if target_enemy_raw is not None:
                if self.inspector_tab == "K-FRAMES":
                    editing_trig_idx = self.selected_seq_idx
                elif self.inspector_tab == "DETAILED_ATTACK":
                    editing_atk_idx = self.selected_attack_edit_idx
                    editing_box_idx = self.selected_box_idx
            
            if self.editor_mode == "ENEMY_EDITOR":
                self.dummy_platform.draw(self.screen, CANVAS_OFFSET_X)
                if self.dummy_enemy:
                    p_fake = pygame.Rect(-100, -100, 0, 0)
                    self.dummy_enemy.draw(
                        surface=self.screen,
                        show_debug=True,
                        player_rect=p_fake,
                        camera_x=0,
                        camera_y=0,
                        zoom=1.0,
                        editing_trigger_idx=editing_trig_idx,
                        editing_attack_idx=editing_atk_idx,
                        editing_box_idx=editing_box_idx,
                        inspector_tab=self.inspector_tab,
                        selected_move_idx=self.selected_move_edit_idx,
                        alpha_surf=self.debug_alpha_surf,
                        game=self
                    )
            else:
                current_zoom = self.zoom if self.editor_mode == "LEVEL_EDITOR" else 1.0

                if self.editor_mode == "LEVEL_EDITOR" and self.snap_to_grid:
                    grid_size = int(40 * current_zoom)
                    if grid_size >= 4:
                        start_grid_x = CANVAS_OFFSET_X - (int(self.camera_x * current_zoom) % grid_size)
                        start_grid_y = - (int(self.camera_y * current_zoom) % grid_size)
                        
                        for x in range(start_grid_x, CANVAS_OFFSET_X + CANVAS_WIDTH, grid_size):
                            if x >= CANVAS_OFFSET_X:
                                pygame.draw.line(self.screen, (40, 40, 45), (x, 0), (x, SCREEN_HEIGHT))
                        for y in range(start_grid_y, SCREEN_HEIGHT, grid_size):
                            if y >= 0:
                                pygame.draw.line(self.screen, (40, 40, 45), (CANVAS_OFFSET_X, y), (CANVAS_OFFSET_X + CANVAS_WIDTH, y))

                for plat in self.platforms:
                    plat.draw(self.screen, self.camera_x, self.camera_y, current_zoom)
                    
                for enemy in self.enemies:
                    p_rect = self.player.rect if self.player else pygame.Rect(0, 0, 0, 0)
                    enemy.draw(
                        surface=self.screen,
                        show_debug=self.show_debug or (self.editor_mode == "LEVEL_EDITOR"),
                        player_rect=p_rect,
                        camera_x=self.camera_x,
                        camera_y=self.camera_y,
                        zoom=current_zoom,
                        editing_trigger_idx=editing_trig_idx,
                        editing_attack_idx=editing_atk_idx,
                        editing_box_idx=editing_box_idx,
                        inspector_tab=self.inspector_tab,
                        selected_move_idx=self.selected_move_edit_idx,
                        alpha_surf=self.debug_alpha_surf,
                        game=self
                    )
                    
                for proj in self.projectiles:
                    proj.draw(self.screen, self.camera_x, self.camera_y, current_zoom)
                    
                if self.player:
                    self.player.draw(self.screen, self.camera_x, self.camera_y, current_zoom)

                if self.editor_mode == "LEVEL_EDITOR" and self.player_start_obj:
                    start_sx = CANVAS_OFFSET_X + (self.player_start_obj.rect.x - self.camera_x) * current_zoom
                    start_sy = (self.player_start_obj.rect.y - self.camera_y) * current_zoom
                    start_sw = self.player_start_obj.rect.width * current_zoom
                    start_sh = self.player_start_obj.rect.height * current_zoom
                    
                    pygame.draw.rect(self.screen, (0, 240, 255), (start_sx, start_sy, start_sw, start_sh), 2)
                    font_start_size = max(8, int(14 * current_zoom))
                    font_start = self.get_cached_font(font_start_size)
                    start_lbl = font_start.render("SPAWN", True, (0, 240, 255))
                    self.screen.blit(start_lbl, (start_sx + 3 * current_zoom, start_sy + 4 * current_zoom))

                if self.editor_mode == "LEVEL_EDITOR" and self.selected_instance:
                    sel_sx = CANVAS_OFFSET_X + (self.selected_instance.rect.x - self.camera_x) * current_zoom
                    sel_sy = (self.selected_instance.rect.y - self.camera_y) * current_zoom
                    sel_sw = self.selected_instance.rect.width * current_zoom
                    sel_sh = self.selected_instance.rect.height * current_zoom
                    pygame.draw.rect(self.screen, (0, 200, 255), (sel_sx, sel_sy, sel_sw, sel_sh), 2)

            # Оптимизация: Рендеринг всей накопленной прозрачной графики отладки ровно один раз перед панелями UI
            self.screen.blit(self.debug_alpha_surf, (0, 0))

            self.ui.draw_left_panel(mouse_clicked_this_frame)
            self.ui.draw_right_panel(mouse_clicked_this_frame, target_enemy_raw)

            if self.editor_mode == "LEVEL_EDITOR" and CANVAS_OFFSET_X <= mouse_pos[0] <= CANVAS_OFFSET_X + CANVAS_WIDTH:
                self.handle_editor_input(mouse_pos, mouse_clicked_this_frame, right_clicked_this_frame)

            font = self.get_cached_font(24)
            player_hp = self.player.hp if self.player else "N/A"
            img = font.render(f"HP: {player_hp} | LSHIFT / RMB: Parry | TAB: Debug Visuals ({'ON' if self.show_debug else 'OFF'}) | SHIFT+R: Reload Level", True, (200, 200, 200))
            self.screen.blit(img, (CANVAS_OFFSET_X + 20, 20))

            if self.flash_timer > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surf.fill((40, 70, 40))
                flash_surf.set_alpha(100)
                self.screen.blit(flash_surf, (0, 0))
                self.flash_timer -= 1

            if not self.player:
                font_err = self.get_cached_font(36)
                err_text = font_err.render("JSON ERROR! Check console.", True, (255, 100, 100))
                err_sub = font_err.render("Fix levels.json & press SHIFT+R", True, (255, 150, 150))
                self.screen.blit(err_text, (SCREEN_WIDTH // 2 - err_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
                self.screen.blit(err_sub, (SCREEN_WIDTH // 2 - err_sub.get_width() // 2, SCREEN_HEIGHT // 2 + 10))

            pygame.display.flip()

        pygame.quit()