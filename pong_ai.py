# Pong AI
# Author: Arthur Goetzke-Coburn
# Email: arthur.goetzkecoburn@gmail.com
#
# An AI that plays the version of Pong provided by Michael Guerzhoy and Denis Begun
"""
TODO: Make AI work on both sides of the board
      Clean up code
      Implement offensive tactics
"""


from math import atan2, sin, cos, sqrt, radians


class PongAI:
    def __init__(self):
        self.side = 1
        self.init_flag = True
        self.x = None
        self.y = None
        self.velocity = None
        self.velocity_x = None
        self.velocity_y = 0
        self.right_paddle = None
        self.prev_right_paddle = None
        self.left_paddle = None
        self.prev_left_paddle = None
        self.ball_rect = None
        self.prev_ball_rect = None
        self.table_size = None
        self.ball_angle = None
        self.direction = 'up'
        self.x_final, self.y_final = 0, 0
        self.bounced_on_enemy = False
        self.wait = False
        self.paddle_velocity = 1
        self.vx_b, self.vy_b = 0, 0

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
                d_wall_x = (self.right_paddle.pos[0] - x_final)
            else:
                d_wall_x = (self.left_paddle.pos[0] - x_final)
            self.velocity_y *= -1
            factor = 1
            if self.velocity_y < 0:
                factor = -1
            return self.calculate_final_pos(d_wall_x, factor*self.table_size[1], x_final, y_final)
        elif bounce_on_enemy:
            d_wall_x = (self.right_paddle.pos[0] - self.left_paddle.pos[0])
            if self.velocity_y > 0:
                d_wall_y = self.table_size[1]-y_final
            else:
                d_wall_y = -y_final
            angle = self.calculate_angle(self.left_paddle, self.ball_rect)

            vx, vy = self.calculate_range_bounce_angle(self.left_paddle, self.ball_rect)
            simplified = True
            if not vx:
                self.velocity_x, self.velocity_y = self.recalculate_ball_speed(angle)
            if simplified:
                self.velocity_x *= -1
            else:
                self.velocity_x, self.velocity_y = vx, vy
            self.vx_b, self.vy_b = self.velocity_x, self.velocity_y
            self.bounced_on_enemy = True
            return self.calculate_final_pos(d_wall_x, d_wall_y, x_final, y_final)
        else:
            return x_final, y_final

    def calculate_angle(self, paddle, ball):
        ball_center_y = ball.pos[1] + ball.size[1]/2
        paddle_center_y = paddle.pos[1] + paddle.size[1]/2
        rel_dis = (ball_center_y - paddle_center_y) / paddle.size[1]
        rel_dis = min(0.5, rel_dis)
        rel_dis = max(-0.5, rel_dis)
        max_angle = 45
        if self.velocity_x > 0:
            sign = 1
        else:
            sign = -1
        return radians(sign*rel_dis*max_angle)

    def recalculate_ball_speed(self, angle):
        vx = cos(angle) * self.velocity_x - sin(angle) * self.velocity_y
        vy = sin(angle) * self.velocity_x + cos(angle) * self.velocity_y
        vx = -vx
        vx = cos(-angle) * vx - sin(-angle) * vy
        vy = sin(-angle) * vx + cos(-angle) * vy
        return vx, vy

    def calculate_range_bounce_angle(self, paddle, ball):
        # Need to calculate y-position enemy bounce
        ball_y_final = 0
        ball_iter_num = 0
        paddle.pos = list(paddle.pos)
        if paddle.pos[1] > ball_y_final:
            max_distance = max(paddle.pos[1]-ball_y_final, paddle.pos[1]+paddle.size[1]-ball_y_final)
            min_distance = min(paddle.pos[1]-ball_y_final, paddle.pos[1]+paddle.size[1]-ball_y_final)
        else:
            max_distance = max(-paddle.pos[1] + ball_y_final, -(paddle.pos[1] + paddle.size[1]) + ball_y_final)
            min_distance = min(-paddle.pos[1] + ball_y_final, -(paddle.pos[1] + paddle.size[1]) + ball_y_final)
        max_attain_dist = abs(ball_iter_num*self.paddle_velocity)
        if abs(max_attain_dist) > abs(max_distance):
            angles = []
            paddle.pos[1] -= max_distance
            angles.append(self.calculate_angle(paddle, ball))
            paddle.pos[1] += max_distance
            paddle.pos[1] -= min_distance
            angles.append(self.calculate_angle(paddle, ball))
            paddle.pos[1] += min_distance
            angle = (angles[0]+angles[1])/2
            return self.recalculate_ball_speed(angle)
        else:
            if max_distance < 0:
                factor = -1
            else:
                factor = 1
            angles = []
            paddle.pos[1] -= (max_attain_dist * factor)
            angles.append(self.calculate_angle(paddle, ball))
            paddle.pos[1] += (max_attain_dist * factor)
            paddle.pos[1] -= min_distance
            angles.append(self.calculate_angle(paddle, ball))
            paddle.pos[1] += min_distance
            angle = (angles[0] + angles[1]) / 2
            return self.recalculate_ball_speed(angle)

    def update(self, paddle_frect, other_paddle_frect, ball_frect, table_size):
        if paddle_frect.pos[0] < table_size[0]/2 and self.init_flag:
            self.side = -1
            self.init_flag = False
        self.right_paddle = paddle_frect
        self.left_paddle = other_paddle_frect
        self.ball_rect = ball_frect
        self.table_size = table_size
        if self.prev_ball_rect:
            self.get_angle_and_velocity()
            if self.velocity_x > 0:
                d_wall_x = self.right_paddle.pos[0] - self.ball_rect.pos[0]
            else:
                d_wall_x = self.left_paddle.pos[0] + self.left_paddle.size[0] - self.ball_rect.pos[0]
            if self.velocity_y > 0:
                d_wall_y = self.table_size[1]-self.ball_rect.pos[1]
            else:
                d_wall_y = -self.ball_rect.pos[1]

            self.x_final, self.y_final = self.calculate_final_pos(d_wall_x, d_wall_y, self.ball_rect.pos[0], self.ball_rect.pos[1])

            if self.right_paddle.pos[1]+self.right_paddle.size[1]/2 < self.y_final:
                self.direction = 'down'
            else:
                self.direction = 'up'

        self.prev_ball_rect = ball_frect
        return self.direction

    def get_calculated_values(self):
        return self.x_final, self.y_final

    def get_bounce_velocity(self):
        return self.vx_b, self.vy_b
