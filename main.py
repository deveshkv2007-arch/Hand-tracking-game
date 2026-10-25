
import pygame
import cv2
import mediapipe as mp

pygame.init()

# ---------------- SETTINGS ----------------

WIDTH, HEIGHT = 900, 600
WORLD_WIDTH = 3000
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Platformer")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 26)
big_font = pygame.font.SysFont(None, 64)

# ---------------- CAMERA ----------------

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ---------------- LEVEL ----------------

platforms = [
    pygame.Rect(0, 550, 600, 50),
    pygame.Rect(700, 550, 400, 50),
    pygame.Rect(1200, 550, 500, 50),
    pygame.Rect(1800, 550, 400, 50),
    pygame.Rect(2300, 550, 700, 50),

    pygame.Rect(250, 440, 150, 20),
    pygame.Rect(480, 360, 150, 20),
    pygame.Rect(760, 430, 150, 20),
    pygame.Rect(1000, 350, 150, 20),
    pygame.Rect(1300, 430, 150, 20),
    pygame.Rect(1500, 340, 150, 20),
    pygame.Rect(1850, 440, 150, 20),
    pygame.Rect(2050, 350, 150, 20),
    pygame.Rect(2400, 430, 150, 20),
    pygame.Rect(2650, 340, 150, 20),
]

def create_coins():
    positions = [
        (300, 400), (530, 320), (800, 390),
        (1050, 310), (1350, 390), (1550, 300),
        (1900, 400), (2100, 310), (2450, 390),
        (2700, 300)
    ]
    return [pygame.Rect(x, y, 20, 20) for x, y in positions]


def create_enemies():
    positions = [
        (350, 520, 350, 500, 2),
        (800, 520, 800, 1000, 3),
        (1350, 520, 1350, 1600, 2),
        (1900, 520, 1900, 2150, 3),
        (2450, 520, 2450, 2850, 2)
    ]

    return [
        {
            "rect": pygame.Rect(x, y, 30, 30),
            "left": left,
            "right": right,
            "speed": speed
        }
        for x, y, left, right, speed in positions
    ]

# ---------------- GAME STATE ----------------

def reset_game():
    global player, velocity_y, on_ground
    global coins, enemies, score, lives
    global game_over, invulnerability, camera_x
    global jump_frames, release_frames
    global jump_cooldown, jump_latched

    player = pygame.Rect(80, 450, 40, 50)
    velocity_y = 0
    on_ground = False

    coins = create_coins()
    enemies = create_enemies()

    score = 0
    lives = 3
    game_over = False
    invulnerability = 0
    camera_x = 0

    jump_frames = 0
    release_frames = 0
    jump_cooldown = 0
    jump_latched = False

reset_game()

GRAVITY = 0.6
JUMP_POWER = -13
PLAYER_SPEED = 6

JUMP_CONFIRM_FRAMES = 4
JUMP_RELEASE_FRAMES = 5
JUMP_COOLDOWN_FRAMES = 15

running = True

# ---------------- MAIN LOOP ----------------

try:
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_r and game_over:
                    reset_game()

        keys = pygame.key.get_pressed()

        # -------- HAND TRACKING --------

        hand_x = None
        index_up = False

        success, frame = cap.read()

        if success:
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]

                mp_draw.draw_landmarks(
                    frame, hand, mp_hands.HAND_CONNECTIONS
                )

                hand_x = hand.landmark[8].x

                index_tip = hand.landmark[8]
                index_joint = hand.landmark[6]

                middle_tip = hand.landmark[12]
                middle_joint = hand.landmark[10]

                ring_tip = hand.landmark[16]
                ring_joint = hand.landmark[14]

                pinky_tip = hand.landmark[20]
                pinky_joint = hand.landmark[18]

                index_up = (
                    index_tip.y < index_joint.y
                    and middle_tip.y > middle_joint.y
                    and ring_tip.y > ring_joint.y
                    and pinky_tip.y > pinky_joint.y
                )

            cv2.imshow("Hand Tracking", frame)

        # -------- PLAYER CONTROL --------

        if not game_over:
            if hand_x is not None:
                target_x = int(hand_x * WIDTH)
                target_x = camera_x + target_x - player.width // 2
                player.x += int((target_x - player.x) * 0.15)
            else:
                if keys[pygame.K_LEFT]:
                    player.x -= PLAYER_SPEED
                if keys[pygame.K_RIGHT]:
                    player.x += PLAYER_SPEED

            player.x = max(0, min(player.x, WORLD_WIDTH - player.width))

            # Jump gesture
            if jump_cooldown > 0:
                jump_cooldown -= 1

            if index_up:
                jump_frames += 1
                release_frames = 0
            else:
                jump_frames = 0
                release_frames += 1

            if release_frames >= JUMP_RELEASE_FRAMES:
                jump_latched = False

            if (
                jump_frames >= JUMP_CONFIRM_FRAMES
                and not jump_latched
                and jump_cooldown == 0
                and on_ground
            ):
                velocity_y = JUMP_POWER
                on_ground = False
                jump_latched = True
                jump_cooldown = JUMP_COOLDOWN_FRAMES

            if keys[pygame.K_SPACE] and on_ground:
                velocity_y = JUMP_POWER
                on_ground = False

            # -------- PHYSICS --------

            old_bottom = player.bottom

            velocity_y += GRAVITY
            player.y += round(velocity_y)

            on_ground = False

            if velocity_y >= 0:
                for platform in platforms:
                    if (
                        player.right > platform.left
                        and player.left < platform.right
                        and old_bottom <= platform.top
                        and player.bottom >= platform.top
                    ):
                        player.bottom = platform.top
                        velocity_y = 0
                        on_ground = True
                        break

            # Coins
            for coin in coins[:]:
                if player.colliderect(coin):
                    coins.remove(coin)
                    score += 1

            # Invulnerability
            if invulnerability > 0:
                invulnerability -= 1

            # Enemies
            for enemy in enemies:
                rect = enemy["rect"]
                rect.x += enemy["speed"]

                if rect.left <= enemy["left"]:
                    rect.left = enemy["left"]
                    enemy["speed"] = abs(enemy["speed"])

                if rect.right >= enemy["right"]:
                    rect.right = enemy["right"]
                    enemy["speed"] = -abs(enemy["speed"])

                if (
                    player.colliderect(rect)
                    and invulnerability == 0
                ):
                    lives -= 1
                    player.x = max(80, camera_x + 80)
                    player.y = 450
                    velocity_y = 0
                    on_ground = False
                    invulnerability = 90

                    if lives <= 0:
                        game_over = True

                    break

            # Falling off the level
            if player.top > HEIGHT and invulnerability == 0:
                lives -= 1
                player.x = max(80, camera_x + 80)
                player.y = 450
                velocity_y = 0
                on_ground = False
                invulnerability = 90

                if lives <= 0:
                    game_over = True

            # Camera follows player
            camera_x = player.centerx - WIDTH // 2
            camera_x = max(0, min(camera_x, WORLD_WIDTH - WIDTH))

        # -------- DRAW WORLD --------

        screen.fill((25, 30, 55))

        # Background stars
        for x in range(0, WIDTH, 100):
            pygame.draw.circle(
                screen, (65, 75, 105),
                (x, 100 + (x % 3) * 45), 2
            )

        # Platforms
        for platform in platforms:
            pygame.draw.rect(
                screen, (80, 200, 130),
                (platform.x - camera_x, platform.y,
                 platform.width, platform.height),
                border_radius=4
            )

        # Coins
        for coin in coins:
            pygame.draw.circle(
                screen, (255, 215, 0),
                (coin.centerx - camera_x, coin.centery), 10
            )

        # Enemies
        for enemy in enemies:
            rect = enemy["rect"]
            pygame.draw.rect(
                screen, (230, 65, 75),
                (rect.x - camera_x, rect.y, rect.width, rect.height),
                border_radius=6
            )

        # Player
        if invulnerability == 0 or invulnerability % 10 < 5:
            pygame.draw.rect(
                screen, (255, 190, 70),
                (player.x - camera_x, player.y,
                 player.width, player.height),
                border_radius=8
            )

            pygame.draw.circle(
                screen, (30, 30, 45),
                (player.x - camera_x + 12, player.y + 14), 3
            )
            pygame.draw.circle(
                screen, (30, 30, 45),
                (player.x - camera_x + 28, player.y + 14), 3
            )

        # HUD
        screen.blit(
            font.render("Move hand: Move | Raise index: Jump",
                        True, (255, 255, 255)),
            (20, 20)
        )
        screen.blit(
            font.render(f"Coins: {score}/{10}",
                        True, (255, 215, 0)),
            (20, 55)
        )
        screen.blit(
            font.render(f"Lives: {lives}",
                        True, (255, 100, 100)),
            (20, 90)
        )

        # Win condition
        if player.x >= WORLD_WIDTH - 100 and not game_over:
            win_text = big_font.render(
                "LEVEL COMPLETE!", True, (255, 215, 0)
            )
            screen.blit(
                win_text,
                win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            )

        # Game over
        if game_over:
            overlay = pygame.Surface(
                (WIDTH, HEIGHT), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            title = big_font.render(
                "GAME OVER", True, (255, 80, 80)
            )
            restart = font.render(
                "Press R to restart | ESC to quit",
                True, (255, 255, 255)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(WIDTH // 2, HEIGHT // 2 - 30)
                )
            )
            screen.blit(
                restart,
                restart.get_rect(
                    center=(WIDTH // 2, HEIGHT // 2 + 30)
                )
            )

        pygame.display.flip()

finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    pygame.quit()
