# UniRide-SME
API et objets métiers de l'application web UniRide

[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](http://forthebadge.com) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white) ![PostgreSQL Badge](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=fff&style=for-the-badge)![Pytest Badge](https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=fff&style=for-the-badge)
![JSON Web Tokens Badge](https://img.shields.io/badge/JSON%20Web%20Tokens-000?logo=jsonwebtokens&logoColor=fff&style=for-the-badge)
![forthebadge](https://forthebadge.com/images/badges/built-by-developers.svg) 

# Prérequis

1. Installez [python](https://www.python.org/downloads/)

2. Clonez le dépôt sur votre machine locale :
```bash
$ git clone https://github.com/DUT-Info-Montreuil/UniRide-SME.git
```

3. Modifier les variables d'environnement disponible dans `uniride-backend-template.env` qui se trouve à la racine pour le bon fonctionnement du site.
   Ces variables d'environnement doivent imperativement etre changer :
   
  ## Configuration API Google Maps 
  - `GOOGLE_API_KEY=AIzdz74yBMre5LC2BJ2f-HFPPhYISSIu0mSSthtrt2Gs`
  
  ## Configuration de l'adresse de l'université
  - `UNIVERSITY_STREET_NUMBER=140`
  - `UNIVERSITY_STREET_NAME=Rue de la Nouvelle France`
  - `UNIVERSITY_POSTAL_CODE=93100`
  - `UNIVERSITY_CITY=Montreuil`
  - `UNIVERSITY_EMAIL_DOMAIN=iut.univ-paris8.fr`
  - `FRONT_END_URL=https://127.0.0.1:5050/`
  
  ## Serveur mail
  - `MAIL_USERNAME=uniride.uniride@gmail.com `
  - `MAIL_PASSWORD=XXX`
  - `MAIL_SERVER=smtp.gmail.com`
  - `SECRET_KEY=XXX`
  - `SECURITY_PASSWORD_SALT=XXX`
  
  ## Dossier de documents
  - `PFP_UPLOAD_FOLDER=chemin\vers\votre\documents\pft`
  - `LICENSE_UPLOAD_FOLDER=chemin\vers\votre\documents\license`
  - `ID_CARD_UPLOAD_FOLDER=chemin\vers\votre\documents\id_card`
  - `SCHOOL_CERTIFICATE_UPLOAD_FOLDER=chemin\vers\votre\documents\school_certificate`
  - `INSURANCE_UPLOAD_FOLDER=chemin\vers\votredocuments\insurance`
  
  ## Configuration token JWT
  - `JWT_SALT=XXX`
  - `JWT_SECRET_KEY=XXX`
  
  
  ## Attente redis
  - `RQ_REDIS_URL=redis://localhost:6379/0 `
  
  ## Cache redis
  - `CACHE_REDIS_HOST=localhost`
  - `CACHE_REDIS_PORT=6379`
  
  ## Base de données
  - `DB_HOST=ip_DB`
  - `DB_NAME=uniride`
  - `DB_USER=uniride`
  - `DB_PWD=XXX`
  - `DB_PORT=5432`
  
  ## Configuration FLask 
  - `FLASK_DEBUG = true`
  - `FLASK_HOST = 0.0.0.0`
  - `FLASK_PORT = 5050`
    
  ## Certificats
  - `CERTIFICATE_CRT_FOLDER=chemin\vers\votre\certificat.crt`
  - `CERTIFICATE_KEY_FOLDER=chemin\vers\votre\clé.key`
   



# Installer les dépendances 
4. Exécutez la commande `pip install .` à l'intérieur du dossier cloné :
```bash
$ pip install .
```

# Lancer le projet
5. Pour lancer le projet il vous faut aller à la racine et en faisant :
```bash
$ python uniride_sme/rest_api.py
```

# Déploiement avec docker 
Pour lancer entièrement l'application UniRide avec docker, vous pouvez vous référer à ce read me [Docker](https://github.com/DUT-Info-Montreuil/UniRide-DEPLOYMENT/blob/main/README.md).

# License
Sous license GNU [GNU GPL3](https://opensource.org/license/gpl-3-0/).

# Besoin d'aide ?
Pour obtenir davantage d'aide sur Python, utilisez la commande `pip --help` ou consultez le README d'Angular CLI [python](https://github.com/python/mypy/blob/master/README.md).

Pour obtenir davantage d'aide sur Flask, consultez le site [Flask](https://flask.palletsprojects.com/en/3.0.x/).

## Auteur
- [CHOUCHANE Rayan / Nayren23](https://github.com/Nayren23)
- [HAMIDI Yassine / TheFanaticV2](https://github.com/TheFanaticV2)
- [BOUAZIZ Ayoub / Ayoub-Bouaziz](https://github.com/Ayoub-Bouaziz)
- [YANG Steven / G8LD](https://github.com/G8LD)
- [FAURE Grégoire / Pawpawzz](https://github.com/Pawpawzz)