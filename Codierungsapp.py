import streamlit as st
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

# Text input for the API key
api_key = st.text_input("Bitte gib deinen OpenAI-Key ein:", type='password')

# Check if the API key is entered
if api_key:
    openai.api_key = api_key

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

def categorize_words(categories, search_words, question_template, progress_bar, selected_model):
    results = {}
    category_string = ", ".join(categories)

    for index, word in enumerate(search_words):
        # Update the progress bar
        progress_value = (index + 1) / len(search_words)
        progress_bar.progress(progress_value)

        # Use the provided question template
        question = question_template.format(word=word.strip())
        prompt = f"{category_string}. {question}"

        response = completion_with_backoff(
            model=selected_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=50,
        )

        # Assuming the response directly contains the category integer
        results[word.strip()] = response.choices[0].message.content.strip()

    return results

st.title("BonsAI Codierungstool")

model_choices = ["gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
selected_model = st.selectbox("Wähle ein Model (https://platform.openai.com/docs/models/overview):", model_choices, index=0)

# Creating Streamlit widgets to capture input using columns
col1, col2, col3 = st.columns([0.8, 3, 3])

with col1:
    category_numbers = st.text_area("Codes:", placeholder="1\n2\n3", height=600)
with col2:
    category_names = st.text_area("Kategorien:", placeholder='Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3', height=600)
with col3:
    search_words = st.text_area("Suchwörter:", placeholder='Offene Nennungen untereinander einfügen\n...\n...\n...', height=600)

question_template = st.text_area("Aufgabe für die KI (Wichtig: Nur bei Bedarf verändern! {word} muss im Satz bleiben):", 'Zu welcher Kategorie oder welchen Kategorien gehören die Suchwörter? Antworte nur in Zahlen. {word}')

if st.button("Los gehts"):
    categories = [f"{num.strip()}: {name.strip()}" for num, name in zip(category_numbers.splitlines(), category_names.splitlines())]
    
    # Initialize the progress bar at 0
    progress_bar = st.progress(0)

    results = categorize_words(categories, search_words.splitlines(), question_template, progress_bar, selected_model)

    # Reset the progress bar (optional)
    progress_bar.empty()

    st.subheader("Ergebnisse:")
    for word, category in results.items():
        st.write(f"**{word}**: {category}")

else:
    st.warning("Bitte gib deinen OpenAI-Key ein.")
