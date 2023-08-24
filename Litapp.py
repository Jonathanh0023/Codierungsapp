import streamlit as st
import openai

# Set the API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

def categorize_words(categories, search_words, question_template):
    results = {}
    category_string = ", ".join(categories)

    for word in search_words:
        question = question_template.format(word=word.strip())
        prompt = f"{category_string}. {question}"

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=50
        )

        results[word.strip()] = response.choices[0].message.content.strip()

    return results
    
# Streamlit interface
st.title("Kategorien Klassifikator")

# Input for categories
category_numbers = st.text_area("Codes:", placeholder="1\n2\n3")
category_names = st.text_area("Kategorien:", placeholder='Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3')
search_words = st.text_area("Suchwörter:", placeholder='Offene Nennungen untereinander einfügen\n...\n...\n...')
question_template = st.text_area(
    "Aufgabe für die KI (Wichtig: Nur bei Bedarf verändern! {word} muss im Satz bleiben):", 
    placeholder='Zu welcher Kategorie oder welchen Kategorien gehören die Suchwörter? Antworte nur in Zahlen. {word}'
)

if st.button("Los gehts"):
    categories = [f"{num.strip()}: {name.strip()}" for num, name in zip(category_numbers.splitlines(), category_names.splitlines())]
    results = categorize_words(categories, search_words.splitlines(), question_template)
    
    # Display results
    st.subheader("Ergebnisse:")
    for word, category in results.items():
        st.write(f"{word}: {category}")
