# 💎 Projet R506 : Le Cristalizateur d'Images

Salut ! Voici mon projet pour le module de **Traitement d'Image (R506)**. 
L'idée était de créer un programme qui transforme n'importe quelle photo en une sorte de vitrail géométrique (un rendu **Low-Poly**) en utilisant des algorithmes de triangulation.

## 🎯 C'est quoi l'objectif ?

C'est pas juste un filtre "artistique". Le vrai but, c'est d'arriver à reconstruire l'image avec le **moins de triangles possible** tout en restant super fidèle à l'original.

*   **Le score de Fidélité** : Le programme compare en temps réel mes triangles avec la vraie photo (calcul d'erreur MSE). Le but est de dépasser les **98%** de ressemblance.
*   **Efficacité** : Si je mets 5000 points pour avoir 98%, c'est facile. Le challenge, c'est d'y arriver avec seulement 400 ou 500 points en les plaçant intelligemment (là où il y a des détails).
*   **Aide visuelle** : Quand j'affiche le maillage (`W`), les triangles les plus "mauvais" s'éclairent pour me dire où je dois rajouter du détail.

---

## 🚀 Ce que j'ai implémenté

1.  **Menu de départ** : Une petite interface pour choisir sur quelle photo on veut bosser (j'en ai mis 5 pour tester : Cyberpunk, Forêt, Portrait, etc.).
2.  **Analyse de Contours (Chapitre 2)** : J'ai codé une détection de gradient pour que le script place automatiquement les points sur les bords et les zones importantes.
3.  **Triangulation de Delaunay (Chapitre 3)** : C'est le gros morceau. Tout est codé en Python pur avec l'algorithme de **Bowyer-Watson** (pas de librairies toutes faites !).
4.  **Optimisation de Lloyd** : Une fonction pour rééquilibrer le maillage et le rendre plus propre visuellement.
5.  **Export SVG** : On peut sauvegarder le résultat en vectoriel pour pouvoir l'agrandir à l'infini sans perdre de qualité.

---

## 🎮 Comment ça marche ?

### Commandes simples :
*   **Clic Gauche** : Ajouter un point là où on veut plus de précision.
*   **Clic Droit** : Supprimer un point si on a été trop gourmand.
*   **Touche H (Hint)** : Garder appuyé pour comparer avec la photo d'origine.
*   **Touche L (Lisser)** : Équilibre les triangles pour un rendu plus harmonieux.
*   **Touche N (Next)** : Passer à l'image suivante dans la galerie.
*   **Touche S (Save)** : Exporte ton chef-d'œuvre en format `.svg`.

---

## 🛠️ Installation

Juste deux petites librairies à installer (Pygame pour l'interface et Pillow pour gérer les pixels) :

```bash
pip install pygame pillow
```

Et pour lancer le projet :
```bash
python cristalizateur.py
```

---
*Réalisé dans le cadre du BUT Informatique - 3ème année.*