<p align="center">
   <img src="./front/src/favicon.png" width="192px" />
</p>

# MicroCRM (P7 - Développeur Full-Stack - Java et Angular - Mettez en œuvre l'intégration et le déploiement continu d'une application Full-Stack)

MicroCRM est une application de démonstration basique ayant pour objectif de servir de socle pour le module "P7 - Développeur Full-Stack".

L'application MicroCRM est une implémentation simplifiée d'un ["CRM" (Customer Relationship Management)](https://fr.wikipedia.org/wiki/Gestion_de_la_relation_client). Les fonctionnalités sont limitées à la création, l'édition et la visualisation des individus liés à des organisations.

![Page d'accueil](./misc/screenshots/screenshot_1.png)
![Édition de la fiche d'un individu](./misc/screenshots/screenshot_2.png)

## Sommaire

- [Code source](#code-source)
- [Démarrer avec Docker Compose](#démarrer-avec-docker-compose)
- [Intégration continue](#intégration-continue)
- [Mises à jour des dépendances](#mises-à-jour-des-dépendances)

## Code source

### Organisation

Ce [monorepo](https://en.wikipedia.org/wiki/Monorepo) contient les 2 composantes du projet "MicroCRM" :

- La partie serveur (ou "backend"), en Java 17 / Spring Boot 3, construite avec Gradle ;
- La partie cliente (ou "frontend"), en Angular 17.

```text
.
├── .github/
│   ├── workflows/main.yaml      # pipeline CI
│   ├── scripts/test_summary.py  # résumé des tests dans l'interface GitHub
│   └── dependabot.yml           # mises à jour automatiques des dépendances
├── back/                        # API Spring Boot (+ Dockerfile)
├── front/                       # application Angular (+ Dockerfile, Caddyfile)
└── docker-compose.yml           # lancement de l'application complète
```

### Démarrer avec les sources

#### Serveur

##### Dépendances

- [OpenJDK 17](https://openjdk.org/) (version utilisée par la CI et les images Docker)

##### Procédure

1. Se positionner dans le répertoire `back` avec une invite de commande :

   ```shell
   cd back
   ```

2. Construire le JAR (les tests sont exécutés pendant le build) :

   ```shell
   # Sur Linux
   ./gradlew build

   # Sur Windows
   gradlew.bat build
   ```

3. Démarrer le service :

   ```shell
   java -jar build/libs/microcrm-0.0.1-SNAPSHOT.jar
   ```

L'API est alors disponible sur http://localhost:8080. Sans configuration, la base HSQLDB est en mémoire : les données sont réinitialisées à chaque démarrage.

#### Client

##### Dépendances

- [Node.js 20](https://nodejs.org/) (20.20.2 dans la CI et l'image Docker), avec npm

##### Procédure

1. Se positionner dans le répertoire `front` avec une invite de commande :

   ```shell
   cd front
   ```

2. (La première fois seulement) Installer les dépendances NodeJS :

   ```shell
   npm ci
   ```

3. Démarrer le service de développement :

   ```shell
   npx @angular/cli serve
   ```

Puis ouvrir l'URL http://localhost:4200 dans votre navigateur. L'API doit être démarrée sur http://localhost:8080 (URL définie dans `front/src/app/config.ts`).

### Exécution des tests

#### Client

**Dépendances**

- Google Chrome ou Chromium

Dans votre terminal :

```shell
cd front

# Mode interactif (relance les tests à chaque modification)
CHROME_BIN=</path/to/google/chrome> npm test

# Exécution unique, sans fenêtre, avec couverture (mode utilisé par la CI)
CHROME_BIN=</path/to/google/chrome> npm run test:ci
```

Rapports produits par `test:ci` :

- résultats JUnit : `front/test-results/junit.xml` ;
- couverture : `front/coverage/microcrm/` (HTML et `lcov.info`).

#### Serveur

Dans votre terminal :

```shell
cd back
./gradlew test
```

Rapports produits :

- résultats des tests : `back/build/reports/tests/test/index.html` ;
- couverture JaCoCo : `back/build/reports/jacoco/test/html/index.html` (et `jacocoTestReport.xml`).

## Démarrer avec Docker Compose

### Dépendances

- [Docker](https://docs.docker.com/get-docker/) avec Docker Compose v2 (inclus dans Docker Desktop)
- Ports 80, 443 et 8080 libres sur la machine

### Lancement

À la racine du dépôt :

```shell
docker compose up -d --build
```

- Application : https://localhost (http://localhost redirige vers HTTPS)
- API : http://localhost:8080

Le front ne démarre que lorsque le back est en bonne santé (`/actuator/health`). Pour suivre l'état des services :

```shell
docker compose ps         # colonne STATUS : "healthy" quand le service est prêt
docker compose logs -f    # journaux des deux services
```

### Certificat HTTPS

Le certificat est émis par l'autorité de certification interne de Caddy : le navigateur affiche un avertissement au premier accès. Pour le supprimer, récupérer le certificat racine puis l'importer dans le magasin de confiance de votre système ou navigateur :

```shell
docker compose cp front:/data/caddy/pki/authorities/local/root.crt ./caddy-root.crt
```

### Données

La base HSQLDB est stockée en mode fichier dans le volume `back-data` : les données sont conservées entre deux redémarrages et deux reconstructions d'image. Les données de démonstration ne sont chargées que si la base est vide.

```shell
docker compose down       # arrête les conteneurs, conserve les données
docker compose down -v    # arrête les conteneurs ET supprime les volumes (données et certificats)
```

### Images

| Service | Dockerfile | Image de base (exécution) | Contenu |
| --- | --- | --- | --- |
| `back` | `back/Dockerfile` | `eclipse-temurin:17-jre-alpine` | JAR Spring Boot, utilisateur non root |
| `front` | `front/Dockerfile` | `caddy:2.11-alpine` | Fichiers Angular compilés servis en HTTPS, utilisateur non root |

Chaque Dockerfile est multi-stage et autonome : il compile l'application à partir des sources. Une image peut être construite seule :

```shell
docker build -t microcrm-back back
docker build -t microcrm-front front
```

## Intégration continue

La pipeline est définie dans `.github/workflows/main.yaml` (GitHub Actions).

### Déclenchement

- push sur `main` ;
- pull request vers `main` (chaque nouveau commit annule l'exécution en cours de la PR) ;
- chaque lundi à 1 h UTC (détection des nouvelles vulnérabilités sans changement de code) ;
- manuellement, depuis l'onglet Actions (`workflow_dispatch`).

### Jobs

| Job | Rôle |
| --- | --- |
| Back-end – build et tests | Compilation Gradle, tests, couverture JaCoCo, envoi du graphe de dépendances à GitHub (sur `main`) |
| Front-end – build et tests | `npm ci`, `npm audit`, build Angular, tests Karma en mode headless, couverture |
| Back-end – analyse SonarQube | Analyse de qualité du back sur SonarQube Cloud |
| Front-end – analyse SonarQube | Analyse de qualité du front sur SonarQube Cloud |
| Images Docker – build et scan Trivy | Construction des deux images, scan Trivy (vulnérabilités, secrets, mauvaises configurations) |

Les résultats des tests sont résumés dans la page de chaque exécution, et les rapports sont téléchargeables en artefacts. Les résultats Trivy sont envoyés dans l'onglet **Security > Code scanning**.

### Contrôles bloquants

- Échec de compilation ou d'un test ;
- Vulnérabilité **CRITICAL** avec correctif disponible dans une image, secret ou mauvaise configuration **CRITICAL** dans le dépôt (Trivy).

Contrôles temporairement non bloquants (voir la documentation technique) :

- quality gates SonarQube : variable `SONAR_QUALITYGATE_WAIT` dans le workflow ;
- `npm audit --audit-level=high` : vulnérabilités connues dans les dépendances Angular 17.

Les jobs « Back-end – build et tests » et « Front-end – build et tests » sont obligatoires pour fusionner une PR dans `main`.

### Configuration du dépôt

| Nom | Type | Rôle |
| --- | --- | --- |
| `SONAR_TOKEN` | Secret | Jeton d'analyse SonarQube Cloud |
| `SONAR_ORGANIZATION` | Variable | Organisation SonarQube Cloud |
| `SONAR_PROJECT_KEY_BACK` | Variable | Clé du projet SonarQube du back |
| `SONAR_PROJECT_KEY_FRONT` | Variable | Clé du projet SonarQube du front |

À activer également : **Settings > Advanced Security > Dependency graph** (nécessaire à l'envoi du graphe de dépendances Gradle).

Les analyses SonarQube et l'envoi des résultats Trivy sont ignorés sur les PR provenant de forks et de Dependabot, qui n'ont pas accès aux secrets et disposent d'un jeton en lecture seule.

## Mises à jour des dépendances

Dependabot (`.github/dependabot.yml`) propose chaque lundi à 3 h UTC, deux heures après l'exécution hebdomadaire de la CI, des pull requests de mise à jour pour :

- les dépendances Gradle (`back`) ;
- les dépendances npm (`front`) ;
- les actions GitHub ;
- les images Docker (`back`, `front`).

Les montées de version majeures d'Angular, de Spring Boot, de Node.js et de Java (images `node` et `eclipse-temurin`) sont exclues : elles font l'objet d'un plan de mise à jour dédié.
