# Contrôles d'époque — rendus produits AVANT/PENDANT la compilation du skill

> Fournis par Thomas le 30/07. Ce sont les **références UX du CGP** — le troisième juge identifié
> par la revue du 30/07 (`docs/revue_controle_interagyr_2026-07-30.md` §2) : le golden protège le
> moteur, L3a protège le lecteur, ces fichiers protègent la **parité de blocs** perçue.

| Fichier | Client | Date | Statut de confiance |
|---|---|---|---|
| `consolide_Interagyr_2026-07-23.html` | INTERAGYR | 23/07 | Contrôle de la revue du 30/07. En partie composé par l'agent (éditorial, double donut, en-têtes datés) : référence de **structure et d'intention**, pas de vérité comptable. |
| `Reporting_Gronier_T2_consolide_2026-07-27.html` | client de référence, T2 2026 | 27/07 (juste avant compilation du skill) | **Avertissement de Thomas : « il a de nombreux défauts, il faut le noter. »** À utiliser comme pièce du chantier UI (styles, blocs présents) et comme contrôle du futur run Gronier — jamais comme vérité de valeurs sans vérification contre les relevés officiels. Rappel : la spec du lecteur §7.3 a déjà documenté la désynchronisation store/classeur de cette époque. **REMPLACÉ comme référence Gronier par la version corrigée du 31/07 (ligne suivante) — gardé pour le diff.** |
| `Reporting_NicolasG_T2_2026_corrige_2026-07-31.html` | client de référence, T2 2026 | 31/07 (corrigé forme + fond) | Version **plus qualitative** fournie par Thomas — remplace celle du 27/07 comme référence Gronier et contrôle du futur run B-v. Doctrine posée en la donnant : **la structure du contrôle INTERAGYR « met tout le monde d'accord », le style Gronier est hyperspécifique**. Enseignements E1–E8 dépouillés dans `docs/chantier_ui_design_2026-07-31.md` §10. Défauts CONNUS de la pièce : écart de 300 000 € entre le donut coté/non coté (926 671 €) et l'Historique/commentaire (626 671 €) ; colonne « Cible (MOIC/TRI) » conservée alors que D-UI-2 l'a supprimée le même jour ; W2/W3 du PE absents (la banque est en avance — D53, ne pas régresser en s'alignant) ; handlers d'accordéon morts. |

Règle d'usage : un contrôle d'époque se **confronte**, il ne se recopie pas. Chaque écart
run-vs-contrôle se qualifie en trois familles (revue §1) : bug, donnée absente, ou choix de style
— et un défaut du contrôle est une quatrième issue possible, à documenter ici quand il est établi.
