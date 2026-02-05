"""FactCheck-50 — 50 curated claims with gold verdicts for pipeline evaluation.

Covers 6 domains: science (10), history (10), current events/geography (10),
statistics/numbers (10), medicine/biology (5), technology (5).

Each claim has a gold verdict (true/false/partial) and explanation.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


FACTCHECK_50 = [
    # === Science (10) ===
    {
        "id": 1,
        "claim": "Water boils at 100\u00b0C at sea level",
        "gold_verdict": "true",
        "gold_explanation": "Water boils at 100\u00b0C (212\u00b0F) at standard atmospheric pressure (1 atm) at sea level.",
        "domain": "science",
        "difficulty": "easy",
    },
    {
        "id": 2,
        "claim": "Light travels at approximately 300,000 km/s in a vacuum",
        "gold_verdict": "true",
        "gold_explanation": "The speed of light in a vacuum is approximately 299,792 km/s, commonly rounded to 300,000 km/s.",
        "domain": "science",
        "difficulty": "easy",
    },
    {
        "id": 3,
        "claim": "The human body has 206 bones",
        "gold_verdict": "true",
        "gold_explanation": "An adult human body typically has 206 bones. Infants have more (around 270) which fuse over time.",
        "domain": "science",
        "difficulty": "easy",
    },
    {
        "id": 4,
        "claim": "Diamond is the hardest naturally occurring substance",
        "gold_verdict": "true",
        "gold_explanation": "Diamond rates 10 on the Mohs hardness scale, making it the hardest known naturally occurring substance.",
        "domain": "science",
        "difficulty": "easy",
    },
    {
        "id": 5,
        "claim": "The Great Wall of China is visible from space with the naked eye",
        "gold_verdict": "false",
        "gold_explanation": "The Great Wall is not visible from low Earth orbit with the naked eye. Multiple astronauts have confirmed this. It is too narrow despite its length.",
        "domain": "science",
        "difficulty": "medium",
    },
    {
        "id": 6,
        "claim": "Humans use only 10% of their brains",
        "gold_verdict": "false",
        "gold_explanation": "This is a widespread myth. Brain imaging studies show that virtually all areas of the brain are active and serve known functions.",
        "domain": "science",
        "difficulty": "easy",
    },
    {
        "id": 7,
        "claim": "Lightning never strikes the same place twice",
        "gold_verdict": "false",
        "gold_explanation": "Lightning frequently strikes the same place multiple times. Tall structures like the Empire State Building are struck dozens of times per year.",
        "domain": "science",
        "difficulty": "easy",
    },
    {
        "id": 8,
        "claim": "Sound travels faster in water than in air",
        "gold_verdict": "true",
        "gold_explanation": "Sound travels approximately 4.3 times faster in water (~1,480 m/s) than in air (~343 m/s) at room temperature.",
        "domain": "science",
        "difficulty": "medium",
    },
    {
        "id": 9,
        "claim": "The Amazon Rainforest produces 20% of the world's oxygen",
        "gold_verdict": "partial",
        "gold_explanation": "While commonly cited, the net oxygen contribution is debated. The rainforest produces roughly 6-9% of oxygen via photosynthesis but consumes nearly as much through respiration and decomposition.",
        "domain": "science",
        "difficulty": "hard",
    },
    {
        "id": 10,
        "claim": "Goldfish have a 3-second memory",
        "gold_verdict": "false",
        "gold_explanation": "Studies have shown goldfish can remember things for months. They can be trained to respond to stimuli and navigate mazes.",
        "domain": "science",
        "difficulty": "easy",
    },
    # === History (10) ===
    {
        "id": 11,
        "claim": "The Declaration of Independence was signed on July 4, 1776",
        "gold_verdict": "partial",
        "gold_explanation": "The Declaration was adopted/approved on July 4, 1776, but most delegates actually signed it on August 2, 1776.",
        "domain": "history",
        "difficulty": "hard",
    },
    {
        "id": 12,
        "claim": "Napoleon Bonaparte was unusually short",
        "gold_verdict": "false",
        "gold_explanation": "Napoleon was approximately 5'7\" (170 cm), which was average or slightly above average for men of his era. The myth stems from confusion between French and English measurement units and British propaganda.",
        "domain": "history",
        "difficulty": "medium",
    },
    {
        "id": 13,
        "claim": "The Titanic sank on April 15, 1912",
        "gold_verdict": "true",
        "gold_explanation": "The RMS Titanic struck an iceberg on April 14 and sank in the early morning hours of April 15, 1912.",
        "domain": "history",
        "difficulty": "easy",
    },
    {
        "id": 14,
        "claim": "The Berlin Wall fell on November 9, 1989",
        "gold_verdict": "true",
        "gold_explanation": "The Berlin Wall was opened on November 9, 1989, after an East German government announcement led to crowds gathering and eventually crossing freely.",
        "domain": "history",
        "difficulty": "easy",
    },
    {
        "id": 15,
        "claim": "Viking helmets had horns",
        "gold_verdict": "false",
        "gold_explanation": "There is no historical evidence that Viking helmets had horns. This is a 19th-century romantic myth. Actual Viking helmets were simple rounded caps.",
        "domain": "history",
        "difficulty": "medium",
    },
    {
        "id": 16,
        "claim": "Albert Einstein failed mathematics in school",
        "gold_verdict": "false",
        "gold_explanation": "Einstein excelled at mathematics from a young age. He mastered calculus by age 15. This myth may stem from a confusion about Swiss grading scales.",
        "domain": "history",
        "difficulty": "medium",
    },
    {
        "id": 17,
        "claim": "The first human-made object in space was Sputnik 1 in 1957",
        "gold_verdict": "partial",
        "gold_explanation": "Sputnik 1 was the first artificial satellite to orbit Earth (1957), but German V-2 rockets crossed the K\u00e1rm\u00e1n line (edge of space) as early as 1944.",
        "domain": "history",
        "difficulty": "hard",
    },
    {
        "id": 18,
        "claim": "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid",
        "gold_verdict": "true",
        "gold_explanation": "The Great Pyramid was built around 2560 BCE. Cleopatra lived around 69-30 BCE. The Moon landing was 1969 CE. Gap to pyramid: ~2500 years. Gap to Moon landing: ~2000 years.",
        "domain": "history",
        "difficulty": "medium",
    },
    {
        "id": 19,
        "claim": "The Spanish Flu originated in Spain",
        "gold_verdict": "false",
        "gold_explanation": "The Spanish Flu did not originate in Spain. Spain was neutral in WWI and freely reported on the pandemic, while other countries censored news. The actual origin is debated (Kansas, France, and China are all candidates).",
        "domain": "history",
        "difficulty": "medium",
    },
    {
        "id": 20,
        "claim": "World War I started because of the assassination of Archduke Franz Ferdinand",
        "gold_verdict": "partial",
        "gold_explanation": "The assassination was the immediate trigger, but WWI had deep underlying causes: militarism, alliances, imperialism, and nationalism. The assassination was the spark, not the sole cause.",
        "domain": "history",
        "difficulty": "hard",
    },
    # === Current Events / Geography (10) ===
    {
        "id": 21,
        "claim": "The Earth's population surpassed 8 billion in 2022",
        "gold_verdict": "true",
        "gold_explanation": "According to the UN, the world population reached 8 billion on November 15, 2022.",
        "domain": "current_events",
        "difficulty": "easy",
    },
    {
        "id": 22,
        "claim": "Mount Everest is the tallest mountain on Earth",
        "gold_verdict": "partial",
        "gold_explanation": "Everest has the highest elevation above sea level (8,849m). However, Mauna Kea in Hawaii is taller base-to-peak (~10,210m, with most underwater), and Chimborazo's summit is farthest from Earth's center.",
        "domain": "current_events",
        "difficulty": "hard",
    },
    {
        "id": 23,
        "claim": "Russia is the largest country by land area",
        "gold_verdict": "true",
        "gold_explanation": "Russia spans approximately 17.1 million km\u00b2, making it the largest country by land area, nearly twice the size of the second largest (Canada).",
        "domain": "current_events",
        "difficulty": "easy",
    },
    {
        "id": 24,
        "claim": "The Sahara is the largest desert in the world",
        "gold_verdict": "partial",
        "gold_explanation": "The Sahara is the largest hot desert. However, Antarctica (~14.2 million km\u00b2) and the Arctic (~13.9 million km\u00b2) are technically larger deserts by the definition of low precipitation.",
        "domain": "current_events",
        "difficulty": "hard",
    },
    {
        "id": 25,
        "claim": "There are 195 countries in the world",
        "gold_verdict": "partial",
        "gold_explanation": "There are 193 UN member states plus 2 observer states (Vatican City and Palestine) = 195. However, the total depends on recognition criteria; disputed territories like Taiwan and Kosovo complicate the count.",
        "domain": "current_events",
        "difficulty": "hard",
    },
    {
        "id": 26,
        "claim": "The Dead Sea is the lowest point on Earth's surface",
        "gold_verdict": "true",
        "gold_explanation": "The Dead Sea shore is approximately 430.5 meters below sea level, making it the lowest elevation on land on Earth's surface.",
        "domain": "current_events",
        "difficulty": "easy",
    },
    {
        "id": 27,
        "claim": "Australia is both a country and a continent",
        "gold_verdict": "true",
        "gold_explanation": "Australia is both a sovereign country and the world's smallest continent (or part of the broader Oceania/Australasia region depending on classification).",
        "domain": "current_events",
        "difficulty": "easy",
    },
    {
        "id": 28,
        "claim": "The Amazon River is the longest river in the world",
        "gold_verdict": "false",
        "gold_explanation": "The Nile is generally considered the longest river (~6,650 km vs Amazon's ~6,400 km), though some recent measurements have challenged this. The Amazon is the largest by water volume.",
        "domain": "current_events",
        "difficulty": "medium",
    },
    {
        "id": 29,
        "claim": "Greenland is the world's largest island",
        "gold_verdict": "true",
        "gold_explanation": "Greenland is the world's largest island at approximately 2.166 million km\u00b2. Australia is larger but is classified as a continent.",
        "domain": "current_events",
        "difficulty": "easy",
    },
    {
        "id": 30,
        "claim": "The Pacific Ocean covers more area than all land on Earth combined",
        "gold_verdict": "true",
        "gold_explanation": "The Pacific Ocean covers approximately 165.25 million km\u00b2, while Earth's total land area is approximately 148.94 million km\u00b2.",
        "domain": "current_events",
        "difficulty": "medium",
    },
    # === Statistics / Numbers (10) ===
    {
        "id": 31,
        "claim": "Pi is exactly 3.14159",
        "gold_verdict": "false",
        "gold_explanation": "Pi is an irrational number that never terminates or repeats. 3.14159 is an approximation. Pi continues: 3.14159265358979...",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 32,
        "claim": "A year on Earth is exactly 365 days",
        "gold_verdict": "false",
        "gold_explanation": "A tropical year is approximately 365.2422 days. This is why we have leap years \u2014 to account for the extra ~0.25 days.",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 33,
        "claim": "The speed of sound is approximately 343 m/s at sea level",
        "gold_verdict": "true",
        "gold_explanation": "The speed of sound in dry air at 20\u00b0C at sea level is approximately 343 m/s (1,235 km/h).",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 34,
        "claim": "Gold's atomic number is 79",
        "gold_verdict": "true",
        "gold_explanation": "Gold (Au) has atomic number 79 on the periodic table.",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 35,
        "claim": "The average human heart beats about 100,000 times per day",
        "gold_verdict": "true",
        "gold_explanation": "At an average resting heart rate of ~72 bpm: 72 \u00d7 60 \u00d7 24 = 103,680 beats per day, approximately 100,000.",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 36,
        "claim": "Absolute zero is -273.15\u00b0C",
        "gold_verdict": "true",
        "gold_explanation": "Absolute zero is exactly 0 Kelvin, which equals -273.15\u00b0C (-459.67\u00b0F).",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 37,
        "claim": "The human genome contains approximately 20,000-25,000 protein-coding genes",
        "gold_verdict": "true",
        "gold_explanation": "Current estimates from the Human Genome Project place the number of protein-coding genes at approximately 20,000-25,000.",
        "domain": "statistics",
        "difficulty": "medium",
    },
    {
        "id": 38,
        "claim": "The distance from Earth to the Sun is approximately 93 million miles",
        "gold_verdict": "true",
        "gold_explanation": "The average Earth-Sun distance (1 AU) is approximately 93 million miles (149.6 million km).",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 39,
        "claim": "The Mariana Trench is approximately 36,000 feet deep",
        "gold_verdict": "true",
        "gold_explanation": "The Challenger Deep in the Mariana Trench reaches approximately 36,070 feet (10,994 meters), making it the deepest known point in Earth's oceans.",
        "domain": "statistics",
        "difficulty": "easy",
    },
    {
        "id": 40,
        "claim": "There are more stars in the universe than grains of sand on Earth",
        "gold_verdict": "true",
        "gold_explanation": "Estimates suggest ~10^24 stars in the observable universe and ~7.5\u00d710^18 grains of sand on Earth. Stars outnumber sand grains by roughly a million to one.",
        "domain": "statistics",
        "difficulty": "medium",
    },
    # === Medicine / Biology (5) ===
    {
        "id": 41,
        "claim": "Antibiotics are effective against viruses",
        "gold_verdict": "false",
        "gold_explanation": "Antibiotics are designed to fight bacterial infections and are ineffective against viruses. Antiviral medications are used for viral infections.",
        "domain": "medicine",
        "difficulty": "easy",
    },
    {
        "id": 42,
        "claim": "The human stomach completely replaces its lining every 3-4 days",
        "gold_verdict": "true",
        "gold_explanation": "The stomach lining (mucosa) regenerates approximately every 3-4 days to protect against the corrosive hydrochloric acid it produces.",
        "domain": "medicine",
        "difficulty": "medium",
    },
    {
        "id": 43,
        "claim": "Cracking your knuckles causes arthritis",
        "gold_verdict": "false",
        "gold_explanation": "Multiple studies, including a notable self-experiment by Dr. Donald Unger over 60 years, found no link between knuckle cracking and arthritis.",
        "domain": "medicine",
        "difficulty": "easy",
    },
    {
        "id": 44,
        "claim": "Carrots significantly improve night vision",
        "gold_verdict": "false",
        "gold_explanation": "While carrots contain vitamin A (important for eye health), eating more carrots won't significantly improve night vision in people with adequate nutrition. This myth was amplified by WWII British propaganda to hide radar technology.",
        "domain": "medicine",
        "difficulty": "medium",
    },
    {
        "id": 45,
        "claim": "The average human body is about 60% water",
        "gold_verdict": "true",
        "gold_explanation": "The adult human body is approximately 55-60% water by weight, varying by age, sex, and body composition.",
        "domain": "medicine",
        "difficulty": "easy",
    },
    # === Technology (5) ===
    {
        "id": 46,
        "claim": "The first iPhone was released in 2007",
        "gold_verdict": "true",
        "gold_explanation": "The original iPhone was announced by Steve Jobs on January 9, 2007, and released on June 29, 2007.",
        "domain": "technology",
        "difficulty": "easy",
    },
    {
        "id": 47,
        "claim": "Moore's Law states that transistor count doubles every 18 months",
        "gold_verdict": "partial",
        "gold_explanation": "Gordon Moore's original 1965 observation was that transistor count doubled roughly every year. He revised this to every two years in 1975. The commonly cited '18 months' is a conflation with Intel executive David House's prediction about chip performance.",
        "domain": "technology",
        "difficulty": "hard",
    },
    {
        "id": 48,
        "claim": "The internet and the World Wide Web are the same thing",
        "gold_verdict": "false",
        "gold_explanation": "The internet is the global network infrastructure. The World Wide Web (invented by Tim Berners-Lee in 1989) is a service that runs on the internet, using HTTP to access web pages. Email, FTP, etc. also use the internet but are not the Web.",
        "domain": "technology",
        "difficulty": "medium",
    },
    {
        "id": 49,
        "claim": "The first email was sent in 1971 by Ray Tomlinson",
        "gold_verdict": "true",
        "gold_explanation": "Ray Tomlinson sent the first network email in late 1971 using ARPANET and introduced the @ sign for addressing. The exact date is not precisely documented.",
        "domain": "technology",
        "difficulty": "medium",
    },
    {
        "id": 50,
        "claim": "Bitcoin was created by Satoshi Nakamoto in 2009",
        "gold_verdict": "true",
        "gold_explanation": "The Bitcoin whitepaper was published in October 2008 by the pseudonymous Satoshi Nakamoto. The genesis block was mined on January 3, 2009.",
        "domain": "technology",
        "difficulty": "easy",
    },
]


def get_dataset() -> list[dict]:
    """Return the FactCheck-50 dataset formatted for the eval runner."""
    return [
        {
            "input": item["claim"],
            "mode": "claim",
            "gold_verdict": item["gold_verdict"],
            "gold_explanation": item["gold_explanation"],
            "domain": item["domain"],
            "difficulty": item["difficulty"],
            "id": item["id"],
        }
        for item in FACTCHECK_50
    ]


def get_stats() -> dict:
    """Return dataset statistics."""
    domains = {}
    difficulties = {}
    verdicts = {}

    for item in FACTCHECK_50:
        domains[item["domain"]] = domains.get(item["domain"], 0) + 1
        difficulties[item["difficulty"]] = difficulties.get(item["difficulty"], 0) + 1
        verdicts[item["gold_verdict"]] = verdicts.get(item["gold_verdict"], 0) + 1

    return {
        "total": len(FACTCHECK_50),
        "by_domain": domains,
        "by_difficulty": difficulties,
        "by_verdict": verdicts,
    }
