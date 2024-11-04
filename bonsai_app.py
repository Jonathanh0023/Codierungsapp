import streamlit as st
import openai
from tenacity import retry, stop_after_attempt, wait_random_exponential
import pandas as pd
from io import BytesIO
import json

def initialize_session_state():
    """Initialize all session state variables if they don't exist"""
    if 'codes_input_text' not in st.session_state:
        st.session_state.codes_input_text = st.session_state.get('codes_input', '')
    if 'categories_input_text' not in st.session_state:
        st.session_state.categories_input_text = st.session_state.get('categories_input', '')
    if 'search_words_input' not in st.session_state:
        st.session_state.search_words_input = st.session_state.get('search_words_input', '')
    if 'study_context_input' not in st.session_state:
        st.session_state.study_context_input = st.session_state.get('study_context_input', '')
    if 'beispiele_input' not in st.session_state:
        st.session_state.beispiele_input = st.session_state.get('beispiele_input', '')
    if 'selected_task_template' not in st.session_state:
        st.session_state.selected_task_template = st.session_state.get('selected_task_template', None)
    if 'task_template' not in st.session_state:
        st.session_state.task_template = None
    if 'instructions_read' not in st.session_state:
        st.session_state.instructions_read = st.session_state.get('instructions_read', False)
    if 'system_message' not in st.session_state:
        st.session_state.system_message = st.session_state.get('system_message', '')
    if 'question_template' not in st.session_state:
        st.session_state.question_template = st.session_state.get('question_template', '')
    if 'codeplan_expander_open' not in st.session_state:
        st.session_state.codeplan_expander_open = st.session_state.get('codeplan_expander_open', False)

def update_session_state(key: str):
    """Update session state from widget value"""
    if f"{key}_area" in st.session_state:
        st.session_state[f"{key}_text"] = st.session_state[f"{key}_area"]
        # Speichere auch im Haupt-Session-State für die JSON-Speicherung
        st.session_state[key] = st.session_state[f"{key}_area"]

# Definiere die Callback-Funktionen am Anfang der bonsai_page() Funktion
def show_instructions():
    st.write("## Willkommen beim BonsAI Codierungstool! 🎯")
    st.markdown("""
        ### So funktioniert's:
        1. **🔑 API-Schlüssel**: Gib deinen OpenAI-API-Schlüssel in der Seitenleiste ein
        2. **🤖 Modell**: Wähle ein Modell aus (für einfache Codierungen reicht gpt-4o-mini)
        3. **📝 Daten eingeben**: 
           - Codes (z.B. 1, 2, 3)
           - Kategorien (z.B. Essen, Trinken, Döner)
           - Offene Nennungen zum Codieren
        4. **🎯 Beispiele**: Gib ein paar typische Beispiele ein - das hilft der KI enorm!
        5. **✨ Start**: Wähle eine Codierungsmethode und klick auf "Los gehts"
        6. **📊 Ergebnisse**: Verfolge den Fortschritt und lade die fertigen Codierungen herunter
        """)
    st.markdown("""
        ### 💡 Tipp: Die geschweiften Klammern `{}`
        Im Prompt findest du geschweifte Klammern - keine Sorge, die werden automatisch ersetzt:
        - `{CODES_AND_CATEGORIES}` → Deine Codes und Kategorien
        - `{word}` → Die aktuelle Nennung
        - `{examples}` → Deine Beispiele
        - `{context_section}` → Dein Studienkontext
        """)
    if st.checkbox("Alles klar, ich habe alles verstanden!"):
        st.session_state.instructions_read = True
        st.rerun()

def bonsai_page():
    initialize_session_state()
    
    # Define task templates
    task_templates = {
        "Single-Label (Die KI vergibt genau einen Code pro Nennung)": """{CODES_AND_CATEGORIES}

            {context_section}
            
            Zu kategorisierende Nennung: {word}
            
            1. Analysiere die Nennung im Kontext der Studie
            2. Wähle die EINE am besten passende Kategorie aus
            3. Berücksichtige nur direkte, eindeutige Übereinstimmungen
            4. Vergib genau einen Code
            
            Antworte ausschließlich mit einem einzigen Code.
            
            Beispiele zur Orientierung:
            {examples}""",

        "Multi-Label (Die KI kann mehrere Codes pro Nennung vergeben)": """{CODES_AND_CATEGORIES}

            {context_section}
            
            Zu kategorisierende Nennung: {word}
            
            1. Lies die Nennung sorgfältig im Studienkontext
            2. Vergleiche sie mit jeder Kategorie:
               - Kategorie 1 '{first_category}'
               - Kategorie 2 '{second_category}'
               - ...
            3. Prüfe auf direkte und indirekte Übereinstimmungen
            4. Vergib alle zutreffenden Codes
            
            Antworte ausschließlich mit den Codes (durch Kommas getrennt).
            
            Beispiele zur Orientierung:
            {examples}"""
    }
    
    # Create a layout with just the "Back to Home" button in the top right
    st.sidebar.title("")
    if st.sidebar.button("🏠 Zurück zur Startseite", use_container_width=True, key="bonsai_back"):
        st.session_state.selected_app = None
        st.rerun()

    # Move API key input to the sidebar and use session state
    api_key = st.sidebar.text_input(
        "Hier deinen OpenAI-Key einfügen:", 
        value=st.session_state.api_key,
        type='password',
        key="api_key_area",
        on_change=update_session_state,
        args=('api_key',)
    )

    # Move model selection to the sidebar
    model_choices = ["gpt-4o-mini", "gpt-4o"]
    selected_model = st.sidebar.selectbox("Wähle ein Model:", model_choices, index=0)

    # Add the instructions to the sidebar
    st.sidebar.markdown("""
    ### 🚀 Schnellstart
    1. **🔑 API-Schlüssel** eingeben
    2. **🤖 Modell** wählen (gpt-4o-mini für einfache Codierungen)
    3. **📋 Codeplan erstellen**:
       - KI-Generierung aus Nennungen
       - Import aus Excel
       - Manuelle Eingabe
    4. **📚 Studienkontext** beschreiben
    5. **🎯 Beispiele** eingeben
    6. **✨ Codierungsmethode** wählen und starten

    ### 💰 Kosten sparen
    - Nutze **gpt-4o-mini** für einfache Codierungen
    - Teste erst mit wenigen Nennungen
    - Gute Beispiele = bessere Ergebnisse

    ### 🎯 Tipps für gute Ergebnisse
    - **Codeplan**: Nutze die KI-Generierung für erste Vorschläge
    - **Studienkontext**: Je präziser, desto besser
    - **Beispiele**: Gib typische Fälle und Grenzfälle an
    - **Codierungsmethode**:
      - Single-Label: Ein Code pro Nennung
      - Multi-Label: Mehrere Codes möglich

    ### 🔄 Workflow-Tipps
    1. Generiere einen ersten Codeplan mit der KI
    2. Passe den Codeplan bei Bedarf an
    3. Füge aussagekräftige Beispiele hinzu
    4. Teste mit wenigen Nennungen
    5. Verfeinere bei Bedarf und starte die Hauptcodierung
    """)

    # Check if the API key is entered
    if not api_key:
        st.warning("👈 Bitte gib deinen OpenAI-Key links in der Seitenleiste ein.")

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    def completion_with_backoff(**kwargs):
        return openai.chat.completions.create(**kwargs)

    # Check if the instructions have been read
    if not st.session_state.instructions_read:
        show_instructions()
    else:
        st.title("BonsAI Codierungstool")

        # Codeplan-Bereich zuerst
        st.markdown("""
        ### 📋 Codeplan erstellen oder importieren
        Der Codeplan ist das Herzstück der Codierung. Du hast folgende Möglichkeiten:
        - **🤖 KI-Generierung**: Lass die KI einen Codeplan aus deinen Nennungen erstellen
        - **📤 Import**: Lade einen bestehenden Codeplan aus einer Excel-Datei
        - **📥 Export**: Speichere deinen manuell eingegebenen Codeplan als Excel-Datei
        - **📝 Manuell**: Trage Codes und Kategorien direkt in die Felder ein
        """)

        # Expander mit neuem Titel und KI-Generierung als ersten Tab
        with st.expander("🎯 Codeplan-Assistent", expanded=st.session_state.codeplan_expander_open):
            tab2, tab1 = st.tabs(["🤖 KI-Generierung", "📤 Import/Export"])
            
            with tab2:
                st.markdown("""
                ### 🤖 KI-gestützte Codeplan-Generierung
                Lass die KI einen Codeplan basierend auf deinen Nennungen erstellen.
                """)
                
                # Einstellungen für die KI-Generierung
                num_categories = st.slider(
                    "Anzahl der zu generierenden Kategorien:",
                    min_value=2,
                    max_value=20,
                    value=5,
                    help="Wähle, wie viele Kategorien die KI erstellen soll"
                )
                
                ai_context = st.text_area(
                    "Studienkontext für die Kategorienbildung:",
                    placeholder="Beschreibe hier den Kontext der Studie, um bessere Kategorien zu erhalten...",
                    height=100
                )
                
                ai_nennungen = st.text_area(
                    "Nennungen für die Kategorienbildung:",
                    placeholder="Füge hier die Nennungen ein, die kategorisiert werden sollen...",
                    height=200
                )
                
                # Speichere generierten Codeplan in Session State
                if 'generated_codes' not in st.session_state:
                    st.session_state.generated_codes = []
                if 'generated_categories' not in st.session_state:
                    st.session_state.generated_categories = []
                
                if st.button("🤖 Codeplan generieren", disabled=not (ai_nennungen and api_key)):
                    if not api_key:
                        st.error("Bitte gib einen OpenAI API-Schlüssel ein.")
                        return
                        
                    openai.api_key = api_key
                    
                    with st.spinner("KI generiert Codeplan..."):
                        # Prompt für die KI
                        prompt = f"""Analysiere die folgenden Nennungen und erstelle {num_categories} sinnvolle Kategorien zur Codierung.

Studienkontext:
{ai_context}

Nennungen:
{ai_nennungen}

Erstelle einen Codeplan mit folgenden Anforderungen:
1. Genau {num_categories} Kategorien
2. Jede Kategorie sollte prägnant und eindeutig sein
3. Die Kategorien sollten alle wichtigen Aspekte der Nennungen abdecken
4. Vergib für jede Kategorie einen numerischen Code (1, 2, 3, ...)

Antworte im Format:
Code | Kategorie | Beschreibung
1 | [Kategorie 1] | [Kurze Beschreibung]
2 | [Kategorie 2] | [Kurze Beschreibung]
...
"""
                        try:
                            response = openai.chat.completions.create(
                                model=selected_model,
                                messages=[
                                    {"role": "system", "content": "Du bist ein Experte für die Entwicklung von Kategoriensystemen und Codeplänen."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.7
                            )
                            
                            # Verarbeite die Antwort
                            result = response.choices[0].message.content
                            
                            # Zeige das Ergebnis in einer Tabelle
                            st.markdown("### Generierter Codeplan")
                            st.text(result)
                            
                            # Extrahiere Codes und Kategorien
                            lines = result.strip().split('\n')[2:]  # Überspringe Header
                            codes = []
                            categories = []
                            for line in lines:
                                if '|' in line:
                                    parts = line.split('|')
                                    if len(parts) >= 2:
                                        codes.append(parts[0].strip())
                                        categories.append(parts[1].strip())
                            
                            # Speichere die generierten Daten im Session State
                            st.session_state.generated_codes = codes
                            st.session_state.generated_categories = categories
                            
                        except Exception as e:
                            st.error(f"Fehler bei der KI-Generierung: {str(e)}")
                
                # Button zum Übernehmen des Codeplans außerhalb des if-Blocks
                if st.session_state.generated_codes and st.session_state.generated_categories:
                    if st.button("✅ Codeplan übernehmen"):
                        st.session_state.codes_input_text = '\n'.join(st.session_state.generated_codes)
                        st.session_state.categories_input_text = '\n'.join(st.session_state.generated_categories)
                        st.success("Codeplan wurde übernommen!")
                        st.rerun()

            with tab1:
                # Bisheriger Export/Import Code
                # Export Button
                codes_list = st.session_state.codes_input_text.splitlines() if st.session_state.codes_input_text else []
                categories_list = st.session_state.categories_input_text.splitlines() if st.session_state.categories_input_text else []
                
                # Im Import/Export Tab (innerhalb des Codeplan-Expanders)
                st.markdown("""
                ### 📤 Export/Import
                Exportiere deinen aktuellen Codeplan oder importiere einen bestehenden:
                """)
                
                # Export des aktuellen Codeplans
                codes_list = st.session_state.codes_input_text.splitlines() if st.session_state.codes_input_text else []
                categories_list = st.session_state.categories_input_text.splitlines() if st.session_state.categories_input_text else []
                
                if codes_list or categories_list:  # Prüfe, ob Daten vorhanden sind
                    # Stelle sicher, dass beide Listen gleich lang sind
                    min_length = min(len(codes_list), len(categories_list))
                    codes_list = codes_list[:min_length]
                    categories_list = categories_list[:min_length]
                    
                    if min_length > 0:  # Nur erstellen wenn es tatsächlich Daten gibt
                        codes_df = pd.DataFrame({
                            'Code': codes_list,
                            'Kategorie': categories_list
                        })
                        
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                            codes_df.to_excel(writer, index=False, sheet_name='Codeplan')
                        
                        st.download_button(
                            label="📥 Aktuellen Codeplan exportieren",
                            data=excel_buffer.getvalue(),
                            file_name="codeplan.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                        # Zeige Warnung wenn Listen unterschiedlich lang waren
                        if len(codes_list) != len(categories_list):
                            st.warning(f"Hinweis: Codes und Kategorien hatten unterschiedliche Längen. Es wurden nur die ersten {min_length} Einträge exportiert.")
                    else:
                        st.info("Bitte füge sowohl Codes als auch Kategorien hinzu, um den Codeplan zu exportieren.")
                else:
                    st.info("Füge zuerst Codes und Kategorien hinzu, um den Codeplan zu exportieren.")
                
                st.markdown("---")  # Trennlinie zwischen Export und Import
                
                # Import Funktionalität
                uploaded_file = st.file_uploader("Codeplan importieren (Excel-Datei)", type=['xlsx'])
                if uploaded_file is not None and not st.session_state.get('import_processed'):
                    try:
                        imported_df = pd.read_excel(uploaded_file)
                        if 'Code' in imported_df.columns and 'Kategorie' in imported_df.columns:
                            st.info("Codeplan wurde erfolgreich geladen. Möchtest du die Daten importieren?")
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if st.button("✅ Ja, importieren"):
                                    # Update the session state directly with the imported values
                                    st.session_state.codes_input_text = '\n'.join(imported_df['Code'].astype(str))
                                    st.session_state.categories_input_text = '\n'.join(imported_df['Kategorie'].astype(str))
                                    st.session_state['import_processed'] = True
                                    st.session_state.codeplan_expander_open = False
                                    st.success("Codeplan erfolgreich importiert!")
                                    st.rerun()
                            with col2:
                                if st.button("❌ Nein, abbrechen"):
                                    st.session_state['import_processed'] = True
                                    st.session_state.codeplan_expander_open = False
                                    st.rerun()
                        else:
                            st.error("Die Excel-Datei muss die Spalten 'Code' und 'Kategorie' enthalten.")
                    except Exception as e:
                        st.error(f"Fehler beim Import: {str(e)}")

        # Manuelle Eingabe danach
        st.markdown("### 📝 Manuelle Eingabe")
        col1, col2, col3 = st.columns([0.8, 3, 3])

        with col1:
            st.text_area(
                "Codes:", 
                value=st.session_state.codes_input_text,
                placeholder="1\n2\n3\n...", 
                height=400,
                key="codes_input_area",
                on_change=update_session_state,
                args=('codes_input',)
            )
        with col2:
            st.text_area(
                "Kategorien:", 
                value=st.session_state.categories_input_text,
                placeholder='Kategorie für Code 1\nKategorie für Code 2\nKategorie für Code 3\n...', 
                height=400,
                key="categories_input_area",
                on_change=update_session_state,
                args=('categories_input',)
            )
        with col3:
            st.text_area(
                "Offene Nennungen:", 
                value=st.session_state.search_words_input,
                placeholder='Offene Nennungen untereinander einfügen', 
                height=400,
                key="search_words_input_area",
                on_change=update_session_state,
                args=('search_words_input',)
            )

        # Im Studienkontext-Bereich
        st.markdown("""
        ### 📚 Studienkontext
        Der Studienkontext hilft der KI, die Nennungen besser zu verstehen:
        - Gibt den thematischen Rahmen der Studie vor
        - Hilft bei der Interpretation mehrdeutiger Begriffe
        - Ermöglicht präzisere Zuordnungen durch Kontextverständnis
        
        *Beispiel*: Bei einer Studie zum "Fußball" wird die Nennung "Schwalbe" anders interpretiert als bei einer Studie zu "Vogelarten im Bürgerpark"
        """)
        
        with st.expander("📝 Studienkontext eingeben", expanded=True):
            st.text_area(
                "Beschreibe hier den Kontext der Studie:",
                value=st.session_state.study_context_input,
                placeholder="Hier den Kontext der Studie beschreiben...",
                height=150,
                key="study_context_input_area",
                on_change=update_session_state,
                args=('study_context_input',)
            )

        # Im Beispiele-Bereich
        with st.expander("📝 Beispiele eingeben", expanded=True):
            st.text_area(
                "Beispiele für die Codierung:", 
                value=st.session_state.beispiele_input,
                placeholder="Hier Beispiele für die Codierung einfügen...", 
                height=150,
                key="beispiele_input_area",
                on_change=update_session_state,
                args=('beispiele_input',)
            )

        # Im Template-Auswahlbereich
        st.markdown("""
        ### 🤖 Vorlage für die KI-Aufgabe
        Wie soll die KI die Codierung durchführen?
        """)
        
        selected_task_template = st.radio(
            label="Wähle eine Codierungsmethode:",
            options=list(task_templates.keys()),
            index=None if st.session_state.selected_task_template is None 
                  else list(task_templates.keys()).index(st.session_state.selected_task_template),
            key="task_template",
            on_change=lambda: setattr(st.session_state, 'selected_task_template', st.session_state.task_template)
        )

        # Disable the "Los gehts" button if no template is selected
        start_disabled = selected_task_template is None
        
        # Wrap advanced settings in expander
        with st.expander("⚙️ Erweiterte Einstellungen"):
            # Systemnachricht ohne zusätzlichen Expander
            st.text_area(
                "🔧 Systemnachricht (nur in Ausnahmefällen anpassen):", 
                value="Du bist ein Experte für die Klassifizierung von Texten. Deine Aufgabe ist es, Nennungen den passenden Kategorien zuzuordnen. Antworte ausschließlich mit den entsprechenden Codes.",
                height=100,
                key="system_message"
            )
            
            st.markdown("---")  # Trennlinie zwischen Systemnachricht und Template-Editor
            
            question_template = st.text_area(
                "Aufgabe für die KI (kann angepasst werden):", 
                value=task_templates[selected_task_template] if selected_task_template else "",
                height=450,
                disabled=selected_task_template is None,
                key="question_template"
            )

        if st.button("Los gehts", disabled=start_disabled):
            if selected_task_template is None:
                st.error("Bitte wähle zuerst eine Vorlage für die KI-Aufgabe aus.")
                return
            
            if not api_key:
                st.error("Bitte gib einen OpenAI API-Schlüssel ein.")
                return

            # Set the API key for OpenAI
            openai.api_key = api_key
            
            # Hole die Werte aus dem Session State
            study_context = st.session_state.study_context_input
            search_words = st.session_state.search_words_input
            beispiele = st.session_state.beispiele_input
            
            codes_list = st.session_state.codes_input_text.splitlines()
            categories_list = st.session_state.categories_input_text.splitlines()
            code_category_pairs = zip(codes_list, categories_list)
            formatted_code_categories = [f"{code} {category}" for code, category in code_category_pairs]
            codes_and_categories = "\n".join(formatted_code_categories)
            
            # Speichere den aktuellen Zustand
            st.session_state.update({
                'codes_input': st.session_state.codes_input_text,
                'categories_input': st.session_state.categories_input_text,
                'search_words_input': search_words,
                'study_context_input': study_context,
                'beispiele_input': beispiele,
                'selected_task_template': selected_task_template,
                'system_message': st.session_state.system_message,
                'question_template': st.session_state.question_template
            })
            
            progress_bar = st.progress(0)
            
            # Initialize DataFrame once and create a placeholder for it
            df = pd.DataFrame(columns=['Nennung', 'Codes'])
            df_placeholder = st.empty()

            # Kontext-Sektion vorbereiten
            context_section = f"Studienkontext:\n{study_context}\n" if study_context else ""
            
            for index, word in enumerate(search_words.splitlines()):
                progress_value = (index + 1) / len(search_words.splitlines())
                progress_bar.progress(progress_value)

                question = question_template.format(
                    CODES_AND_CATEGORIES=codes_and_categories,
                    word=word.strip(),
                    first_category=categories_list[0],
                    second_category=categories_list[1],
                    examples=beispiele,
                    context_section=context_section
                )
                messages = [
                    {"role": "system", "content": st.session_state.system_message},
                    {"role": "user", "content": question}
                ]
                print("Messages sent to OpenAI API:", messages)
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
                        
                # Append to DataFrame
                new_row = pd.DataFrame({'Nennung': [word.strip()], 'Codes': [complete_response.strip()]})
                df = pd.concat([df, new_row], ignore_index=True)

                # Update DataFrame display
                df_placeholder.dataframe(df)  # Aktualisiert das DataFrame in Echtzeit

            progress_bar.empty()

            # Split codes into separate columns
            def split_codes(row):
                codes = [code.strip() for code in row['Codes'].split(',')]
                return pd.Series(codes, index=[f'Code {i+1}' for i in range(len(codes))])

            # Create expanded DataFrame for export
            export_df = df.copy()
            codes_expanded = export_df.apply(split_codes, axis=1)
            export_df = pd.concat([export_df['Nennung'], codes_expanded], axis=1)

            # Create download button for Excel file
            def convert_df_to_excel():
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='Codierungen')
                return output.getvalue()

            excel_data = convert_df_to_excel()
            st.download_button(
                label="📥 Excel-Datei herunterladen",
                data=excel_data,
                file_name="codierungen.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Add custom CSS for consistent styling
        st.markdown("""
            <style>
            /* Import Ucity font */
            @import url('https://fonts.cdnfonts.com/css/ucity');
            
            /* Apply Ucity font to all elements */
            * {
                font-family: 'Ucity', sans-serif !important;
            }
            
            /* Modern text area styling */
            .stTextArea textarea {
                font-family: 'Ucity', sans-serif !important;
                font-size: 16px !important;
                line-height: 1.5 !important;
                padding: 12px !important;
                background-color: #ffffff !important;
                border: 1px solid #e0e0e0 !important;
                border-radius: 5px !important;
                color: #2c3e50 !important;
            }
            
            .stTextArea textarea:focus {
                border-color: #e5007f !important;
                box-shadow: 0 0 0 1px #e5007f !important;
            }
            
            /* Make text areas more readable */
            textarea {
                color: #2c3e50 !important;
                background-color: #ffffff !important;
            }
            </style>
        """, unsafe_allow_html=True)
