#!/usr/bin/env python3
# coding: utf-8
"""
academia_ingles.py — Academia Foschi IA  ▸ VERSIÓN 2.0
Curso completo A0→C2 siguiendo metodología Cambridge / CEFR.
250+ lecciones · 5 habilidades · Personajes · Aprendizaje adaptativo
Requiere: pip install flask anthropic
Variable de entorno: ANTHROPIC_API_KEY

═══════════════════════════════════════════════════════════
  PARTE 1 — HTML completo, CSS, datos de currículo y JS
  (ensamblar con parte2.py y parte3.py)
═══════════════════════════════════════════════════════════
"""

# ─────────────────────────────────────────────────────────────
#  DATOS DEL CURRÍCULO CEFR (A0 → C2)
#  Cada nivel tiene módulos; cada módulo tiene lecciones.
# ─────────────────────────────────────────────────────────────

CURRICULUM = {
    "A0": {
        "label": "🌱 A0 — Cero Absoluto",
        "color": "#6366f1",
        "lessons": 40,
        "modules": [
            {
                "id": "a0_m1", "title": "¿Cómo funciona el inglés?",
                "emoji": "🧠", "lessons": 5,
                "topics": ["Diferencias español-inglés", "Orden de las palabras", "Por qué no se pronuncia todo", "Los sonidos del inglés", "El ritmo del idioma"]
            },
            {
                "id": "a0_m2", "title": "El Alfabeto",
                "emoji": "🔤", "lessons": 6,
                "topics": ["Letras A-F con sonido y ejemplo", "Letras G-L con sonido y ejemplo", "Letras M-R con sonido y ejemplo", "Letras S-Z con sonido y ejemplo", "Repaso completo del alfabeto", "Deletrear palabras simples"]
            },
            {
                "id": "a0_m3", "title": "Sonidos Esenciales",
                "emoji": "🎵", "lessons": 8,
                "topics": ["El sonido TH (the, this, that)", "Los sonidos R y L", "SH y CH", "Los vocales largas: OO, EE", "Los diptongos: AI, OI, AU", "El sonido de la A (cat, man, hat)", "Consonantes mudas: K en know, W en write", "Práctica de sonidos combinados"]
            },
            {
                "id": "a0_m4", "title": "Las 100 Palabras Esenciales",
                "emoji": "📝", "lessons": 10,
                "topics": ["Saludos y despedidas", "Sí, No, Por favor, Gracias", "Números del 1 al 20", "Colores básicos", "La familia", "El cuerpo", "La casa", "Comida y agua", "Días y meses", "Preguntas básicas: What, Who, Where, When"]
            },
            {
                "id": "a0_m5", "title": "Primera Conversación",
                "emoji": "💬", "lessons": 6,
                "topics": ["Hello — Hi — Goodbye", "What is your name? / My name is...", "How are you? / I'm fine, thank you.", "Presentarse: nombre, país, edad", "Nice to meet you", "Primera conversación completa"]
            },
            {
                "id": "a0_m6", "title": "Gramática Desde Cero",
                "emoji": "⚡", "lessons": 5,
                "topics": ["I am / You are / He is", "Negaciones: I am not / You are not", "Preguntas: Am I? / Are you? / Is he?", "A / An / The — cuándo usarlos", "Singular y plural: cat → cats"]
            },
        ]
    },
    "A1": {
        "label": "🟢 A1 — Principiante",
        "color": "#10b981",
        "lessons": 60,
        "modules": [
            {
                "id": "a1_m1", "title": "Presentación Personal",
                "emoji": "🙋", "lessons": 8,
                "topics": ["My name is... I'm from...", "I am [edad] years old", "I work as a...", "I live in...", "My family: mother, father, sister, brother", "My hobbies: I like / I love / I enjoy", "Describing yourself: tall, short, young", "Full introduction conversation"]
            },
            {
                "id": "a1_m2", "title": "La Vida Cotidiana",
                "emoji": "☀️", "lessons": 8,
                "topics": ["Morning routine vocabulary", "I wake up at... / I go to bed at...", "Days of the week in context", "What time is it? / At what time?", "I eat breakfast / lunch / dinner", "I go to work / school by bus", "Weekend activities", "Talking about your day"]
            },
            {
                "id": "a1_m3", "title": "Compras y Números",
                "emoji": "🛒", "lessons": 8,
                "topics": ["Numbers 20-1000", "How much is this? / It costs...", "I want / I need / I would like", "Big / small / cheap / expensive", "In a shop: Can I help you?", "Colors and sizes in shopping", "Paying: cash / card / change", "Shopping dialogue practice"]
            },
            {
                "id": "a1_m4", "title": "El Verbo TO BE y Presente Simple",
                "emoji": "🔧", "lessons": 10,
                "topics": ["I am / You are / He is / She is / We are / They are", "Negative: I am not / You are not", "Questions: Am I? / Are you? / Is she?", "Short answers: Yes, I am. / No, I'm not.", "Present Simple: I work / You work / He works", "Negatives: I don't work / He doesn't work", "Questions: Do you work? / Does he work?", "Frequency: always, usually, sometimes, never", "Telling the time", "Verb TO HAVE: I have / She has"]
            },
            {
                "id": "a1_m5", "title": "Lugares y Direcciones",
                "emoji": "📍", "lessons": 8,
                "topics": ["Places: bank, hospital, school, supermarket", "Where is the...? / It's near the...", "Left, right, straight ahead, turn", "How far is it? / It's 2 blocks away", "Prepositions: in, on, at, next to, between", "Asking for directions", "Following directions", "Dialogue: How do I get to the station?"]
            },
            {
                "id": "a1_m6", "title": "Situaciones Básicas",
                "emoji": "🎭", "lessons": 8,
                "topics": ["At the restaurant: ordering food", "At the doctor: What's wrong?", "At the hotel: check-in", "On the phone: Hello, can I speak to...?", "At the airport: passport, boarding pass", "At the bank: I'd like to...", "Emergencies: Help! / Call the police!", "Review: A1 complete conversation"]
            },
        ]
    },
    "A2": {
        "label": "🔵 A2 — Básico",
        "color": "#3b82f6",
        "lessons": 60,
        "modules": [
            {
                "id": "a2_m1", "title": "Pasado Simple",
                "emoji": "⏮️", "lessons": 10,
                "topics": ["Regular verbs: worked, played, walked", "Irregular verbs: went, ate, saw, did", "Negative: I didn't go / She didn't eat", "Questions: Did you go? / What did you do?", "When did you...? / How long did you...?", "Yesterday / last week / last year", "Telling a story in the past", "My weekend: what I did", "Past of TO BE: was / were", "Past continuous: I was working when..."]
            },
            {
                "id": "a2_m2", "title": "Futuro y Planes",
                "emoji": "🔮", "lessons": 8,
                "topics": ["Going to: I'm going to travel next month", "Will: I think it will rain", "Present continuous as future: I'm meeting her tonight", "Making plans: Shall we...? / Would you like to...?", "Calendar and appointments", "This weekend / next week / in two days", "Making and canceling appointments", "Future dialogue practice"]
            },
            {
                "id": "a2_m3", "title": "Descripciones y Comparaciones",
                "emoji": "🔍", "lessons": 8,
                "topics": ["Adjectives: beautiful, old, modern, crowded", "Comparatives: bigger than / more expensive than", "Superlatives: the tallest / the most popular", "Describing places: my city is...", "Describing people: he looks like...", "Describing objects: it's made of...", "Describing feelings: I feel happy / tired / nervous", "Comparison dialogue"]
            },
            {
                "id": "a2_m4", "title": "Salud y Cuerpo",
                "emoji": "🏥", "lessons": 8,
                "topics": ["Parts of the body (advanced)", "I have a headache / stomachache / fever", "Symptoms: I feel dizzy / I can't sleep", "At the doctor's: What seems to be the problem?", "The doctor says: You should... / You shouldn't...", "Medicine and prescriptions", "Healthy lifestyle vocabulary", "Medical emergency conversation"]
            },
            {
                "id": "a2_m5", "title": "Trabajo y Estudios",
                "emoji": "💼", "lessons": 8,
                "topics": ["Jobs and professions vocabulary", "Describing your job: I work in... / I'm responsible for...", "Work environment: office, factory, hospital", "I studied... / I have a degree in...", "Job interview basics: Tell me about yourself", "Skills: I'm good at... / I can...", "Workplace phrases: meeting, deadline, report", "Work dialogue: job interview"]
            },
            {
                "id": "a2_m6", "title": "Viajes y Turismo",
                "emoji": "✈️", "lessons": 8,
                "topics": ["At the airport: check-in, boarding, customs", "At the hotel: reservation, room service, checkout", "Transport: taxi, bus, train, subway", "Asking about transport: How do I get to...?", "Sightseeing: visiting monuments, museums", "Food abroad: trying local cuisine", "Problems while traveling: lost, stolen, sick", "Travel conversation practice"]
            },
        ]
    },
    "B1": {
        "label": "🟡 B1 — Intermedio",
        "color": "#f59e0b",
        "lessons": 60,
        "modules": [
            {
                "id": "b1_m1", "title": "Presente Perfecto",
                "emoji": "✅", "lessons": 10,
                "topics": ["Have/has + past participle", "I have lived here for 5 years", "She has never been to London", "Have you ever...? / Yes, I have / No, I haven't", "Already, yet, just, ever, never", "Present Perfect vs Past Simple", "Life experiences: I've been to...", "Talking about achievements", "Recent news: has happened / have discovered", "Practice: interview with Present Perfect"]
            },
            {
                "id": "b1_m2", "title": "Condicionales",
                "emoji": "🔀", "lessons": 8,
                "topics": ["Zero conditional: If water boils, it becomes steam", "First conditional: If it rains, I will stay home", "Second conditional: If I had money, I would travel", "Unless / as long as / provided that", "Wishes: I wish I could... / I wish I had...", "Regrets: I should have... / I could have...", "Advice with conditionals", "Conditional conversation practice"]
            },
            {
                "id": "b1_m3", "title": "Narrar e Historias",
                "emoji": "📖", "lessons": 8,
                "topics": ["Sequencing: first, then, after that, finally", "Setting the scene: It was a dark night...", "Past continuous for background: I was cooking when...", "Dramatic narration: Suddenly / All of a sudden", "Describing emotions in a story", "Direct vs indirect speech", "Telling a funny / scary / interesting story", "Story: a day that changed my life"]
            },
            {
                "id": "b1_m4", "title": "Expresar Opiniones",
                "emoji": "💭", "lessons": 8,
                "topics": ["I think / I believe / In my opinion...", "I agree / I disagree / I'm not sure", "That's a good point / However...", "I see your point, but...", "From my perspective...", "Softeners: kind of, sort of, quite, rather", "Debating: social media is good/bad", "Opinion practice: TV, technology, environment"]
            },
            {
                "id": "b1_m5", "title": "Medios y Cultura",
                "emoji": "🎬", "lessons": 8,
                "topics": ["Talking about movies: genre, plot, actors", "Books: What's it about? / The main character is...", "Music: I'm into... / I can't stand...", "TV shows and streaming", "Social media vocabulary", "Current events: talking about the news", "Recommending: You should watch... / It's worth...", "Culture dialogue: What did you do last weekend?"]
            },
            {
                "id": "b1_m6", "title": "Gramática Nivel Medio",
                "emoji": "⚙️", "lessons": 8,
                "topics": ["Passive voice: It was built in 1900", "Reported speech: She said that she was tired", "Modal verbs in the past: could have / should have", "Relative clauses: the man who / the city where", "Infinitive vs gerund: I like swimming / I want to swim", "Phrasal verbs (básicos): give up, look after, find out", "Connectors: although, despite, however, therefore", "Grammar review: B1 test practice"]
            },
        ]
    },
    "B2": {
        "label": "🟠 B2 — Intermedio Alto",
        "color": "#f97316",
        "lessons": 50,
        "modules": [
            {
                "id": "b2_m1", "title": "Fluidez y Naturalidad",
                "emoji": "🌊", "lessons": 10,
                "topics": ["Collocations: make a decision / take a risk", "Idioms: break the ice / once in a blue moon", "Discourse markers: in addition, on the other hand", "Hedging: It seems to me / As far as I know", "Fillers: you know, I mean, well, actually", "Sounding natural: contractions and weak forms", "American vs British English", "Speed and fluency practice", "Conversations without preparation", "Mock interview in English"]
            },
            {
                "id": "b2_m2", "title": "El Mundo Laboral",
                "emoji": "🏢", "lessons": 10,
                "topics": ["Writing a professional email", "Business meetings: agenda, minutes, AOB", "Presentations: Today I'm going to talk about...", "Negotiations: I'm afraid that's not possible / What if we...?", "Conference calls vocabulary", "Business idioms: touch base, ballpark figure", "Networking: small talk at events", "Formal complaints: I'm writing to express my concern", "Performance review language", "Business culture differences"]
            },
            {
                "id": "b2_m3", "title": "Debates y Argumentación",
                "emoji": "⚖️", "lessons": 10,
                "topics": ["Structuring an argument", "Thesis and counter-argument", "Statistics and evidence: According to research...", "Conceding a point: You have a point, but...", "Strengthening your argument: Not only that, but...", "Hot topics: climate change debate", "Ethics discussion: AI and jobs", "Media literacy: fact vs opinion", "Debate practice: for and against", "Formal presentation with Q&A"]
            },
            {
                "id": "b2_m4", "title": "Gramática Avanzada",
                "emoji": "🔬", "lessons": 10,
                "topics": ["Advanced passive: It is believed that... / It is said that...", "Complex conditionals: mixed conditionals", "Inversion for emphasis: Never have I seen...", "Cleft sentences: It was John who called", "Advanced relative clauses: whose, whom, whereby", "Noun clauses: The fact that... / What I need is...", "Advanced phrasal verbs: bring about, set off, carry out", "Ellipsis and substitution", "Emphatic do: I DO like it!", "Grammar test B2 level"]
            },
            {
                "id": "b2_m5", "title": "Temas del Mundo Real",
                "emoji": "🌍", "lessons": 10,
                "topics": ["Environment and sustainability", "Technology and the future", "Health and wellbeing", "Education systems around the world", "Economy: inflation, unemployment, GDP", "Politics: democracy, voting, elections", "Society: inequality, migration, diversity", "Science and innovation", "Sport and competition", "Arts and creativity: what is art?"]
            },
        ]
    },
    "C1C2": {
        "label": "🔴 C1/C2 — Avanzado",
        "color": "#dc2626",
        "lessons": 40,
        "modules": [
            {
                "id": "c1_m1", "title": "Precisión y Estilo",
                "emoji": "✨", "lessons": 8,
                "topics": ["Nuance in vocabulary: affect vs effect, imply vs infer", "Register: formal, informal, academic, journalistic", "Rhetorical devices: metaphor, irony, understatement", "Collocations at advanced level", "Connotation and pragmatics", "Style guide: writing professionally", "The art of persuasion", "Academic writing conventions"]
            },
            {
                "id": "c1_m2", "title": "Profesional y Académico",
                "emoji": "🎓", "lessons": 8,
                "topics": ["Academic writing: essays and reports", "Research methodology language", "Critical thinking in English", "Conference presenting at C1 level", "Cross-cultural communication", "Negotiating at executive level", "Legal and contractual language basics", "Medical/scientific language basics"]
            },
            {
                "id": "c1_m3", "title": "Inglés Nativo",
                "emoji": "🗣️", "lessons": 8,
                "topics": ["Advanced idioms and slang (appropriate contexts)", "Understanding native-speed speech", "British humour and understatement", "American cultural references", "Accents: UK, US, Australian, Indian", "News and documentary comprehension", "Literary English: novels and poetry", "Cinema without subtitles"]
            },
            {
                "id": "c1_m4", "title": "Conversación C1/C2",
                "emoji": "💡", "lessons": 8,
                "topics": ["Philosophy and abstract ideas", "Ethical dilemmas discussion", "Current events deep analysis", "Creative storytelling at C2 level", "Spontaneous debates any topic", "Translating difficult concepts", "Teaching others in English", "C2 proficiency mock exam"]
            },
            {
                "id": "c1_m5", "title": "Exámenes y Certificaciones",
                "emoji": "📜", "lessons": 8,
                "topics": ["Cambridge B2 First preparation", "IELTS Academic preparation", "TOEFL strategies", "C1 Advanced exam practice", "C2 Proficiency exam practice", "Writing band 8-9 essays", "Speaking test: how to impress examiners", "Full mock examination C1/C2"]
            },
        ]
    }
}

# ─────────────────────────────────────────────────────────────
#  PERSONAJES DEL CURSO
# ─────────────────────────────────────────────────────────────
CHARACTERS = {
    "emily":    {"name": "Emily", "emoji": "👩‍🏫", "role": "Profesora", "desc": "Paciente, motivadora. Tu profe principal.", "accent": "British"},
    "mike":     {"name": "Mike",  "emoji": "👨‍💼", "role": "Colega de trabajo", "desc": "Habla rápido y usa expresiones de negocios.", "accent": "American"},
    "officer":  {"name": "Officer Chen", "emoji": "👮", "role": "Oficial de policía", "desc": "Formal, claro, vocabulario específico.", "accent": "American"},
    "doctor":   {"name": "Dr. Sarah", "emoji": "👩‍⚕️", "role": "Médica", "desc": "Usa términos médicos, muy precisa.", "accent": "British"},
    "waiter":   {"name": "Carlos", "emoji": "🧑‍🍳", "role": "Mesero", "desc": "Amigable, vocabulario de restaurante.", "accent": "American"},
    "customs":  {"name": "Officer Kim", "emoji": "🛂", "role": "Aduanero", "desc": "Serio, preguntas de aduana y viajes.", "accent": "American"},
    "friend":   {"name": "Alex",  "emoji": "🧑", "role": "Amigo", "desc": "Informal, usa slang, conversación natural.", "accent": "Australian"},
    "interviewer": {"name": "Ms. Torres", "emoji": "👩‍💻", "role": "Entrevistadora de trabajo", "desc": "Profesional, evalúa tu inglés corporativo.", "accent": "American"},
}

# Vocabulario para juegos niños
VOCAB_KIDS = {
    "animals":  [{"e":"🐶","w":"Dog","es":"perro"},{"e":"🐱","w":"Cat","es":"gato"},{"e":"🐦","w":"Bird","es":"pájaro"},{"e":"🐟","w":"Fish","es":"pez"},{"e":"🐘","w":"Elephant","es":"elefante"},{"e":"🦁","w":"Lion","es":"león"},{"e":"🐻","w":"Bear","es":"oso"},{"e":"🐰","w":"Rabbit","es":"conejo"},{"e":"🦊","w":"Fox","es":"zorro"},{"e":"🐸","w":"Frog","es":"rana"},{"e":"🐯","w":"Tiger","es":"tigre"},{"e":"🦋","w":"Butterfly","es":"mariposa"}],
    "colors":   [{"e":"🔴","w":"Red","es":"rojo"},{"e":"🔵","w":"Blue","es":"azul"},{"e":"🟡","w":"Yellow","es":"amarillo"},{"e":"🟢","w":"Green","es":"verde"},{"e":"⚫","w":"Black","es":"negro"},{"e":"⚪","w":"White","es":"blanco"},{"e":"🟠","w":"Orange","es":"naranja"},{"e":"🟣","w":"Purple","es":"morado"},{"e":"🟤","w":"Brown","es":"marrón"},{"e":"🩷","w":"Pink","es":"rosa"}],
    "fruits":   [{"e":"🍎","w":"Apple","es":"manzana"},{"e":"🍌","w":"Banana","es":"banana"},{"e":"🍇","w":"Grapes","es":"uvas"},{"e":"🍓","w":"Strawberry","es":"frutilla"},{"e":"🍊","w":"Orange","es":"naranja"},{"e":"🍋","w":"Lemon","es":"limón"},{"e":"🍑","w":"Peach","es":"durazno"},{"e":"🍉","w":"Watermelon","es":"sandía"},{"e":"🍍","w":"Pineapple","es":"ananá"},{"e":"🥭","w":"Mango","es":"mango"}],
    "numbers":  [{"e":"1️⃣","w":"One","es":"uno"},{"e":"2️⃣","w":"Two","es":"dos"},{"e":"3️⃣","w":"Three","es":"tres"},{"e":"4️⃣","w":"Four","es":"cuatro"},{"e":"5️⃣","w":"Five","es":"cinco"},{"e":"6️⃣","w":"Six","es":"seis"},{"e":"7️⃣","w":"Seven","es":"siete"},{"e":"8️⃣","w":"Eight","es":"ocho"},{"e":"9️⃣","w":"Nine","es":"nueve"},{"e":"🔟","w":"Ten","es":"diez"}],
    "body":     [{"e":"👁️","w":"Eye","es":"ojo"},{"e":"👂","w":"Ear","es":"oreja"},{"e":"👃","w":"Nose","es":"nariz"},{"e":"👄","w":"Mouth","es":"boca"},{"e":"💪","w":"Arm","es":"brazo"},{"e":"🦵","w":"Leg","es":"pierna"},{"e":"🖐️","w":"Hand","es":"mano"},{"e":"👣","w":"Foot","es":"pie"},{"e":"🦷","w":"Tooth","es":"diente"},{"e":"💇","w":"Hair","es":"pelo"}],
    "clothes":  [{"e":"👕","w":"T-shirt","es":"remera"},{"e":"👖","w":"Pants","es":"pantalón"},{"e":"👟","w":"Shoes","es":"zapatillas"},{"e":"🧤","w":"Gloves","es":"guantes"},{"e":"🎩","w":"Hat","es":"sombrero"},{"e":"🧣","w":"Scarf","es":"bufanda"},{"e":"👗","w":"Dress","es":"vestido"},{"e":"🧦","w":"Socks","es":"medias"},{"e":"🧥","w":"Coat","es":"abrigo"},{"e":"👙","w":"Swimsuit","es":"malla"}],
}

ABC_DATA = {
    "A":{"word":"Apple","ipa":"/ˈæpəl/","es":"Manzana 🍎","sound":"The letter A makes the sound /æ/ like in cat, or /eɪ/ like in name"},
    "B":{"word":"Ball","ipa":"/bɔːl/","es":"Pelota ⚽","sound":"The letter B makes the sound /b/ like in boy, big, bag"},
    "C":{"word":"Cat","ipa":"/kæt/","es":"Gato 🐱","sound":"The letter C makes the sound /k/ like in cat, or /s/ like in city"},
    "D":{"word":"Dog","ipa":"/dɒɡ/","es":"Perro 🐶","sound":"The letter D makes the sound /d/ like in dog, day, door"},
    "E":{"word":"Egg","ipa":"/ɛɡ/","es":"Huevo 🥚","sound":"The letter E makes the sound /ɛ/ like in egg, or /iː/ like in she"},
    "F":{"word":"Fish","ipa":"/fɪʃ/","es":"Pez 🐟","sound":"The letter F makes the sound /f/ like in fish, food, fun"},
    "G":{"word":"Girl","ipa":"/ɡɜːrl/","es":"Niña 👧","sound":"The letter G makes the sound /ɡ/ like in girl, or /dʒ/ like in gym"},
    "H":{"word":"Hat","ipa":"/hæt/","es":"Sombrero 🎩","sound":"The letter H makes the sound /h/ like in hat, hot, happy"},
    "I":{"word":"Ice cream","ipa":"/aɪs kriːm/","es":"Helado 🍦","sound":"The letter I makes the sound /ɪ/ like in it, or /aɪ/ like in ice"},
    "J":{"word":"Juice","ipa":"/dʒuːs/","es":"Jugo 🧃","sound":"The letter J makes the sound /dʒ/ like in juice, jump, joy"},
    "K":{"word":"Kite","ipa":"/kaɪt/","es":"Cometa 🪁","sound":"The letter K makes the sound /k/ like in kite, king, kitchen"},
    "L":{"word":"Lion","ipa":"/ˈlaɪən/","es":"León 🦁","sound":"The letter L makes the sound /l/ like in lion, love, light"},
    "M":{"word":"Moon","ipa":"/muːn/","es":"Luna 🌙","sound":"The letter M makes the sound /m/ like in moon, mother, music"},
    "N":{"word":"Nose","ipa":"/noʊz/","es":"Nariz 👃","sound":"The letter N makes the sound /n/ like in nose, night, number"},
    "O":{"word":"Orange","ipa":"/ˈɒrɪndʒ/","es":"Naranja 🍊","sound":"The letter O makes the sound /ɒ/ like in orange, or /oʊ/ like in go"},
    "P":{"word":"Pizza","ipa":"/ˈpiːtsə/","es":"Pizza 🍕","sound":"The letter P makes the sound /p/ like in pizza, park, pen"},
    "Q":{"word":"Queen","ipa":"/kwiːn/","es":"Reina 👑","sound":"Q is always followed by U. It makes the sound /kw/ like in queen, quick"},
    "R":{"word":"Rainbow","ipa":"/ˈreɪnboʊ/","es":"Arcoíris 🌈","sound":"The letter R makes the sound /r/ like in rainbow, run, red"},
    "S":{"word":"Sun","ipa":"/sʌn/","es":"Sol ☀️","sound":"The letter S makes the sound /s/ like in sun, or /z/ like in rose"},
    "T":{"word":"Tree","ipa":"/triː/","es":"Árbol 🌳","sound":"The letter T makes the sound /t/ like in tree, time, talk"},
    "U":{"word":"Umbrella","ipa":"/ʌmˈbrɛlə/","es":"Paraguas ☂️","sound":"The letter U makes the sound /ʌ/ like in umbrella, or /juː/ like in uniform"},
    "V":{"word":"Violin","ipa":"/ˌvaɪəˈlɪn/","es":"Violín 🎻","sound":"The letter V makes the sound /v/ like in violin, very, voice"},
    "W":{"word":"Water","ipa":"/ˈwɔːtər/","es":"Agua 💧","sound":"The letter W makes the sound /w/ like in water, wind, work"},
    "X":{"word":"Xylophone","ipa":"/ˈzaɪləfoʊn/","es":"Xilófono 🎵","sound":"X makes the sound /z/ at the start (xylophone) or /ks/ in the middle (box, taxi)"},
    "Y":{"word":"Yellow","ipa":"/ˈjɛloʊ/","es":"Amarillo 🟡","sound":"The letter Y makes the sound /j/ like in yellow, year, yes"},
    "Z":{"word":"Zebra","ipa":"/ˈziːbrə/","es":"Cebra 🦓","sound":"The letter Z makes the sound /z/ like in zebra, zero, zone"},
}

PRON_WORDS = [
    {"e":"🍎","w":"Apple","ipa":"/ˈæp.əl/"},{"e":"🐶","w":"Dog","ipa":"/dɒɡ/"},
    {"e":"📚","w":"Book","ipa":"/bʊk/"},{"e":"🏠","w":"House","ipa":"/haʊs/"},
    {"e":"🚗","w":"Car","ipa":"/kɑːr/"},{"e":"🌳","w":"Tree","ipa":"/triː/"},
    {"e":"🍕","w":"Pizza","ipa":"/ˈpiːt.sə/"},{"e":"☀️","w":"Sun","ipa":"/sʌn/"},
    {"e":"🎵","w":"Music","ipa":"/ˈmjuː.zɪk/"},{"e":"💻","w":"Computer","ipa":"/kəmˈpjuː.tər/"},
    {"e":"✈️","w":"Airplane","ipa":"/ˈeər.pleɪn/"},{"e":"🌊","w":"Ocean","ipa":"/ˈoʊ.ʃən/"},
    {"e":"🌙","w":"Moon","ipa":"/muːn/"},{"e":"⭐","w":"Star","ipa":"/stɑːr/"},
    {"e":"🐱","w":"Cat","ipa":"/kæt/"},{"e":"🍌","w":"Banana","ipa":"/bəˈnɑː.nə/"},
    {"e":"🌺","w":"Flower","ipa":"/ˈflaʊ.ər/"},{"e":"🦋","w":"Butterfly","ipa":"/ˈbʌt.ər.flaɪ/"},
    {"e":"🌍","w":"World","ipa":"/wɜːrld/"},{"e":"🎉","w":"Celebrate","ipa":"/ˈsel.ɪ.breɪt/"},
]

BADGES = [
    {"id":"first_star","e":"🌟","n":"Primera Estrella","d":"Primeros 10 puntos"},
    {"id":"star_50","e":"⭐","n":"Coleccionista","d":"50 puntos acumulados"},
    {"id":"voice_5","e":"🎤","n":"Voz de Oro","d":"Practicaste pronunciación 5 veces"},
    {"id":"chat_10","e":"💬","n":"Gran Conversador","d":"10 mensajes al profe"},
    {"id":"lesson_5","e":"📖","n":"Estudioso","d":"Completaste 5 lecciones"},
    {"id":"star_200","e":"🏆","n":"Campeón","d":"200 puntos acumulados"},
    {"id":"streak_7","e":"🔥","n":"Racha de Fuego","d":"7 días seguidos"},
    {"id":"star_500","e":"🎓","n":"Maestro del Inglés","d":"500 puntos totales"},
    {"id":"perfect_pron","e":"💎","n":"Pronunciación Perfecta","d":"100% en pronunciación"},
    {"id":"all_abc","e":"🔤","n":"Maestro del Alfabeto","d":"Repasaste todo el ABC"},
]

# ─────────────────────────────────────────────────────────────
#  HTML PRINCIPAL
# ─────────────────────────────────────────────────────────────

ACADEMIA_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>🎓 Academia Foschi IA</title>
<style>
/* ── Reset & Tokens ── */
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --ink:#1a1235;--ink2:#4c3a8a;--ink3:#7c6bb0;
  --bg:#f4f2ff;--bg2:#ffffff;--bg3:#ede9fe;
  --pur:#6c3fc5;--pur2:#9061ea;--pur3:#c4b5fd;--pur4:#ede9fe;
  --grn:#10b981;--grn2:#d1fae5;
  --red:#ef4444;--red2:#fee2e2;
  --amb:#f59e0b;--amb2:#fef3c7;
  --blu:#3b82f6;--blu2:#dbeafe;
  --kids-bg:#fff8ed;--kids-acc:#f59e0b;--kids-ink:#92400e;
  --rad:14px;--rad-sm:8px;--rad-lg:20px;--rad-pill:999px;
  --shadow:0 2px 20px rgba(108,63,197,.12);
  --shadow-lg:0 8px 40px rgba(108,63,197,.18);
  --font:'Segoe UI',system-ui,sans-serif;
  --transition:all .22s cubic-bezier(.4,0,.2,1);
}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--bg);color:var(--ink);min-height:100vh;overflow-x:hidden}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--pur3);border-radius:10px}

/* ── Header ── */
.header{
  background:linear-gradient(135deg,#4a1fa8 0%,#7c3aed 50%,#9333ea 100%);
  color:#fff;padding:14px 20px 12px;position:sticky;top:0;z-index:100;
  box-shadow:0 4px 24px rgba(108,63,197,.35);
}
.header-inner{max-width:900px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.header h1{font-size:1.4rem;font-weight:800;letter-spacing:-.3px}
.header-sub{font-size:.75rem;opacity:.8;margin-top:1px}
.header-cefr{display:flex;gap:6px;flex-wrap:wrap}
.cefr-badge{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);border-radius:var(--rad-pill);padding:3px 10px;font-size:.7rem;font-weight:700;cursor:pointer;transition:var(--transition)}
.cefr-badge:hover,.cefr-badge.on{background:rgba(255,255,255,.9);color:var(--pur)}

/* ── Mode switcher ── */
.mode-bar{display:flex;gap:10px;justify-content:center;padding:16px 16px 4px}
.mbtn{
  flex:1;max-width:200px;padding:14px 12px;border-radius:var(--rad);border:2.5px solid transparent;
  cursor:pointer;font-weight:700;font-size:.92rem;text-align:center;transition:var(--transition);
  box-shadow:var(--shadow);background:#fff
}
.mbtn.adult{color:var(--pur);border-color:var(--pur)}
.mbtn.adult.on{background:linear-gradient(135deg,var(--pur),var(--pur2));color:#fff;box-shadow:0 4px 20px rgba(108,63,197,.35)}
.mbtn.kids{color:var(--kids-ink);border-color:var(--kids-acc);background:var(--kids-bg)}
.mbtn.kids.on{background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#fff;border-color:transparent;box-shadow:0 4px 20px rgba(245,158,11,.35)}
.mbtn .ico{font-size:1.7rem;display:block;margin-bottom:3px}

/* ── Layout ── */
.main{max-width:900px;margin:0 auto;padding:8px 14px 60px}

/* ── Tabs ── */
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0 10px;padding:2px}
.tab{
  padding:7px 14px;border-radius:var(--rad-pill);border:2px solid var(--pur3);
  background:#fff;color:var(--pur);font-weight:600;cursor:pointer;font-size:.8rem;
  transition:var(--transition);white-space:nowrap
}
.tab.on{background:var(--pur);color:#fff;border-color:var(--pur);box-shadow:0 2px 10px rgba(108,63,197,.3)}
.tab:hover:not(.on){background:var(--pur4);border-color:var(--pur)}
.ktab{border-color:#fed7aa;color:var(--kids-ink)}
.ktab.on{background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#fff;border-color:transparent}

/* ── Cards ── */
.card{background:#fff;border-radius:var(--rad);padding:18px;box-shadow:var(--shadow);margin-bottom:14px}
.card-hd{color:var(--pur);font-size:1rem;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px}

/* ── Sections ── */
.sec{display:none}.sec.on{display:block}

/* ── Chat ── */
#chatBox,#kidsChatBox{
  height:300px;overflow-y:auto;background:var(--bg);border-radius:var(--rad-sm);
  padding:12px;display:flex;flex-direction:column;gap:8px;margin-bottom:10px
}
#kidsChatBox{background:#fff8ed}
.msg{max-width:84%;padding:10px 14px;border-radius:12px;line-height:1.55;font-size:.875rem}
.msg.ai{background:#fff;border:1.5px solid var(--pur3);align-self:flex-start;color:var(--ink)}
.msg.usr{background:linear-gradient(135deg,var(--pur),var(--pur2));color:#fff;align-self:flex-end}
.msg.corr{background:var(--amb2);border:1.5px solid #fcd34d;color:#78350f;align-self:flex-start;font-size:.8rem;border-radius:10px}
.msg.kid-ai{background:#fff3e0;border:1.5px solid #fed7aa;align-self:flex-start;color:#78350f}
.msg-avatar{font-size:1.1rem;margin-bottom:3px;display:block}
.msg-name{font-size:.68rem;font-weight:700;opacity:.6;margin-bottom:2px}

/* ── Input row ── */
.row{display:flex;gap:8px;align-items:center}
.row input,.inp{
  flex:1;padding:10px 14px;border-radius:var(--rad-pill);border:2px solid var(--pur3);
  font-size:.88rem;outline:none;transition:border .2s;font-family:var(--font);background:#fff
}
.row input:focus,.inp:focus{border-color:var(--pur);box-shadow:0 0 0 3px rgba(108,63,197,.12)}
textarea{
  width:100%;padding:11px 14px;border-radius:var(--rad);border:2px solid var(--pur3);
  font-size:.88rem;resize:vertical;min-height:90px;outline:none;
  font-family:var(--font);transition:border .2s;background:#fff
}
textarea:focus{border-color:var(--pur);box-shadow:0 0 0 3px rgba(108,63,197,.12)}

/* ── Buttons ── */
.btn{
  padding:9px 18px;border-radius:var(--rad-pill);border:none;
  background:linear-gradient(135deg,var(--pur),var(--pur2));color:#fff;
  font-weight:700;cursor:pointer;font-size:.83rem;transition:var(--transition);
  white-space:nowrap;display:inline-flex;align-items:center;gap:5px
}
.btn:hover:not(:disabled){opacity:.88;transform:translateY(-1px)}
.btn:disabled{opacity:.45;cursor:default;transform:none}
.btn.sm{padding:6px 13px;font-size:.76rem}
.btn.grn{background:linear-gradient(135deg,var(--grn),#059669)}
.btn.org{background:linear-gradient(135deg,var(--amb),#d97706)}
.btn.red{background:linear-gradient(135deg,var(--red),#dc2626)}
.btn.ghost{background:transparent;color:var(--pur);border:2px solid var(--pur3)}
.btn.ghost:hover{background:var(--pur4)}

/* ── Progress bars ── */
.bar-wrap{background:#e5e7eb;border-radius:var(--rad-pill);height:12px;overflow:hidden;margin:5px 0}
.bar{height:100%;border-radius:var(--rad-pill);transition:width .6s ease;background:linear-gradient(90deg,var(--grn),#34d399)}

/* ── Chips ── */
.chips{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}
.chip{
  padding:6px 14px;border-radius:var(--rad-pill);border:2px solid var(--pur3);
  background:#fff;cursor:pointer;font-weight:600;color:var(--pur2);font-size:.79rem;
  transition:var(--transition)
}
.chip.on,.chip:hover{background:var(--pur);color:#fff;border-color:var(--pur)}
.kchip{color:var(--kids-ink);border-color:#fed7aa}
.kchip.on,.kchip:hover{background:var(--kids-acc);color:#fff;border-color:var(--kids-acc)}

/* ── Character cards ── */
.char-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin-bottom:14px}
.char-card{
  border:2.5px solid var(--pur3);border-radius:var(--rad);padding:12px;text-align:center;
  cursor:pointer;transition:var(--transition);background:#fff
}
.char-card:hover,.char-card.on{border-color:var(--pur);background:var(--pur4);transform:translateY(-2px);box-shadow:var(--shadow)}
.char-card.on{border-color:var(--pur);background:var(--pur);color:#fff}
.char-card.on .char-role{color:rgba(255,255,255,.75)}
.char-emoji{font-size:2.2rem;display:block;margin-bottom:5px}
.char-name{font-weight:700;font-size:.85rem}
.char-role{font-size:.72rem;color:var(--ink3);margin-top:2px}

/* ── Curriculum tree ── */
.level-nav{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.lvl-btn{
  padding:7px 16px;border-radius:var(--rad-pill);border:2.5px solid var(--pur3);
  font-size:.8rem;font-weight:700;cursor:pointer;color:var(--ink3);transition:var(--transition);
  background:#fff
}
.lvl-btn.on{color:#fff;border-color:transparent;box-shadow:0 3px 12px rgba(0,0,0,.15)}
.module-list{display:flex;flex-direction:column;gap:10px}
.module-card{
  border:2px solid #e5e7eb;border-radius:var(--rad);overflow:hidden;
  transition:var(--transition);background:#fff
}
.module-card:hover{border-color:var(--pur3);box-shadow:var(--shadow)}
.module-hd{
  display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer;
  user-select:none
}
.module-emoji{font-size:1.5rem}
.module-title{font-weight:700;font-size:.9rem;color:var(--ink);flex:1}
.module-count{font-size:.75rem;color:var(--ink3);background:var(--bg3);padding:2px 8px;border-radius:var(--rad-pill)}
.module-arrow{color:var(--ink3);font-size:.8rem;transition:transform .2s}
.module-card.open .module-arrow{transform:rotate(180deg)}
.module-body{display:none;padding:0 14px 14px}
.module-card.open .module-body{display:block}
.lesson-list{display:flex;flex-direction:column;gap:6px;margin-top:8px}
.lesson-item{
  display:flex;align-items:center;gap:10px;padding:9px 12px;
  border-radius:var(--rad-sm);border:1.5px solid #f0f0f0;cursor:pointer;
  transition:var(--transition);background:#fafafa
}
.lesson-item:hover{background:var(--pur4);border-color:var(--pur3)}
.lesson-item.done{background:var(--grn2);border-color:#a7f3d0}
.lesson-item.active{background:var(--pur);color:#fff;border-color:var(--pur)}
.lesson-num{font-size:.7rem;font-weight:700;color:var(--ink3);min-width:22px}
.lesson-item.active .lesson-num{color:rgba(255,255,255,.7)}
.lesson-name{font-size:.82rem;font-weight:600;flex:1}
.lesson-done-ico{font-size:.85rem}

/* ── Pronunciation ── */
.pron-word{font-size:2.5rem;font-weight:800;color:var(--pur);text-align:center;letter-spacing:1px;padding:10px 0 2px}
.pron-ipa{font-size:1rem;color:var(--pur3);text-align:center;margin-bottom:6px}
.pron-emoji{font-size:3.5rem;text-align:center;display:block;margin:4px 0}
.sound-indicator{
  display:flex;align-items:center;justify-content:center;gap:4px;
  height:40px;margin:8px 0
}
.sound-bar{
  width:4px;height:8px;background:var(--pur3);border-radius:3px;
  transition:height .1s ease;min-height:4px
}

/* ── Level indicator ── */
.level-pill{
  display:inline-flex;align-items:center;gap:5px;padding:4px 12px;
  border-radius:var(--rad-pill);font-size:.75rem;font-weight:700;
  background:var(--pur4);color:var(--pur)
}
.adaptive-msg{
  padding:8px 12px;border-radius:var(--rad-sm);font-size:.78rem;font-weight:600;
  margin-bottom:10px;border-left:3px solid var(--grn)
}
.adaptive-msg.up{background:var(--grn2);color:#065f46;border-color:var(--grn)}
.adaptive-msg.down{background:var(--amb2);color:#78350f;border-color:var(--amb)}

/* ── Skill scores ── */
.skill-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px;margin:10px 0}
.skill-card{border-radius:var(--rad);padding:12px;text-align:center;background:#fff;border:2px solid #f0f0f0}
.skill-emoji{font-size:1.6rem;margin-bottom:4px;display:block}
.skill-name{font-size:.72rem;font-weight:700;color:var(--ink2);margin-bottom:4px}
.skill-pct{font-size:1.1rem;font-weight:800}
.pct-g{color:var(--grn)}.pct-m{color:var(--amb)}.pct-l{color:var(--red)}

/* ── Kids section ── */
.kidsec{background:var(--kids-bg);border-radius:var(--rad);padding:14px;min-height:60vh}
.star-bar{
  display:flex;align-items:center;justify-content:flex-end;gap:6px;
  font-weight:800;color:var(--kids-ink);font-size:.9rem;padding:2px 0 10px
}
.star-count{font-size:1.2rem;font-weight:900;color:var(--kids-acc)}
.big-emi{font-size:4.5rem;text-align:center;display:block;margin:8px 0;line-height:1}
.gq{font-size:1.1rem;font-weight:800;text-align:center;color:var(--kids-ink);margin-bottom:14px}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.opt{
  padding:13px;border-radius:12px;border:2.5px solid #fed7aa;background:#fff;
  font-size:.95rem;font-weight:700;cursor:pointer;transition:var(--transition);
  color:var(--kids-ink);text-align:center
}
.opt:hover:not(:disabled){background:var(--kids-bg);border-color:var(--kids-acc);transform:scale(1.02)}
.opt.ok{background:#d1fae5;border-color:var(--grn);color:#065f46;pointer-events:none}
.opt.ng{background:var(--red2);border-color:var(--red);color:#7f1d1d;pointer-events:none}
.memo-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.mc{
  aspect-ratio:1;border-radius:14px;background:linear-gradient(135deg,var(--pur),var(--pur2));
  display:flex;align-items:center;justify-content:center;font-size:2.8rem;
  cursor:pointer;transition:var(--transition);user-select:none;border:2px solid transparent;
  color:#fff;font-weight:700;min-height:90px
}
.mc:hover:not(.flipped):not(.match){transform:scale(1.06)}
.mc.flipped{background:#fff;border-color:var(--pur3);color:var(--ink);font-size:1.1rem}
.mc.match{background:var(--grn2);border-color:var(--grn);pointer-events:none;color:#065f46}
.abc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(52px,1fr));gap:5px;margin-bottom:14px}
.abc-btn{
  padding:8px 4px;border-radius:var(--rad-sm);background:var(--pur4);
  border:2px solid var(--pur3);font-size:.9rem;font-weight:800;cursor:pointer;
  color:var(--pur);text-align:center;transition:var(--transition)
}
.abc-btn:hover{background:var(--pur);color:#fff}
.word-card{
  background:var(--pur4);border-radius:var(--rad);padding:18px;
  text-align:center;margin-bottom:14px;border:2px solid var(--pur3)
}
.word-en{font-size:2rem;font-weight:800;color:var(--pur)}
.word-es{font-size:.95rem;color:var(--pur2);margin-top:5px}
.word-ipa{font-size:.85rem;color:var(--pur3);margin-top:3px;font-style:italic}
.word-sound{font-size:.78rem;color:var(--ink3);margin-top:6px;line-height:1.4}

/* ── Badges ── */
.bdg-grid{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px}
.bdg{text-align:center;width:86px}
.bdg .be{font-size:2.2rem;filter:grayscale(0)}
.bdg.locked .be{filter:grayscale(1);opacity:.35}
.bdg .bn{font-weight:700;font-size:.7rem;color:var(--ink2);margin-top:3px}
.bdg .bl{font-size:.62rem;color:var(--ink3)}

/* ── Popup ── */
.popup{
  position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) scale(0);
  background:#fff;border-radius:24px;padding:28px 36px;
  box-shadow:0 20px 60px rgba(0,0,0,.25);z-index:9999;
  text-align:center;transition:transform .3s cubic-bezier(.34,1.56,.64,1);
  pointer-events:none;min-width:220px
}
.popup.show{transform:translate(-50%,-50%) scale(1);pointer-events:auto}
.popup .pe{font-size:3.5rem;display:block;margin-bottom:6px}
.popup h3{font-size:1.25rem;color:var(--pur);font-weight:800}
.popup p{color:var(--ink3);margin-top:4px;font-size:.85rem}

/* ── Corrector ── */
.corr-box{
  background:#f0fdf4;border:1.5px solid #a7f3d0;border-radius:var(--rad);
  padding:14px;margin-top:10px;color:#065f46;line-height:1.65;
  white-space:pre-wrap;font-size:.85rem
}
.err-box{background:var(--red2);border-color:#fecdd3;color:#881337}

/* ── Spinner ── */
.spin{
  display:inline-block;width:14px;height:14px;
  border:2px solid rgba(255,255,255,.3);border-top-color:#fff;
  border-radius:50%;animation:spin .5s linear infinite;vertical-align:middle
}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── Feedback indicators ── */
.fb{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:var(--rad-pill);font-size:.75rem;font-weight:700}
.fb.perfect{background:#d1fae5;color:#065f46}
.fb.almost{background:var(--amb2);color:#78350f}
.fb.mistake{background:var(--red2);color:#7f1d1d}

/* ── Responsive ── */
@media(max-width:600px){
  .header h1{font-size:1.2rem}
  .opts{grid-template-columns:1fr}
  .memo-grid{grid-template-columns:repeat(2,1fr)}
  .mbtn{max-width:100%;width:100%}
  .mode-bar{flex-direction:column;align-items:center}
  .char-grid{grid-template-columns:repeat(auto-fill,minmax(100px,1fr))}
  .skill-grid{grid-template-columns:repeat(auto-fill,minmax(90px,1fr))}
  .header-cefr{display:none}
}
</style>
</head>
<body>

<!-- ══ HEADER ══ -->
<div class="header">
  <div class="header-inner">
    <div>
      <h1>🎓 Academia Foschi IA</h1>
    </div>
    <div class="header-cefr" id="cefrNav">
      <div class="cefr-badge on" onclick="jumpToLevel('A0',this)">A0</div>
      <div class="cefr-badge" onclick="jumpToLevel('A1',this)">A1</div>
      <div class="cefr-badge" onclick="jumpToLevel('A2',this)">A2</div>
      <div class="cefr-badge" onclick="jumpToLevel('B1',this)">B1</div>
      <div class="cefr-badge" onclick="jumpToLevel('B2',this)">B2</div>
      <div class="cefr-badge" onclick="jumpToLevel('C1C2',this)">C1/C2</div>
      <a href="/" style="background:rgba(255,255,255,.9);color:#6c3fc5;border-radius:999px;padding:3px 12px;font-size:.72rem;font-weight:800;text-decoration:none;display:inline-flex;align-items:center;gap:4px;margin-left:6px;">⬅ Foschi IA</a>
    </div>
  </div>
</div>

<!-- ══ MODE SWITCHER ══ -->
<div class="mode-bar">
  <button class="mbtn adult on" id="btnA" onclick="setMode('adult')">
    <span class="ico">🧑</span>Adultos
  </button>
  <button class="mbtn kids" id="btnK" onclick="setMode('kids')">
    <span class="ico">👶</span>Niños
  </button>
</div>

<div class="main">

<!-- ══════════════════════════════ ADULTOS ══════════════════════════════ -->
<div id="mAdult">
  <div class="tabs">
    <button class="tab on"  onclick="aTab('curso',this)">📚 Curso</button>
    <button class="tab"     onclick="aTab('conv',this)">💬 Conversación</button>
    <button class="tab"     onclick="aTab('pron',this)">🎤 Pronunciación</button>
    <button class="tab"     onclick="aTab('corrector',this)">✍️ Corrector</button>
    <button class="tab"     onclick="aTab('prog',this)">📈 Progreso</button>
  </div>

  <!-- ── CURSO ── -->
  <div id="t-curso" class="sec on">
    <div class="card">
      <div class="card-hd">📚 Tu Ruta de Aprendizaje — CEFR</div>
      <div class="level-nav" id="levelNav"></div>
      <div class="module-list" id="moduleList"></div>
    </div>
  </div>

  <!-- ── CONVERSACIÓN ── -->
  <div id="t-conv" class="sec">
    <div class="card">
      <div class="card-hd">
        <span>💬 Conversación con tu Profe</span>
        <span class="level-pill" id="convLevelPill">🌱 A0</span>
        <button id="btnTTS" onclick="toggleTTS()" class="btn ghost sm" style="margin-left:auto" title="Activar/desactivar voz del profesor">🔊 Voz ON</button>
      </div>

      <!-- Selector de personaje -->
      <p style="font-size:.8rem;color:var(--ink3);margin-bottom:8px">
        Elegí con quién practicar hoy:
      </p>
      <div class="char-grid" id="charGrid"></div>

      <!-- Selector de tema -->
      <div class="chips" id="topicChips">
        <div class="chip on" onclick="setTopic(this,'greetings')">👋 Saludos</div>
        <div class="chip" onclick="setTopic(this,'work')">💼 Trabajo</div>
        <div class="chip" onclick="setTopic(this,'travel')">✈️ Viajes</div>
        <div class="chip" onclick="setTopic(this,'restaurant')">🍽️ Restaurante</div>
        <div class="chip" onclick="setTopic(this,'medical')">🏥 Médico</div>
        <div class="chip" onclick="setTopic(this,'family')">👨‍👩‍👧 Familia</div>
        <div class="chip" onclick="setTopic(this,'shopping')">🛒 Compras</div>
        <div class="chip" onclick="setTopic(this,'opinion')">💭 Debate</div>
        <div class="chip" onclick="setTopic(this,'job_interview')">🏢 Entrevista</div>
        <div class="chip" onclick="setTopic(this,'free')">🗣️ Libre</div>
      </div>

      <!-- Feedback adaptativo -->
      <div id="adaptiveMsg" style="display:none"></div>

      <!-- Chat box -->
      <div id="chatBox"></div>
      <div class="row">
        <input id="chatIn" placeholder="Escribí en inglés..." onkeydown="if(event.key==='Enter')sendChat()"/>
        <button class="btn" onclick="sendChat()" id="btnSend">Enviar</button>
        <button class="btn ghost" onclick="speakInput()" title="Pronunciar mi texto">🔊</button>
      </div>
    </div>
  </div>

  <!-- ── PRONUNCIACIÓN ── -->
  <div id="t-pron" class="sec">
    <div class="card">
      <div class="card-hd">🎤 Pronunciación</div>
      <span class="pron-emoji" id="pronEmi">🍎</span>
      <div class="pron-word" id="pronW">Apple</div>
      <div class="pron-ipa" id="pronIpa">/ˈæp.əl/</div>
      <p style="text-align:center;color:var(--ink3);font-size:.78rem;margin-bottom:10px">
        Escuchá → prestá atención al sonido → repetí
      </p>
      <div class="sound-indicator" id="soundBars">
        <div class="sound-bar"></div><div class="sound-bar"></div><div class="sound-bar"></div>
        <div class="sound-bar"></div><div class="sound-bar"></div><div class="sound-bar"></div>
        <div class="sound-bar"></div><div class="sound-bar"></div>
      </div>
      <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:10px 0">
        <button class="btn org" onclick="listenWord()">🔊 Escuchar</button>
        <button class="btn grn" onclick="startPron()" id="btnPron">🎤 Hablar</button>
        <button class="btn ghost" onclick="nextPron()">Siguiente ➜</button>
      </div>
      <div id="pronRes"></div>
    </div>
  </div>

  <!-- ── CORRECTOR ── -->
  <div id="t-corrector" class="sec">
    <div class="card">
      <div class="card-hd">✍️ Corrector de Inglés</div>
      <p style="color:var(--ink3);font-size:.8rem;margin-bottom:10px">
        Escribí cualquier texto en inglés. La IA lo corrige y explica cada error en español con la regla gramatical.
      </p>
      <textarea id="corrTxt" placeholder="Ej: I have 25 years old. Yesterday I go to the market and buyed some things..."></textarea>
      <button class="btn" style="margin-top:8px;width:100%" onclick="correctText()" id="btnCorr">
        🔍 Corregir texto
      </button>
      <div id="corrRes"></div>
    </div>
  </div>

  <!-- ── PROGRESO ── -->
  <div id="t-prog" class="sec">
    <div class="card">
      <div class="card-hd">📈 Tu Progreso</div>
      <div class="skill-grid" id="skillGrid"></div>
      <hr style="border:none;border-top:1px solid #f0f0f0;margin:14px 0"/>
      <p style="font-size:.8rem;font-weight:700;color:var(--ink2);margin-bottom:10px">Temas por habilidad</p>
      <div id="progList"></div>
      <button class="btn ghost" style="margin-top:12px" onclick="loadProg()">🔄 Actualizar</button>
    </div>
  </div>
</div>

<!-- ══════════════════════════════ NIÑOS ══════════════════════════════ -->
<div id="mKids" style="display:none">
  <div class="kidsec">
    <div class="star-bar">
      ⭐ <span class="star-count" id="stC">0</span> puntos
    </div>

    <div class="tabs">
      <button class="tab ktab on" onclick="kTab('abcLearn',this)">🔤 ABC</button>
      <button class="tab ktab" onclick="kTab('games',this)">🎮 Juegos</button>
      <button class="tab ktab" onclick="kTab('memo',this)">🃏 Memotest</button>
      <button class="tab ktab" onclick="kTab('kpron',this)">🎤 Pronunciar</button>
      <button class="tab ktab" onclick="kTab('kchat',this)">🧑‍🏫 Profe</button>
      <button class="tab ktab" onclick="kTab('badges',this)">🏆 Logros</button>
    </div>

    <!-- ABC -->
    <div id="t-abcLearn" class="sec on">
      <div class="card">
        <div class="card-hd">🔤 Aprendé el Abecedario en Inglés</div>
        <p style="color:var(--ink3);font-size:.8rem;margin-bottom:10px">
          Tocá una letra para escucharla y aprender su pronunciación 🎵
        </p>
        <div class="abc-grid" id="abcGrid"></div>
        <div id="letterInfo" style="display:none">
          <div class="word-card">
            <div class="word-en" id="liLetter">A</div>
            <div class="word-es" id="liWord">Apple 🍎</div>
            <div class="word-ipa" id="liIpa">/ˈæpəl/</div>
            <div class="word-sound" id="liSound">The letter A makes the sound /æ/ like in cat</div>
          </div>
          <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:10px">
            <button class="btn org" onclick="speakLetter()">🔊 Escuchar</button>
            <button class="btn grn" onclick="kidsSpeak2()" id="btnKSpk2">🎤 Repetir</button>
            <button class="btn ghost" onclick="nextABCLetter()">Siguiente ➜</button>
          </div>
          <div id="letterResult"></div>
        </div>
      </div>
    </div>

    <!-- JUEGOS -->
    <div id="t-games" class="sec">
      <div class="card">
        <div class="card-hd">🎮 ¿Qué es esto?</div>
        <div class="chips">
          <div class="chip kchip on" onclick="setKTopic(this,'animals')">🐶 Animales</div>
          <div class="chip kchip" onclick="setKTopic(this,'colors')">🎨 Colores</div>
          <div class="chip kchip" onclick="setKTopic(this,'fruits')">🍎 Frutas</div>
          <div class="chip kchip" onclick="setKTopic(this,'numbers')">🔢 Números</div>
          <div class="chip kchip" onclick="setKTopic(this,'body')">🦴 Cuerpo</div>
          <div class="chip kchip" onclick="setKTopic(this,'clothes')">👕 Ropa</div>
        </div>
        <span class="big-emi" id="gEmi">🐶</span>
        <div class="gq" id="gQ">What animal is this?</div>
        <div class="opts" id="optsGrid"></div>
        <div style="text-align:center;margin-top:14px;display:flex;gap:8px;justify-content:center">
          <button class="btn org" onclick="nextGame()">➜ Siguiente</button>
          <button class="btn ghost" onclick="kidsHearWord()">🔊 Escuchar</button>
        </div>
      </div>
    </div>

    <!-- MEMOTEST -->
    <div id="t-memo" class="sec">
      <div class="card">
        <div class="card-hd">🃏 Memotest</div>
        <p style="color:var(--ink3);font-size:.8rem;margin-bottom:10px">
          Emparejá el emoji con su palabra en inglés. ¡Memoria! 🧠
        </p>
        <div class="chips">
          <div class="chip kchip on" onclick="setMemoTopic(this,'animals')">🐶 Animales</div>
          <div class="chip kchip" onclick="setMemoTopic(this,'fruits')">🍎 Frutas</div>
          <div class="chip kchip" onclick="setMemoTopic(this,'colors')">🎨 Colores</div>
        </div>
        <div class="memo-grid" id="memoGrid"></div>
        <button class="btn" style="margin-top:12px;width:100%" onclick="initMemo()">🔄 Nuevo juego</button>
      </div>
    </div>

    <!-- PRONUNCIACIÓN NIÑOS -->
    <div id="t-kpron" class="sec">
      <div class="card" style="text-align:center">
        <div class="card-hd" style="justify-content:center">🎤 ¡Aprendé a decirlo!</div>
        <span class="big-emi" id="kpEmi">🍎</span>
        <div class="pron-word" id="kpW">Apple</div>
        <div class="pron-ipa" id="kpIpa">/ˈæp.əl/</div>
        <p style="color:var(--ink3);font-size:.8rem;margin:8px 0 14px">
          Primero escuchá despacio, después decilo vos 😄
        </p>
        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:14px">
          <button class="btn org" onclick="kListen()">🔊 Escuchar</button>
          <button class="btn grn" onclick="kSpeak()" id="btnKS">🎤 ¡Lo digo yo!</button>
          <button class="btn ghost" onclick="nextKWord()">Siguiente ➜</button>
        </div>
        <div id="kVR"></div>
      </div>
    </div>

    <!-- CHAT NIÑOS -->
    <div id="t-kchat" class="sec">
      <div class="card">
        <div class="card-hd">🧑‍🏫 Hablá con el Profe</div>
        <div id="kidsChatBox"></div>
        <div class="row">
          <input id="kChatIn" placeholder="Escribí en inglés o español..." onkeydown="if(event.key==='Enter')sendKChat()"/>
          <button class="btn org" onclick="sendKChat()">Enviar</button>
        </div>
      </div>
    </div>

    <!-- LOGROS -->
    <div id="t-badges" class="sec">
      <div class="card">
        <div class="card-hd">🏆 Tus Logros</div>
        <div class="bdg-grid" id="bdgList"></div>
      </div>
    </div>

  </div><!-- kidsec -->
</div><!-- mKids -->

</div><!-- main -->

<!-- ══ POPUP ══ -->
<div class="popup" id="popup">
  <span class="pe" id="pEmi">⭐</span>
  <h3 id="pTit">¡Muy bien!</h3>
  <p id="pMsg">¡Seguí así!</p>
</div>

</body>
</html>
"""

#!/usr/bin/env python3
# coding: utf-8
"""
academia_ingles_parte_2.py — Academia Foschi IA  ▸ VERSIÓN 2.0
═══════════════════════════════════════════════════════════
  PARTE 2 — JavaScript completo: Adultos
  · Currículo CEFR interactivo
  · Selector de personajes
  · Conversación con IA y aprendizaje adaptativo
  · Pronunciación con feedback
  · Corrector gramatical
  · Sistema de progreso y repaso
  (ensamblar con parte1.py y parte3.py)
═══════════════════════════════════════════════════════════
"""

ACADEMIA_JS_PART2 = r"""
<script>
// ═══════════════════════════════════════════════════════════
//  ESTADO GLOBAL
// ═══════════════════════════════════════════════════════════
const ST = {
  mode: 'adult',          // 'adult' | 'kids'
  level: 'A0',            // nivel CEFR actual del alumno
  char: 'emily',          // personaje activo
  topic: 'greetings',     // tema de conversación
  history: [],            // historial de mensajes (chat adultos)
  lessonsDone: new Set(),  // lecciones completadas
  activeLesson: null,      // lección activa actual
  // Aprendizaje adaptativo
  adaptive: {
    streak: 0,            // respuestas correctas seguidas
    errors: 0,            // errores en la sesión
    msgCount: 0,          // mensajes enviados
    difficulty: 'normal', // 'easy' | 'normal' | 'hard'
    errorTopics: {},      // topic -> count de errores
  },
  // Progreso por habilidad
  skills: {
    listening:   { done: 0, total: 50 },
    speaking:    { done: 0, total: 50 },
    reading:     { done: 0, total: 50 },
    writing:     { done: 0, total: 50 },
    grammar:     { done: 0, total: 50 },
  },
  pronIdx: 0,             // índice en lista de pronunciación
  currentWord: null,      // palabra actual en pronunciación
  ttsEnabled: true,       // profesor lee en voz alta
};

// Currículum completo inyectado desde Python
const CURRICULUM = """ + "CURRICULUM_PLACEHOLDER" + r""";

// Personajes inyectados desde Python
const CHARACTERS = """ + "CHARACTERS_PLACEHOLDER" + r""";

// Palabras de pronunciación inyectadas desde Python
const PRON_WORDS = """ + "PRON_WORDS_PLACEHOLDER" + r""";

// ═══════════════════════════════════════════════════════════
//  MODO (Adultos / Niños)
// ═══════════════════════════════════════════════════════════
function setMode(m) {
  ST.mode = m;
  document.getElementById('mAdult').style.display = m === 'adult' ? '' : 'none';
  document.getElementById('mKids').style.display  = m === 'kids'  ? '' : 'none';
  document.getElementById('btnA').classList.toggle('on', m === 'adult');
  document.getElementById('btnK').classList.toggle('on', m === 'kids');
  if (m === 'adult') { renderCurriculum(); renderCharGrid(); }
  if (m === 'kids')  { initKids(); }
}

// ═══════════════════════════════════════════════════════════
//  TABS ADULTOS
// ═══════════════════════════════════════════════════════════
function aTab(id, el) {
  document.querySelectorAll('#mAdult .sec').forEach(s => s.classList.remove('on'));
  document.querySelectorAll('#mAdult .tab').forEach(t => t.classList.remove('on'));
  document.getElementById('t-' + id).classList.add('on');
  el.classList.add('on');
  if (id === 'prog') loadProg();
  if (id === 'pron' && !ST.currentWord) nextPron();
}

// ═══════════════════════════════════════════════════════════
//  CURRÍCULO — renderizado interactivo
// ═══════════════════════════════════════════════════════════
let currentCurrLevel = 'A0';

function renderCurriculum(lvl) {
  lvl = lvl || currentCurrLevel;
  currentCurrLevel = lvl;
  const data = CURRICULUM[lvl];
  if (!data) return;

  // Botones de nivel
  const nav = document.getElementById('levelNav');
  nav.innerHTML = Object.entries(CURRICULUM).map(([k, v]) =>
    `<button class="lvl-btn${k === lvl ? ' on' : ''}"
       style="${k === lvl ? 'background:' + v.color + ';border-color:' + v.color + ';' : ''}"
       onclick="renderCurriculum('${k}')">${v.label}</button>`
  ).join('');

  // Lista de módulos
  const list = document.getElementById('moduleList');
  list.innerHTML = data.modules.map((mod, mi) => {
    const topics = mod.topics.map((t, ti) => {
      const lsnId = `${mod.id}_l${ti}`;
      const done  = ST.lessonsDone.has(lsnId);
      const active = ST.activeLesson === lsnId;
      return `
        <div class="lesson-item${done ? ' done' : ''}${active ? ' active' : ''}"
             onclick="startLesson('${lsnId}', '${escHtml(t)}', '${lvl}', '${escHtml(mod.title)}')">
          <span class="lesson-num">${ti + 1}</span>
          <span class="lesson-name">${t}</span>
          <span class="lesson-done-ico">${done ? '✅' : active ? '▶️' : '○'}</span>
        </div>`;
    }).join('');

    return `
      <div class="module-card" id="mod_${mod.id}">
        <div class="module-hd" onclick="toggleModule('${mod.id}')">
          <span class="module-emoji">${mod.emoji}</span>
          <span class="module-title">${mod.title}</span>
          <span class="module-count">${mod.lessons} lecciones</span>
          <span class="module-arrow">▼</span>
        </div>
        <div class="module-body">
          <div class="lesson-list">${topics}</div>
          <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn sm" onclick="practiceModule('${mod.id}','${escHtml(mod.title)}','${lvl}')">
              💬 Practicar módulo
            </button>
            <button class="btn sm ghost" onclick="testModule('${mod.id}','${escHtml(mod.title)}','${lvl}')">
              📝 Mini test
            </button>
          </div>
        </div>
      </div>`;
  }).join('');
}

function toggleModule(id) {
  const card = document.getElementById('mod_' + id);
  card.classList.toggle('open');
}

function startLesson(lsnId, topic, level, modTitle) {
  ST.activeLesson = lsnId;
  ST.level = level;
  // Ir a pestaña conversación y arrancar la lección
  document.querySelectorAll('#mAdult .sec').forEach(s => s.classList.remove('on'));
  document.querySelectorAll('#mAdult .tab').forEach(t => t.classList.remove('on'));
  document.getElementById('t-conv').classList.add('on');
  document.querySelector('#mAdult .tab').classList.add('on');
  // actualizar pill de nivel
  document.getElementById('convLevelPill').textContent =
    (CURRICULUM[level] ? CURRICULUM[level].label.split('—')[0].trim() : level);
  // Arrancar con mensaje contextual
  ST.history = [];
  const box = document.getElementById('chatBox');
  box.innerHTML = '';
  const prompt = `Comienza una lección nueva sobre: "${topic}" (módulo: ${modTitle}, nivel: ${level}).
Saluda al alumno, explícale brevemente qué van a aprender hoy y da el primer paso de la lección.
Habla en español cuando expliques, en inglés cuando practiques. Sé motivador y claro.`;
  sendAI(prompt, true);
  // Re-renderizar para mostrar lección activa
  renderCurriculum(level);
}

function practiceModule(modId, modTitle, level) {
  aTab('conv', document.querySelector('#mAdult .tab'));
  ST.history = [];
  document.getElementById('chatBox').innerHTML = '';
  const prompt = `El alumno quiere practicar conversación del módulo: "${modTitle}" (nivel ${level}).
Crea un diálogo de práctica real, como si fuera una situación de la vida cotidiana relacionada con ese módulo.
Empieza tú con la primera línea de la conversación en inglés y espera la respuesta del alumno.`;
  sendAI(prompt, true);
}

function testModule(modId, modTitle, level) {
  aTab('conv', document.querySelector('#mAdult .tab'));
  ST.history = [];
  document.getElementById('chatBox').innerHTML = '';
  const prompt = `Crea un mini test rápido de 5 preguntas sobre el módulo "${modTitle}" (nivel ${level}).
Hace una pregunta por vez. Espera la respuesta antes de seguir. Al final da una puntuación y feedback.
Mezcla gramática, vocabulario y uso real del idioma.`;
  sendAI(prompt, true);
}

function jumpToLevel(lvl, el) {
  document.querySelectorAll('.cefr-badge').forEach(b => b.classList.remove('on'));
  el.classList.add('on');
  setMode('adult');
  aTab('curso', document.querySelector('#mAdult .tab'));
  renderCurriculum(lvl);
}

// ═══════════════════════════════════════════════════════════
//  PERSONAJES
// ═══════════════════════════════════════════════════════════
function renderCharGrid() {
  const grid = document.getElementById('charGrid');
  grid.innerHTML = Object.entries(CHARACTERS).map(([id, c]) =>
    `<div class="char-card${id === ST.char ? ' on' : ''}" onclick="selectChar('${id}', this)">
      <span class="char-emoji">${c.emoji}</span>
      <div class="char-name">${c.name}</div>
      <div class="char-role">${c.role}</div>
    </div>`
  ).join('');
}

function selectChar(id, el) {
  ST.char = id;
  document.querySelectorAll('.char-card').forEach(c => c.classList.remove('on'));
  el.classList.add('on');
  // Resetear conversación con nuevo personaje
  ST.history = [];
  document.getElementById('chatBox').innerHTML = '';
  const c = CHARACTERS[id];
  addMsg('chatBox', 'ai',
    `${c.emoji} <b>${c.name}</b> — ${c.role}<br>
    <small style="opacity:.7">${c.desc} · Acento ${c.accent}</small>`);
}

function setTopic(el, topic) {
  ST.topic = topic;
  document.querySelectorAll('.chip:not(.kchip)').forEach(c => c.classList.remove('on'));
  el.classList.add('on');
}

// ═══════════════════════════════════════════════════════════
//  CONVERSACIÓN CON IA — Adultos
// ═══════════════════════════════════════════════════════════
async function sendChat() {
  const inp = document.getElementById('chatIn');
  const txt = inp.value.trim();
  if (!txt) return;
  inp.value = '';
  inp.disabled = true;
  document.getElementById('btnSend').disabled = true;

  addMsg('chatBox', 'usr', escHtml(txt));
  ST.history.push({ role: 'user', content: txt });
  ST.adaptive.msgCount++;

  const typing = addMsg('chatBox', 'ai', '<span class="spin"></span> escribiendo…');
  try {
    const reply = await callClaude(buildAdultSystemPrompt(), ST.history);
    typing.remove();
    // Procesar feedback adaptativo
    processAdaptiveFeedback(txt, reply);
    // Mostrar respuesta del personaje
    const c = CHARACTERS[ST.char];
    addMsg('chatBox', 'ai',
      `<span class="msg-avatar">${c.emoji}</span>
       <span class="msg-name">${c.name}</span>
       ${formatAIMsg(reply)}`);
    ST.history.push({ role: 'assistant', content: reply });
    // Marcar lección como hecha si hay activa
    if (ST.activeLesson && ST.adaptive.msgCount % 5 === 0) {
      ST.lessonsDone.add(ST.activeLesson);
      renderCurriculum(currentCurrLevel);
    }
    // Profesor lee la respuesta en voz alta
    speakAIReply(reply);
  } catch(e) {
    typing.remove();
    addMsg('chatBox', 'ai', '❌ Error al conectar con la IA. Revisá tu API key.');
  }
  inp.disabled = false;
  document.getElementById('btnSend').disabled = false;
  inp.focus();
}

function buildAdultSystemPrompt() {
  const c = CHARACTERS[ST.char];
  const lvlData = CURRICULUM[ST.level] || CURRICULUM['A0'];
  const diff = ST.adaptive.difficulty;

  return `Sos ${c.name}, ${c.role} en la Academia Foschi IA.
Descripción: ${c.desc}. Acento: ${c.accent}.

NIVEL DEL ALUMNO: ${ST.level} — ${lvlData.label}
TEMA ACTUAL: ${ST.topic}
DIFICULTAD ADAPTATIVA: ${diff}

ROL:
- Actuás como ${c.role} en una conversación real de la vida cotidiana.
- Hablás principalmente en inglés.
- Cuando el alumno comete un error, lo corregís con este formato exacto:
  🟡 Pequeño error: dijiste "_X_" → lo correcto es "_Y_" porque [razón breve]
  Después repetís la corrección y pedís que la repita antes de seguir.
- Si dice algo perfecto: "🟢 Perfect! [continúa la conversación]"
- Si el error es grave: "🔴 Ojo: [explicación]"
- Ajustás la complejidad según el nivel ${ST.level}:
  ${diff === 'easy'   ? 'Usá frases MUY simples, más español, más apoyo.' : ''}
  ${diff === 'normal' ? 'Mezcla equilibrada de inglés y español cuando explicás.' : ''}
  ${diff === 'hard'   ? 'Todo en inglés, frases complejas, vocabulario avanzado.' : ''}
- Nunca abandonés el rol.
- Después de 4-5 intercambios sin errores, introducís vocabulario nuevo apropiado para el nivel.
- Si el alumno pregunta algo de gramática, explicás en español con ejemplos claros.
- Sos paciente, motivador, y siempre terminás con una pregunta o invitación a seguir.`;
}

function processAdaptiveFeedback(userMsg, aiReply) {
  const a = ST.adaptive;
  const hasError = aiReply.includes('🔴') || aiReply.includes('🟡');
  const isPerfect = aiReply.includes('🟢');

  if (isPerfect) {
    a.streak++;
    a.errors = Math.max(0, a.errors - 1);
  } else if (hasError) {
    a.streak = 0;
    a.errors++;
    // registrar error por topic
    a.errorTopics[ST.topic] = (a.errorTopics[ST.topic] || 0) + 1;
  }

  // Ajustar dificultad
  const prev = a.difficulty;
  if (a.streak >= 5 && a.errors === 0) {
    a.difficulty = 'hard';
  } else if (a.streak >= 3) {
    a.difficulty = 'normal';
  } else if (a.errors >= 3) {
    a.difficulty = 'easy';
  }

  // Mostrar mensaje adaptativo si cambió
  if (prev !== a.difficulty) {
    const adMsg = document.getElementById('adaptiveMsg');
    adMsg.style.display = 'block';
    if (a.difficulty === 'hard') {
      adMsg.className = 'adaptive-msg up';
      adMsg.innerHTML = '🚀 ¡Excelente progreso! Estoy subiendo la dificultad.';
    } else if (a.difficulty === 'easy') {
      adMsg.className = 'adaptive-msg down';
      adMsg.innerHTML = '💡 Voy más despacio para que practiques mejor.';
    } else {
      adMsg.className = 'adaptive-msg up';
      adMsg.innerHTML = '⚖️ Ritmo equilibrado. ¡Seguís bien!';
    }
    setTimeout(() => { adMsg.style.display = 'none'; }, 4000);
  }

  // Actualizar skill de speaking/writing
  if (isPerfect) ST.skills.writing.done = Math.min(ST.skills.writing.done + 1, ST.skills.writing.total);
  if (a.msgCount % 3 === 0) ST.skills.grammar.done = Math.min(ST.skills.grammar.done + 1, ST.skills.grammar.total);
}

// ═══════════════════════════════════════════════════════════
//  PRONUNCIACIÓN
// ═══════════════════════════════════════════════════════════
function nextPron() {
  const words = PRON_WORDS;
  ST.pronIdx = (ST.pronIdx + 1) % words.length;
  ST.currentWord = words[ST.pronIdx];
  const w = ST.currentWord;
  document.getElementById('pronEmi').textContent  = w.e;
  document.getElementById('pronW').textContent    = w.w;
  document.getElementById('pronIpa').textContent  = w.ipa;
  document.getElementById('pronRes').innerHTML    = '';
  stopSoundBars();
}

function listenWord() {
  if (!ST.currentWord) return;
  speak(ST.currentWord.w, 'en-US');
  animateSoundBars();
  setTimeout(stopSoundBars, 2200);
  ST.skills.listening.done = Math.min(ST.skills.listening.done + 1, ST.skills.listening.total);
}

function startPron() {
  if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
    document.getElementById('pronRes').innerHTML =
      '<div class="corr-box err-box">⚠️ Tu navegador no soporta reconocimiento de voz. Usá Chrome.</div>';
    return;
  }
  const btn = document.getElementById('btnPron');
  btn.disabled = true;
  btn.innerHTML = '🎤 Escuchando…';
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const r = new SR();
  r.lang = 'en-US';
  r.interimResults = false;
  r.maxAlternatives = 3;
  r.start();
  animateSoundBars();

  r.onresult = async (e) => {
    stopSoundBars();
    btn.disabled = false;
    btn.innerHTML = '🎤 Hablar';
    const said = Array.from(e.results[0]).map(alt => alt.transcript.trim().toLowerCase());
    const target = ST.currentWord.w.toLowerCase();
    const best = said[0];
    const match = said.some(s => s.includes(target) || target.includes(s) || levenshtein(s, target) <= 2);

    let html;
    if (match) {
      html = `<div class="corr-box">
        🟢 <b>¡Perfecto!</b> Dijiste "<b>${best}</b>" — exactamente correcto 🎉
      </div>`;
      ST.skills.speaking.done = Math.min(ST.skills.speaking.done + 1, ST.skills.speaking.total);
      showPopup('🎤', '¡Excelente pronunciación!', `"${ST.currentWord.w}" — perfecto`);
    } else {
      // Pedir feedback a la IA
      html = `<div class="corr-box" style="background:var(--amb2);border-color:#fcd34d;color:#78350f">
        🟡 Dijiste "<b>${best}</b>"<br>
        La palabra es: <b>${ST.currentWord.w}</b> ${ST.currentWord.ipa}<br>
        <small>Escuchá de nuevo y repetí con más atención al sonido inicial.</small>
      </div>`;
    }
    document.getElementById('pronRes').innerHTML = html;
  };

  r.onerror = () => {
    stopSoundBars();
    btn.disabled = false;
    btn.innerHTML = '🎤 Hablar';
    document.getElementById('pronRes').innerHTML =
      '<div class="corr-box err-box">❌ No pude escucharte. Intentá de nuevo.</div>';
  };
}

function animateSoundBars() {
  document.querySelectorAll('.sound-bar').forEach((b, i) => {
    b._interval = setInterval(() => {
      b.style.height = (8 + Math.random() * 28) + 'px';
    }, 80 + i * 20);
  });
}

function stopSoundBars() {
  document.querySelectorAll('.sound-bar').forEach(b => {
    clearInterval(b._interval);
    b.style.height = '8px';
  });
}

function speakInput() {
  const txt = document.getElementById('chatIn').value.trim();
  if (txt) speak(txt, 'en-US');
}

// ═══════════════════════════════════════════════════════════
//  CORRECTOR DE INGLÉS
// ═══════════════════════════════════════════════════════════
async function correctText() {
  const txt = document.getElementById('corrTxt').value.trim();
  if (!txt) return;
  const btn = document.getElementById('btnCorr');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span> Corrigiendo…';
  document.getElementById('corrRes').innerHTML = '';

  const systemPrompt = `Sos un profesor de inglés experto. Analizás textos escritos por estudiantes hispanohablantes.
Para cada error encontrado:
1. Subrayá la frase original con error
2. Mostrá la corrección
3. Explicá la regla gramatical en español de forma clara
4. Dá un ejemplo adicional

Formato de respuesta:
---
❌ Error: "[texto original con error]"
✅ Corrección: "[texto correcto]"
📚 Regla: [explicación en español]
💡 Ejemplo: [otro ejemplo de uso correcto]
---

Si el texto está perfecto, decilo y felicitá al alumno con entusiasmo.
Al final dá una puntuación del 1 al 10 y un comentario general sobre el nivel de inglés.`;

  try {
    const res = await callClaude(systemPrompt, [{ role: 'user', content: `Corregí este texto: "${txt}"` }]);
    document.getElementById('corrRes').innerHTML =
      `<div class="corr-box">${formatAIMsg(res)}</div>`;
    ST.skills.writing.done = Math.min(ST.skills.writing.done + 2, ST.skills.writing.total);
  } catch(e) {
    document.getElementById('corrRes').innerHTML =
      '<div class="corr-box err-box">❌ Error al conectar con la IA.</div>';
  }
  btn.disabled = false;
  btn.innerHTML = '🔍 Corregir texto';
}

// ═══════════════════════════════════════════════════════════
//  PROGRESO
// ═══════════════════════════════════════════════════════════
function loadProg() {
  const skills = [
    { k: 'listening', n: 'Listening',    e: '👂' },
    { k: 'speaking',  n: 'Speaking',     e: '🗣️' },
    { k: 'reading',   n: 'Reading',      e: '📖' },
    { k: 'writing',   n: 'Writing',      e: '✍️' },
    { k: 'grammar',   n: 'Grammar',      e: '⚙️' },
  ];

  // Skill cards
  document.getElementById('skillGrid').innerHTML = skills.map(s => {
    const pct = Math.round((ST.skills[s.k].done / ST.skills[s.k].total) * 100);
    const cls = pct >= 70 ? 'pct-g' : pct >= 40 ? 'pct-m' : 'pct-l';
    return `
      <div class="skill-card">
        <span class="skill-emoji">${s.e}</span>
        <div class="skill-name">${s.n}</div>
        <div class="skill-pct ${cls}">${pct}%</div>
        <div class="bar-wrap" style="margin-top:5px">
          <div class="bar" style="width:${pct}%"></div>
        </div>
      </div>`;
  }).join('');

  // Temas con errores (repaso)
  const errList = document.getElementById('progList');
  const errs = Object.entries(ST.adaptive.errorTopics).sort((a,b) => b[1]-a[1]);
  if (errs.length === 0) {
    errList.innerHTML = '<p style="color:var(--ink3);font-size:.8rem">Sin errores registrados aún. ¡Seguí practicando!</p>';
  } else {
    errList.innerHTML = errs.map(([topic, count]) =>
      `<div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #f0f0f0">
        <span style="font-size:.8rem;flex:1;color:var(--ink2)">${topic}</span>
        <span style="font-size:.75rem;color:var(--red);font-weight:700">${count} error${count>1?'es':''}</span>
        <button class="btn sm ghost" onclick="repasarTopic('${topic}')">Repasar</button>
      </div>`
    ).join('');
  }

  // Resumen de nivel
  const total = ST.lessonsDone.size;
  const levelEl = document.getElementById('skillGrid');
  // Ya renderizado arriba, podemos agregar resumen abajo
}

function repasarTopic(topic) {
  ST.topic = topic;
  aTab('conv', document.querySelector('#mAdult .tab'));
  ST.history = [];
  document.getElementById('chatBox').innerHTML = '';
  const prompt = `El alumno tiene dificultades con el tema: "${topic}".
Diseñá un ejercicio de repaso corto y efectivo. Comenzá con una explicación breve en español,
luego practicá con 3 ejercicios concretos. Sé muy claro y paciente.`;
  sendAI(prompt, true);
}

// ═══════════════════════════════════════════════════════════
//  LLAMADA A LA IA (Anthropic API)
// ═══════════════════════════════════════════════════════════
async function callClaude(system, messages, maxTokens = 900) {
  const res = await fetch('/api/chat_ingles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ system, messages, max_tokens: maxTokens })
  });
  if (!res.ok) throw new Error('API error ' + res.status);
  const data = await res.json();
  return data.content || data.reply || '';
}

// Función para enviar prompt de sistema directo (inicio de lección, etc.)
async function sendAI(prompt, asSystem) {
  const typing = addMsg('chatBox', 'ai', '<span class="spin"></span> preparando lección…');
  try {
    const msgs = asSystem
      ? [{ role: 'user', content: prompt }]
      : [...ST.history, { role: 'user', content: prompt }];
    const reply = await callClaude(buildAdultSystemPrompt(), msgs);
    typing.remove();
    const c = CHARACTERS[ST.char];
    addMsg('chatBox', 'ai',
      `<span class="msg-avatar">${c.emoji}</span>
       <span class="msg-name">${c.name}</span>
       ${formatAIMsg(reply)}`);
    ST.history.push({ role: 'user', content: prompt });
    ST.history.push({ role: 'assistant', content: reply });
    // Profesor lee la respuesta en voz alta
    speakAIReply(reply);
  } catch(e) {
    typing.remove();
    addMsg('chatBox', 'ai', '❌ Error de conexión. Verificá el servidor.');
  }
}

// ═══════════════════════════════════════════════════════════
//  UTILIDADES DE UI
// ═══════════════════════════════════════════════════════════
function addMsg(boxId, cls, html) {
  const box = document.getElementById(boxId);
  const d = document.createElement('div');
  d.className = 'msg ' + cls;
  d.innerHTML = html;
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
  return d;
}

function formatAIMsg(txt) {
  // Convertir markdown básico + indicadores de feedback a HTML
  return txt
    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
    .replace(/\*(.*?)\*/g, '<i>$1</i>')
    .replace(/🟢(.*)/g, '<span class="fb perfect">🟢$1</span>')
    .replace(/🟡(.*)/g, '<span class="fb almost">🟡$1</span>')
    .replace(/🔴(.*)/g, '<span class="fb mistake">🔴$1</span>')
    .replace(/\n/g, '<br>');
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function speak(text, lang) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang || 'en-US';
  u.rate = 0.88;
  window.speechSynthesis.speak(u);
}

function toggleTTS() {
  ST.ttsEnabled = !ST.ttsEnabled;
  const btn = document.getElementById('btnTTS');
  if (ST.ttsEnabled) {
    btn.innerHTML = '🔊 Voz ON';
    btn.classList.remove('red');
  } else {
    btn.innerHTML = '🔇 Voz OFF';
    btn.classList.add('red');
    window.speechSynthesis.cancel();
  }
}

// Lee la respuesta del profesor en voz alta.
// Extrae primero las líneas en inglés (entre comillas o líneas sin español),
// y omite las explicaciones en español para no confundir al alumno.
function speakAIReply(txt) {
  if (!window.speechSynthesis) return;
  if (!ST.ttsEnabled) return;

  // Quitar emojis de feedback, markdown, HTML
  let clean = txt
    .replace(/🟢|🟡|🔴/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/<[^>]+>/g, '')
    .trim();

  // Si el nivel es A0/A1 leer todo despacio (mezcla español/inglés esperada)
  const slowLevels = ['A0','A1'];
  const rate = slowLevels.includes(ST.level) ? 0.75 : 0.88;

  // Limitar a primeras 300 chars para no leer parrafones enteros
  if (clean.length > 300) clean = clean.substring(0, 300) + '…';

  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(clean);
  // Detectar si hay más inglés que español para elegir el idioma de síntesis
  const spanishWords = (clean.match(/\b(que|es|de|en|un|una|con|para|por|el|la|los|las|si|no|yo|vos|sos|tenés|hola|bien|gracias)\b/gi) || []).length;
  const englishWords = (clean.match(/\b(the|is|are|you|your|I|my|we|it|this|that|in|a|an|to|do|does|did|have|has|will|can|hello|good|great)\b/gi) || []).length;
  u.lang = englishWords >= spanishWords ? 'en-US' : 'es-ES';
  u.rate = rate;
  window.speechSynthesis.speak(u);
}

function showPopup(emi, title, msg) {
  const p = document.getElementById('popup');
  document.getElementById('pEmi').textContent = emi;
  document.getElementById('pTit').textContent = title;
  document.getElementById('pMsg').textContent = msg;
  p.classList.add('show');
  setTimeout(() => p.classList.remove('show'), 2800);
}

// Distancia de Levenshtein para comparar pronunciaciones
function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m+1 }, (_, i) => Array.from({ length: n+1 }, (_, j) => i === 0 ? j : j === 0 ? i : 0));
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1] : 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
  return dp[m][n];
}

// ═══════════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', () => {
  renderCurriculum('A0');
  renderCharGrid();
  nextPron();
  // Mensaje de bienvenida en chat
  const c = CHARACTERS[ST.char];
  addMsg('chatBox', 'ai',
    `${c.emoji} <b>Hola! Soy ${c.name}</b>, tu profe de inglés 👋<br>
    <small>Elegí un tema arriba y escribime en inglés o en español para empezar. ¡No te preocupes por los errores, para eso estoy yo! 😊</small>`);
});
</script>
"""

#!/usr/bin/env python3
# coding: utf-8
"""
academia_ingles_parte_3.py — Academia Foschi IA  ▸ VERSIÓN 2.0
═══════════════════════════════════════════════════════════
  PARTE 3 — JavaScript modo Niños + Flask backend + ensamblado
  · ABC interactivo con audio y reconocimiento de voz
  · Juego ¿Qué es esto? con categorías
  · Memotest
  · Pronunciación niños
  · Chat con profe infantil
  · Sistema de badges y estrellas
  · Flask: rutas /api/chat y /api/correct
  · Función build_app() que ensambla las 3 partes
  (ensamblar con parte1.py y parte2.py)
═══════════════════════════════════════════════════════════
"""

import json
import os

# ─────────────────────────────────────────────────────────────
#  JAVASCRIPT — MODO NIÑOS + INICIALIZACIÓN FINAL
# ─────────────────────────────────────────────────────────────

ACADEMIA_JS_PART3 = r"""
<script>
// ═══════════════════════════════════════════════════════════
//  DATOS NIÑOS (inyectados desde Python)
// ═══════════════════════════════════════════════════════════
const VOCAB_KIDS = VOCAB_KIDS_PLACEHOLDER;
const ABC_DATA   = ABC_DATA_PLACEHOLDER;
const PRON_KIDS  = [
  {"e":"🍎","w":"Apple","ipa":"/ˈæp.əl/"},{"e":"🐶","w":"Dog","ipa":"/dɒɡ/"},
  {"e":"🐱","w":"Cat","ipa":"/kæt/"},{"e":"🍌","w":"Banana","ipa":"/bəˈnɑː.nə/"},
  {"e":"🏠","w":"House","ipa":"/haʊs/"},{"e":"🌳","w":"Tree","ipa":"/triː/"},
  {"e":"☀️","w":"Sun","ipa":"/sʌn/"},{"e":"🌙","w":"Moon","ipa":"/muːn/"},
  {"e":"🍕","w":"Pizza","ipa":"/ˈpiːt.sə/"},{"e":"🦁","w":"Lion","ipa":"/ˈlaɪ.ən/"},
  {"e":"🐘","w":"Elephant","ipa":"/ˈel.ɪ.fənt/"},{"e":"🌈","w":"Rainbow","ipa":"/ˈreɪn.boʊ/"},
];
const BADGES_DEF = BADGES_PLACEHOLDER;

// ═══════════════════════════════════════════════════════════
//  ESTADO NIÑOS
// ═══════════════════════════════════════════════════════════
const KST = {
  stars: 0,
  badges: new Set(),
  abcIdx: 0,
  currentLetter: 'A',
  gameTopic: 'animals',
  gameItem: null,
  gameOpts: [],
  memoTopic: 'animals',
  memoCards: [],
  memoFlipped: [],
  memoMatched: new Set(),
  kidsPronIdx: 0,
  kidsHistory: [],
  voiceCount: 0,
  chatCount: 0,
  abcDone: new Set(),
  streakDays: parseInt(localStorage.getItem('kst_streak') || '0'),
};

// ═══════════════════════════════════════════════════════════
//  INIT NIÑOS
// ═══════════════════════════════════════════════════════════
function initKids() {
  buildABCGrid();
  nextGame();
  initMemo();
  nextKWord();
  renderBadges();
  updateStars(0);
  // Mensaje de bienvenida
  const box = document.getElementById('kidsChatBox');
  if (!box.innerHTML) {
    addMsg('kidsChatBox', 'kid-ai',
      '🦁 <b>¡Hola!</b> Soy <b>Leo el León</b>, tu profe de inglés.<br>' +
      'Podés escribirme en español o en inglés. ¡Vamos a aprender juntos! 🎉');
  }
}

// ═══════════════════════════════════════════════════════════
//  TABS NIÑOS
// ═══════════════════════════════════════════════════════════
function kTab(id, el) {
  document.querySelectorAll('.sec[id^="t-"]').forEach(s => {
    if (s.closest('#mKids')) s.classList.remove('on');
  });
  document.querySelectorAll('.ktab').forEach(t => t.classList.remove('on'));
  document.getElementById('t-' + id).classList.add('on');
  el.classList.add('on');
}

// ═══════════════════════════════════════════════════════════
//  ESTRELLAS Y BADGES
// ═══════════════════════════════════════════════════════════
function updateStars(add) {
  KST.stars += add;
  document.getElementById('stC').textContent = KST.stars;
  checkBadges();
}

function checkBadges() {
  const checks = [
    { id: 'first_star',  cond: KST.stars >= 10 },
    { id: 'star_50',     cond: KST.stars >= 50 },
    { id: 'voice_5',     cond: KST.voiceCount >= 5 },
    { id: 'chat_10',     cond: KST.chatCount >= 10 },
    { id: 'star_200',    cond: KST.stars >= 200 },
    { id: 'star_500',    cond: KST.stars >= 500 },
    { id: 'perfect_pron',cond: KST.voiceCount >= 10 },
    { id: 'all_abc',     cond: KST.abcDone.size >= 26 },
    { id: 'streak_7',    cond: KST.streakDays >= 7 },
  ];
  let newBadge = false;
  checks.forEach(c => {
    if (c.cond && !KST.badges.has(c.id)) {
      KST.badges.add(c.id);
      newBadge = true;
      const b = BADGES_DEF.find(x => x.id === c.id);
      if (b) showPopup(b.e, '¡Nuevo logro!', b.n + ': ' + b.d);
    }
  });
  if (newBadge) renderBadges();
}

function renderBadges() {
  document.getElementById('bdgList').innerHTML = BADGES_DEF.map(b =>
    `<div class="bdg${KST.badges.has(b.id) ? '' : ' locked'}">
      <div class="be">${b.e}</div>
      <div class="bn">${b.n}</div>
      <div class="bl">${b.d}</div>
    </div>`
  ).join('');
}

// ═══════════════════════════════════════════════════════════
//  ABC INTERACTIVO
// ═══════════════════════════════════════════════════════════
function buildABCGrid() {
  const grid = document.getElementById('abcGrid');
  grid.innerHTML = Object.keys(ABC_DATA).map(l =>
    `<button class="abc-btn${KST.abcDone.has(l) ? '" style="background:var(--grn2);border-color:var(--grn);color:#065f46' : ''}"
       onclick="showLetter('${l}')">${l}</button>`
  ).join('');
}

function showLetter(l) {
  KST.currentLetter = l;
  const d = ABC_DATA[l];
  document.getElementById('liLetter').textContent = l;
  document.getElementById('liWord').textContent   = d.word + ' — ' + d.es;
  document.getElementById('liIpa').textContent    = d.ipa;
  document.getElementById('liSound').textContent  = d.sound;
  document.getElementById('letterInfo').style.display = 'block';
  document.getElementById('letterResult').innerHTML = '';
  // Auto-hablar la letra
  speak(l, 'en-US');
  setTimeout(() => speak(d.word, 'en-US'), 900);
}

function speakLetter() {
  const l = KST.currentLetter;
  const d = ABC_DATA[l];
  speak(l, 'en-US');
  setTimeout(() => speak(d.word, 'en-US'), 700);
}

function nextABCLetter() {
  const letters = Object.keys(ABC_DATA);
  KST.abcIdx = (KST.abcIdx + 1) % letters.length;
  showLetter(letters[KST.abcIdx]);
}

function kidsSpeak2() {
  if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
    document.getElementById('letterResult').innerHTML =
      '<div class="corr-box err-box">⚠️ Tu navegador no soporta voz. Usá Chrome.</div>';
    return;
  }
  const btn = document.getElementById('btnKSpk2');
  btn.disabled = true;
  btn.textContent = '🎤 Escuchando…';
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const r = new SR();
  r.lang = 'en-US';
  r.interimResults = false;
  r.start();

  r.onresult = (e) => {
    btn.disabled = false;
    btn.textContent = '🎤 Repetir';
    const said = e.results[0][0].transcript.trim().toLowerCase();
    const target = ABC_DATA[KST.currentLetter].word.toLowerCase();
    const ok = said.includes(target) || levenshtein(said, target) <= 2;
    if (ok) {
      document.getElementById('letterResult').innerHTML =
        '<div class="corr-box">🌟 ¡Perfecto! Dijiste <b>' + said + '</b> — ¡Muy bien!</div>';
      updateStars(5);
      KST.voiceCount++;
      KST.abcDone.add(KST.currentLetter);
      buildABCGrid(); // actualizar color del botón
      showPopup('⭐', '¡+5 estrellas!', 'Pronunciación perfecta de ' + KST.currentLetter);
    } else {
      document.getElementById('letterResult').innerHTML =
        '<div class="corr-box" style="background:var(--amb2);border-color:#fcd34d;color:#78350f">' +
        '🔄 Dijiste "' + said + '". Intentá decir <b>' + ABC_DATA[KST.currentLetter].word + '</b> de nuevo.</div>';
    }
  };
  r.onerror = () => { btn.disabled = false; btn.textContent = '🎤 Repetir'; };
}

// ═══════════════════════════════════════════════════════════
//  JUEGO ¿QUÉ ES ESTO?
// ═══════════════════════════════════════════════════════════
function setKTopic(el, topic) {
  KST.gameTopic = topic;
  document.querySelectorAll('.kchip').forEach(c => c.classList.remove('on'));
  el.classList.add('on');
  nextGame();
}

function nextGame() {
  const vocab = VOCAB_KIDS[KST.gameTopic] || VOCAB_KIDS.animals;
  const idx = Math.floor(Math.random() * vocab.length);
  KST.gameItem = vocab[idx];

  document.getElementById('gEmi').textContent = KST.gameItem.e;
  document.getElementById('gQ').textContent =
    KST.gameTopic === 'colors'  ? 'What color is this?' :
    KST.gameTopic === 'numbers' ? 'What number is this?' :
    KST.gameTopic === 'fruits'  ? 'What fruit is this?' :
    KST.gameTopic === 'body'    ? 'What body part is this?' :
    KST.gameTopic === 'clothes' ? 'What clothing is this?' :
    'What animal is this?';

  // 4 opciones: 1 correcta + 3 distractores
  const pool = vocab.filter(v => v.w !== KST.gameItem.w);
  const distractors = pool.sort(() => Math.random() - .5).slice(0, 3);
  KST.gameOpts = [...distractors, KST.gameItem].sort(() => Math.random() - .5);

  document.getElementById('optsGrid').innerHTML = KST.gameOpts.map((opt, i) =>
    `<button class="opt" onclick="checkGame(${i})">${opt.w}</button>`
  ).join('');
}

function checkGame(i) {
  const btns = document.querySelectorAll('.opt');
  const chosen = KST.gameOpts[i];
  if (chosen.w === KST.gameItem.w) {
    btns[i].classList.add('ok');
    btns.forEach((b, j) => { if (j !== i) b.disabled = true; });
    updateStars(10);
    speak(KST.gameItem.w, 'en-US');
    showPopup('🌟', '¡Correcto!', KST.gameItem.w + ' — ' + KST.gameItem.es);
  } else {
    btns[i].classList.add('ng');
    // Mostrar cuál era la correcta
    KST.gameOpts.forEach((opt, j) => {
      if (opt.w === KST.gameItem.w) btns[j].classList.add('ok');
    });
    btns.forEach(b => b.disabled = true);
  }
  setTimeout(nextGame, 1800);
}

function kidsHearWord() {
  if (KST.gameItem) speak(KST.gameItem.w, 'en-US');
}

// ═══════════════════════════════════════════════════════════
//  MEMOTEST
// ═══════════════════════════════════════════════════════════
function setMemoTopic(el, topic) {
  KST.memoTopic = topic;
  document.querySelectorAll('.kchip').forEach(c => c.classList.remove('on'));
  el.classList.add('on');
  initMemo();
}

function initMemo() {
  const vocab = (VOCAB_KIDS[KST.memoTopic] || VOCAB_KIDS.animals).slice(0, 6);
  // Crear pares: emoji + palabra
  const pairs = vocab.flatMap(v => [
    { type: 'emoji', val: v.e, match: v.w },
    { type: 'word',  val: v.w, match: v.w },
  ]);
  KST.memoCards = pairs.sort(() => Math.random() - .5);
  KST.memoFlipped = [];
  KST.memoMatched = new Set();

  document.getElementById('memoGrid').innerHTML = KST.memoCards.map((c, i) =>
    `<div class="mc" id="mc${i}" onclick="flipMemo(${i})">?</div>`
  ).join('');
}

function flipMemo(i) {
  if (KST.memoMatched.has(i) || KST.memoFlipped.includes(i)) return;
  if (KST.memoFlipped.length >= 2) return;

  const card = document.getElementById('mc' + i);
  card.classList.add('flipped');
  card.textContent = KST.memoCards[i].val;
  KST.memoFlipped.push(i);

  if (KST.memoFlipped.length === 2) {
    const [a, b] = KST.memoFlipped;
    const ca = KST.memoCards[a], cb = KST.memoCards[b];
    if (ca.match === cb.match && ca.type !== cb.type) {
      // ¡Par!
      setTimeout(() => {
        document.getElementById('mc'+a).classList.add('match');
        document.getElementById('mc'+b).classList.add('match');
        KST.memoMatched.add(a);
        KST.memoMatched.add(b);
        KST.memoFlipped = [];
        updateStars(15);
        speak(ca.match, 'en-US');
        if (KST.memoMatched.size === KST.memoCards.length) {
          showPopup('🏆', '¡Completaste el Memotest!', '¡Sos increíble! 🎉');
          updateStars(30);
        }
      }, 400);
    } else {
      setTimeout(() => {
        [a, b].forEach(idx => {
          const el = document.getElementById('mc' + idx);
          el.classList.remove('flipped');
          el.textContent = '?';
        });
        KST.memoFlipped = [];
      }, 900);
    }
  }
}

// ═══════════════════════════════════════════════════════════
//  PRONUNCIACIÓN NIÑOS
// ═══════════════════════════════════════════════════════════
function nextKWord() {
  KST.kidsPronIdx = (KST.kidsPronIdx + 1) % PRON_KIDS.length;
  const w = PRON_KIDS[KST.kidsPronIdx];
  document.getElementById('kpEmi').textContent = w.e;
  document.getElementById('kpW').textContent   = w.w;
  document.getElementById('kpIpa').textContent = w.ipa;
  document.getElementById('kVR').innerHTML = '';
}

function kListen() {
  const w = PRON_KIDS[KST.kidsPronIdx];
  speak(w.w, 'en-US');
  updateStars(1);
}

function kSpeak() {
  if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
    document.getElementById('kVR').innerHTML =
      '<div class="corr-box err-box">⚠️ Tu navegador no soporta voz. Usá Chrome.</div>';
    return;
  }
  const btn = document.getElementById('btnKS');
  btn.disabled = true;
  btn.textContent = '🎤 Escuchando…';
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const r = new SR();
  r.lang = 'en-US';
  r.interimResults = false;
  r.start();

  r.onresult = (e) => {
    btn.disabled = false;
    btn.textContent = '🎤 ¡Lo digo yo!';
    const said = e.results[0][0].transcript.trim().toLowerCase();
    const target = PRON_KIDS[KST.kidsPronIdx].w.toLowerCase();
    const ok = said.includes(target) || levenshtein(said, target) <= 2;
    KST.voiceCount++;
    if (ok) {
      document.getElementById('kVR').innerHTML =
        '<div class="corr-box">🌟 ¡Perfecto! Dijiste <b>' + said + '</b> 🎉</div>';
      updateStars(8);
      showPopup('⭐', '¡+8 estrellas!', '¡Pronunciación perfecta!');
      setTimeout(nextKWord, 1500);
    } else {
      document.getElementById('kVR').innerHTML =
        '<div class="corr-box" style="background:var(--amb2);border-color:#fcd34d;color:#78350f">' +
        '🔄 Dijiste "' + said + '". ¡Intentá de nuevo!<br>' +
        '<small>Escuchá bien y repetí despacio 😊</small></div>';
    }
  };
  r.onerror = () => { btn.disabled = false; btn.textContent = '🎤 ¡Lo digo yo!'; };
}

// ═══════════════════════════════════════════════════════════
//  CHAT CON PROFE NIÑOS (IA)
// ═══════════════════════════════════════════════════════════
async function sendKChat() {
  const inp = document.getElementById('kChatIn');
  const txt = inp.value.trim();
  if (!txt) return;
  inp.value = '';
  addMsg('kidsChatBox', 'usr', escHtml(txt));
  KST.kidsHistory.push({ role: 'user', content: txt });
  KST.chatCount++;

  const typing = addMsg('kidsChatBox', 'kid-ai', '<span class="spin"></span> Leo está pensando…');
  const system = `Sos Leo el León 🦁, un profesor de inglés muy divertido y paciente para niños de 4 a 12 años.
Siempre respondés con mucha energía, emojis y entusiasmo. Usás palabras simples.
Si el niño escribe en español, respondés en español y le enseñás la palabra en inglés.
Si escribe en inglés, lo felicitás muchísimo y seguís en inglés simple.
Siempre terminás con una pregunta fácil o un juego breve para mantener el interés.
Nunca usás lenguaje difícil. Siempre sos positivo, nunca decís que algo está "mal" — siempre decís "¡Casi! Probemos de nuevo 🌟".
Usás muchos emojis de animales, estrellas y corazones.`;

  try {
    const reply = await callClaude(system, KST.kidsHistory, 500);
    typing.remove();
    addMsg('kidsChatBox', 'kid-ai', '🦁 ' + formatAIMsg(reply));
    KST.kidsHistory.push({ role: 'assistant', content: reply });
    updateStars(3);
    checkBadges();
  } catch(e) {
    typing.remove();
    addMsg('kidsChatBox', 'kid-ai', '🦁 ¡Ups! Leo no pudo responder. ¡Intentá de nuevo! 😊');
  }
}
</script>
"""


# ─────────────────────────────────────────────────────────────
#  ENSAMBLADO HTML — autónomo, sin imports externos
# ─────────────────────────────────────────────────────────────

def build_full_html():
    """Genera el HTML completo inyectando todos los datos como JSON embebido."""
    curriculum_json = json.dumps(CURRICULUM,  ensure_ascii=False)
    characters_json = json.dumps(CHARACTERS,  ensure_ascii=False)
    pron_words_json = json.dumps(PRON_WORDS,  ensure_ascii=False)
    vocab_kids_json = json.dumps(VOCAB_KIDS,  ensure_ascii=False)
    abc_data_json   = json.dumps(ABC_DATA,    ensure_ascii=False)
    badges_json     = json.dumps(BADGES,      ensure_ascii=False)

    # Inyectar placeholders JS adultos (con o sin comillas)
    js2 = ACADEMIA_JS_PART2
    for _old, _new in [
        ('"CURRICULUM_PLACEHOLDER"',  curriculum_json),
        ('CURRICULUM_PLACEHOLDER',    curriculum_json),
        ('"CHARACTERS_PLACEHOLDER"',  characters_json),
        ('CHARACTERS_PLACEHOLDER',    characters_json),
        ('"PRON_WORDS_PLACEHOLDER"',  pron_words_json),
        ('PRON_WORDS_PLACEHOLDER',    pron_words_json),
    ]:
        js2 = js2.replace(_old, _new)

    # Inyectar placeholders JS niños
    js3 = (ACADEMIA_JS_PART3
           .replace('VOCAB_KIDS_PLACEHOLDER', vocab_kids_json)
           .replace('ABC_DATA_PLACEHOLDER',   abc_data_json)
           .replace('BADGES_PLACEHOLDER',     badges_json))

    return ACADEMIA_HTML.replace('</body>', js2 + '\n' + js3 + '\n</body>')


# ─────────────────────────────────────────────────────────────
#  FLASK BACKEND — OpenAI
# ─────────────────────────────────────────────────────────────

def create_flask_app():
    from flask import Flask, request, jsonify
    from openai import OpenAI, AuthenticationError, RateLimitError

    app   = Flask(__name__)
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    @app.route("/")
    def index():
        return build_full_html()

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data     = request.get_json(force=True)
        system   = data.get("system", "Sos un profesor de inglés.")
        messages = data.get("messages", [])
        max_tok  = int(data.get("max_tokens", 900))

        if len(messages) > 20:
            messages = messages[-20:]

        # Construir mensajes para OpenAI (system va primero)
        oai_messages = [{"role": "system", "content": system}] + messages

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=max_tok,
                messages=oai_messages,
            )
            content = resp.choices[0].message.content or ""
            return jsonify({"content": content})
        except AuthenticationError:
            return jsonify({"error": "API key inválida. Revisá OPENAI_API_KEY."}), 401
        except RateLimitError:
            return jsonify({"error": "Límite de uso alcanzado. Esperá un momento."}), 429
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "version": "2.0"})

    return app


# ─────────────────────────────────────────────────────────────
#  INTEGRACIÓN CON FOSCHI IA — init_academia_ingles(app)
# ─────────────────────────────────────────────────────────────

def _register_routes(app):
    from flask import request, jsonify, redirect
    from openai import OpenAI, AuthenticationError, RateLimitError

    _client_holder = [None]

    def _get_client():
        if _client_holder[0] is None:
            _client_holder[0] = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        return _client_holder[0]

    _cached_html = build_full_html()

    @app.route("/academia")
    @app.route("/ingles")
    def academia_index():
        return _cached_html

    @app.route("/api/chat_ingles", methods=["POST"])
    def academia_chat():
        data     = request.get_json(force=True)
        system   = data.get("system", "Sos un profesor de inglés.")
        messages = data.get("messages", [])
        max_tok  = int(data.get("max_tokens", 900))

        if len(messages) > 20:
            messages = messages[-20:]

        oai_messages = [{"role": "system", "content": system}] + messages

        try:
            resp = _get_client().chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=max_tok,
                messages=oai_messages,
            )
            content = resp.choices[0].message.content or ""
            return jsonify({"content": content})
        except AuthenticationError:
            return jsonify({"error": "API key inválida. Revisá OPENAI_API_KEY."}), 401
        except RateLimitError:
            return jsonify({"error": "Límite de uso alcanzado. Esperá un momento."}), 429
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/health_academia")
    def academia_health():
        return jsonify({"status": "ok", "version": "2.0"})


def init_academia_ingles(app):
    """
    Integra la Academia de Inglés en la app Flask de Foschi IA.
    Registra /ingles, /academia, /api/chat_ingles y /api/health_academia.
    Requiere: OPENAI_API_KEY en variables de entorno.
    """
    _register_routes(app)


# ─────────────────────────────────────────────────────────────
#  PUNTO DE ENTRADA STANDALONE
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app   = create_flask_app()
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    key   = bool(os.environ.get("OPENAI_API_KEY"))
    print(f"""
╔══════════════════════════════════════════════════╗
║         🎓  Academia Foschi IA  —  v2.0          ║
╠══════════════════════════════════════════════════╣
║  http://localhost:{port:<4}                            ║
║  API key: {"✅ Configurada" if key else "❌ Falta OPENAI_API_KEY":<37} ║
╚══════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=debug)