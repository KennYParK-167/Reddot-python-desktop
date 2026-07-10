# REDDOT - Desktop.


10. SUJET ARSB DE VEILLE TECHNOLOGIQUE POUR L1.  
Theme : Chat en Ligne Simple.

```markdown
# Sujet 1 : Chat en Ligne Simple

## Description
Développement d'une application de messagerie instantanée permettant à plusieurs utilisateurs de communiquer en temps réel via un réseau local ou Internet. L'application repose sur une architecture client-serveur assurant l'échange des messages entre les utilisateurs connectés et intègre une base de données pour l'enregistrement des conversations avec horodatage des messages.

---

## Technologies
* Python
* Tkinter
* Socket TCP
* Threads
* SQLite ou MySQL

---

## Fonctionnalités minimales
* Connexion de plusieurs utilisateurs
* Envoi et réception de messages en temps réel
* Gestion d'un serveur central
* Interface graphique simple et conviviale
* Affichage des utilisateurs connectés
* Enregistrement des messages dans une base de données
* Horodatage automatique des conversations
* Consultation de l'historique des discussions
* Gestion des utilisateurs connectés
```

> Une application de chat commune, sobre, minimaliste contenant qu'un salon pour tout les utilisateurs. <br /> <br />
> ![Image de reprensentation du projet](./assets/Capture%20d'écran%202026-07-09%20144532.png)

<br />

## Contributeurs du projets :
```markdown
- RINDRANIRINA Anthony Stehano | L1C - N'375/LA/25-26 (Chef de Projet/Groupe)
- RABEZORO Anjaritina Bryan | L1C | N'370/LA/25-26
- BE Yolin Brayane | L1C | N'368/LA/25-26
- ANDRINIAINA Henintsoa Anthonny | L1C | N'389/LA/25-26
- RASAMIMANANA Heritiana Hiarilala | L1C | N'399/LA/25-26
- RANDRIANOELISON Jerinirina Fiderana | L1C | N'391/LA/25-26 
```

<br />


## Aperçu du design.

> Lien du design PENPOT : [Penpot design Link](https://design.penpot.app/#/workspace?team-id=511bd401-aa1d-80ff-8008-3373a9bae12e&file-id=f2b396a6-c4f1-8031-8008-4ccedff9943c&page-id=f2b396a6-c4f1-8031-8008-4ccedff9943d.)

Page d'inscription :  
![Inscription Page :](./assets/Capture%20d'écran%202026-07-09%20131815.png)

<br />
<br />

Page de Connexion :  
![Connexon Page :](./assets/Capture%20d'écran%202026-07-09%20131800.png)

<br />
<br />

Page de Discussion :  
![Chat Page :](./assets/Capture%20d'écran%202026-07-09%20131843.png)

<br />
<br />

Page d'Administration :  
![Admin Page :](./assets/Capture%20d'écran%202026-07-09%20131830.png)

<br />
<br />

## Fonctionnalités :

- **Authentification Sécurisée** : Connexion via JWT.
- **Mode Sombre Natif** : Interface optimisée pour le confort visuel et tres basique.
- **Synchronisation Temps Réel** : Base de données mise à jour instantanément.
- **Desktope** : Application seulement sur Ordinateur ayant Python.

<br />

## Stack Technique Utiliser :

- **Language** : Python.
- **Frontend** : TKinter
- **Backend** : FastAPI
- **Style** : TKinter Syle

<br />

## Installation & Utilisation avec Lancement :

### Prérequis
- Python
- Pip install lib

### Lancement Local

1. **Cloner le dépôt :**
   ```bash
   git clone https://github.com/KennYParK-167/Reddot-python-desktop
   cd Reddot-python-desktop
   ```
2. **Lancement des fichiers :**
    - 1er : APP_REQ.bat - Pour installer les dependances lier a Python et les Libs.
    - 2eme : APP_API.bet - Lancer le et ne le quitter pas durant l'utilisation de l'application car il permet la liaison entre le DB et l'APP.
    - 3eme : APP.bat - L'application en lui même (A vraiment lancer avec l'APP_API.bat)


<br />

## Structure du Projet (Optionnel mais pro)

```markdown
## 📁 Structure du Projet

```text
├── /Reddot-python-desktop
│   ├── Backups/        # Le backups fait par IA pour l'init du projet.
│   ├── client/         # Contenant l'app principal. (app.py)
│   ├── db/             # Gestion du SQL distant.
│   └── server/         # Backend de l'app avec les method_fastapi.
```

<br />


## Licence & Contributeurs
```markdown
## 📄 Licence

Distribué sans sous licence.
