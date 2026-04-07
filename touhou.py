import pygame
import math
import random
import json
import os

# --- Configuration ---
WIDTH, HEIGHT = 600, 800
FPS = 60
PLAYER_SPEED = 5
FOCUS_SPEED = 2
WHITE, BLACK, RED, BLUE, PINK, GOLD, GREEN = (255, 255, 255), (0, 0, 0), (255, 50, 50), (50, 50, 255), (255, 100,
                                                                                                        255), (255, 215,
                                                                                                               0), (0,
                                                                                                                    255,
                                                                                                                    100)


class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, WHITE, (0, 0, 8, 20))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 12

    def update(self, *args):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (16, 16), 16)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        self.hitbox_radius = 4
        self.shoot_delay = 0

    def update(self, keys, all_sprites, p_bullets):
        speed = FOCUS_SPEED if keys[pygame.K_LSHIFT] else PLAYER_SPEED
        if keys[pygame.K_LEFT] and self.rect.left > 0: self.rect.x -= speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH: self.rect.x += speed
        if keys[pygame.K_UP] and self.rect.top > 0: self.rect.y -= speed
        if keys[pygame.K_DOWN] and self.rect.bottom < HEIGHT: self.rect.y += speed

        # Shooting Logic (Z Key)
        if keys[pygame.K_z] and self.shoot_delay <= 0:
            b1 = PlayerBullet(self.rect.centerx - 10, self.rect.top)
            b2 = PlayerBullet(self.rect.centerx + 10, self.rect.top)
            all_sprites.add(b1, b2);
            p_bullets.add(b1, b2)
            self.shoot_delay = 5  # Rapid fire

        if self.shoot_delay > 0:
            self.shoot_delay -= 1


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, color):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (6, 6), 6)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, *args):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if not (-50 <= self.rect.x <= WIDTH + 50 and -50 <= self.rect.y <= HEIGHT + 50):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, RED, [(30, 0), (60, 60), (0, 60)])
        self.rect = self.image.get_rect(center=(WIDTH // 2, 150))
        self.timer = 0
        self.hp = 100
        self.max_hp = 100

    def update(self, *args):
        self.timer += 1
        hover_range = 150
        self.rect.centerx = (WIDTH // 2) + math.sin(self.timer * 0.02) * hover_range

    def fire(self, level, player, all_sprites, bullets):
        if level == 1 and self.timer % 15 == 0:
            for i in range(6):
                angle = (i / 6) * 2 * math.pi + (self.timer * 0.1)
                b = Bullet(self.rect.centerx, self.rect.centery, angle, 3, PINK)
                all_sprites.add(b);
                bullets.add(b)
        elif level == 2 and self.timer % 50 == 0:
            for i in range(20):
                angle = (i / 20) * 2 * math.pi
                b = Bullet(self.rect.centerx, self.rect.centery, angle, 2.5, WHITE)
                all_sprites.add(b);
                bullets.add(b)
        elif level == 3 and self.timer % 4 == 0:
            b = Bullet(random.randint(0, WIDTH), -10, 1.57, 5, RED)
            all_sprites.add(b);
            bullets.add(b)
        elif level >= 4 and self.timer % 40 == 0:
            angle = math.atan2(player.rect.centery - self.rect.centery, player.rect.centerx - self.rect.centerx)
            for i in range(-2, 3):
                b = Bullet(self.rect.centerx, self.rect.centery, angle + (i * 0.15), 6, GOLD)
                all_sprites.add(b);
                bullets.add(b)


def load_highscore():
    if os.path.exists("danmaku_save.json"):
        with open("danmaku_save.json", "r") as f: return json.load(f).get("best_time", 0)
    return 0


def save_highscore(t):
    with open("danmaku_save.json", "w") as f: json.dump({"best_time": round(t, 2)}, f)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 20)

    all_sprites = pygame.sprite.Group()
    e_bullets = pygame.sprite.Group()
    p_bullets = pygame.sprite.Group()

    player = Player()
    boss = Enemy()
    all_sprites.add(player, boss)

    best_time = load_highscore()
    start_ticks = pygame.time.get_ticks()
    level = 1
    running = True

    while running:
        clock.tick(FPS)
        current_time = (pygame.time.get_ticks() - start_ticks) / 1000

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        # --- Logic ---
        player.update(keys, all_sprites, p_bullets)
        boss.update()
        boss.fire(level, player, all_sprites, e_bullets)
        p_bullets.update()
        e_bullets.update()

        # 1. Player Bullets hitting Boss
        hits = pygame.sprite.spritecollide(boss, p_bullets, True)
        for hit in hits:
            boss.hp -= 1
            if boss.hp <= 0:
                level += 1
                boss.hp = boss.max_hp + (level * 20)  # Boss gets tankier
                boss.max_hp = boss.hp

        # 2. Boss Bullets hitting Player Hitbox
        for b in e_bullets:
            dist = math.hypot(player.rect.centerx - b.rect.centerx, player.rect.centery - b.rect.centery)
            if dist < player.hitbox_radius + 4:
                if current_time > best_time: save_highscore(current_time)
                running = False

        # --- Render ---
        screen.fill(BLACK)
        all_sprites.draw(screen)
        p_bullets.draw(screen)

        # HUD & Boss HP Bar
        pygame.draw.rect(screen, RED, (WIDTH // 2 - 100, 50, 200, 10))
        pygame.draw.rect(screen, GREEN, (WIDTH // 2 - 100, 50, 200 * (boss.hp / boss.max_hp), 10))

        screen.blit(font.render(f"TIME: {round(current_time, 1)}s", True, WHITE), (10, 10))
        screen.blit(font.render(f"LVL: {level}", True, PINK), (WIDTH // 2 - 30, 10))
        screen.blit(font.render(f"PB: {best_time}s", True, GOLD), (WIDTH - 150, 10))

        if keys[pygame.K_LSHIFT]:  # Hitbox visual
            pygame.draw.circle(screen, WHITE, player.rect.center, 8, 1)
            pygame.draw.circle(screen, RED, player.rect.center, 3)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
