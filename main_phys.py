import math
import random
import pygame
import pymunk
import sys
import matplotlib.pyplot as plt

pygame.init()

# Set up display and maximize window
info = pygame.display.Info()
w, h = 800, 600
screen = pygame.display.set_mode((w, h))
pygame.display.set_caption("Free Fall Simulation")

# Set up Pymunk
space = pymunk.Space()
space.gravity = (0, 981)  

# Load desert image
desert_image = pygame.image.load("landscape_1.png").convert()
desert_image = pygame.transform.scale(desert_image, (w, h))  # Adjust the scale as needed
grass_image = pygame.image.load("water_1.jpg").convert()
grass_image = pygame.transform.scale(grass_image, (w, h))  # Adjust the scale as needed



# Helper function to draw text
def draw_text(screen, text, position, font_size=22, color=(0, 0, 0)):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

# Input box class
class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (200, 200, 200)
        self.text = text
        self.txt_surface = pygame.font.Font(None, 25).render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = (0, 0, 0) if self.active else (200, 200, 200)
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                    self.color = (200, 200, 200)
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = pygame.font.Font(None, 25).render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_text(self):
        return self.text

# Center the input boxes and buttons
center_x = w // 2
input_width = 140
input_height = 30
input_margin = 50
start_button_width = 140
start_button_height = 32

weight_box = InputBox(center_x - input_width // 2, 110, input_width, input_height)
height_box = InputBox(center_x - input_width // 2, 130 + input_margin, input_width, input_height)
gravity_box = InputBox(center_x - input_width // 2, 150 + 2 * input_margin, input_width, input_height)
direction_box = InputBox(center_x - input_width // 2, 170 + 3 * input_margin, input_width, input_height)
input_boxes = [weight_box, height_box, gravity_box, direction_box]

start_button_color = (0, 255, 0)
start_button_rect = pygame.Rect(center_x - start_button_width // 2, 300 + 4 * input_margin, start_button_width, start_button_height)

back_button_color = (255, 0, 0)
back_button_rect = pygame.Rect(650, 10, 210, 32)

# Ground type selection
ground_types = ["Land", "Water"]
selected_ground_type = "Land"
ground_buttons = [pygame.Rect(center_x - 60, 370 + i * 40, 20, 20) for i in range(len(ground_types))]

def handle_ground_selection(event):
    global selected_ground_type
    for i, button in enumerate(ground_buttons):
        if button.collidepoint(event.pos):
            selected_ground_type = ground_types[i]

def draw_ground_selection(screen):
    for i, button in enumerate(ground_buttons):
        pygame.draw.rect(screen, (0, 0, 0), button, 2)
        if ground_types[i] == selected_ground_type:
            pygame.draw.circle(screen, (0, 0, 0), button.center, 8)
        draw_text(screen, ground_types[i], (button.x + 30, button.y - 5))

# Set up ground
ground_y = h - 50
ground = pymunk.Segment(space.static_body, (0, ground_y), (w, ground_y), 5)
if selected_ground_type == "Land":
    ground.elasticity = 0.1
else:
    ground.elasticity = -0.6
space.add(ground)

# Collision handler
def collision_handler(arbiter, space, data):
    global ground_y
    ball_shape = arbiter.shapes[0]
    ball_body = ball_shape.body
    
    if hasattr(ball_body, 'bounced') and ball_body.bounced:
        return True

    ball_body.bounced = True  # Mark the ball as bounced

    # Create two new balls upon collision
    positions=[]
    force=ball_body.mass*height*gravity/100000
    if force<=10 or selected_ground_type == "Water":
        peaces=1
        new_mass = ball_body.mass
        new_radius = ball_shape.radius 
    else:
        peaces= int(math.log(force))
        new_mass = ball_body.mass / 2
        new_radius = ball_shape.radius / 2  
    for i in range(0,peaces):
        positions.append((random.randint(-20, 20),0))
    
    for offset in positions:
        new_ball_body = pymunk.Body(new_mass, pymunk.moment_for_circle(new_mass, 0, new_radius))
        new_ball_body.position = ball_body.position + offset
        new_ball_body.velocity = ball_body.velocity
        new_ball_body.bounced = True  # Ensure the new balls have not bounced yet
        new_ball_shape = pymunk.Circle(new_ball_body, new_radius)
        if selected_ground_type == "Land":
            new_ball_shape.elasticity = 0.5
        else:
            new_ball_shape.elasticity = 0.5
        
        space.add(new_ball_body, new_ball_shape)

    # Remove the original ball
    space.remove(ball_body, ball_shape)

    return True

# Data lists for plotting
time_data = []
velocity_data = []

# Simulation function
def create_simulation(weight, height, gravity, direction):
    # Clear previous objects
    for body in space.bodies:
        space.remove(body)
    for shape in space.shapes:
        if isinstance(shape, pymunk.Segment):
            continue
        space.remove(shape)

    space.gravity = (0, gravity)
    
    ball_mass = weight
    ball_radius = int(weight**(1/2))
    ball_body = pymunk.Body(ball_mass, pymunk.moment_for_circle(ball_mass, 0, ball_radius))
    
    initial_ball_position = w / 2, h - height - 50  # Position based on height input
    ball_body.position = initial_ball_position
    ball_body.bounced = False  # Initialize the bounced flag
    ball_shape = pymunk.Circle(ball_body, ball_radius)
    if selected_ground_type == "Land":
        ball_shape.elasticity = 0.5
    else:
        ball_shape.elasticity = 0.5
    #ball_shape.elasticity = 0.1
    space.add(ball_body, ball_shape)

    # Apply horizontal velocity based on direction input
    ball_body.velocity = (direction, 0)

    # Set up collision handler
    handler = space.add_collision_handler(0, 0)
    handler.post_solve = collision_handler

    running = True
    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()  # Start timer

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(event.pos):
                    running = False

        screen.fill((255, 255, 255))

        # Draw ground
        pygame.draw.line(screen, (0, 0, 0), (0, ground_y), (w, ground_y), 5)
        if selected_ground_type == "Land":
            screen.blit(desert_image, (0, 10))
        else:
            #screen.blit(grass_image, (0, 10))
            pygame.draw.line(screen, (0, 255, 255), (0, ground_y), (w, ground_y), 50)

        # Draw the basket at the initial position
        basket_width, basket_height = 2*ball_radius, 20
        basket_x = initial_ball_position[0] - basket_width // 2
        basket_y = initial_ball_position[1] - basket_height // 2
        pygame.draw.rect(screen, (139, 69, 19), (basket_x, basket_y, basket_width, basket_height))

        # Draw the ball
        for shape in space.shapes:
            if isinstance(shape, pymunk.Circle):
                pos_x, pos_y = shape.body.position
                pygame.draw.circle(screen, (0, 0, 255), (int(pos_x), int(pos_y)), int(shape.radius))

        # Draw the back button
        pygame.draw.rect(screen, back_button_color, back_button_rect)
        draw_text(screen, "Back to Menu", (back_button_rect.x + 10, back_button_rect.y + 5))

        # Draw the elapsed time
        elapsed_time = (pygame.time.get_ticks() - start_ticks) / 1000  # Convert to seconds
        draw_text(screen, f"Time: {elapsed_time:.2f}s", (10, 10))

        # Collect velocity data
        velocity = math.sqrt(ball_body.velocity.x ** 2 + ball_body.velocity.y ** 2)
        vt=math.sqrt(2*gravity*velocity)
        time_data.append(elapsed_time)
        velocity_data.append(vt)

        #end_ticks = pygame.time.get_ticks()
        #time_to_ground = (end_ticks - start_ticks) / 1000  # Convert to seconds
        if shape.body.position.y >= ground_y - ball_radius:
        #    draw_text(screen, f"Time: {time_to_ground:.2f}s", (10, 30))
            running = False  # Stop the simulation
        
        space.step(1 / 60.0)
        pygame.display.flip()
        clock.tick(60)

# Main loop
running = True
in_simulation = False
error_message = None
MAX_DIRECTION = 30  # Set a maximum direction value

while running:
    if not in_simulation:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for box in input_boxes:
                box.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                handle_ground_selection(event)
                if start_button_rect.collidepoint(event.pos):
                    try:
                        weight = float(weight_box.get_text())
                        height = float(height_box.get_text())
                        gravity = float(gravity_box.get_text())
                        direction = float(direction_box.get_text())
                        if height > 500:
                            error_message = "Height cannot exceed screen height (500)"
                        elif abs(direction) > MAX_DIRECTION:
                            error_message = f"Direction cannot exceed {MAX_DIRECTION}"
                        else:
                            in_simulation = True
                            error_message = None
                    except ValueError:
                        error_message = "Please enter valid numerical values."
        
        screen.fill((255, 255, 255))
        draw_text(screen, "Weight: (kg)", (center_x - 60, 87))
        draw_text(screen, "Height: (m)", (center_x - 60, 157))
        draw_text(screen, "Gravity:", (center_x - 60, 227))
        draw_text(screen, "Wind: (m/s)", (center_x - 60, 297))

        for box in input_boxes:
            box.draw(screen)

        pygame.draw.rect(screen, start_button_color, start_button_rect)
        draw_text(screen, "Start", (start_button_rect.x + 50, start_button_rect.y + 5))

         # Draw the ground selection buttons
        draw_ground_selection(screen)
        
        if error_message:
            draw_text(screen, error_message, (center_x - 140, 450), font_size=22, color=(255, 0, 0))

        pygame.display.flip()

    else:
        create_simulation(weight, height, gravity, direction)
        in_simulation = False
        
        # Plot the velocity-time graph after the simulation
        plt.figure()
        plt.plot(time_data, velocity_data, label='Velocity')
        plt.xlabel('Time (s)')
        plt.ylabel('Velocity (m/s)')
        plt.title('Velocity-Time Graph')
        plt.legend()
        plt.show()

pygame.quit()
sys.exit()