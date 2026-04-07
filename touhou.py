import pygame
import math
import random
import json
import os
import asyncio

# --- Configuration ---
WIDTH, HEIGHT = 600, 800
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
PINK = (255, 100, 255)
GOLD = (255, 215, 0)
GREEN = (0, 255, 100)

STATE_PLAYING = 0
STATE_GAMEOVER = 1


class Starfield:
    def __init__(self):
        # Create 3 layers of stars: (x, y, speed, size)
        self.stars = []
        for _ in range(50):
            self.stars.append([random.randint(0, WIDTH), random.randint(0, HEIGHT), 1, 1])  # Slow back
        for _ in range(30):
            self.stars.append([random.randint(0, WIDTH), random.randint(0, HEIGHT), 2, 2])  # Mid
        for _ in range(15):
            self.stars.append([random.randint(0, WIDTH), random.randint(0, HEIGHT), 4, 3])  # Fast front

    def update(self):
        for star in self.stars:
            star[1] += star[2]  # Move Y by speed
            if star[1] > HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, WIDTH)

    def draw(self, screen):
        for star in self.stars:
            # Distant stars are dimmer (gray), close stars are bright (white)
            color = (150, 150, 150) if star[2] < 3 else WHITE
            pygame.draw.circle(screen, color, (star[0], star[1]), star[3])


class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (200, 255, 255), (0, 0, 10, 24))
        pygame.draw.ellipse(self.image, WHITE, (2, 4, 6, 16))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 18

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0: self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, BLUE, [(20, 0), (40, 40), (20, 30), (0, 40)])
        pygame.draw.circle(self.image, (100, 200, 255), (20, 20), 5)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        self.hitbox_radius = 4
        self.shoot_delay = 0

    def update(self, keys, all_sprites, p_bullets):
        speed = 2.5 if keys[pygame.K_LSHIFT] else 6.5
        if keys[pygame.K_LEFT] and self.rect.left > 0: self.rect.x -= speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH: self.rect.x += speed
        if keys[pygame.K_UP] and self.rect.top > 0: self.rect.y -= speed
        if keys[pygame.K_DOWN] and self.rect.bottom < HEIGHT: self.rect.y += speed

        if keys[pygame.K_z] and self.shoot_delay <= 0:
            b = PlayerBullet(self.rect.centerx, self.rect.top)
            all_sprites.add(b);
            p_bullets.add(b)
            self.shoot_delay = 4
        if self.shoot_delay > 0: self.shoot_delay -= 1


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 80
        self.base_image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.base_image, (150, 0, 0), (40, 40), 40)
        pygame.draw.circle(self.base_image, RED, (40, 40), 30, 5)
        pygame.draw.rect(self.base_image, GOLD, (20, 35, 40, 10))
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(WIDTH // 2, 150))
        self.hp = 150
        self.max_hp = 150
        self.timer = 0
        self.flash_timer = 0
        self.shake_offset = (0, 0)
        self.invuln_timer = 0

    def take_damage(self, amt):
        if self.invuln_timer <= 0:
            self.hp -= amt
            self.flash_timer = 4
            return True
        return False

    def update(self):
        self.timer += 1
        if self.invuln_timer > 0: self.invuln_timer -= 1

        base_x = (WIDTH // 2) + math.sin(self.timer * 0.02) * 150
        base_y = 150 + math.cos(self.timer * 0.03) * 30

        if self.flash_timer > 0:
            self.flash_timer -= 1
            self.image = self.base_image.copy()
            self.image.fill(WHITE, special_flags=pygame.BLEND_RGB_ADD)
            self.shake_offset = (random.randint(-5, 5), random.randint(-5, 5))
        elif self.invuln_timer > 0:
            self.image = self.base_image.copy()
            if (self.timer // 4) % 2 == 0:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image = self.base_image
            self.image.set_alpha(255)
            self.shake_offset = (0, 0)

        self.rect.center = (base_x + self.shake_offset[0], base_y + self.shake_offset[1])

    def fire(self, level, player, all_sprites, bullets):
        if self.invuln_timer > 0: return

        if level == 1:
            if self.timer % 12 == 0:
                angle = (self.timer * 0.08)
                for i in range(6):
                    b_angle = angle + (i * (2 * math.pi / 6))
                    all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, b_angle, 3, PINK))
                    bullets.add(all_sprites.sprites()[-1])
        elif level == 2:
            if self.timer % 45 == 0:
                for i in range(18):
                    b_angle = (i * (2 * math.pi / 18))
                    all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, b_angle, 2.8, WHITE))
                    bullets.add(all_sprites.sprites()[-1])
        elif level == 3:
            if self.timer % 20 == 0:
                for i in range(4):
                    b_angle = (i * (math.pi / 2)) + (self.timer * 0.03)
                    all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, b_angle, 4.5, RED))
                    bullets.add(all_sprites.sprites()[-1])
        elif level == 4:
            if self.timer % 8 == 0:
                angle = -(self.timer * 0.12)
                for i in range(4):
                    b_angle = angle + (i * (2 * math.pi / 4))
                    all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, b_angle, 4, PINK))
                    bullets.add(all_sprites.sprites()[-1])
            if self.timer % 60 == 0:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, math.atan2(dy, dx), 7, GOLD))
                bullets.add(all_sprites.sprites()[-1])
        elif level == 5:
            if self.timer % 5 == 0:
                angle1 = math.sin(self.timer * 0.05) * 1.5 + math.pi / 2
                all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, angle1, 5, PINK))
                bullets.add(all_sprites.sprites()[-1])
                angle2 = -math.sin(self.timer * 0.05) * 1.5 + math.pi / 2
                all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, angle2, 5, RED))
                bullets.add(all_sprites.sprites()[-1])
        elif level >= 6:
            if self.timer % 30 == 0:
                for i in range(24):
                    b_angle = (i * (2 * math.pi / 24)) + (self.timer * 0.01)
                    all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, b_angle, 2, GOLD))
                    bullets.add(all_sprites.sprites()[-1])
            if self.timer % 40 == 0:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                all_sprites.add(Bullet(self.rect.centerx, self.rect.centery, math.atan2(dy, dx), 9, WHITE))
                bullets.add(all_sprites.sprites()[-1])


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, color):
        super().__init__()
        self.image = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (7, 7), 7)
        pygame.draw.circle(self.image, WHITE, (7, 7), 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if not (-50 <= self.rect.x <= WIDTH + 50 and -50 <= self.rect.y <= HEIGHT + 50):
            self.kill()


def load_data():
    if os.path.exists("save.json"):
        try:
            with open("save.json", "r") as f:
                return json.load(f)
        except:
            pass
    return {"max_phase": 1}


def save_data(phase):
    data = load_data()
    if phase > data["max_phase"]:
        data["max_phase"] = phase
        with open("save.json", "w") as f: json.dump(data, f)


async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font_sub = pygame.font.SysFont("monospace", 20)
    font_main = pygame.font.SysFont("Arial", 48, bold=True)

    def reset_game():
        all_sprites = pygame.sprite.Group()
        e_bullets = pygame.sprite.Group()
        p_bullets = pygame.sprite.Group()
        p = Player()
        b = Enemy()
        all_sprites.add(p, b)
        return all_sprites, e_bullets, p_bullets, p, b, 1

    starfield = Starfield()
    all_sprites, e_bullets, p_bullets, player, boss, level = reset_game()
    game_state = STATE_PLAYING
    persistent_data = load_data()

    running = True
    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN: mouse_click = True

        if game_state == STATE_PLAYING:
            starfield.update()
            player.update(keys, all_sprites, p_bullets)
            boss.update()
            boss.fire(level, player, all_sprites, e_bullets)
            p_bullets.update()
            e_bullets.update()

            hits = pygame.sprite.spritecollide(boss, p_bullets, True)
            for hit in hits:
                if boss.take_damage(2):
                    if boss.hp <= 0:
                        level += 1
                        save_data(level)
                        persistent_data = load_data()
                        boss.invuln_timer = 100
                        boss.hp = 150 + (level * 60)
                        boss.max_hp = boss.hp
                        for b in e_bullets: b.kill()

            for b in e_bullets:
                dist = math.hypot(player.rect.centerx - b.rect.centerx, player.rect.centery - b.rect.centery)
                if dist < player.hitbox_radius + 4:
                    game_state = STATE_GAMEOVER

        screen.fill(BLACK)
        starfield.draw(screen)
        all_sprites.draw(screen)
        p_bullets.draw(screen)

        # UI
        pygame.draw.rect(screen, (50, 50, 50), (100, 20, 400, 15))
        pygame.draw.rect(screen, GREEN, (100, 20, 400 * (max(0, boss.hp) / boss.max_hp), 15))
        pygame.draw.rect(screen, WHITE, (100, 20, 400, 15), 2)

        txt_level = font_sub.render(f"PHASE: {level}", True, WHITE)
        txt_best = font_sub.render(f"MAX PHASE: {persistent_data['max_phase']}", True, GOLD)
        screen.blit(txt_level, (100, 40))
        screen.blit(txt_best, (100, 65))

        if keys[pygame.K_LSHIFT] and game_state == STATE_PLAYING:
            pygame.draw.circle(screen, WHITE, player.rect.center, 10, 1)
            pygame.draw.circle(screen, RED, player.rect.center, 3)

        if game_state == STATE_GAMEOVER:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            msg = font_main.render("MISSION FAILED", True, RED)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 100))
            btn_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
            btn_color = (150, 150, 150) if btn_rect.collidepoint(mouse_pos) else (100, 100, 100)
            if btn_rect.collidepoint(mouse_pos) and mouse_click:
                all_sprites, e_bullets, p_bullets, player, boss, level = reset_game()
                game_state = STATE_PLAYING
            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
            pygame.draw.rect(screen, WHITE, btn_rect, 2, border_radius=10)
            btn_txt = font_sub.render("RETRY", True, WHITE)
            screen.blit(btn_txt,
                        (btn_rect.centerx - btn_txt.get_width() // 2, btn_rect.centery - btn_txt.get_height() // 2))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
