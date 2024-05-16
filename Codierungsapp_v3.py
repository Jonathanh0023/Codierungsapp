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
        margin-top: -60px;  /* Adjust this value as needed */
    }}
    </style>
    """    

# Inject the CSS with markdown
st.markdown(background_style, unsafe_allow_html=True)

# Add a sidebar for navigation
st.sidebar.title("Navigation")

# Move API key input to the sidebar
api_key = st.sidebar.text_input("Bitte gib deinen OpenAI-Key ein:", type='password')

# Move model selection to the sidebar
model_choices = ["gpt-4o", gpt-3.5-turbo"]
selected_model = st.sidebar.selectbox("Wähle ein Model:", model_choices, index=0)

# Add the instructions to the sidebar
st.sidebar.markdown("""
## Anleitung zur Nutzung der BonsAI-App

### So geht's

1. **API-Schlüssel eingeben**: Gib deinen OpenAI-API-Schlüssel in der Seitenleiste ein.
2. **Modell auswählen**: Wähle ein Modell aus. [Mehr Infos zu den Modellen und Kosten](https://platform.openai.com/docs/models)
3. **Daten eingeben**: Trage deine Codes, Kategorien und offenen Nennungen ein.
4. **Optionen anpassen**: Passe bei Bedarf die Beispiele, die Systemnachricht und die Aufgabe für die KI an.
5. **Starten**: Klicke auf "Los gehts", um die Kategorisierung zu starten.
6. **Ergebnisse ansehen**: Verfolge den Fortschritt und sieh dir die Ergebnisse direkt in der App an.

### Erklärung der geschweiften Klammern `{}` im Prompt
Die geschweiften Klammern `{}` im Prompt sind Platzhalter, die durch die tatsächlichen Werte ersetzt werden, bevor der Prompt an die KI gesendet wird. Hier sind die Platzhalter und was sie bedeuten:

- `{CODES_AND_CATEGORIES}`: Wird durch die Liste der Codes und Kategorien ersetzt.
- `{word}`: Wird durch die aktuelle Nennung ersetzt, die kategorisiert werden soll.
- `{first_category}` und `{second_category}`: Werden durch die ersten beiden Kategorien aus der Liste ersetzt.
- `{examples}`: Wird durch die eingegebenen Beispiele ersetzt.
""")

# Check if the API key is entered
if api_key:
    openai.api_key = api_key
else:
    st.warning("Bitte gib deinen OpenAI-Key ein.")

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    # Replace with the new method if different from openai.Completion.create()
    return openai.chat.completions.create(**kwargs)

def categorize_words(codes, categories, search_words, question_template, progress_bar, selected_model, system_message):
    results = {}
    code_category_mapping = dict(zip(codes, categories))

    for index, word in enumerate(search_words):
        progress_value = (index + 1) / len(search_words)
        progress_bar.progress(progress_value)

        question = question_template.format(CODES="\n".join(codes), KATEGORIEN="\n".join(categories), word=word.strip())
        response = completion_with_backoff(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": question}
            ],
            temperature=0.2,
            max_tokens=50,
            stream=True
        )

        # Speichere die komplette Antwort der KI
        complete_response = ""
        for chunk in response:
            complete_response += chunk.choices[0].delta.content or ""
        results[word.strip()] = complete_response

    return results

st.title("BonsAI Codierungstool")

# Creating Streamlit widgets to capture input using columns
col1, col2, col3 = st.columns([0.8, 3, 3])

with col1:
    codes = st.text_area("Codes:", placeholder="1\n2\n3\n...", height=400)
with col2:
    categories = st.text_area("Kategorien:", placeholder='Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3\n...', height=400)
with col3:
    search_words = st.text_area("Offene Nennungen:", placeholder='Offene Nennungen untereinander einfügen', height=400)

beispiele = st.text_area("Beispiele:", placeholder='Beispiele von Nennungen mit Codes', height=100)

system_message = st.text_area("Systemnachricht (Hier kann die KI eingestellt werden):", 'Du bist Experte in Multi-label Klassifizierungen von Nennungen. Du antwortest nur mit den entsprechenden Codes.')
question_template = st.text_area("Hier die Aufgabe für die KI einstellen:", 
"""{CODES_AND_CATEGORIES}
    
Hier ist die zu kategorisierende offene Nennung: 
{word}
    
Denke sorgfältig darüber nach, zu welchen Kategorien die Nennung '{word}' am besten passt. Berücksichtige dabei den Inhalt und Kontext der Nennung. 
    
Gehe für jede Kategorie wie folgt in einem Loop vor:
Frage dich: Passt die Nennung '{word}' zur Kategorie 1 '{first_category}', passt die Nennung zur Kategorie 2 '{second_category}', usw ... ? 
Wenn die Antwort 'ja' ist, dann vergib den entsprechenden Code für diese Kategorie.
Wenn die Antwort 'nein' ist, dann vergib keinen Code für diese Kategorie.
    
Antworte nur mit den entsprechenden numerischen Codes der Kategorien. Wenn die Nennung zu mehreren Kategorien passt, liste alle zutreffenden Codes auf, getrennt durch Kommas.

Hier sind einige Beispiele:
{examples}""", height=200)

if st.button("Los gehts"):
    codes_list = codes.splitlines()
    categories_list = categories.splitlines()
    code_category_pairs = zip(codes_list, categories_list)
    formatted_code_categories = [f"{code} {category}" for code, category in code_category_pairs]
    codes_and_categories = "\n".join(formatted_code_categories)
    progress_bar = st.progress(0)
    placeholder = st.empty()  # Create a placeholder to display streamed responses

    all_responses = ""  # Initialize an empty string to accumulate responses

    for index, word in enumerate(search_words.splitlines()):
        progress_value = (index + 1) / len(search_words.splitlines())
        progress_bar.progress(progress_value)

        question = question_template.format(
            CODES_AND_CATEGORIES=codes_and_categories,
            word=word.strip(),
            first_category=categories_list[0],
            second_category=categories_list[1],
            examples=beispiele  
        )
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": question}
        ]
        print("Messages sent to OpenAI API:", messages)  # Add this line to print the messages
        stream = openai.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=0.2,
            max_tokens=50,
            stream=True
        )

        # Accumulate the complete response for the current word
        complete_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                complete_response += chunk.choices[0].delta.content

        # Append the formatted response to all_responses
        all_responses += f"**{word}**: {complete_response.strip()}\n\n"
        placeholder.markdown(all_responses)  # Update the placeholder with all accumulated responses

    progress_bar.empty()
