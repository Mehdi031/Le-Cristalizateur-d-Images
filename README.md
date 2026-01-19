# 💎 Le Cristalizateur d'Images

Bienvenue sur mon projet de fin de module **R506 (Traitement d'Image)**.
L'objectif ? Créer un pont entre le pixel et le vecteur. Ce programme prend n'importe quelle photo et la redessine sous forme de vitrail géométrique (style **Low-Poly**), le tout calculé en temps réel.

## 🎯 L'Objectif : Le Challenge de Fidélité

Ce n'est plus seulement un outil de dessin, c'est un **challenge d'optimisation**. Votre but est d'atteindre **98% de Fidélité Visuelle** avec le moins de triangles possible.

*   **Mesure technique** : Le programme calcule l'erreur quadratique moyenne (MSE) entre vos triangles et l'image originale.
*   **Score d'Efficacité** : Plus vous utilisez de points pour le même résultat, plus votre score baisse. Soyez stratégique !
*   **Aide au diagnostic** : En mode filaire (`W`), les triangles les plus "imprécis" (qui s'éloignent le plus de la photo) s'affichent plus brillamment pour vous guider.

Au lieu d'utiliser des filtres tout faits, j'ai voulu recréer la logique "à la main" :

* **Intelligence du détail** : Le programme ne pose pas les points au hasard. Il "regarde" l'image, détecte les contours et les zones contrastées pour placer plus de détails là où c'est nécessaire (comme sur les yeux d'un visage).
* **100% Algo Maison** : Pas de solution de facilité avec `numpy` ou `scipy`. La triangulation (Delaunay) et les calculs matriciels sont codés en Python pur pour montrer la mécanique interne.
* **C'est vivant** : Ce n'est pas juste un script qui tourne. Vous pouvez cliquer pour ajouter des points, sculpter le maillage et voir l'image évoluer sous vos yeux.

## 🎮 Comment jouer avec ?

### Prérequis

Il vous faut juste Python et deux petites librairies graphiques :

```bash
pip install pygame pillow

```

### Lancement

1. Prenez une image (photo, paysage...), renommez-la `input.jpg` et mettez-la dans le dossier.
2. Lancez la magie :
```bash
python cristalizateur.py

```


3. **Commandes :**
* `Touche N` : **Change d'image** (cycle les fichiers JPG/PNG du dossier).
* `Clic Gauche` : Ajoutez du détail manuellement.
* `Clic Droit` : Simplifiez la zone (supprime un point).
* `Touche L` : **Relaxe le maillage** (rend les triangles plus beaux/équilibrés).
* `Espace` : Active l'évolution **Automatique**.
3. **Commandes Spéciales :**
* `Touche H` (Maintenir) : Affiche l'image originale (pour comparer).
* `Touche L` : Optimise la position des points (Relaxation de Lloyd).
* `Touche N` : Changer d'image.
* `Touche S` : Exporter le SVG et valider votre score.



*(Note : Si vous n'avez pas d'image sous la main, le programme générera un dégradé synthétique pour ne pas planter).*

## 🎓 Ce que ce code démontre (Liens R506)

Ce projet regroupe les 4 grands axes du cours :

* **🎨 La Couleur (Chap. 1)** : Le programme échantillonne la moyenne des couleurs (RGB) au cœur de chaque triangle pour un rendu fidèle.
* **🖼️ Le Bitmap (Chap. 2)** : Manipulation directe des pixels et implémentation manuelle de filtres pour analyser la luminance et les contrastes.
* **📐 Le Vectoriel (Chap. 3)** : Tout est géré sous forme de coordonnées et de polygones, exportables en XML/SVG propre.
* **⚡ L'Animation (Chap. 4)** : Utilisation d'une boucle de rendu fluide et gestion événementielle (souris/clavier) via Pygame.

---

*Réalisé par [Ton Nom] - BUT Informatique 3ème Année.*