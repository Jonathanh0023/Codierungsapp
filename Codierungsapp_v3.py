import streamlit as st
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

# Set page title and favicon
st.set_page_config(page_title="BonsAI", page_icon="https://sw01.rogsurvey.de/data/bonsai/Kara_23_19/logo_Bonsa_BONSAI_neu.png", layout="centered")

# Define the CSS to inject for background image
background_image_url = "https://r4.wallpaperflare.com/wallpaper/902/658/531/tree-bonsai-tree-black-hd-bonsai-tree-wallpaper-78062c2abf5c5769eec0e982d2691b30.jpg"
background_style = f"""
    <style>
    .stApp {{
        background-image: url("{background_image_url}");
        background-size: cover;
        background-position: 500px -65px;
        background-repeat: no-repeat;
    }}
    .main {{
        margin-top: -90px;  /* Adjust this value as needed */
    }}
    </style>
    """    

# Inject the CSS with markdown
st.markdown(background_style, unsafe_allow_html=True)

# Text input for the API key
api_key = st.text_input("Bitte gib deinen OpenAI-Key ein:", type='password')

# Check if the API key is entered
if api_key:
    openai.api_key = api_key

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

def categorize_words(codes, categories, search_words, question_template, progress_bar, selected_model, system_message):
    results = {}
    code_category_mapping = dict(zip(codes, categories))

    for index, word in enumerate(search_words):
        # Update the progress bar
        progress_value = (index + 1) / len(search_words)
        progress_bar.progress(progress_value)

        # Use the provided question template and replace {CODES}, {KATEGORIEN}, and {word} with the actual values
        question = question_template.format(CODES="\n".join(codes), KATEGORIEN="\n".join(categories), word=word.strip())

        response = completion_with_backoff(
            model=selected_model,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0.2,
            max_tokens=50,
        )

        # Extract the codes from the response
        assigned_codes = response.choices[0].message.content.strip().split(",")
        assigned_categories = [code_category_mapping[code.strip()] for code in assigned_codes if code.strip() in code_category_mapping]

        results[word.strip()] = ", ".join(assigned_categories)

    return results

st.title("BonsAI Codierungstool")

model_choices = ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-0125"]
selected_model = st.selectbox("Wähle ein Model:", model_choices, index=0)

# Creating Streamlit widgets to capture input using columns
col1, col2, col3 = st.columns([0.8, 3, 3])

with col1:
    codes = st.text_area("Codes:", placeholder="1\n2\n3\n...", height=400)
with col2:
    categories = st.text_area("Kategorien:", placeholder='Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3\n...', height=400)
with col3:
    search_words = st.text_area("Offene Nennungen:", placeholder='Offene Nennungen untereinander einfügen', height=400)

system_message = st.text_area("Systemnachricht (Hier kann die KI eingestellt werden):", 'Du wirst als hilfreicher Assistent bei der Auswertung von offenen Nennungen in der Marktforschung agieren. Deine Aufgabe ist es zu bestimmen, zu welcher Kategorie oder welchen Kategorien eine offene Nennung gehört.')
question_template = st.text_area("Hier die Aufgabe für die KI einstellen:", 
"""Hier ist die Liste der Codes und ihrer entsprechenden Kategorien:

Codes:
{CODES}

Kategorien:
{KATEGORIEN}

Hier ist die zu kategorisierende offene Nennung: 
{word}

Denke sorgfältig darüber nach, zu welcher Kategorie oder welchen Kategorien die Nennung am besten passt. Berücksichtige dabei den Inhalt und Kontext der Nennung. 

Gehe für jede Kategorie wie folgt vor:
Frage dich: Passt <Kategorie> zur <Nennung>? 
Wenn die Antwort 'ja' ist, dann vergib den entsprechenden Code für diese Kategorie.
Wenn die Antwort 'nein' ist, dann vergib keinen Code für diese Kategorie.

Gib deine finale Einschätzung, zu welcher Kategorie oder welchen Kategorien die Nennung gehört, in <Antwort> Tags an. Antworte dabei nur mit den entsprechenden numerischen Codes der Kategorien. Wenn die Nennung zu mehreren Kategorien passt, liste alle zutreffenden Codes auf, getrennt durch Kommas.""")

if st.button("Los gehts"):
    codes_list = codes.splitlines()
    categories_list = categories.splitlines()
    
    # Initialize the progress bar at 0
    progress_bar = st.progress(0)

    results = categorize_words(codes_list, categories_list, search_words.splitlines(), question_template, progress_bar, selected_model, system_message)

    # Reset the progress bar (optional)
    progress_bar.empty()

    st.subheader("Ergebnisse:")
    for word, category in results.items():
        st.write(f"**{word}**: {category}")

else:
    st.warning("Bitte gib deinen OpenAI-Key ein.")
