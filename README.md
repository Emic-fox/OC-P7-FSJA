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
- [Déployer à partir des images publiées](#déployer-à-partir-des-images-publiées)
- [Monitoring (Elastic Stack)](#monitoring-elastic-stack)
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
├── monitoring/                  # stack Elastic (Filebeat, Logstash, Elasticsearch, Kibana), hors CI
├── docker-compose.yml           # lancement de l'application complète (construction depuis les sources)
└── docker-compose.deploy.yml    # déploiement à partir des images publiées sur GHCR
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

## Déployer à partir des images publiées

À chaque fusion sur `main`, la CI publie les deux images sur GitHub Container Registry, avec deux étiquettes : `latest` et le SHA court du commit.

- `ghcr.io/emic-fox/microcrm-back`
- `ghcr.io/emic-fox/microcrm-front`

Le fichier `docker-compose.deploy.yml` lance l'application à partir de ces images, sans construction : il suffit seul, sans les sources.

```shell
docker compose -f docker-compose.deploy.yml pull
docker compose -f docker-compose.deploy.yml up -d
```

Pour déployer une version précise (retour arrière, par exemple), indiquer son SHA court :

```shell
MICROCRM_TAG=<sha> docker compose -f docker-compose.deploy.yml up -d
```

Les adresses, le certificat et les données sont les mêmes qu'avec `docker-compose.yml` (voir ci-dessus).

## Monitoring (Elastic Stack)

Les logs des conteneurs de MicroCRM sont centralisés dans une stack Elastic 9.5 (anciennement ELK), lancée à part de l'application et hors CI :

```text
conteneurs back et front -> Filebeat -> Logstash -> Elasticsearch -> Kibana
```

En conteneur, le back écrit ses logs applicatifs et son journal d'accès en JSON (profil Spring `docker`), et le front ses logs d'accès Caddy. Logstash les range dans les data streams `logs-microcrm.back-default` et `logs-microcrm.front-default`. Le détail est commenté dans les fichiers de `monitoring/`.

> Sécurité d'Elasticsearch désactivée pour l'instant, ports publiés sur `127.0.0.1` : à réserver au poste local.

### Lancement

Prévoir environ 4,5 Go de mémoire pour Docker en plus de l'application (Windows : paramètre `memory` de `.wslconfig`).

```shell
docker compose up -d --build                              # application
docker compose -f monitoring/docker-compose.yml up -d     # stack Elastic
```

Kibana : http://localhost:5601 (une à deux minutes au premier démarrage).

Pour alimenter les tableaux de bord :

- activité normale : utiliser l'application (listes, fiches, création et modification) ;
- erreur 404 : ouvrir http://localhost:8080/persons/999999 ;
- pic d'activité (Git Bash) : `for i in $(seq 300); do curl -s -o /dev/null http://localhost:8080/persons & done; wait`.

Si aucun log n'arrive : `docker compose -f monitoring/docker-compose.yml logs filebeat logstash`.

### Arrêt

```shell
docker compose -f monitoring/docker-compose.yml down       # logs conservés (volume es-data)
docker compose -f monitoring/docker-compose.yml down -v    # logs supprimés
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
| Images Docker – construction | Construction des deux images, nommées comme sur GHCR, et transmission aux jobs suivants |
| Images Docker – smoke test | Démarrage avec `docker-compose.deploy.yml` et vérification que l'API et le front répondent |
| Images Docker – scan Trivy | Vulnérabilités, secrets et mauvaises configurations, résultats dans l'onglet Security |
| Images Docker – publication sur GHCR | Sur `main` uniquement, une fois toute la chaîne réussie : publication des images testées et analysées (`latest` et SHA court) |

Les résultats des tests sont résumés dans la page de chaque exécution, et les rapports sont téléchargeables en artefacts. Les résultats Trivy sont envoyés dans l'onglet **Security > Code scanning**.

### Contrôles bloquants

- Échec de compilation ou d'un test ;
- Échec du smoke test : l'application assemblée ne démarre pas ou ne répond pas ;
- Vulnérabilité **CRITICAL** avec correctif disponible dans une image, secret ou mauvaise configuration **CRITICAL** dans le dépôt (Trivy).

Contrôles temporairement non bloquants (voir la documentation technique) :

- quality gates SonarQube : variable `SONAR_QUALITYGATE_WAIT` dans le workflow ;
- `npm audit --audit-level=high` : vulnérabilités connues dans les dépendances Angular 17.
- seuil Trivy de l'image back : vulnérabilités CRITICAL de Tomcat et Spring embarqués par Spring Boot 3.2.5, à rendre bloquant après sa mise à jour.

Les jobs « Back-end – build et tests », « Front-end – build et tests », « Images Docker – construction », « Images Docker – smoke test » et « Images Docker – scan Trivy » sont obligatoires pour fusionner une PR dans `main`.

### Configuration du dépôt

| Nom | Type | Rôle |
| --- | --- | --- |
| `SONAR_TOKEN` | Secret | Jeton d'analyse SonarQube Cloud |
| `SONAR_ORGANIZATION` | Variable | Organisation SonarQube Cloud |
| `SONAR_PROJECT_KEY_BACK` | Variable | Clé du projet SonarQube du back |
| `SONAR_PROJECT_KEY_FRONT` | Variable | Clé du projet SonarQube du front |

À activer également : **Settings > Advanced Security > Dependency graph** (nécessaire à l'envoi du graphe de dépendances Gradle).

La publication sur GHCR utilise le `GITHUB_TOKEN` fourni par GitHub Actions : aucun secret supplémentaire n'est nécessaire.

Les analyses SonarQube et l'envoi des résultats Trivy sont ignorés sur les PR provenant de forks et de Dependabot, qui n'ont pas accès aux secrets et disposent d'un jeton en lecture seule.

## Mises à jour des dépendances

Dependabot (`.github/dependabot.yml`) propose chaque lundi à 3 h UTC, deux heures après l'exécution hebdomadaire de la CI, des pull requests de mise à jour pour :

- les dépendances Gradle (`back`) ;
- les dépendances npm (`front`) ;
- les actions GitHub ;
- les images Docker (`back`, `front`).

Les montées de version majeures d'Angular, de Spring Boot, de Node.js et de Java (images `node` et `eclipse-temurin`) sont exclues : elles font l'objet d'un plan de mise à jour dédié.
