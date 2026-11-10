# Pixo Pre-A1 curriculum (Cambridge Pre A1 Starters vocabulary, GSE Young Learners objectives).
# Each unit: 16 new items -> 4 sessions of 4 items. Items in quotes are chunks (expressions).
import csv, json, sys

MODULES = [
  ("M1", "Bonjour Pixo ! (moi et les autres)", [
    ("U1", "Hello!", "Saluer, dire oui/non, se présenter",
     ["hello", "bye", "yes", "no",
      "hi", "goodbye", "please", "thank you",
      "\"my name's…\"", "\"what's your name?\"", "OK", "sorry",
      "well done", "wow", "\"see you!\"", "\"me too\""],
     ["GSE 10 (oral) saluer et prendre congé (hello, hi, bye)", "GSE 11 (oral) se présenter (My name's…)", "GSE 12 (oral) demander le prénom", "GSE 11 (écoute) mots de politesse"]),
    ("U2", "Colours", "Reconnaître et nommer les couleurs",
     ["red", "blue", "yellow", "green",
      "orange", "pink", "purple", "brown",
      "black", "white", "grey", "colour",
      "\"what colour is it?\"", "\"it's…\"", "rainbow*", "favourite"],
     ["GSE 10 (écoute) reconnaître noms et adjectifs familiers (couleurs)", "GSE 19 (oral) décrire un objet par sa couleur", "GSE 21 (oral) demander la couleur d'un objet"]),
    ("U3", "My body", "Nommer les parties du corps",
     ["head", "eye", "nose", "mouth",
      "ear", "hair", "face", "hand",
      "arm", "leg", "foot", "body",
      "\"touch your…\"", "smile", "clap", "wave"],
     ["GSE 23 (oral) nommer les parties du corps", "GSE 15 (écoute) comprendre des verbes d'action (clap…)", "GSE 13 (écoute) suivre des consignes courtes avec gestes"]),
    ("U4", "Numbers 1-10", "Compter jusqu'à 10, dire son âge",
     ["one", "two", "three", "four",
      "five", "six", "seven", "eight",
      "nine", "ten", "\"how many?\"", "count",
      "\"how old are you?\"", "\"I'm (six)\"", "birthday", "cake"],
     ["GSE 10 (oral) utiliser les nombres jusqu'à 10", "GSE 13 (oral) dire combien il y a de choses (≤10)", "GSE 12 (oral) dire son âge"]),
    ("U5", "How are you?", "Dire comment on se sent",
     ["happy", "sad", "angry", "\"how are you?\"",
      "\"I'm OK\"", "funny", "scary", "silly",
      "good", "great", "nice", "fantastic",
      "big", "small", "\"oh dear!\"", "\"don't worry\""],
     ["GSE 14 (oral) demander comment ça va", "GSE 22 (oral) dire comment on se sent (happy…)", "GSE 17 (oral) donner une évaluation simple (good/bad)"]),
    ("U6", "Let's move!", "Comprendre et faire des actions",
     ["stand up", "sit down", "jump", "run",
      "walk", "stop", "look", "listen",
      "point", "\"don't run!\"", "throw", "catch",
      "kick", "swim", "fly", "\"let's play!\""],
     ["GSE 15 (écoute) comprendre des verbes d'action", "GSE 16 (écoute) comprendre une consigne négative (Don't run)", "GSE 18 (écoute) comprendre des ordres dans un jeu"]),
  ]),
  ("M2", "Ma famille et ma maison", [
    ("U7", "My family", "Présenter sa famille",
     ["mum", "dad", "brother", "sister",
      "baby", "grandma", "grandpa", "family",
      "boy", "girl", "friend", "kid",
      "man", "woman", "\"this is my…\"", "\"who's this?\""],
     ["GSE 21 (écoute) comprendre le nom des membres de la famille", "GSE 18 (oral) nommer des personnes avec des mots isolés", "GSE 19 (écoute) comprendre une présentation (nom, âge)"]),
    ("U8", "Pets and farm", "Nommer les animaux familiers et de la ferme",
     ["cat", "dog", "fish", "bird",
      "cow", "horse", "sheep", "duck",
      "chicken", "goat", "donkey", "mouse",
      "pet", "animal", "frog", "spider"],
     ["GSE 18 (oral) nommer des animaux avec des mots isolés", "GSE 19 (écoute) identifier des animaux dans une image", "GSE 18 (écoute) reconnaître des mots dans une chanson"]),
    ("U9", "At the zoo", "Nommer et décrire les animaux du zoo",
     ["elephant", "monkey", "tiger", "giraffe",
      "zebra", "crocodile", "snake", "hippo",
      "bear", "polar bear", "lizard", "bee",
      "tail", "zoo", "long", "short"],
     ["GSE 18 (oral) nommer des animaux", "GSE 19 (oral) décrire avec quelques mots (couleur, nombre)", "GSE 23 (oral) décrire la taille (It's big)"]),
    ("U10", "My house", "Nommer les pièces et les meubles",
     ["house", "kitchen", "bedroom", "bathroom",
      "living room", "garden", "door", "window",
      "bed", "table", "chair", "sofa",
      "lamp", "mirror", "clock", "box"],
     ["GSE 19 (oral) nommer des objets de l'environnement proche", "GSE 21 (écoute) comprendre une question sur un objet proche", "GSE 21 (oral) demander ce que c'est (What is it?)"]),
    ("U11", "My toys", "Nommer ses jouets",
     ["ball", "doll", "car", "robot",
      "teddy", "kite", "balloon", "train",
      "plane", "boat", "bike", "game",
      "toy", "monster", "alien", "helicopter"],
     ["GSE 18 (oral) nommer des objets familiers", "GSE 21 (oral) donner quelque chose (Here you are)", "GSE 22 (oral) jeux avec expressions fixes"]),
    ("U12", "Where is it?", "Dire où sont les choses",
     ["in", "on", "under", "\"where's…?\"",
      "next to", "behind", "in front of", "between",
      "here", "there", "\"here you are\"", "find",
      "\"it's in the box\"", "open", "close", "put"],
     ["GSE 24 (écoute) comprendre où sont les choses (phrases simples)", "GSE 21 (oral) donner quelque chose (Here you are)", "GSE 19 (écoute) suivre des consignes pour faire quelque chose"]),
  ]),
  ("M3", "Manger, s'habiller, ma journée", [
    ("U13", "Yummy fruit", "Nommer les fruits et les boissons",
     ["apple", "banana", "lime", "grape",
      "pear", "lemon", "mango", "watermelon",
      "milk", "water", "juice", "drink",
      "pineapple", "coconut", "kiwi", "fruit"],
     ["GSE 19 (oral) dire ce qu'on veut manger ou boire (mots + gestes)", "GSE 18 (oral) nommer des objets en image", "GSE 10 (écoute) reconnaître des noms familiers"]),
    ("U14", "Lunch time", "Repas et politesse à table",
     ["bread", "egg", "rice", "meat",
      "carrot", "tomato", "potato", "pea",
      "breakfast", "lunch", "dinner", "eat",
      "\"I'd like…\"", "\"yes, please\"", "\"no, thank you\"", "ice cream"],
     ["GSE 19 (oral) mots de politesse (please, thank you)", "GSE 19 (oral) dire ce qu'on voudrait (I'd like)", "GSE 25 (écoute) comprendre des besoins immédiats"]),
    ("U15", "My clothes", "Nommer ses vêtements",
     ["hat", "shoe", "sock", "T-shirt",
      "dress", "skirt", "shirt", "jacket",
      "trousers", "shorts", "jeans", "boots",
      "glasses", "bag", "baseball cap", "wear"],
     ["GSE 22 (oral) nommer des vêtements avec images", "GSE 26 (écoute) comprendre la description de vêtements", "GSE 19 (oral) décrire par la couleur"]),
    ("U16", "My day", "Les moments de la journée",
     ["morning", "afternoon", "evening", "night",
      "day", "today", "sleep", "\"go to bed\"",
      "\"good morning\"", "\"good night\"", "clean", "wash*",
      "\"happy birthday!\"", "year", "party*", "sing"],
     ["GSE 10 (oral) formules de salutation polie (Good morning)", "GSE 18 (écoute) comprendre le moment de la journée", "GSE 16 (oral) réciter une comptine"]),
    ("U17", "Numbers 11-20", "Compter jusqu'à 20",
     ["eleven", "twelve", "thirteen", "fourteen",
      "fifteen", "sixteen", "seventeen", "eighteen",
      "nineteen", "twenty", "number", "first",
      "second", "third", "last*", "\"how many…?\""],
     ["GSE 17 (oral) dire combien il y a de choses (≤20)", "GSE 18 (oral) utiliser les nombres jusqu'à 20", "GSE 20 (oral) nombres ordinaux"]),
    ("U18", "Snack time", "Demander poliment",
     ["lemonade", "chocolate", "sweets", "biscuit*",
      "\"can I have…?\"", "want", "give", "share*",
      "\"thanks!\"", "\"pardon?\"", "hot*", "cold*",
      "burger", "chips", "sausage", "food"],
     ["GSE 21 (oral) expressions fixes courtes", "GSE 19 (oral) politesse", "GSE 26 (oral) exprimer un besoin immédiat (I want a drink)"]),
  ]),
  ("M4", "Dehors et à l'école", [
    ("U19", "At school", "Le matériel et les consignes de classe",
     ["book", "pen", "pencil", "crayon",
      "ruler", "eraser", "desk", "teacher",
      "class", "draw", "colour (verb)", "\"open your book\"",
      "\"close the door\"", "paper", "picture", "board"],
     ["GSE 13 (écoute) suivre des consignes de classe", "GSE 17 (écoute) reconnaître le début et la fin d'une activité", "GSE 19 (écoute) suivre des consignes pour colorier ou dessiner"]),
    ("U20", "Let's go!", "Les transports",
     ["bus", "truck", "motorbike", "ship",
      "drive", "ride", "go", "fast*",
      "\"beep beep!\"*", "street", "shop", "park",
      "\"let's go!\"", "car park*", "slow*", "\"stop!\""],
     ["GSE 18 (oral) nommer des objets en image", "GSE 21 (oral) actions de base", "GSE 25 (écoute) comprendre des directions simples"]),
    ("U21", "At the beach", "La plage et la nature",
     ["beach", "sea", "sand", "shell",
      "sun", "tree", "flower", "\"splash!\"*",
      "\"take a photo\"", "\"it's sunny\"*", "fishing", "camera",
      "playground", "\"look!\"", "see", "jellyfish"],
     ["GSE 19 (écoute) identifier des objets dans une image", "GSE 24 (écoute) phrases simples sur la météo", "GSE 18 (oral) nommer des choses autour de soi"]),
    ("U22", "Sports", "Les sports et les jeux",
     ["football", "tennis", "basketball", "baseball",
      "badminton", "hockey", "table tennis", "sport",
      "hit", "bounce", "bat", "racket",
      "\"good game!\"*", "win*", "team*", "\"your turn!\"*"],
     ["GSE 18 (oral) nommer des activités", "GSE 22 (oral) jeux avec expressions fixes", "GSE 18 (écoute) comprendre des ordres dans un jeu"]),
    ("U23", "ABC song", "Les lettres et leurs sons (oral)",
     ["A-B-C-D", "E-F-G", "H-I-J-K", "L-M-N-O-P",
      "Q-R-S", "T-U-V", "W-X-Y-Z", "alphabet",
      "letter", "\"how do you spell…?\"*", "sound*", "word",
      "spell", "name", "\"A is for apple\"*", "\"B is for ball\"*"],
     ["GSE 10 (écoute) reconnaître les lettres par leur son et leur nom", "GSE 10 (oral) dire les lettres de l'alphabet", "GSE 13 (oral) dire les sons de l'alphabet avec images"]),
    ("U24", "Story time", "Chansons et histoires",
     ["song", "music", "story", "guitar",
      "piano", "photo", "beautiful", "ugly",
      "old", "new", "young", "\"the end\"*",
      "\"once upon a time\"*", "\"again!\"*", "radio", "\"I love it!\""],
     ["GSE 18 (écoute) comprendre quelques mots d'une histoire lue", "GSE 22 (oral) chanter une chanson de mémoire", "GSE 25 (écoute) comprendre l'essentiel d'une histoire avec images"]),
  ]),
]

OUTLINE = [
  ("A1 (Movers, GSE 22-29)", [
    ("M5", "Ma ville", "café, library, market, supermarket, bus stop, cinema, opposite", "GSE 25 directions simples ; GSE 29 dire où se trouve un objet"),
    ("M6", "Mon corps et ma santé", "shoulder, neck, tooth/teeth, headache, temperature, ill, nurse", "GSE 26 exprimer un besoin ; GSE 29 demander comment l'autre se sent"),
    ("M7", "La nature et la météo", "weather, cloud, windy, forest, river, mountain, island", "GSE 27 dire le temps qu'il fait ; GSE 24 comprendre la météo"),
    ("M8", "Ce que j'aime, ce que je sais faire", "always, never, sometimes, dance, skip, party, holiday", "GSE 28 can / can't ; GSE 29 goûts (likes / dislikes)"),
    ("M9", "Les métiers et ma semaine", "week, weekend, farmer, dentist, cook, clown, pirate", "GSE 29 dire le métier de quelqu'un ; GSE 29 routines quotidiennes"),
  ]),
  ("A2 (Flyers, GSE 30-42)", [
    ("M10", "Voyages et transports", "journey, passenger, ticket, taxi, airport, railway", "Raconter un trajet simple ; comprendre des horaires"),
    ("M11", "Le monde et l'espace", "planet, space, desert, astronaut, environment", "Décrire et comparer (as … as, bigger than)"),
    ("M12", "Raconter et imaginer", "yesterday, tomorrow, might, will, because, if", "Raconter une petite histoire au passé ; faire des projets"),
  ]),
]

def rows():
    out = []
    n = 0
    for mid, mname, units in MODULES:
        for uid, uname, goal, items, objs in units:
            assert len(items) == 16, (uid, len(items))
            for s in range(4):
                n += 1
                out.append(dict(module=mid, module_title=mname, unit=uid, unit_title=uname,
                                session=f"{uid}.S{s+1}", n=n, goal=goal,
                                new_items=", ".join(items[s*4:(s+1)*4]),
                                objectives=" ; ".join(objs)))
        n += 1
        out.append(dict(module=mid, module_title=mname, unit="Bilan", unit_title=f"Bilan oral {mid}",
                        session=f"{mid}.BILAN", n=n, goal="Bilan oral sans note, inspiré de l'épreuve orale de Starters",
                        new_items="(aucun mot nouveau : révision de tout le module)", objectives="Objectifs GSE du module"))
    return out

if __name__ == "__main__":
    r = rows()
    words = [w for _, _, us in MODULES for u in us for w in u[3]]
    starred = [w for w in words if w.endswith("*")]
    print(len(r), "sessions;", len(words), "items;", len(set(words)), "unique;", len(starred), "hors liste Starters")
    dupes = sorted({w for w in words if words.count(w) > 1})
    print("doublons:", dupes)
    with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(r[0].keys()))
        w.writeheader(); w.writerows(r)
    json.dump({"modules": MODULES, "outline": OUTLINE}, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
