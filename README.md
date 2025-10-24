GestionVisiteurs — README
Version : 1.0.0

1) Présentation
GestionVisiteurs est une application desktop (Kivy / KivyMD) pour gérer des visiteurs et partager des documents entre utilisateurs.
Ce paquet installe l'exécutable et les ressources nécessaires.

2) Prérequis système
- Windows 10/11 (64-bit recommandé)
- Visual C++ Redistributable (MSVC) installé (si absent, installez depuis Microsoft)
- Espace disque : ~50 Mo (peut varier selon vos données)

3) Installation
- Lancez l'installateur fourni (GestionVisiteursInstaller.exe).
- Par défaut l'application sera installée dans C:\Program Files\GestionVisiteurs.
- Un raccourci sera créé dans le menu Démarrer. Optionnellement un raccourci Bureau si demandé.

4) Premier démarrage
- Au premier démarrage, l'application crée la base de données utilisateur dans :
  %APPDATA%\GestionVisiteurs\gestion_visiteurs.db
- Si un modèle de base est fourni, il sera copié automatiquement.
- Connectez-vous avec un compte existant ou créez un compte administrateur suivant la procédure de votre organisation.

5) Emplacement des fichiers importants
- Exécutable : C:\Program Files\GestionVisiteurs\GestionVisiteurs.exe
- Ressources incluses : C:\Program Files\GestionVisiteurs\pictures\
- Base de données utilisateur (persistante) : %APPDATA%\GestionVisiteurs\gestion_visiteurs.db

6) Mise à jour
- Pour mettre à jour, fermez l'application, installez la nouvelle version via l'installateur fourni.
- L'installation ne doit pas écraser la base de données dans %APPDATA% (préservée).

7) Dépannage rapide
- L'application ne démarre pas / erreur à l'ouverture :
  - Lancez l'exécutable depuis une console pour voir les messages d'erreur.
  - Vérifiez la présence de Visual C++ Redistributable.
  - Désactivez temporairement l'antivirus si l'exe est bloqué.
- Erreurs de base de données :
  - Vérifiez que le dossier %APPDATA%\GestionVisiteurs\ est accessible en écriture.
  - Supprimez le fichier gestion_visiteurs.db corrompu (après sauvegarde), relancez pour recréer.
- Problèmes d'icônes / rendu graphique :
  - Assurez-vous que les fichiers .ico/.png sont présents dans le dossier pictures du programme.
  - Si erreurs liées à Kivy (GL backend), contactez le support ou lancez depuis une machine de test.

8) Notifications
- L'application utilise des notifications locales (système) pour informer d'un nouveau visiteur ou document.
- Assurez-vous que les notifications Windows sont activées pour l'application.

9) Désinstallation
- Utilisez "Ajouter ou supprimer des programmes" pour désinstaller.
- La base de données dans %APPDATA%\GestionVisiteurs n'est pas supprimée automatiquement (sauvegardez si nécessaire).

10) Support & contact
- Responsable : Diallo Mamadou Tahirou mrtdsow@outlook.com
- Fournir : version de l'application, capture écran de l'erreur, fichier journal (si existant).

11) Licence
- Aucune licence.

Merci d'avoir choisi GestionVisiteurs.