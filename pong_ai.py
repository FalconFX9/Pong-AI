# Pong AI
# Author: Arthur Goetzke-Coburn
# Email: arthur.goetzkecoburn@gmail.com
#
# An AI that plays the version of Pong provided by Michael Guerzhoy and Denis Begun


from math import atan2, sin, cos, sqrt


class PongAI:
    def __init__(self):
        self.x = None
        self.y = None
        self.velocity = None
        self.velocity_x = None
        self.velocity_y = None
        self.paddle_rect = None
        self.prev_paddle_rect = None
        self.enemy_rect = None
        self.prev_enemy_rect = None
        self.ball_rect = None
        self.prev_ball_rect = None
        self.table_size = None
        self.ball_angle = None
        self.direction = 'up'
        self.x_final, self.y_final = 0, 0
        self.bounced_on_enemy = False
        self.wait = False

    def get_angle_and_velocity(self):
        d_x = self.ball_rect.pos[0] - self.prev_ball_rect.pos[0]
        d_y = self.ball_rect.pos[1] - self.prev_ball_rect.pos[1]
        self.ball_angle = atan2(d_y, d_x)
        self.velocity = sqrt(d_x**2+d_y**2)
        self.velocity_x = d_x
        self.velocity_y = d_y

    def calculate_final_pos(self, d_wall_x, d_wall_y, x, y):
        iter_num_x = d_wall_x / self.velocity_x
        if self.velocity_y != 0:
            iter_num_y = d_wall_y / self.velocity_y
        else:
            iter_num_y = iter_num_x + 1
        bounce = False
        bounce_on_enemy = False
        if iter_num_y < iter_num_x:
            bounce = True
        else:
            if self.velocity_x < 0:
                bounce_on_enemy = True
            else:
                if self.bounced_on_enemy:
                    self.wait = True
                    self.bounced_on_enemy = False

        if self.wait:
            if iter_num_x < iter_num_y:
                self.wait = False
            else:
                return x, y
        iter_num = min(iter_num_x, iter_num_y)
        x_final = (self.velocity_x * iter_num) + x
        y_final = (self.velocity_y * iter_num) + y
        if bounce:
            if self.velocity_x > 0:
                d_wall_x = self.paddle_rect.pos[0]-x_final
            else:
                d_wall_x = self.enemy_rect.pos[0]-x_final
            self.velocity_y *= -1
            factor = 1
            if self.velocity_y < 0:
                factor = -1
            return self.calculate_final_pos(d_wall_x, factor*self.table_size[1], x_final, y_final)
        elif bounce_on_enemy:
            d_wall_x = self.paddle_rect.pos[0] - self.enemy_rect.pos[0]
            if self.velocity_y > 0:
                d_wall_y = self.table_size[1]-y_final
            else:
                d_wall_y = -y_final
            self.velocity_x *= -1
            self.bounced_on_enemy = True
            return self.calculate_final_pos(d_wall_x, d_wall_y, x_final, y_final)
        else:
            return x_final, y_final

    def update(self, paddle_frect, other_paddle_frect, ball_frect, table_size):
        self.paddle_rect = paddle_frect
        self.enemy_rect = other_paddle_frect
        self.ball_rect = ball_frect
        self.table_size = table_size
        if self.prev_ball_rect:
            self.get_angle_and_velocity()
            if self.velocity_x > 0:
                d_wall_x = self.paddle_rect.pos[0]-self.ball_rect.pos[0]
            else:
                d_wall_x = self.enemy_rect.pos[0]-self.ball_rect.pos[0]
            if self.velocity_y > 0:
                d_wall_y = self.table_size[1]-self.ball_rect.pos[1]
            else:
                d_wall_y = -self.ball_rect.pos[1]
            self.x_final, self.y_final = self.calculate_final_pos(d_wall_x, d_wall_y, self.ball_rect.pos[0], self.ball_rect.pos[1])
            if self.paddle_rect.pos[1]+self.paddle_rect.size[1]/2 < self.y_final:
                self.direction = 'down'
            else:
                self.direction = 'up'

        self.prev_ball_rect = ball_frect
        return self.direction

    def get_calculated_values(self):
        return self.x_final, self.y_final

