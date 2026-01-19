import pygame
import random
import math
import time
import os
from PIL import Image, ImageDraw

# =============================================================================
# LE CRISTALIZATEUR D'IMAGES
# =============================================================================

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def dist_sq(self, other):
        return (self.x - other.x)**2 + (self.y - other.y)**2

class Triangle:
    def __init__(self, p1, p2, p3):
        self.points = [p1, p2, p3]
        self.color = (128, 128, 128)
        self.error = 0 
        self.update_circumcircle()

    def update_circumcircle(self):
        p1, p2, p3 = self.points
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        D = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if abs(D) < 0.0001: D = 0.0001
        self.center_x = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / D
        self.center_y = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / D
        self.radius_sq = (x1 - self.center_x)**2 + (y1 - self.center_y)**2

    def contains_point_in_circumcircle(self, p):
        return (p.x - self.center_x)**2 + (p.y - self.center_y)**2 <= self.radius_sq

class MeshGenerator:
    def __init__(self, width, height, initial_img_path=None):
        self.width = width
        self.height = height
        self.points = []
        self.triangles = []
        self.show_wireframe = False
        self.show_hint = False
        self.fidelity = 0
        self.image_list = self.discover_images()
        self.image_index = 0
        
        if initial_img_path:
            # Trouver l'index de l'image choisie
            for i, p in enumerate(self.image_list):
                if p == initial_img_path:
                    self.image_index = i
                    break
        
        self.load_image_by_index(self.image_index)

    def discover_images(self):
        exts = ('.jpg', '.jpeg', '.png', '.bmp')
        return sorted([f for f in os.listdir('.') if f.lower().endswith(exts)])

    def load_image_by_index(self, index):
        if not self.image_list:
            self.img = self.create_fallback_gradient()
            self.current_image_path = "Généré"
        else:
            self.image_index = index % len(self.image_list)
            self.current_image_path = self.image_list[self.image_index]
            try:
                self.img = Image.open(self.current_image_path).convert("RGB")
                self.img = self.img.resize((self.width, self.height))
            except:
                self.img = self.create_fallback_gradient()
        
        self.image_data = self.img.load()
        self.pygame_img = pygame.image.fromstring(self.img.tobytes(), self.img.size, self.img.mode)
        self.reset()

    def cycle_image(self):
        self.load_image_by_index(self.image_index + 1)
        self.analyze_edges(100)

    def create_fallback_gradient(self):
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        for y in range(self.height):
            color = (int(255 * (1 - y/self.height)), 50, int(255 * (y/self.height)))
            draw.line([(0, y), (self.width, y)], fill=color)
        return img

    def reset(self):
        self.points = [Point(0,0), Point(self.width,0), Point(0,self.height), Point(self.width,self.height),
                       Point(self.width//2,0), Point(self.width//2,self.height), Point(0,self.height//2), Point(self.width,self.height//2)]
        self.triangulate()

    def analyze_edges(self, count=100):
        new_points = []
        for _ in range(count * 5):
            if len(new_points) >= count: break
            x, y = random.randint(5, self.width-6), random.randint(5, self.height-6)
            r, g, b = self.image_data[x, y]
            lum = 0.299*r + 0.587*g + 0.114*b
            others = [self.image_data[x+2, y], self.image_data[x-2, y], self.image_data[x, y+2], self.image_data[x, y-2]]
            grad = sum(abs(lum - (0.299*p[0] + 0.587*p[1] + 0.114*p[2])) for p in others) / 4
            if grad > 20 or random.random() < 0.01:
                new_points.append(Point(x, y))
        self.points.extend(new_points)
        self.triangulate()

    def triangulate(self):
        st = [Point(-self.width*2, -self.height), Point(self.width*2, -self.height), Point(self.width//2, self.height*2)]
        self.triangles = [Triangle(st[0], st[1], st[2])]
        for p in self.points:
            bad = [t for t in self.triangles if t.contains_point_in_circumcircle(p)]
            poly = []
            for t in bad:
                for i in range(3):
                    edge = (t.points[i], t.points[(i+1)%3])
                    is_shared = any(other != t and any((edge[0]==other.points[j] and edge[1]==other.points[(j+1)%3]) or (edge[1]==other.points[j] and edge[0]==other.points[(j+1)%3]) for j in range(3)) for other in bad)
                    if not is_shared: poly.append(edge)
            for t in bad: self.triangles.remove(t)
            for e in poly: self.triangles.append(Triangle(e[0], e[1], p))
        self.triangles = [t for t in self.triangles if not any(p in st for p in t.points)]
        self.calculate_fidelity()

    def calculate_fidelity(self):
        total_error = 0
        for t in self.triangles:
            cx = int((t.points[0].x + t.points[1].x + t.points[2].x) / 3)
            cy = int((t.points[0].y + t.points[1].y + t.points[2].y) / 3)
            cx, cy = max(0, min(self.width-1, cx)), max(0, min(self.height-1, cy))
            t.color = self.image_data[cx, cy]
            err = 0
            samples = [(cx, cy), (int(t.points[0].x), int(t.points[0].y)), (int(t.points[1].x), int(t.points[1].y)), (int(t.points[2].x), int(t.points[2].y))]
            for sx, sy in samples:
                sx, sy = max(0, min(self.width-1, sx)), max(0, min(self.height-1, sy))
                pc = self.image_data[sx, sy]
                err += (t.color[0]-pc[0])**2 + (t.color[1]-pc[1])**2 + (t.color[2]-pc[2])**2
            t.error = math.sqrt(err / len(samples))
            total_error += t.error
        avg_err = total_error / (len(self.triangles) if self.triangles else 1)
        self.fidelity = max(0, 100 - (avg_err / 1.5)) 

    def relax_points(self):
        if not self.triangles: return
        new_points = self.points[:8]
        for i in range(8, len(self.points)):
            p = self.points[i]
            adj = [t for t in self.triangles if p in t.points]
            if adj:
                new_points.append(Point(sum((t.points[0].x + t.points[1].x + t.points[2].x)/3 for t in adj)/len(adj),
                                        sum((t.points[0].y + t.points[1].y + t.points[2].y)/3 for t in adj)/len(adj)))
            else: new_points.append(p)
        self.points = new_points
        self.triangulate()

    def export_svg(self, filename="challenge_output.svg"):
        with open(filename, "w") as f:
            f.write(f'<svg viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg">\n')
            for t in self.triangles:
                pts = " ".join([f"{p.x},{p.y}" for p in t.points])
                rgb = f"rgb({t.color[0]},{t.color[1]},{t.color[2]})"
                f.write(f'  <polygon points="{pts}" fill="{rgb}" stroke="{rgb}" stroke-width="0.3"/>\n')
            f.write("</svg>")
        print(f"Sauvegardé : {filename} (Fidélité: {self.fidelity:.1f}%)")

def draw_text(screen, text, x, y, size=20, color=(255, 255, 255), center=False):
    font = pygame.font.SysFont("Arial", size, bold=True)
    img = font.render(text, True, color)
    if center:
        rect = img.get_rect(center=(x, y))
        screen.blit(img, rect)
    else:
        screen.blit(img, (x, y))

def menu_loop(screen):
    clock = pygame.time.Clock()
    exts = ('.jpg', '.jpeg', '.png', '.bmp')
    images = sorted([f for f in os.listdir('.') if f.lower().endswith(exts)])
    selected_img = None
    
    while selected_img is None:
        screen.fill((20, 20, 30))
        draw_text(screen, "💎 LE CRISTALIZATEUR D'IMAGES", 500, 100, 40, (0, 255, 200), center=True)
        draw_text(screen, "Choisissez votre point de départ :", 500, 180, 20, (200, 200, 200), center=True)
        
        for i, img_name in enumerate(images):
            y_pos = 250 + i * 40
            rect = pygame.Rect(300, y_pos - 15, 400, 30)
            mouse_pos = pygame.mouse.get_pos()
            hover = rect.collidepoint(mouse_pos)
            color = (255, 255, 255) if hover else (150, 150, 150)
            if hover: pygame.draw.rect(screen, (40, 40, 60), rect, border_radius=5)
            draw_text(screen, f"{i+1}. {img_name}", 500, y_pos, 22, color, center=True)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
                if event.type == pygame.MOUSEBUTTONDOWN and hover:
                    selected_img = img_name
        
        if not images:
            draw_text(screen, "(Aucune image trouvée - Le dégradé sera utilisé)", 500, 300, 18, (255, 100, 100), center=True)
            draw_text(screen, "Appuyez sur ESPACE pour continuer", 500, 400, 20, center=True)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    selected_img = "fallback"

        pygame.display.flip()
        clock.tick(30)
    return selected_img

def main():
    pygame.init()
    W, H = 1000, 750
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Le Cristalizateur d'Images 💎")
    
    # ÉTAPE 1 : MENU DE SÉLECTION
    choice = menu_loop(screen)
    
    # ÉTAPE 2 : CHARGEMENT DU MESH
    mesh = MeshGenerator(W, H, initial_img_path=choice if choice != "fallback" else None)
    mesh.analyze_edges(200)
    
    clock = pygame.time.Clock()
    auto_mode = False
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if event.button == 1: mesh.points.append(Point(mx, my)); mesh.triangulate()
                elif event.button == 3 and len(mesh.points) > 8:
                    idx = -1; d_min = 1000
                    for i in range(8, len(mesh.points)):
                        d = (mesh.points[i].x-mx)**2 + (mesh.points[i].y-my)**2
                        if d < d_min: d_min = d; idx = i
                    if idx != -1: mesh.points.pop(idx); mesh.triangulate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s: mesh.export_svg()
                elif event.key == pygame.K_w: mesh.show_wireframe = not mesh.show_wireframe
                elif event.key == pygame.K_r: mesh.reset(); mesh.analyze_edges(200)
                elif event.key == pygame.K_n: mesh.cycle_image() # N pour CHANGER D'IMAGE
                elif event.key == pygame.K_l: mesh.relax_points()
                elif event.key == pygame.K_SPACE: auto_mode = not auto_mode
                elif event.key == pygame.K_h: mesh.show_hint = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_h: mesh.show_hint = False

        if auto_mode and random.random() < 0.2: mesh.analyze_edges(5)

        screen.fill((15, 15, 20))
        if mesh.show_hint:
             screen.blit(mesh.pygame_img, (0,0))
        else:
            for t in mesh.triangles:
                pts = [(p.x, p.y) for p in t.points]
                pygame.draw.polygon(screen, t.color, pts)
                if mesh.show_wireframe:
                    alpha = min(255, int(t.error * 5))
                    pygame.draw.polygon(screen, (255, 255, 255, alpha), pts, 1)

        # HUD
        overlay = pygame.Surface((W, 115), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 210), (0, 0, W, 115))
        screen.blit(overlay, (0, 0))
        
        eff_score = (mesh.fidelity**2) / (len(mesh.points) / 5)
        
        draw_text(screen, f"🏆 OBJECTIF : 98% FIDÉLITÉ (Actuel: {mesh.fidelity:.1f}%)", 20, 15, 24, (255, 215, 0))
        draw_text(screen, f"Source: {mesh.current_image_path}  |  Score Efficacité: {int(eff_score)}", 20, 48, 18)
        draw_text(screen, "[TOUCHE N: IMAGE SUIVANTE] | [L: Relaxer] | [H: Original] | [S: Sauvegarder]", 20, 78, 15, (0, 255, 180))

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()
