
import pygame
import cv2
import mediapipe as mp

pygame.init()

# -------------------- SETTINGS --------------------

WIDTH, HEIGHT = 900, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Platformer")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 64)

# -------------------- CAMERA --------------------

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# -------------------- LEVEL --------------------

platforms = [
    pygame.Rect(0, 550, 900, 50),
    pygame.Rect(200, 440, 150, 20),
    pygame.Rect(420, 350, 150, 20),
    pygame.Rect(650, 260, 150, 20),
]

# -------------------- GAME STATE --------------------

def create_coins():
    return [
        pygame.Rect(260, 400, 20, 20),
        pygame.Rect(470, 310, 20, 20),
        pygame.Rect(700, 220, 20, 20),
    ]


def create_enemies():
    return [
        {
            "rect": pygame.Rect(280, 410, 30, 30),
            "left": 220,
            "right": 330,
            "speed": 2
        },
        {
            "rect": pygame.Rect(480, 320, 30, 30),
            "left": 430,
            "right": 540,
            "speed": 2
        },
    ]


def reset_game():
    global player, velocity_y, on_ground
    global coins, enemies, score, lives
    global game_over, invulnerability
    global jump_frames, release_frames
    global jump_cooldown, jump_latched

    player = pygame.Rect(100, 500, 40, 50)
    velocity_y = 0
    on_ground = False

    coins = create_coins()
    enemies = create_enemies()

    score = 0
    lives = 3
    game_over = False
    invulnerability = 0

    jump_frames = 0
    release_frames = 0
    jump_cooldown = 0
    jump_latched = False


reset_game()

# Jump settings
JUMP_CONFIRM_FRAMES = 4
JUMP_RELEASE_FRAMES = 5
JUMP_COOLDOWN_FRAMES = 15

gravity = 0.6
jump_power = -13
player_speed = 5

running = True

# -------------------- MAIN LOOP --------------------

try:
    while running:
        clock.tick(FPS)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_r and game_over:
                    reset_game()

        keys = pygame.key.get_pressed()

        # -------------------- HAND TRACKING --------------------

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
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS
                )

                # Index fingertip controls horizontal movement
                hand_x = hand.landmark[8].x

                # Detect raised index finger
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

                cv2.putText(
                    frame,
                    f"Index: {hand_x:.2f}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

            else:
                cv2.putText(
                    frame,
                    "No hand detected",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            cv2.imshow("Hand Tracking - Press Q to close game", frame)

        # Keyboard fallback if no hand is detected
        if not game_over:
            if hand_x is not None:
                target_x = int(hand_x * WIDTH) - player.width // 2
                player.x += int((target_x - player.x) * 0.2)
            else:
                if keys[pygame.K_LEFT]:
                    player.x -= player_speed

                if keys[pygame.K_RIGHT]:
                    player.x += player_speed

            player.left = max(0, player.left)
            player.right = min(WIDTH, player.right)

            # -------------------- JUMP CONTROL --------------------

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
                velocity_y = jump_power
                on_ground = False
                jump_latched = True
                jump_cooldown = JUMP_COOLDOWN_FRAMES

            # Keyboard jump
            if keys[pygame.K_SPACE] and on_ground:
                velocity_y = jump_power
                on_ground = False

            # -------------------- PHYSICS --------------------

            old_bottom = player.bottom

            velocity_y += gravity
            player.y += round(velocity_y)

            on_ground = False

            # Land on platforms when falling
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

            # -------------------- COINS --------------------

            for coin in coins[:]:
                if player.colliderect(coin):
                    coins.remove(coin)
                    score += 1

            # -------------------- INVULNERABILITY --------------------

            if invulnerability > 0:
                invulnerability -= 1

            # -------------------- ENEMIES --------------------

            for enemy in enemies:
                enemy_rect = enemy["rect"]

                enemy_rect.x += enemy["speed"]

                if enemy_rect.left <= enemy["left"]:
                    enemy_rect.left = enemy["left"]
                    enemy["speed"] = abs(enemy["speed"])

                if enemy_rect.right >= enemy["right"]:
                    enemy_rect.right = enemy["right"]
                    enemy["speed"] = -abs(enemy["speed"])

                if (
                    player.colliderect(enemy_rect)
                    and invulnerability == 0
                ):
                    lives -= 1

                    player.x = 100
                    player.y = 500
                    velocity_y = 0
                    on_ground = False

                    invulnerability = 90

                    if lives <= 0:
                        game_over = True

                    break

            # Falling off the screen costs a life
            if player.top > HEIGHT and invulnerability == 0:
                lives -= 1

                player.x = 100
                player.y = 500
                velocity_y = 0
                on_ground = False

                invulnerability = 90

                if lives <= 0:
                    game_over = True

        # -------------------- DRAW GAME --------------------

        screen.fill((25, 30, 55))

        # Platforms
        for platform in platforms:
            pygame.draw.rect(
                screen,
                (80, 200, 130),
                platform,
                border_radius=4
            )

        # Coins
        for coin in coins:
            pygame.draw.circle(
                screen,
                (255, 215, 0),
                coin.center,
                10
            )
            pygame.draw.circle(
                screen,
                (255, 245, 150),
                coin.center,
                5
            )

        # Enemies
        for enemy in enemies:
            rect = enemy["rect"]

            pygame.draw.rect(
                screen,
                (230, 65, 75),
                rect,
                border_radius=6
            )

            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (rect.x + 9, rect.y + 10),
                4
            )
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (rect.x + 22, rect.y + 10),
                4
            )

        # Player with blinking during invulnerability
        if invulnerability == 0 or invulnerability % 10 < 5:
            pygame.draw.rect(
                screen,
                (255, 190, 70),
                player,
                border_radius=8
            )

            pygame.draw.circle(
                screen,
                (30, 30, 45),
                (player.x + 12, player.y + 14),
                3
            )
            pygame.draw.circle(
                screen,
                (30, 30, 45),
                (player.x + 28, player.y + 14),
                3
            )

        # HUD
        screen.blit(
            font.render(
                "Move hand: Move | Raise index: Jump",
                True,
                (255, 255, 255)
            ),
            (20, 20)
        )

        screen.blit(
            font.render(
                f"Coins: {score}/3",
                True,
                (255, 215, 0)
            ),
            (20, 55)
        )

        screen.blit(
            font.render(
                f"Lives: {lives}",
                True,
                (255, 100, 100)
            ),
            (20, 90)
        )

        # Game over overlay
        if game_over:
            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            title = big_font.render(
                "GAME OVER",
                True,
                (255, 80, 80)
            )

            restart_text = font.render(
                "Press R to restart | ESC to quit",
                True,
                (255, 255, 255)
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(WIDTH // 2, HEIGHT // 2 - 30)
                )
            )

            screen.blit(
                restart_text,
                restart_text.get_rect(
                    center=(WIDTH // 2, HEIGHT // 2 + 30)
                )
            )

        pygame.display.flip()

finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    pygame.quit()
