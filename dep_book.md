# Cheat sheet des relations de Dependency Parsing (Universal Dependencies)

---

## Clausal Argument Relations :

* **NSUBJ** (Nominal subject)

  * **Définition :** Sujet du verbe, exprimé par un nom, pronom ou groupe nominal.
  * **Exemple :** **Marie**NSUBJ aime les gâteaux.*

* **DOBJ** (Direct object)

  * **Définition :** Objet direct d’un verbe transitif.
  * **Exemple :** *Il lit \[**un livre**]OBJ.*

* **IOBJ** (Indirect object)

  * **Définition :** Objet indirect introduit sans préposition obligatoire (typique en espagnol, catalan) ; en français on a plutôt *obl*.
  * **Exemple :** *(Esp.) "Le dio \[**dinero**]OBJ \[**a Juan**]IOBJ."*

* **CCOMP** (Clausal complement)

  * **Définition :** Proposition complétive avec son propre sujet (ou sujet implicite) régie sans préposition.
  * **Exemple :** *Je pense \[**qu’il viendra**]CCOMP.*

* **XCOMP** (Open clausal complement)

  * **Définition :** Complément propositionnel dont le sujet est contrôlé par l’élément gouverneur (sujet partagé).
  * **Exemple :** *Elle veut \[**partir**]XCOMP.*

---

## Nominal Modifier Relations :

* **NMOD** (Nominal modifier)

  * **Définition :** Groupe nominal, pronom ou nom propre modifiant un autre nom (génitif, complément du nom, etc.).
  * **Exemple :** *le livre \[**de Marie**]NMOD*

* **AMOD** (Adjectival modifier)

  * **Définition :** Adjectif modifiant un nom.
  * **Exemple :** *un \[**grand**]AMOD arbre*

* **NUMMOD** (Numeric modifier)

  * **Définition :** Nombre ou expression numérique modifiant un nom.
  * **Exemple :** *\[**trois**]NUMMOD chats*

* **APPOS** (Appositional modifier)

  * **Définition :** Nom ou groupe nominal en apposition décrivant un autre nom.
  * **Exemple :** *Paris, \[**capitale de la France**]APPOS, est magnifique.*

* **DET** (Determiner)

  * **Définition :** Déterminant précédant un nom (articles, démonstratifs, possessifs, etc.).
  * **Exemple :** *\[**Les**]DET enfants jouent.*

* **CASE** (Case marking)

  * **Définition :** Marqueurs de cas : prépositions, postpositions, etc., rattachés au mot qu’ils introduisent.
  * **Exemple :** *livre \[**de**]CASE Marie*

---

## Other Notable Relations :

* **CONJ** (Conjunct)

  * **Définition :** Élément coordonné partageant le même gouverneur qu’un autre.
  * **Exemple :** *Pierre \[**et**]CC Marie \[**voyagent**]CONJ.*  (ici « Marie » est CONJ de « Pierre »)

* **CC** (Coordinating conjunction)

  * **Définition :** Conjonction de coordination reliant des éléments de même statut.
  * **Exemple :** *Il mange \[**et**]CC dort.*
  
* **OBL:MOD** (oblique modifier)

  * **Définition :** est une étiquette utilisée pour marquer un complément circonstanciel (de temps, lieu, manière, cause, etc.), qui modifie un nom (et non un verbe, comme obl tout court).
  * **Exemple :** *oui je prends le métro \[**le matin**] à huit heures et demie*

