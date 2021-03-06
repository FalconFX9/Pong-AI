# Pong AI
# Author: Arthur Goetzke-Coburn
# Email: arthur.goetzkecoburn@gmail.com
#
# An AI that plays the version of Pong provided by Michael Guerzhoy and Denis Begun
"""
TODO: Clean up code
      Create correct non-recursive physics simulator (find the math/fix the math)

Runtime issues:
    -offensive tactics result in a 520x slowdown
        -due to running physics loop for a massive range of positions (~100-200)
    -offensive tactics result in a ~2x slowdown with non-recursive bounce estimates
        -model does not seem to be 100% correct, needs fixing, but seems to be reasonably accurate

Test results:
    -Middle return vs simple collision prediction
        -1000-747
    -Middle return vs iterative collision prediction
        -1000-786
    -Middle return vs complex collision prediction
        -1000-649
    -Middle return + Max VX offense vs simple collision prediction
        -1000-412
    -Middle return + Max VX offense vs Middle return
        -Run 1
            -839-1000
        -Run 2 (tried to fix some code that was weird related to bounces)
            -637-1000
                -Compute time was faster by ~10x
    -Middle return + max DY offense vs Middle return:
        -1000-532
            -Much slower computation time (avg comp. time of 0.00046s), or 0.00016s slower than timeout -- i7-7700HQ
        -1000-503
            -With fixing of bounced_on_enemy, avg comp. time was 0.00041s -- i7-7700HQ
        -1000-712 (reduced offensive precision)
            -Faster computation time of 0.000127s, but a much worse offensive result -- R5 4500U
        -1000-439 (normal offensive code, testing on laptop)
            -Avg. comp time of 0.00046s -- R5 4500U
    -Middle return + max DY offense vs Chaser AI:
        -1000-114
            -Avg. comp time of 0.00055s -- R5 4500U
    -Middle return + max DY offense (non-reducing DY) vs Middle return:
        -1000-701
            -Avg. comp time of 0.000366s -- R5 4500U
    -Middle return + max DY, min vx > vy offense vs Middle return:
        -1000-363
            -Avg. comp time of 0.0001847s -- i7-7700HQ
        -1000-363
            -Avg. comp time of 0.000221s -- R5 4500U
        -1000-367
            -Avg. comp time of 3.7x10-7s, running the timeout function call with 0.0003s timeout -- R5 4500U
        -1000-338
            -Avg. comp time of 6.65x10-7s, running the timeout function call with 0.0001s timeout -- R5 4500U
    -Middle return + max DY, min vx > 1.6vy offense vs Middle return:
        -1000-361
            -Avg. comp time of 5.87x10-7s, running the timeout function call with 0.0001s timeout -- R5 4500U
        -Same but factor = +- 2
            -1000-386, 3.85x10-7s
        -1000-373
    -Middle return + max DY, min vx > vy offense, non-recursive bounce calculation vs Middle return
        -1000-345
            -Avg. comp time of 0.21244ms, no timeout -- R5 4500U
        -1000-341
            -Avg. comp time of 0.214ms, no timeout -- R5 4500U
        -1000-380
            -Avg. comp time of 0.509ms, timeout function used -- R5 4500U
    -Middle return + max DY, min vx > vy offense, non-recursive bounce calculation vs Chaser
        -1000-57
            -Threading calculation time ~0.3ms, avg. comp time of 0.49ms with timeout -- R5 4500U
    -Weirdness
"""

from math import atan2, sin, cos, sqrt, radians
import time


class PongAI:
    def __init__(self, test=False):
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
        self.test = test
        self.p_min, self.p_max = 0, 0
        self.best_ball_send = 0
        self.table = {}

    def create_lookup_table(self):
        """ Creates a 4-D lookup table to avoid re-calculating the game physics, currently unused as it runs too slowly
        """
        pos_min = self.left_paddle.size[1]
        pos_max = self.table_size[1] - self.right_paddle.size[1]
        for i in range(pos_min * 10, pos_max * 10):
            print(i, pos_min * 10, pos_max * 10)
            for v_x in range(int(0.5 * 100), int(10 * 100)):
                for v_y in range(int(0.5 * 100), int(10 * 100)):
                    for b_pos_x in range(int(self.left_paddle.pos[0] + self.left_paddle.size[0]),
                                         int(self.table_size[0] - self.right_paddle.pos[0])):
                        for b_pos_y in range(int(self.ball_rect.size[1]),
                                             int(self.table_size[1] - self.ball_rect.size[1])):
                            self.velocity_x = v_x
                            self.velocity_y = v_y
                            if self.velocity_x > 0:
                                d_wall_x = self.right_paddle.pos[0] - self.ball_rect.pos[0]
                            else:
                                d_wall_x = self.left_paddle.pos[0] + self.left_paddle.size[0] - self.ball_rect.pos[0]
                            if self.velocity_y > 0:
                                d_wall_y = self.table_size[1] - (self.ball_rect.pos[1] + self.ball_rect.size[1])
                            else:
                                d_wall_y = -(self.ball_rect.pos[1] + self.ball_rect.size[1])

                            self.table[(i / 10, v_x / 100, v_y / 100, b_pos_x, b_pos_y)] = self.calculate_final_pos(
                                d_wall_x, d_wall_y, b_pos_x, b_pos_y)
                            self.velocity_x *= -1
                            self.velocity_y *= -1
                            if self.velocity_x > 0:
                                d_wall_x = self.right_paddle.pos[0] - self.ball_rect.pos[0]
                            else:
                                d_wall_x = self.left_paddle.pos[0] + self.left_paddle.size[0] - self.ball_rect.pos[0]
                            if self.velocity_y > 0:
                                d_wall_y = self.table_size[1] - (self.ball_rect.pos[1] + self.ball_rect.size[1])
                            else:
                                d_wall_y = -(self.ball_rect.pos[1] + self.ball_rect.size[1])
                            self.velocity_x = v_x
                            self.velocity_y = v_y
                            self.table[(i / 10, v_x / 100, v_y / 100, b_pos_x, b_pos_y)] = self.calculate_final_pos(
                                d_wall_x, d_wall_y, b_pos_x, b_pos_y)

    def get_angle_and_velocity(self):
        """ Updates the ball's position and velocity, runs at the start of each frame
        """
        d_x = self.ball_rect.pos[0] - self.prev_ball_rect.pos[0]
        d_y = self.ball_rect.pos[1] - self.prev_ball_rect.pos[1]
        self.ball_angle = atan2(d_y, d_x)
        self.velocity = sqrt(d_x ** 2 + d_y ** 2)
        self.velocity_x = d_x
        self.velocity_y = d_y

    def calculate_final_pos(self, d_wall_x, d_wall_y, x, y, offense=False):
        """ A recursive function to calculate the final position of the ball
        Args:
            d_wall_x: distance from the ball to the paddle it is heading towards
            d_wall_y: distance from the ball to either the top or bottom wall
            x, y: position of the ball
            offense: whether the function is being used to compute offense (halts recursion when the enemy paddle is hit)
        """
        if abs(self.velocity_x) < 0.5:
            self.velocity_x = (d_wall_x / abs(d_wall_x)) * 0.5
        iter_num_x = d_wall_x / self.velocity_x
        if self.velocity_y != 0:
            iter_num_y = d_wall_y / self.velocity_y
        else:
            iter_num_y = iter_num_x + 1
        bounce = False
        self.bounced_on_enemy = False
        if iter_num_y < iter_num_x:
            bounce = True
        else:
            if self.velocity_x * self.side < 0:
                self.bounced_on_enemy = True
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
        if offense and self.bounced_on_enemy:  # Returns final ball position when the ball hits the enemy paddle x pos
            return x_final, y_final
        if self.velocity_x * self.side < 0:  # Replaces bounced_on_enemy, tells the paddle to just go to the center
            return 0, self.table_size[1] / 2
        if bounce:  # Calculates bounces on top and bottom walls
            if self.velocity_x > 0:
                d_wall_x = (self.right_paddle.pos[0] - x_final)
            else:
                d_wall_x = (self.left_paddle.pos[0] - x_final)
            self.velocity_y *= -1
            factor = 1
            if self.velocity_y < 0:
                factor = -1
            try:
                return self.calculate_final_pos(d_wall_x, factor * self.table_size[1], x_final, y_final, offense)
            except RecursionError:
                return x_final, y_final
        elif self.bounced_on_enemy:  # Currently unused, estimates the returning bounce from the enemy
            if self.side == 1:
                d_wall_x = (self.right_paddle.pos[0] - self.left_paddle.pos[0])
            else:
                d_wall_x = self.left_paddle.pos[0] - self.right_paddle.pos[0]
            if self.velocity_y > 0:
                d_wall_y = self.table_size[1] - y_final
            else:
                d_wall_y = -y_final
            # angle = self.calculate_angle(self.left_paddle.pos[1], y_final)  # Should this be y_final of ball.pos[1]?

            # vx, vy = self.calculate_range_bounce_angle(self.left_paddle, self.ball_rect)
            simplified = True
            if False:
                self.velocity_x, self.velocity_y = self.recalculate_ball_speed(angle)
            if simplified:
                self.velocity_x *= -1
            # else:
            #    self.velocity_x, self.velocity_y = vx, vy
            self.vx_b, self.vy_b = self.velocity_x, self.velocity_y
            return self.calculate_final_pos(d_wall_x, d_wall_y, x_final, y_final, offense)
        else:
            return x_final, y_final

    def calculate_final_pos_no_recursion(self, dx, dy, x, y, offense=False):
        """ Calculates the final position of the ball without using recursion
        Currently does not work correctly (returned values are incorrect, but the AI seems to work regardless)
        Runs ~50-100x faster than the recursive function
        Same args as calculate_final_pos
        The mathematical model this is based on appears to be incorrect, and needs fixing
        """
        if abs(self.velocity_x) < 0.1:
            self.velocity_x = (dx / abs(dx)) * 0.1
        iter_num = dx / self.velocity_x
        distance_y = abs(self.velocity_y) * iter_num
        sign_y = self.velocity_y / abs(self.velocity_y)
        distance_y -= abs(dy)
        num_bounces = abs(distance_y) % self.table_size[1]
        x_final = self.velocity_x * iter_num
        if num_bounces % 2 != 0:
            y_final = (distance_y % (self.table_size[1] - self.ball_rect.size[1])) * sign_y * -1 + y
            y_final -= self.table_size[1]
        y_final = (distance_y % (self.table_size[1] - self.ball_rect.size[1])) * sign_y + y
        return x_final, y_final

    def offense(self, x_f, y_f, paddle, other_paddle):
        """ Calculates the best position for the paddle to be in to hit the ball past the enemy paddle
        Args:
            x_f, y_f: final position of the ball when it gets to the x-plane of this paddle
            paddle: rect object of our paddle
            other_paddle: rect object of the enemy paddle
        """
        d_y = y_f - (paddle.pos[1] + paddle.size[1])
        if paddle.pos[0] < self.table_size[0] / 2:
            d_x = (self.ball_rect.pos[0]) - (paddle.pos[0] + paddle.size[0])
        else:
            d_x = (self.ball_rect.pos[0] + self.ball_rect.size[0]) - (paddle.pos[0])
        iter_num_x = abs(d_x / self.velocity_x)  # Number of iterations the ball needs to reach the paddle
        iter_num_y = abs(d_y)  # Number of iterations the paddle needs to reach the y position of the ball
        if iter_num_x < iter_num_y:
            if d_y < 0:
                paddle_max = (iter_num_x * self.paddle_velocity * -1) + paddle.pos[1] + (paddle.size[1] / 2)
                paddle_min = (y_f - paddle.pos[1]) + paddle.pos[1] + (paddle.size[1] / 2)
            else:
                paddle_max = (iter_num_x * self.paddle_velocity) + paddle.pos[1] + (paddle.size[1] / 2)
                paddle_min = (y_f - paddle.pos[1] + paddle.size[1]) + paddle.pos[1] + (paddle.size[1] / 2)
        else:
            if d_y < 0:
                paddle_max = (iter_num_y * self.paddle_velocity * -1) + paddle.pos[1] + (paddle.size[1] / 2)
                paddle_min = (y_f - paddle.pos[1]) + paddle.pos[1] + (paddle.size[1] / 2)
            else:
                paddle_max = (iter_num_y * self.paddle_velocity) + paddle.pos[1] + (paddle.size[1] / 2)
                paddle_min = (y_f - paddle.pos[1] + paddle.size[1]) + paddle.pos[1] + (paddle.size[1] / 2)
        # paddle_max and paddle_min represent the y-axis bounds of the range of positions the paddle can have and still
        # hit the ball
        vx = None
        factor = 1
        if paddle_min > paddle_max:  # Inverts the for loop if paddle_min and max are inverted
            factor = -1
        dy_max = 0
        pos_y = 0
        for pos in range(int(paddle_min), int(paddle_max), 1 * factor):  # Iterates through possible paddle positions
            theta = self.calculate_angle(pos - (paddle.size[1] / 2), y_f)
            vx, vy = self.recalculate_ball_speed(theta)
            if abs(vx) > abs(vy):  # We really only care about sending it in the corner at a high speed/direct path
                # which is enforced by this condition
                yb_f = self.calculate_best_pos(vx, vy, x_f, y_f)
                d_y = abs(yb_f) - abs(other_paddle.pos[1] + other_paddle.size[1])  # distance from calculated ball
                # position to the enemy paddle (higher is better)
                if dy_max < abs(d_y):
                    dy_max = d_y
                    pos_y = pos
                    self.best_ball_send = yb_f

        return pos_y  # Best position the paddle can be in

    def calculate_best_pos(self, vx, vy, x_f, y_f):
        """ Calculates the distance from the ball to the wall and passes it to calculate_final_pos
        """
        og_vx, og_vy = self.velocity_x, self.velocity_y
        self.velocity_x, self.velocity_y = vx, vy
        if vx > 0:
            d_wall_x = self.right_paddle.pos[0] - (self.left_paddle.pos[0] + self.left_paddle.size[0])
        else:
            d_wall_x = self.left_paddle.pos[0] + self.left_paddle.size[0] - self.right_paddle.pos[0]
        if vy > 0:
            d_wall_y = self.table_size[1] - (self.ball_rect.pos[1] + self.ball_rect.size[1])
        else:
            d_wall_y = -(self.ball_rect.pos[1] + self.ball_rect.size[1])
        # xb_f, yb_f = self.calculate_final_pos(d_wall_x, d_wall_y, x_f, y_f, True)
        xb_f, yb_f = self.calculate_final_pos_no_recursion(d_wall_x, d_wall_y, x_f, y_f, True)
        self.velocity_x, self.velocity_y = og_vx, og_vy

        return yb_f  # Returns the final position of the ball for the given initial speed

    def calculate_angle(self, paddle_y, ball_y):
        """ Copied from the pong game's physics engine. Calculates the angle the ball bounces off of the paddle.
        """
        ball_center_y = ball_y + self.ball_rect.size[1] / 2
        paddle_center_y = paddle_y + self.left_paddle.size[1] / 2
        rel_dis = (ball_center_y - paddle_center_y) / self.left_paddle.size[1]
        rel_dis = min(0.5, rel_dis)
        rel_dis = max(-0.5, rel_dis)
        max_angle = 45
        if self.velocity_x > 0:
            sign = 1
        else:
            sign = -1
        return radians(sign * rel_dis * max_angle)

    def recalculate_ball_speed(self, angle):
        """ Copied from the pong game's physics engine. Takes the calculate bounce angle and recalculates the speed
        Does not take into account the speed multiplier (should it?)
        """
        vx = cos(angle) * self.velocity_x - sin(angle) * self.velocity_y
        vy = sin(angle) * self.velocity_x + cos(angle) * self.velocity_y
        vx = -vx
        vx = cos(-angle) * vx - sin(-angle) * vy
        vy = sin(-angle) * vx + cos(-angle) * vy
        return vx, vy

    def calculate_range_bounce_angle(self, paddle, ball):
        """ Calculates the range of angles the ball could take when bouncing off the enemy paddle.
        Currently unused as it was not effective.
        """
        # Need to calculate y-position enemy bounce
        ball_y_final = 0
        ball_iter_num = 0
        paddle.pos = list(paddle.pos)
        if paddle.pos[1] > ball_y_final:
            max_distance = max(paddle.pos[1] - ball_y_final, paddle.pos[1] + paddle.size[1] - ball_y_final)
            min_distance = min(paddle.pos[1] - ball_y_final, paddle.pos[1] + paddle.size[1] - ball_y_final)
        else:
            max_distance = max(-paddle.pos[1] + ball_y_final, -(paddle.pos[1] + paddle.size[1]) + ball_y_final)
            min_distance = min(-paddle.pos[1] + ball_y_final, -(paddle.pos[1] + paddle.size[1]) + ball_y_final)
        max_attain_dist = abs(ball_iter_num * self.paddle_velocity)
        if abs(max_attain_dist) > abs(max_distance):
            angles = []
            paddle.pos[1] -= max_distance
            angles.append(self.calculate_angle(paddle, ball.pos[1]))
            paddle.pos[1] += max_distance
            paddle.pos[1] -= min_distance
            angles.append(self.calculate_angle(paddle, ball.pos[1]))
            paddle.pos[1] += min_distance
            angle = (angles[0] + angles[1]) / 2
            return self.recalculate_ball_speed(angle)
        else:
            if max_distance < 0:
                factor = -1
            else:
                factor = 1
            angles = []
            paddle.pos[1] -= (max_attain_dist * factor)
            angles.append(self.calculate_angle(paddle, ball.pos[1]))
            paddle.pos[1] += (max_attain_dist * factor)
            paddle.pos[1] -= min_distance
            angles.append(self.calculate_angle(paddle, ball.pos[1]))
            paddle.pos[1] += min_distance
            angle = (angles[0] + angles[1]) / 2
            return self.recalculate_ball_speed(angle)

    def update(self, paddle_frect, other_paddle_frect, ball_frect, table_size):
        """ Gets the information from the game and calls all the helper function, and returns an instruction for the
        paddle.
        """
        if paddle_frect.pos[0] < table_size[0] / 2:
            self.side = -1
            self.right_paddle = other_paddle_frect
            self.left_paddle = paddle_frect
        else:
            self.right_paddle = paddle_frect
            self.left_paddle = other_paddle_frect
        self.ball_rect = ball_frect
        self.table_size = table_size
        if self.prev_ball_rect:
            self.get_angle_and_velocity()
            # if self.init_flag:
            #    time_i = time.time()
            # self.create_lookup_table()
            #    print(time.time()-time_i)
            #    self.init_flag = False
            if self.velocity_x > 0:
                d_wall_x = self.right_paddle.pos[0] - self.ball_rect.pos[0]
            else:
                d_wall_x = self.left_paddle.pos[0] + self.left_paddle.size[0] - self.ball_rect.pos[0]
            if self.velocity_y > 0:
                d_wall_y = self.table_size[1] - (self.ball_rect.pos[1] + self.ball_rect.size[1])
            else:
                d_wall_y = -(self.ball_rect.pos[1] + self.ball_rect.size[1])

            self.x_final, self.y_final = self.calculate_final_pos(d_wall_x, d_wall_y, self.ball_rect.pos[0],
                                                                  self.ball_rect.pos[1])
            if self.test and self.velocity_x * self.side > 0:
                self.y_final = self.offense(self.x_final, self.y_final, paddle_frect, other_paddle_frect)
            if paddle_frect.pos[1] + paddle_frect.size[1] / 2 < self.y_final:
                self.direction = 'down'
            else:
                self.direction = 'up'

        self.prev_ball_rect = ball_frect
        return self.direction

    def get_calculated_values(self):
        """ Used to visualize estimated ball position in real-time
        """
        return self.x_final, self.y_final

    def get_bounce_velocity(self):
        """ Used to visualize estimated ball bounce angle in real-time
        """
        return self.vx_b, self.vy_b

    def get_p_minmax(self):
        """ Used to visualize something at some point, currently unused
        """
        return self.p_min, self.p_max
