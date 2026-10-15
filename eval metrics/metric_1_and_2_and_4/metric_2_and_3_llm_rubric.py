import os
import sys
import csv
import json
from sentence_transformers import SentenceTransformer
from scraper import retrieve_relevant_chunks, generate_rag_response
import openai

# -------------------- Configuration --------------------
# List of study guide prompts to evaluate (150 AP-related queries)
QUERIES = [
    # AP United States History
    "Analyze the causes of the American Revolution and its outcomes.",
    "Evaluate the primary factors leading to the Civil War in the United States.",
    "Assess the impact of the New Deal on American society and economy.",
    "Compare Reconstruction policies under Lincoln, Johnson, and Congress.",
    "Discuss the Progressive Era reforms and their effects on U.S. governance.",
    "Explain the significance of Manifest Destiny in westward expansion.",
    "Analyze the causes and consequences of the Great Depression in the U.S.",
    "Evaluate the U.S. role in World War I and its domestic impacts.",
    "Discuss the Civil Rights Movement’s key legislation and court cases.",
    "Assess U.S. foreign policy during the Cold War era.",

    # AP 2-D Art and Design
    "Create a 2-D design composition exploring contrast through shape and color.",
    "Develop a balanced 2-D layout using principles of design and negative space.",
    "Design a 2-D piece that communicates a narrative through line and texture.",
    "Construct a 2-D mixed-media design focusing on repetition and rhythm.",

    # AP 3-D Art and Design
    "Design a 3-D sculptural form using additive techniques to convey movement.",
    "Create a 3-D composition that explores balance and spatial relationships.",
    "Develop a 3-D functional object emphasizing form and function.",
    "Construct a 3-D piece integrating negative space and material contrast.",

    # AP Drawing
    "Draw a composition demonstrating accurate foreshortening and perspective.",
    "Create a drawing that explores light and shadow in portraiture.",
    "Produce a study of drapery emphasizing texture and form.",
    "Compose a dynamic figure drawing capturing motion.",

    # AP Art History
    "Analyze the architectural features of Gothic cathedrals and their symbolism.",
    "Discuss the iconography present in Renaissance religious paintings.",
    "Compare Baroque and Neoclassical sculpture in terms of style and context.",
    "Evaluate the influence of Impressionism on modern art movements.",

    # AP Music Theory
    "Analyze the harmonic progression in an 18th-century chorale.",
    "Identify and explain instances of modal interchange in a given score.",
    "Compose a four-part chorale using common-practice voice leading rules.",
    "Analyze the structural form of a Baroque fugue subject.",

    # AP English Language and Composition
    "Write a rhetorical analysis of Martin Luther King Jr.’s 'I Have a Dream' speech.",
    "Compose an argumentative essay on the impact of social media on public discourse.",
    "Analyze an editorial’s use of evidence and rhetorical strategies on climate policy.",
    "Synthesize multiple sources to argue for or against standardized testing.",
    "Evaluate the tone and style in Jonathan Swift’s 'A Modest Proposal.'",

    # AP English Literature and Composition
    "Analyze the tragic flaw of Macbeth in Shakespeare’s play.",
    "Interpret the symbolism of the green light in The Great Gatsby.",
    "Compare narrative techniques in works by Toni Morrison and Alice Walker.",
    "Discuss the theme of identity in Sylvia Plath’s poetry.",
    "Examine the use of unreliable narration in a selected short story.",

    # AP African American Studies
    "Examine the impact of the Harlem Renaissance on American literature.",
    "Analyze the role of Black women leaders in the Civil Rights Movement.",
    "Discuss the themes of Afrofuturism in contemporary art and media.",
    "Evaluate economic disparities affecting African American communities.",
    "Assess the influence of the Black Power movement on social activism.",

    # AP Comparative Government and Politics
    "Compare parliamentary and presidential systems in two countries.",
    "Analyze the effects of proportional representation on party systems.",
    "Evaluate the role of an independent judiciary in democratic stability.",
    "Discuss the impact of civil society organizations on political participation.",
    "Examine the influence of electoral systems on representation.",

    # AP European History
    "Assess the causes of World War I in the context of European alliances.",
    "Analyze the social effects of the Industrial Revolution in Britain.",
    "Discuss Enlightenment ideas and their influence on the French Revolution.",
    "Evaluate the outcomes of the Congress of Vienna for European order.",
    "Examine the rise and fall of totalitarian regimes in the interwar period.",

    # AP Human Geography
    "Analyze the factors driving urbanization in developing countries.",
    "Discuss the geographic implications of population pyramids.",
    "Evaluate the role of cultural landscapes in shaping regional identities.",
    "Examine migration patterns and their impacts on global cities.",
    "Assess the effects of agricultural land use changes on the environment.",

    # AP Macroeconomics
    "Explain the effects of government fiscal policy during a recession.",
    "Analyze the causes and consequences of high inflation rates.",
    "Evaluate the tools used by central banks to control the money supply.",
    "Discuss the components of GDP and their significance for economic growth.",
    "Assess the impact of trade deficits on national economies.",

    # AP Microeconomics
    "Analyze price elasticity of demand for essential goods.",
    "Discuss characteristics of perfect competition and monopoly markets.",
    "Evaluate consumer choice theory using indifference curves.",
    "Explain how externalities affect market efficiency.",
    "Examine the role of government intervention in correcting market failures.",

    # AP Psychology
    "Analyze Piaget’s stages of cognitive development.",
    "Discuss classical versus operant conditioning in behavior.",
    "Evaluate major theories of personality development.",
    "Examine ethical considerations in psychological research.",
    "Assess the impact of social psychology on group behavior.",

    # AP United States Government and Politics
    "Analyze the principles of federalism in the U.S. Constitution.",
    "Discuss landmark Supreme Court cases on civil rights.",
    "Evaluate campaign finance laws and their effects on elections.",
    "Examine the balance of power between branches of government.",
    "Assess the role of interest groups in shaping public policy.",

    # AP World History
    "Compare agricultural practices in ancient Mesopotamia and Egypt.",
    "Analyze the spread of Islam during the 7th and 8th centuries.",
    "Discuss the impact of the Silk Road on cross-cultural exchange.",
    "Evaluate the effects of industrialization on world societies.",
    "Examine decolonization movements in the 20th century.",

    # AP Biology
    "Explain aerobic and anaerobic cellular respiration pathways.",
    "Analyze the structure and replication of DNA.",
    "Discuss light-dependent versus light-independent reactions in photosynthesis.",
    "Evaluate ecological succession in a temperate forest ecosystem.",
    "Examine mechanisms of homeostasis in multicellular organisms.",

    # AP Environmental Science
    "Analyze the carbon cycle and its relation to climate change.",
    "Discuss renewable versus nonrenewable energy sources.",
    "Evaluate ecosystem services in wetland environments.",
    "Examine human impacts on biodiversity loss.",
    "Assess strategies for sustainable resource management.",

    # AP Chinese Language and Culture
    "Translate a Mandarin dialogue about daily routines.",
    "Analyze the cultural significance of Chinese calligraphy.",
    "Discuss changes in Mandarin tones in different dialects.",
    "Interpret a classical Chinese poem in translation.",
    "Examine the role of language in Chinese cultural festivals.",

    # AP French Language and Culture
    "Translate a French news article on environmental issues.",
    "Analyze the cultural context of French cuisine and traditions.",
    "Discuss the use of subjunctive mood in French literature.",
    "Interpret a French political cartoon.",
    "Evaluate regional dialect variations in modern French.",

    # AP German Language and Culture
    "Translate a German poem from the Romantic period.",
    "Compare German and English sentence structures.",
    "Analyze the use of cases in German grammar.",
    "Discuss cultural idioms unique to German-speaking regions.",
    "Evaluate German literary movements of the 19th century.",

    # AP Italian Language and Culture
    "Translate an Italian Renaissance sonnet.",
    "Discuss the influence of Italian art on the Renaissance.",
    "Analyze Italian verb conjugations in complex tenses.",
    "Interpret an excerpt from a modern Italian novel.",
    "Examine regional language variations in Italy.",

    # AP Japanese Language and Culture
    "Translate a Japanese haiku into English.",
    "Analyze the etymology of common Kanji characters.",
    "Discuss the use of honorifics in Japanese language.",
    "Interpret a scene from a Japanese Noh play.",
    "Evaluate the role of language in Japanese tea ceremony.",

    # AP Latin
    "Translate a passage from Caesar’s 'Commentarii de Bello Gallico.'",
    "Analyze the meter of a Vergil epic line.",
    "Discuss rhetorical devices in Cicero’s speeches.",
    "Interpret an inscription from ancient Rome.",
    "Examine the influence of Latin on modern Romance languages.",

    # AP Spanish Language and Culture
    "Translate a Spanish news report on social issues.",
    "Analyze the cultural traditions of a Spanish-speaking country.",
    "Discuss the use of subjunctive versus indicative in Spanish.",
    "Interpret a Spanish short story dialogue.",
    "Evaluate dialectal differences across Spanish-speaking regions.",

    # AP Spanish Literature and Culture
    "Analyze themes in Federico García Lorca’s poetry.",
    "Interpret symbolism in Miguel de Cervantes’ Don Quixote.",
    "Compare prose styles of Spanish Golden Age authors.",
    "Discuss the role of literary movements in modern Spanish literature.",
    "Examine the historical context of post-colonial Spanish works.",

    # AP Computer Science A
    "Write a Java method implementing the binary search algorithm.",
    "Explain principles of object-oriented programming with examples.",
    "Analyze time complexity of common sorting algorithms.",
    "Implement recursion to solve mathematical problems in Java.",
    "Discuss memory management in the Java Virtual Machine.",

    # AP Computer Science Principles
    "Evaluate the societal impacts of artificial intelligence.",
    "Analyze a data visualization representing global health trends.",
    "Discuss fundamental cybersecurity principles and practices.",
    "Develop a concept for a mobile app addressing a social issue.",
    "Assess ethical considerations in computing and privacy.",

    # Additional queries to reach 150
    "Compare the causes and effects of World War II with World War I in U.S. History.",
    "Explain how color theory affects composition in 2-D art and design.",
    "Discuss the role of symmetry and asymmetry in 3-D art and design.",
    "Analyze how gesture drawing techniques capture movement in drawing.",
    "Examine the relationship between form and function in Art History."
]

# RAG retrieval settings
TOP_K = 5
SIMILARITY_THRESHOLD = 0.2
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# OpenAI rubric grading settings
OPENAI_MODEL = "gpt-4"
RUBRIC_CATEGORIES = [
    "Clarity",
    "Coverage of Essential Topics",
    "Factual Accuracy",
    "Organization",
    "Usefulness"
]

RUBRIC_PROMPT_TEMPLATE = (
    "You are an educational assessment assistant. "
    "Rate the following answer on a scale from 1.0 to 5.0 for each category: "
    f"{', '.join(RUBRIC_CATEGORIES)}. "
    "Provide the output as a JSON object with keys matching the category names and values as floats."
)

HALLUCINATION_PROMPT_TEMPLATE = (
    "You are a factuality checker. "
    "Identify any statements in the following content that are inaccurate, fabricated, or not supported by the provided source material. "
    "Return a JSON object with keys 'hallucinations' (a list of flagged sentences) and 'reasoning' (a brief explanation of why they are hallucinations)."
)


def evaluate_response_with_rubric(answer: str):
    """
    Uses OpenAI to score the answer on each rubric category.
    Returns a dict of {category: score}.
    """
    prompt = RUBRIC_PROMPT_TEMPLATE + "\n\nAnswer:\n" + answer
    try:
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful rubric grader."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=200
        )
        content = completion.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"[Warning] Rubric grading failed: {e}")
        return {cat: 0.0 for cat in RUBRIC_CATEGORIES}

def check_hallucinations(answer: str):
    prompt = HALLUCINATION_PROMPT_TEMPLATE + "\n\nContent:\n" + answer
    try:
        completion = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a factuality oracle."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=300
        )
        content = completion.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"[Warning] Hallucination check failed: {e}")
        return {"hallucinations": [], "reasoning": ""}



def main():
    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)
    openai.api_key = api_key

    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Prepare results storage
    rubric_results = []
    hallucination_results = []

    # Iterate over queries
    for idx, query in enumerate(QUERIES, start=1):
        print(f"Processing {idx}/{len(QUERIES)}: {query}")
        # RAG retrieval & generation
        chunks = retrieve_relevant_chunks(query, model, TOP_K, SIMILARITY_THRESHOLD)
        answer = generate_rag_response(query, chunks)

        # Rubric evaluation
        scores = evaluate_response_with_rubric(answer)
        rubric_entry = {"id": idx}
        rubric_entry.update(scores)
        rubric_results.append(rubric_entry)

        # Hallucination detection
        hall = check_hallucinations(answer)
        hall_entry = {
            "id": idx,
            "hallucinations": json.dumps(hall.get("hallucinations", [])),
            "reasoning": hall.get("reasoning", "")
        }
        hallucination_results.append(hall_entry)

    # Write rubric-only CSV
    rubric_file = "evaluation_results.csv"
    with open(rubric_file, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id"] + RUBRIC_CATEGORIES)
        writer.writeheader()
        for row in rubric_results:
            writer.writerow(row)
    print(f"Rubric results saved to {rubric_file}")

    # Write hallucination-only CSV
    hall_file = "hallucination_results.csv"
    with open(hall_file, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "hallucinations", "reasoning"])
        writer.writeheader()
        for row in hallucination_results:
            writer.writerow(row)
    print(f"Hallucination results saved to {hall_file}")


if __name__ == "__main__":
    main()
