import pygame
import random
import math
import time
import os
from PIL import Image, ImageDraw

# =============================================================================
# PROJET R506 : LE CRISTALIZATEUR D'IMAGES
# =============================================================================

class Point:
    """Structure simple pour stocker les coordonnées d'un sommet."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def dist_sq(self, other):
        """Calcule la distance au carré entre deux points (plus rapide que sqrt)."""
        return (self.x - other.x)**2 + (self.y - other.y)**2

class Triangle:
    """Gère un triangle du maillage."""
    def __init__(self, p1, p2, p3):
        self.points = [p1, p2, p3]
        self.color = (0, 0, 0) # Couleur moyenne extraite de l'image
        self.error = 0         # Écart de couleur par rapport à la photo originale
        self.calc_cercle_circonscrit()

    def calc_cercle_circonscrit(self):
        """Calculer le centre et le rayon du cercle circonscrit (Méthode géométrique)."""
        p1, p2, p3 = self.points
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y

        # On utilise les formules de géométrie analytique
        D = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        
        # Sécurité pour éviter la division par zéro (points alignés)
        if abs(D) < 0.0001: D = 0.0001
        
        self.cx = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / D
        self.cy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / D
        self.radius_sq = (x1 - self.cx)**2 + (y1 - self.cy)**2

    def contient_point_dans_cercle(self, p):
        """Vérifie si le point p est à l'intérieur du cercle circonscrit (Règle de Delaunay)."""
        return (p.x - self.cx)**2 + (p.y - self.cy)**2 <= self.radius_sq

class GenerateurMaillage:
    """Cœur de l'application : gère les points, la triangulation et l'analyse bitmap."""
    def __init__(self, width, height, chemin_image=None):
        self.w = width
        self.h = height
        self.points = []
        self.triangles = []
        self.img_idx = 0
        self.filaire = False   # Afficher les traits ou non
        self.voir_aide = False # Voir l'image d'origine
        self.fidélité = 0.0
        
        # Scanner le dossier pour trouver des photos
        self.liste_images = self.charger_liste_images()
        
        if chemin_image in self.liste_images:
            self.img_idx = self.liste_images.index(chemin_image)
            
        self.charger_image(self.img_idx)

    def charger_liste_images(self):
        """Récupère tous les fichiers images du dossier."""
        extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        return sorted([f for f in os.listdir('.') if f.lower().endswith(extensions)])

    def charger_image(self, index):
        """Charge l'image choisie et prépare les données pixels."""
        if not self.liste_images:
            # Sécurité : générer un dégradé si le dossier est vide
            img = Image.new("RGB", (self.w, self.h))
            draw = ImageDraw.Draw(img)
            for y in range(self.h):
                color = (int(255 * (1-y/self.h)), 50, int(255 * y/self.h))
                draw.line([(0, y), (self.w, y)], fill=color)
            self.nom_actuel = "Démo (Dégradé)"
        else:
            self.img_idx = index % len(self.liste_images)
            self.nom_actuel = self.liste_images[self.img_idx]
            try:
                img = Image.open(self.nom_actuel).convert("RGB")
                img = img.resize((self.w, self.h))
            except:
                img = Image.new("RGB", (self.w, self.h))

        self.pixels = img.load()
        # On garde une version Pygame pour l'affichage du fond
        mode = img.mode
        size = img.size
        data = img.tobytes()
        self.surface_originale = pygame.image.fromstring(data, size, mode)
        self.reset()

    def reset(self):
        """Réinitialise les points avec juste les 4 coins et 4 milieux de bords."""
        self.points = [
            Point(0,0), Point(self.w,0), Point(0,self.h), Point(self.w,self.h),
            Point(self.w//2,0), Point(self.w//2,self.h), Point(0,self.h//2), Point(self.w,self.h//2)
        ]
        self.calculer_triangulation()

    def analyse_bitmap(self, nb=100):
        """[CHAPITRE 2] : Placement intelligent de points basé sur le contraste."""
        points_trouvés = 0
        tentatives = 0
        while points_trouvés < nb and tentatives < nb * 10:
            x = random.randint(5, self.w-6)
            y = random.randint(5, self.h-6)
            
            # On compare la luminance du pixel avec ses voisins (Gradient simple)
            pix = self.pixels[x, y]
            lum = sum(pix)/3
            voisins = [self.pixels[x+2, y], self.pixels[x-2, y], self.pixels[x, y+2], self.pixels[x, y-2]]
            grad = sum(abs(lum - sum(v)/3) for v in voisins) / 4
            
            # Si le contraste est fort (> seuil), on ajoute un point
            if grad > 20 or random.random() < 0.01:
                self.points.append(Point(x, y))
                points_trouvés += 1
            tentatives += 1
        
        self.calculer_triangulation()

    def calculer_triangulation(self):
        """[CHAPITRE 3] : Algorithme de Bowyer-Watson pour Delaunay."""
        # Triangle conteneur géant
        st = [Point(-self.w*2, -self.h), Point(self.w*2, -self.h), Point(self.w//2, self.h*2)]
        self.triangles = [Triangle(st[0], st[1], st[2])]

        for p in self.points:
            # Trouver les triangles dont le cercle contient p
            mauvais = [t for t in self.triangles if t.contient_point_dans_cercle(p)]
            
            # Trouver les bords de la cavité formée par ces triangles
            cavité = []
            for t in mauvais:
                for i in range(3):
                    edge = (t.points[i], t.points[(i+1)%3])
                    # Si le côté n'est pas partagé avec un autre triangle "mauvais", c'est un bord
                    partagé = False
                    for t2 in mauvais:
                        if t == t2: continue
                        for j in range(3):
                            e2 = (t2.points[j], t2.points[(j+1)%3])
                            if (edge[0]==e2[0] and edge[1]==e2[1]) or (edge[0]==e2[1] and edge[1]==e2[0]):
                                partagé = True; break
                        if partagé: break
                    if not partagé: cavité.append(edge)
            
            # Remplacer les anciens triangles par des nouveaux reliés à p
            for t in mauvais: self.triangles.remove(t)
            for edge in cavité: self.triangles.append(Triangle(edge[0], edge[1], p))

        # Supprimer les triangles liés au super-triangle de départ
        self.triangles = [t for t in self.triangles if not any(pt in st for pt in t.points)]
        self.calculer_couleurs_et_score()

    def calculer_couleurs_et_score(self):
        """[CHAPITRE 1] : Choix de la couleur et mesure de l'erreur."""
        err_totale = 0
        for t in self.triangles:
            # On prend la couleur au centre de gravité
            cx = int((t.points[0].x+t.points[1].x+t.points[2].x)/3)
            cy = int((t.points[0].y+t.points[1].y+t.points[2].y)/3)
            cx, cy = max(0, min(self.w-1, cx)), max(0, min(self.h-1, cy))
            t.color = self.pixels[cx, cy]
            
            # Évaluation locale de l'erreur (pour le score et l'aide visuelle)
            err_locale = 0
            points_test = [(cx, cy), (int(t.points[0].x), int(t.points[0].y)), (int(t.points[1].x), int(t.points[1].y))]
            for tx, ty in points_test:
                tx, ty = max(0, min(self.w-1, tx)), max(0, min(self.h-1, ty))
                orig = self.pixels[tx, ty]
                err_locale += (t.color[0]-orig[0])**2 + (t.color[1]-orig[1])**2 + (t.color[2]-orig[2])**2
            t.error = math.sqrt(err_locale / 3)
            err_totale += t.error
        
        # Calcul de fidélité pour le challenge pédagogique
        if self.triangles:
            moy_err = err_totale / len(self.triangles)
            self.fidélité = max(0, 100 - (moy_err / 1.5))

    def optimiser(self):
        """Lisse le maillage (Relaxation de Lloyd)."""
        if not self.triangles: return
        nouveaux = self.points[:8] # On fixe le contour
        for i in range(8, len(self.points)):
            p = self.points[i]
            adj = [t for t in self.triangles if p in t.points]
            if adj:
                nx = sum((t.points[0].x+t.points[1].x+t.points[2].x)/3 for t in adj)/len(adj)
                ny = sum((t.points[0].y+t.points[1].y+t.points[2].y)/3 for t in adj)/len(adj)
                nouveaux.append(Point(nx, ny))
            else: nouveaux.append(p)
        self.points = nouveaux
        self.calculer_triangulation()

    def exporter(self):
        """Export SVG version XML."""
        nom = f"rendu_{int(time.time())}.svg"
        with open(nom, "w") as f:
            f.write(f'<svg viewBox="0 0 {self.w} {self.h}" xmlns="http://www.w3.org/2000/svg">\n')
            for t in self.triangles:
                pts = " ".join([f"{int(p.x)},{int(p.y)}" for p in t.points])
                f.write(f'  <polygon points="{pts}" fill="rgb{t.color}" stroke="rgb{t.color}" stroke-width="0.3"/>\n')
            f.write("</svg>\n")
        print(f"Exportation SVG réussie : {nom}")

def dessiner_texte(screen, txt, x, y, size=18, color=(255, 255, 255), center=False):
    font = pygame.font.SysFont("Verdana", size, bold=True)
    surf = font.render(txt, True, color)
    if center:
        rect = surf.get_rect(center=(x, y))
        screen.blit(surf, rect)
    else:
        screen.blit(surf, (x, y))

def menu_demarrage(screen):
    """Menu étudiant pour choisir l'image."""
    imgs = sorted([f for f in os.listdir('.') if f.lower().endswith(('.jpg', '.png', '.bmp'))])
    choix = None
    while choix is None:
        screen.fill((25, 25, 30))
        dessiner_texte(screen, "LE CRISTALIZATEUR D'IMAGES (Projet R506)", 500, 100, 30, (0, 255, 200), True)
        dessiner_texte(screen, "Sélectionnez une photo pour commencer :", 500, 180, 16, (180, 180, 180), True)
        
        for i, nom in enumerate(imgs):
            rect = pygame.Rect(350, 240 + i*40, 300, 32)
            hover = rect.collidepoint(pygame.mouse.get_pos())
            if hover: pygame.draw.rect(screen, (50, 50, 70), rect, border_radius=5)
            dessiner_texte(screen, f"> {nom}", 500, 255 + i*40, 18, (255,255,255) if hover else (140,140,140), True)
            
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and hover: choix = nom
        
        if not imgs:
            dessiner_texte(screen, "(Aucune photo trouvée, déposez des .jpg ici !)", 500, 300, 16, (255, 100, 100), True)
            dessiner_texte(screen, "Appuyez sur ENTRÉE pour continuer quand même", 500, 350, 18, center=True)
            for ev in pygame.event.get():
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN: choix = "demo"

        pygame.display.flip()
    return choix

def main():
    pygame.init()
    W, H = 1000, 750
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Cristalizateur - BUT Info R506")
    
    choix = menu_demarrage(screen)
    gen = GenerateurMaillage(W, H, choix if choix != "demo" else None)
    gen.analyse_bitmap(150)
    
    clock = pygame.time.Clock()
    auto = False
    run = True
    
    while run:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: run = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if ev.button == 1: # Clic gauche : nouveau point manuel
                    gen.points.append(Point(mx, my))
                    gen.calculer_triangulation()
                elif ev.button == 3 and len(gen.points) > 8: # Clic droit : on vire le point le plus proche
                    im_min = -1; d_min = 2000
                    for i in range(8, len(gen.points)):
                        d = (gen.points[i].x-mx)**2 + (gen.points[i].y-my)**2
                        if d < d_min: d_min = d; im_min = i
                    if im_min != -1: gen.points.pop(im_min); gen.calculer_triangulation()
            
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_s: gen.exporter()
                elif ev.key == pygame.K_w: gen.filaire = not gen.filaire
                elif ev.key == pygame.K_r: gen.reset(); gen.analyse_bitmap(150)
                elif ev.key == pygame.K_n: gen.charger_image(gen.img_idx + 1); gen.analyse_bitmap(150)
                elif ev.key == pygame.K_l: gen.optimiser()
                elif ev.key == pygame.K_h: gen.voir_aide = True
                elif ev.key == pygame.K_SPACE: auto = not auto
            elif ev.type == pygame.KEYUP:
                if ev.key == pygame.K_h: gen.voir_aide = False

        if auto and random.random() < 0.2: gen.analyse_bitmap(5)

        # Dessin sur l'écran
        screen.fill((20, 20, 25))
        if gen.voir_aide:
             screen.blit(gen.surface_originale, (0,0))
        else:
            for t in gen.triangles:
                pts = [(p.x, p.y) for p in t.points]
                pygame.draw.polygon(screen, t.color, pts)
                if gen.filaire:
                    # Plus le triangle est imprécis, plus il "clignote" en blanc
                    alpha = min(255, int(t.error * 6))
                    pygame.draw.polygon(screen, (255, 255, 255, alpha), pts, 1)

        # Barre de texte (HUD)
        hud = pygame.Surface((W, 110), pygame.SRCALPHA)
        pygame.draw.rect(hud, (0, 0, 0, 200), (0, 0, W, 110))
        screen.blit(hud, (0, 0))
        
        # Petit calcul de score arbitraire pour le fun
        score = int((gen.fidélité**2) / (len(gen.points)/7))
        
        dessiner_texte(screen, f"🎯 Fidélité Graphique : {gen.fidélité:.1f}%", 20, 15, 24, (255, 220, 0))
        dessiner_texte(screen, f"Source : {gen.nom_actuel}  |  Score Efficacité : {score}", 20, 48, 16, (200, 200, 200))
        dessiner_texte(screen, "[N] Image Suivante | [L] Lisser | [H] Image d'origine | [S] Sauvegarder SVG", 20, 78, 14, (0, 255, 180))

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()
