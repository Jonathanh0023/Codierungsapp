import streamlit as st
import openai

# Text input for the API key
api_key = st.text_input("Bitte gib deinen OpenAI-Key ein:", type='password')

# Check if the API key is entered
if api_key:
    openai.api_key = api_key

def categorize_words(categories, search_words, question_template, progress_bar):
    results = {}
    category_string = ", ".join(categories)

    for index, word in enumerate(search_words):
        # Update the progress bar
        progress_value = (index + 1) / len(search_words)
        progress_bar.progress(progress_value)

        # Use the provided question template
        question = question_template.format(word=word.strip())
        prompt = f"{category_string}. {question}"

        response = openai.ChatCompletion.create(
            model="gpt-4",
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

# Creating Streamlit widgets to capture input using columns
col1, col2, col3 = st.columns([0.8, 3, 3])

with col1:
    category_numbers = st.text_area("Codes:", placeholder="1\n2\n3\n...\n...\n...", height=400)
with col2:
    category_names = st.text_area("Kategorien:", placeholder='Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3\n...\n...\n...', height=400)
with col3:
    search_words = st.text_area("Suchwörter:", placeholder='Offene Nennungen untereinander einfügen', height=400)

question_template = st.text_area("Aufgabe für die KI (Wichtig: Nur bei Bedarf verändern! {word} muss im Satz bleiben):", 'Zu welcher Kategorie oder welchen Kategorien gehören die Suchwörter? Antworte nur in Zahlen. {word}')

if st.button("Los gehts"):
    categories = [f"{num.strip()}: {name.strip()}" for num, name in zip(category_numbers.splitlines(), category_names.splitlines())]
    
    # Initialize the progress bar at 0
    progress_bar = st.progress(0)

    results = categorize_words(categories, search_words.splitlines(), question_template, progress_bar)

    # Reset the progress bar (optional)
    progress_bar.empty()

    st.subheader("Ergebnisse:")
    for word, category in results.items():
        st.write(f"**{word}**: {category}")

else:
    st.warning("Bitte gib deinen OpenAI-Key ein.")