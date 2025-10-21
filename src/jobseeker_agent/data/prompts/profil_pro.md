# Sources annexes
[[Trajectoire et perspectives#RL vs RO]]
[[Thèse méthode et enseignements#Compétences que j'ai apprise]]
# Profil
## 1. Titre et Positionnement Principal

**Ingénieur de Recherche en IA**
Spécialisé dans les **systèmes de décision autonomes** pour des applications complexes (défense, robotique), avec une expertise au croisement de la **recherche opérationnelle/optimisation** et le **deep reinforcement learning**, complétée par une expérience pratique en **Computer Vision**.

## 2. Accroches / Pitchs possibles
### Pitch 1 : Pour Grand Groupe (Défense/Aéro)
- **Angle d'attaque** : Stabilité, expertise profonde, connaissance du domaine.
- **Pitch** : "Docteur spécialisé dans les systèmes de décision pour la défense. Durant ma thèse chez Thales sur le projet FCAS, j'ai conçu des algorithmes d'optimisation (RO/RL) qui ont amélioré les performances des systèmes de 33%."
Mettre en avant la capacité à travailler sur des projets complexes dans des environnements structurés. Mentionner le travail d'équipe, la fiabilité et l'adaptabilité. Aligner mes objectifs avec la mission ou les projets de l'entreprise.
### Pitch 2 : Pour Startup (Polyvalence et Autonomie)
- **Angle d'attaque** : Capacité à apprendre vite, à être autonome et à connecter plusieurs domaines.
- **Pitch** : "Mon profil est polyvalent. J'ai un socle théorique solide en algorithmes de décision (RO, RL), et j'ai prouvé ma capacité à monter en compétence et à livrer un projet technique complet et complexe dans un nouveau domaine comme la Computer Vision. Je suis un 'problem-solver' autonome, capable de faire le pont entre la R&D et l'implémentation."
### Pitch 3 : Pour Rôle "Tech Généraliste" (Mise en avant de la méthode)
- **Angle d'attaque** : Mettre en avant la capacité à résoudre des problèmes, quelle que soit la technologie.
- **Pitch** : "Bien que mon cœur d'expertise soit les systèmes de décision, ma véritable force est ma méthode pour aborder un problème technique de A à Z. Mon projet en Computer Vision en est le meilleur exemple : parti de zéro, j'ai mené une démarche itérative et rigoureuse pour construire une solution performante. C'est cette capacité à apprendre, structurer et résoudre que je peux appliquer à de nouveaux défis, qu'il s'agisse de travailler avec des LLMs, sur de la création de site web, ou toute autre problématique."
### Pitch 4 : Le Pitch "Général" (Pour toute situation)
- **Angle d'attaque** : Équilibré et concis.
- **Pitch** : "Je suis un chercheur-ingénieur spécialisé dans les systèmes de décision autonomes. Mon profil combine une expertise théorique en recherche opérationnelle et reinforcement learning, acquise durant ma thèse, et une expérience pratique en Computer Vision que j'ai développée via un projet personnel poussé. Je cherche à appliquer cette double compétence à des problèmes complexes."
## 3. Domaines de Compétences : Le Matériau Brut
### A. Recherche Opérationnelle / Optimisation (Thèse)
- **Postulat / Doutes (Le point de départ)** : Je n'ai pas de formation initiale spécialisée en RO. J'ai commencé ma thèse avec un bagage mathématique que je considérais comme fébrile, ce qui a été un défi majeur au début.
- **Présentation / Forces (La trajectoire et les acquis)** : Ma thèse a été une montée en compétence intensive et autonome. En partant de zéro, j'ai acquis une compréhension solide des concepts de la RO (problèmes d'optimisation, simplex, branch & bound...). Mon doctorat prouve ma capacité à m'approprier un domaine théorique exigeant, à le maîtriser et à l'appliquer pour résoudre un problème industriel complexe. Cette expérience m'a apporté une grande rigueur dans la modélisation mathématique, la conduite d'expérimentations et la communication scientifique. C'est la preuve de ma résilience et de ma capacité à transformer une faiblesse en expertise.
- **Détails Techniques & Réalisations Concrètes** :
    - **Problématique maîtrisée** : Optimisation combinatoire stochastique (non-linéaire en nombres entiers) pour l'allocation de ressources d'un radar.
    - **Modélisation** : Traduction d'un cahier des charges opérationnel complexe en un modèle mathématique rigoureux.
    - **Conception d'Algorithmes** :
        - Une **heuristique gloutonne**, pour une utilisation en temps réel (compromis vitesse/optimalité).
        - Un **algorithme de programmation dynamique** optimal mais coûteux, fruit d'un travail de recherche approfondi.
        - Adaptation et modification de l'algorithme **FAB (Forward-And-Backward)** aux nouvelles propriétés du problème.
    - **Résultats Chiffrés** :
        - Amélioration des performances de **33% en moyenne** par rapport à la baseline Thales.
        - Formulation de **recommandations opérationnelles** concrètes (ex: l'heuristique a des pertes de performance très faibles ; arrêter l'algorithme à la 4ème itération est un excellent compromis temps/performance).
    - **Compétences Scientifiques Associées** :
        - **Validation théorique** : Obtention de bornes sur les performances via relaxation de contraintes.
        - **Preuves mathématiques** : Capacité à formaliser et prouver des propositions.
        - **Framework expérimental** : Conception d'un cadre de test pour comparer rigoureusement les algorithmes.
        - **Communication** : Rédaction de papiers scientifiques et présentations en conférences internationales.
### B. Computer Vision (Projet Perso Calibration)
- **Contexte / Mon positionnement (Projet d'odométrie visuelle)** : Ce projet a été entrepris de manière autonome avec un double objectif : répondre à la suggestion d'Harmattan AI de renforcer mes compétences en Computer Vision, et explorer la perception pour les algorithmes de décision ancrés dans le monde réel (robotique, systèmes embarqués). J'ai choisi le challenge de Comma.ai, une entreprise dont j'apprécie l'approche technique. Ce projet, plus long que prévu, a été une expérience enrichissante, mettant en lumière ma méthode de travail et ma capacité à m'approprier de nouveaux domaines techniques.
- **Démarche** : Projet structuré en "arcs" itératifs, documenté dans un [rapport détaillé](https://vaillus.github.io/Calibration_challenge/fr/).
- **Détails techniques** :
    - **Prise en main d'OpenCV** pour le traitement vidéo et l'extraction du flux optique.
    - **Intégration de modèles de segmentation type YOLOv8** pour le masquage des éléments perturbateurs (véhicules, capot).
    - **Développement d'une méthode de filtrage et d'optimisation robuste** :
        - Minimisation d'un score de colinéarité (fonction de coût).
        - Utilisation de la descente de gradient (Adam from scratch) pour la recherche de l'épipole.
        - Application de fonctions sigmoïdes pour une pondération souple des vecteurs.
        - **Optimisation Bayésienne (`skopt`)** pour la recherche des paramètres optimaux sur un espace à 6 dimensions.
    - **Techniques complémentaires** : Analyse de la convexité de la fonction de coût, implémentation d'un lissage par moyenne exponentielle bi-directionnelle en post-traitement.
- **Résultats concrets & Analyse Critique** :
    - Score final de **8.58%** sur le jeu de validation.
    - résultat déçevant de 30% sur le jeu de test.
    - **Analyse approfondie des limites** : Identification de la faiblesse du modèle dans les virages, menant au diagnostic de la confusion entre Foyer d'Expansion (FoE) et Épipole. Compréhension de la nécessité d'approches basées sur la géométrie épipolaire pour les mouvements combinés (translation + rotation). Cette phase de diagnostic, documentée, démontre une rigueur intellectuelle et une capacité à remettre en question l'approche initiale pour progresser.
- **Compétences clés démontrées par ce projet** :  
    - **Passion pour l'algorithmie et l'apprentissage autonome** : Investissement significatif pour maîtriser un nouveau domaine technique.  
    - **Rigueur méthodologique** : Approche itérative, justification des choix, et analyse critique des résultats (démontré par le rapport détaillé).  
    - **Capacité de communication technique** : Rédaction d'un blog didactique accessible même aux non-experts.  
    - **Résolution de problèmes complexes** : Du prototype à l'optimisation, en s'adaptant aux contraintes (ex: accélération MLX sur Mac M1).
En revanche, ce projet ne me permettra pas d'obtenir un top job en computer vision je pense. C'est un projet perso qui démontre mes compétences plus générales d'ingénieur de recherche, ma passion pour l'algorithmie et mon intérêt pour la computer vision qui est un sujet important dans les problématiques de robotique/système autonome. Sauf si la job description précise explicitement que la computer vision est un aspect important du travail, mettre plus le PhD en avant.
### C. Machine Learning & Reinforcement Learning
- **Postulat / Mes doutes** : Reconnait un profil perçu parfois comme "bâtard" en raison d'une absence de projet phare en RL, malgré un investissement significatif. Cependant, la base théorique et les implémentations réalisées sont solides.
- **Présentation / Mes forces** : Possède une compréhension approfondie des fondements du Machine Learning (réseaux de neurones, concepts clés) et une solide base théorique et pratique en Reinforcement Learning. Cette double expertise, combinée à la Recherche Opérationnelle, offre une perspective unique sur les systèmes de décision, permettant de choisir l'approche la plus adaptée aux problèmes concrets. Démontre une forte passion pour la conception d'agents artificiels intelligents et les algorithmes d'apprentissage par l'exploration et l'interaction.
- **Détails Techniques & Réalisations Concrètes** :
    - **Machine Learning (Fondamentaux et Application)** :
        - **Connaissances fondamentales** : Étude et implémentation de réseaux de neurones (RNN, CNN), compréhension des mécanismes internes (fonctions d'activation, propagation, backpropagation). Maîtrise des concepts clés (overfitting, underfitting, validation croisée).
        - **Projet IBM (Stage)** : Expérience concrète en data science et data engineering pour un projet de maintenance prédictive, incluant la construction de pipelines de données complexes et l'application de machine learning (RNN, random forest).
        - **Data Mining** : Pratique sur un projet Kaggle pour l'extraction et l'analyse de données.
    - **Reinforcement Learning (Auto-apprentissage et Implémentation)** :
        - **Étude approfondie** : Lecture du livre de Sutton et Barto, compréhension des principes des Processus de Décision Markoviens (MDPs) etc.
        - **Implémentation pratique** : Réalisation de plusieurs algorithmes de RL (ex: Deep Q-Networks, Policy Gradients, PPO) à partir de la littérature scientifique.
        - **Expérimentation** : Tests sur des environnements "jouets" (ex: Atari), permettant de saisir les défis liés à l'entraînement, la stabilité et l'exploration.
        - **Vision des systèmes** : Grande motivation pour concevoir des environnements de simulation dans lesquels des agents peuvent apprendre et évoluer, inspiré par les succès du DRL sur des jeux complexes. Prise en main de Godot pour créer des environnements de simulation.
    - **Passion & Veille** : Engagement continu via l'écoute de podcasts spécialisés (Lex Friedman, Doerkech) et une curiosité active pour l'évolution et les applications du domaine.
### D. Agentic Workflow
Depuis la sortie de GPT-2, je suis fasciné par les LLMs et leur utilisation. Je les utilise tous les jours dans ma vie pro et personnelle, que ce soit pour programmer avec Cursor ou faire mes cartes anki avec mon prompt [[anki prompt]] que j'ai pas mal affiné avec le temps.
J'ai vu des offres passer qui proposent de faire des agents basés sur des LLMs pour faire des tâches diverses.
Ce [tweet de François Chollet](https://x.com/JacksonAtkinsX/status/1975556245617512460) a peut-être créé le déclic chez moi. Les gens arrivent vraiment à faire des choses cool.
Je pense que j'aimerais bien travailler sur des programmes agentiques.
C'est pas du RL ni de la RO, mais c'est des agents autonomes, plus ou moins, et je trouve ça super cool. En plus j'ai le sentiment que je vais pouvoir recouper ça avec mes autres skills à un moment ou à un autre.
J'ai donc suivi le cours sur les [[agentic workflow Andrew Ng]] pour comprendre comment fonctionne tout ça. Par hasard, il se trouve que je suis probablement un des premiers élèves au monde à avoir fini le cours puisque je l'ai commencé le jour de sa sortie et que je l'ai bourriné sur le weekend!
Maintenant, je me lance dans la full automatisation de mon workflow de recherche d'emploi avec des agents.
Le projet est déjà pas mal avancé maintenant (https://github.com/Vaillus/JobseekerAgent).
Je prends en main langgraph et langchain.
keywords: tool-augmented workflow, agent frameworks

## 4. Expériences (Format détaillé pour préparation d'entretiens)
### Projet | Workflow de recherche d'emploi (Octobre 2025)
Maintenant que j'ai fini le cours de Andrew Ng, j'avais déjà commencé à faire des prompts qui m'aident à faire, qui m'assistent, pour que des agents m'assistent dans ma recherche d'emploi. Donc par exemple un prompt qui m'aide à évaluer des offres, si c'est un bon fit pour moi, et j'utilise Cursor pour corriger mon CV. J'ai déjà fait une petite partie du travail, et maintenant l'objectif c'est de complètement automatiser la pipeline de postulation avec des agents, grâce à ce que j'ai appris dans le cours.
En revanche, si je postule à un job qui demande l'utilisation de workflow d'agent, il faut que je me présente comme ayant déjà ces compétences. (eg. langchain, langgraph, ...) Je pense que ça va aller vite et peu de gens maîtrisent déjà ça.
J'ai pas utilisé de RAG sur ce projet. Par contre, j'ai utilisé LangChain pour la gestion des agents et des pipelines, et je projette d'utiliser langgraph très prochainement.


### Projet | Calibration de Caméra (Mai - Août 2025)
- **Situation** : Après ma thèse et un retour d'entretien m'orientant vers le CV, j'ai décidé de construire un projet public et techniquement profond pour démontrer mes compétences. J'ai choisi le challenge de calibration de Comma.ai.
- **Tâche** : Estimer les angles de rotation (pitch, yaw) de la caméra par rapport à la direction de la voiture, uniquement à partir de la vidéo. Pas en temps réel.
- **Actions** : J'ai structuré mon travail en 5 arcs itératifs :
    1. **Baseline** : Approche naïve par flux optique. Score très mauvais (>1000%).
    2. **Segmentation** : Ajout de YOLOv8 pour masquer les sources de bruit (voitures, capot). Amélioration de 60%.
    3. **Nouvelle méthode d'optimisation** : Définition d'un score de colinéarité et minimisation par descente de gradient. Score de ~170%.
    4. **Filtrage & Accélération** : Introduction d'un filtrage des vecteurs et optimisation drastique du code (passage à MLX, sampling intelligent) pour permettre une recherche de paramètres. Score de ~54%.
    5. **Raffinements** : Généralisation du filtrage (sigmoïdes), optimisation bayésienne des paramètres, et ajout d'un lissage en post-traitement.
- **Résultat** : Un score final de **8.58%** sur les données de validation. Un rapport technique complet documentant chaque étape. Une analyse lucide des limites du modèle (échec dans les virages) et des pistes d'amélioration (décomposition du mouvement).
### Thèse CIFRE | Thales DMS (2020 - 2023)
- **Situation** : Au sein du projet FCAS (avion de chasse du futur), les pilotes sont surchargés par la gestion manuelle des capteurs.
- **Tâche** : Automatiser la gestion du radar pour la recherche de cibles aériennes mobiles, afin d'optimiser l'utilisation des ressources et d'améliorer les performances.
- **Actions** :
    1. **Modélisation** : J'ai étudié le fonctionnement complexe du radar et l'ai modélisé comme un problème d'optimisation combinatoire.
    2. **Conception d'Algorithmes** : J'ai développé et comparé deux approches : une heuristique gloutonne (rapide) et un algorithme de programmation dynamique (optimal).
    3. **Validation** : J'ai implémenté un framework de simulation dans Godot pour tester et comparer rigoureusement les algorithmes sur de multiples scénarios. J'ai aussi calculé des bornes théoriques pour évaluer la "distance à l'optimalité".
- **Résultat** : Les algorithmes conçus ont amélioré les performances de détection de **33% en moyenne** par rapport à la solution existante. Mon travail a fourni des recommandations directement utilisables par Thales.
### Stage | Consultant Data Science Junior chez IBM (Fév - Juil 2019)
- **Situation** : Stage de fin d'études au sein des équipes de conseil d'IBM.
- **Tâche** : Développement d'un outil de maintenance prédictive pour un acteur majeur du secteur pétrolier et gazier français.
- **Actions** : Implémentation d'un pipeline de préparation de données et d'un modèle de deep learning récurrent pour prédire les pannes.
- **Résultat** : Livraison d'un PoC (Proof of Concept) fonctionnel au client.
## 5. Qualités Personnelles et Méthodes de Travail
- **Auto-amélioration Structurée** :
    - **Constat** : Je suis par nature étourdi et chaotique, avec une mémoire passive peu fiable.
    - **Système mis en place** :
        - **Obsidian** : Depuis 3 ans, j'écris tout. Journal quotidien, revue hebdomadaire, objectifs. C'est mon second cerveau. (Résultat : 1700 pages, perçu comme très organisé).
        - **Anki** : J'utilise la répétition espacée pour tout ce que je veux mémoriser activement (maths, espagnol, dessin, concepts de programmation). Je transforme les livres/podcasts en cartes.
    - **Conclusion** : J'ai développé un "méta-skill" pour apprendre n'importe quoi de manière efficace en transformant mes faiblesses en forces.
- **Curiosité Profonde / Apprentissage Obsessionnel** :
    - Quand un sujet m'intéresse, je le structure de manière quasi-obsessionnelle pour le maîtriser.
    - **Exemples** :
        - **Dessin** : Objectif "portrait", puis constat de lacunes, donc reprise des bases (volume, perspective, anatomie) via des livres convertis en cartes Anki et un système d'exercices quotidiens.
        - **Musique** : Création de 120 playlists Spotify pour structurer et comprendre mes propres goûts musicaux.
- **Rigueur et Introspection Technique** :
    - Je ne me contente pas de faire fonctionner les choses, je veux comprendre pourquoi elles fonctionnent et où sont leurs limites.
    - **Exemple** : La section "Bilan et Perspectives" de mon projet CV est la plus importante. J'y explique pourquoi ma méthode a échoué sur le jeu de test. Cette capacité à faire un diagnostic honnête de mon propre travail est une force.
    - **Leçon apprise** : "Toujours implémenter les solutions à fort impact et faible effort en premier. [...] elles clarifient le vrai problème à résoudre."
## 6. Ma vision stratégique : L'ingénierie des systèmes de décision de demain (RO + RL)
Mon parcours m'a doté d'une perspective rare et stratégique sur le développement de l'intelligence artificielle. Je me positionne au croisement de la Recherche Opérationnelle (RO) et du Deep Reinforcement Learning (DRL), deux disciplines que je considère comme intrinsèquement liées et complémentaires pour la conception des systèmes intelligents du futur.

Alors que de nombreux professionnels se spécialisent dans l'une ou l'autre de ces approches, je suis convaincu que leur synergie est la clé pour résoudre les problèmes de décision les plus complexes :
- La **Recherche Opérationnelle** apporte la rigueur mathématique, la modélisation formelle et les garanties d'optimalité ou de performances pour des problèmes bien définis.
- Le **Deep Reinforcement Learning** offre la flexibilité et la capacité d'adaptation pour des environnements complexes, stochastiques et peu structurés, où les modèles classiques peinent à scale-up.

Cette double compétence me permet non seulement d'évaluer la meilleure approche pour un problème donné, mais aussi de concevoir des architectures hybrides innovantes. Je suis particulièrement enthousiaste à l'idée de développer les "compétences" spécifiques (low-level skills) qui seront employées par des systèmes intelligents de plus haut niveau, comme les Large Language Models, pour interagir efficacement avec le monde réel. Ce positionnement me place à l'avant-garde des recherches sur les agents autonomes et l'IA générale, en me permettant de travailler sur des problèmes concrets avec une vision long-terme.
## 7. Compétences Techniques Clés (Hard Skills)
- **Langues** : Anglais (Courant), Espagnol (Bonne maîtrise).
- **Programmation** : Python (avancé), programmation sur GPU (PyTorch, JAX), vectorisation/parallélisation de code.
- **Machine Learning / Deep Learning** : Réseaux de neurones (RNN, CNN, LSTM, transformer), concepts clés (overfitting, underfitting, validation croisée).
- **Reinforcement Learning** : Algorithmes (DQN, Policy Gradients), MDPs, implémentation et expérimentation.
- **Recherche Opérationnelle / Optimisation** : Modélisation mathématique, Simplex, Branch & Bound, Optimisation Bayésienne (scikit-optimize).
- **Computer Vision** : OpenCV, intégration de modèles de segmentation (YOLOv8).
- **Data Science / Engineering** : Data mining, construction de pipelines de données.
- **Environnements de simulation** : Godot.

J'ai codé quasiment exclusivement en Python ces 6 dernières années. J'ai fait un peu de Gdscript quand je travaillais sur ma simulation Godot au début de ma thèse, et j'ai fait un peu de javascript en travaillant sur diverses interfaces.
Mon premier contact avec la programmation a été le C en première année d'école d'ingé, ce qui m'a je pense permis d'avoir de solides bases de compréhension de la programmation pour commencer.
Ensuite, j'ai un peu étudié le C++ et le java, j'ai fait des projets avec dans la première partie de mes études. Mais vraiment that's it.

# Compétences que je peux vite acquérir et qui sont ajoutables au CV si elles sont explicitement demandées dans l'offre
- SQL (faire l'assignment de Benoit)
- dockerisation (dockeriser mon projet de calibration)
- agentic workflow
- vector databases ?
- RAG/eval/orchestration ?

# Divers
Je parle couremment anglais, français et mon voyage de sept mois en amérique du sud m'a permis d'acquérir une bonne maîtrise de l'espagnol. Genre je peux avoir des conversations d'une heure sans problème, même si j'ai jamais lu de livre en espagnol.