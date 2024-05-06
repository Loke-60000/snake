import pygame
import sys
import random
import os
import numpy as np
import time


def generate_sine_wave(frequency, duration, volume=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    audio = tone * (2**15 - 1) * volume
    audio = audio.astype(np.int16)
    return pygame.mixer.Sound(buffer=audio)


class Snake:
    def __init__(self, cell_size, width, height):
        self.cell_size = cell_size
        self.width = width
        self.height = height
        self.direction = (cell_size, 0)
        self.body = [(100, 100), (90, 100), (80, 100)]
        self.last_direction_change_time = time.time()
        self.direction_change_interval = 0.1

    def move(self):
        new_head = (self.body[0][0] + self.direction[0],
                    self.body[0][1] + self.direction[1])
        self.body.insert(0, new_head)
        self.body.pop()

    def change_direction(self, new_direction):
        current_time = time.time()
        time_elapsed = current_time - self.last_direction_change_time
        if time_elapsed >= self.direction_change_interval:
            if (
                (new_direction == (0, -self.cell_size) and self.direction != (0, self.cell_size)) or
                (new_direction == (0, self.cell_size) and self.direction != (0, -self.cell_size)) or
                (new_direction == (-self.cell_size, 0) and self.direction != (self.cell_size, 0)) or
                (new_direction == (self.cell_size, 0)
                 and self.direction != (-self.cell_size, 0))
            ):
                self.direction = new_direction
                self.last_direction_change_time = current_time

    def check_collision(self):
        head = self.body[0]
        return (
            head[0] < 0 or head[0] >= self.width or
            head[1] < 0 or head[1] >= self.height or
            head in self.body[1:]
        )

    def draw(self, screen, obj_color):
        for segment in self.body:
            pygame.draw.rect(screen, obj_color, pygame.Rect(
                segment[0], segment[1], self.cell_size, self.cell_size))


class Food:
    def __init__(self, cell_size, width, height):
        self.cell_size = cell_size
        self.width = width
        self.height = height
        self.position = (0, 0)
        self.generate_position()

    def generate_position(self):
        self.position = (random.randrange(0, self.width, self.cell_size),
                         random.randrange(0, self.height, self.cell_size))

    def draw(self, screen, obj_color):
        pygame.draw.rect(screen, obj_color, pygame.Rect(
            self.position[0], self.position[1], self.cell_size, self.cell_size))


class Game:
    def __init__(self):
        pygame.init()
        self.width = 600
        self.height = 600
        self.cell_size = 20
        self.fps = 10
        self.score = 0
        self.score_increment = 10
        self.game_state = 'start_menu'
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game")
        self.font = pygame.font.Font(os.path.join(
            os.path.dirname(__file__), "assets/Quinquefive-ALoRM.ttf"), 15)
        self.bgm_path = os.path.join(
            os.path.dirname(__file__), "assets/S;G-Laboratory.mp3")
        self.start_menu_bgm_path = os.path.join(
            os.path.dirname(__file__), "assets/S;G-Village.mp3")
        self.end_game_bgm_path = os.path.join(
            os.path.dirname(__file__), "assets/S;G-Solitude.mp3")
        self.obj_color = (56, 73, 2)
        self.black = (169, 224, 0)
        self.snake = Snake(self.cell_size, self.width, self.height)
        self.food = Food(self.cell_size, self.width, self.height)
        pygame.mixer.music.load(self.start_menu_bgm_path)
        pygame.mixer.music.play(-1)
        self.eat_sound = generate_sine_wave(
            900, 0.2)
        self.death_sound = generate_sine_wave(
            120, 0.3)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if self.game_state == 'start_menu' and event.key:
                        self.game_state = 'playing'
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(self.bgm_path)
                        pygame.mixer.music.play(-1)
                    elif self.game_state == 'playing':
                        if event.key == pygame.K_UP:
                            self.snake.change_direction((0, -self.cell_size))
                        elif event.key == pygame.K_DOWN:
                            self.snake.change_direction((0, self.cell_size))
                        elif event.key == pygame.K_LEFT:
                            self.snake.change_direction((-self.cell_size, 0))
                        elif event.key == pygame.K_RIGHT:
                            self.snake.change_direction((self.cell_size, 0))
                    elif self.game_state == 'game_over' and event.key == pygame.K_RETURN:
                        self.reset_game()

            self.update_game_logic()
            self.draw()
            clock.tick(self.fps)

    def update_game_logic(self):
        if self.game_state == 'playing':
            self.snake.move()
            if self.snake.check_collision():
                self.death_sound.play()
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.end_game_bgm_path)
                pygame.mixer.music.play(-1)
                self.game_state = 'game_over'
            elif self.snake.body[0] == self.food.position:
                self.score += self.score_increment
                self.fps = min(self.fps + 1, 30)
                self.snake.body.append(self.snake.body[-1])
                self.food.generate_position()
                self.eat_sound.play()

    def draw(self):
        self.screen.fill(self.black)
        if self.game_state == 'start_menu':
            self.draw_start_menu()
        elif self.game_state == 'playing':
            self.snake.draw(self.screen, self.obj_color)
            self.food.draw(self.screen, self.obj_color)
            score_text = self.font.render(
                f'Score: {self.score}', True, self.obj_color)
            self.screen.blit(score_text, (10, 10))
        elif self.game_state == 'game_over':
            self.draw_game_over()
        pygame.display.flip()

    def draw_start_menu(self):
        start_image_path = os.path.join(
            os.path.dirname(__file__), "assets/start.png")
        start_image = pygame.image.load(start_image_path).convert()
        start_image = pygame.transform.scale(
            start_image, (int(self.width * 0.75), int(self.height * 0.75)))
        self.screen.blit(start_image, (self.width *
                         0.125, self.height * 0.125))
        start_text = self.font.render(
            "Press any key to start", True, self.obj_color)
        self.screen.blit(
            start_text, ((self.width - start_text.get_width()) / 2, self.height - 60))
        game_by_text = self.font.render(
            "- A game by Hideo Kojima -", True, self.obj_color)
        self.screen.blit(
            game_by_text, ((self.width - game_by_text.get_width()) / 2, self.height - 30))

    def draw_game_over(self):
        game_over_image_path = os.path.join(
            os.path.dirname(__file__), "assets/gameOver.png")
        game_over_image = pygame.image.load(game_over_image_path).convert()
        game_over_image = pygame.transform.scale(
            game_over_image, (self.width // 2, self.height // 2))
        self.screen.blit(game_over_image, ((
            self.width - game_over_image.get_width()) / 2, self.height * 0.25))
        game_over_text = self.font.render("Game Over", True, self.obj_color)
        self.screen.blit(
            game_over_text, ((self.width - game_over_text.get_width()) / 2, 10))
        final_score_text = self.font.render(
            f'Final Score: {self.score}', True, self.obj_color)
        self.screen.blit(final_score_text,
                         ((self.width - final_score_text.get_width()) / 2, 50))
        restart_text = self.font.render(
            "Press Enter to restart", True, self.obj_color)
        self.screen.blit(
            restart_text, ((self.width - restart_text.get_width()) / 2, 90))
        music_credit_text = self.font.render(
            """BGM from Raym Agini's yt channel""", True, self.obj_color)
        self.screen.blit(
            music_credit_text, ((self.width - music_credit_text.get_width()) / 2, self.height - 50))

    def reset_game(self):
        self.score = 0
        self.fps = 10
        self.snake = Snake(self.cell_size, self.width, self.height)
        self.food = Food(self.cell_size, self.width, self.height)
        self.game_state = 'start_menu'
        pygame.mixer.music.load(self.start_menu_bgm_path)
        pygame.mixer.music.play(-1)


if __name__ == "__main__":
    game = Game()
    game.run()
