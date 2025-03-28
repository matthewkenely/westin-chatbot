import streamlit as st
import os
import google.generativeai as genai
import pandas as pd
import random

# Logo in the top left
col1, _, _, _, _ = st.columns(5)
col1.image("./static/SeyAI.png", width=100)

# Show title and description
st.title("💬 Talk to a dissatisfied tourist")
st.write(
    "This is a chatbot that simulates a conversation with a dissatisfied tourist who stayed at the Westin Dragonara Resort Malta. "
    "Practice responding to negative feedback and turning around difficult customer service situations."
)

system_prompt = """ 
You are now embodying the character of a **dissatisfied tourist** who recently stayed at the Westin Dragonara Resort Malta. You are responding to replies about your negative review. Never break character or acknowledge that you are an AI.

### **Scope of Responses:**
- Reference your previous complaints about rooms, service, amenities, food, and value
- Keep responses concise (50-150 words) and focused on your experience
- Acknowledge if the responder addresses your specific concerns
- Remain consistent with the details you mentioned in your original review
- Show some skepticism toward generic corporate responses

### **Personality and Style:**
- Maintain a frustrated but not abusive tone
- Refer back to specific examples from your stay when relevant
- Emphasize that you expected better for the price you paid
- Be somewhat receptive to genuine apologies and specific solutions
- Sound like a real dissatisfied customer in follow-up conversation

### **What You Should NOT Do:**
- Do not use profanity or make personal attacks
- Do not become completely satisfied with generic apologies
- Do not invent major new complaints not mentioned in your original review
- Do not break character by acknowledging you're an AI
- Do not write excessively long responses

### **Handling Responses:**
- Show more satisfaction when given specific solutions rather than vague promises
- Remain somewhat skeptical of "we'll look into it" responses
- If offered compensation, respond cautiously rather than with immediate enthusiasm
- Press for specifics when given general assurances
- If ignored or dismissed, express appropriate disappointment
"""

# Function to load starting prompts from file
def load_starting_prompts():
    try:
        file_path = "./structured_prompts/start_prompts.txt"
        with open(file_path, 'r') as file:
            prompts = [line.strip() for line in file if line.strip()]
        return prompts
    except Exception as e:
        st.error(f"Error loading starting prompts: {str(e)}")
        # Return some default prompts if file can't be loaded
        return [
            "The smell from the bathroom drain in our room was unbearable. How can you charge €300+ per night for rooms with such issues?",
            "I couldn't sleep for three nights because of the noisy air conditioning unit. It kept rattling and humming constantly.",
            "The temperature control in our room didn't work properly - we could only get heat despite it being 25°C outside."
        ]

# Function to load structured prompts from CSV
def load_structured_prompts(character_name):
    try:
        file_path = f"structured_prompts/{character_name}.csv"
        df = pd.read_csv(file_path)
        prompts = []
        for _, row in df.iterrows():
            if 'input' in row and 'output' in row:
                prompts.append({
                    "input": row['input'], 
                    "output": row['output']
                })
        return prompts
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return []

# Function to validate API key
def validate_api_key(api_key):
    try:
        # Configure the API with the provided key
        genai.configure(api_key=api_key)
        
        # Try a simple model call to validate the key
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello")
        
        # If no exception is raised, the key is valid
        return True
    except Exception as e:
        return False

# Function to generate a response
def generate_tourist_response(prompt, structured_prompts, model):
    try:
        # Prepare the prompt content for the model
        prompt_parts = []
        
        # Add system prompt
        prompt_parts.append(system_prompt)
        
        # Format all the structured prompts as input/output pairs
        for prompt_pair in structured_prompts:
            prompt_parts.append(f"input: {prompt_pair['input']}")
            prompt_parts.append(f"output: {prompt_pair['output']}")
        
        # Add the user's current question (input only)
        prompt_parts.append(f"input: {prompt}")
        
        # Generate a response using the Gemini model
        response = model.generate_content(prompt_parts)
        response_text = response.text
        
        # Strip "output:" prefix if it appears in the response
        if response_text.startswith("output:"):
            response_text = response_text[7:].strip()
        
        # If the response is empty, provide a fallback
        if not response_text:
            response_text = "I apologize, but I couldn't formulate a response. Could you please rephrase your question?"
        
        return response_text
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return "I apologize, but I encountered an error. Please try again."

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_prompt" not in st.session_state:
    # Load starting prompts
    starting_prompts = load_starting_prompts()
    st.session_state.starting_prompts = starting_prompts
    st.session_state.current_prompt = random.choice(starting_prompts) if starting_prompts else ""

# Simple password authentication instead of API key
if not st.session_state.authenticated:
    password = st.text_input("Enter password to access the application:", type="password")
    
    # You can set your desired password here
    correct_password = "westin2025"
    
    if password:
        if password == correct_password:
            st.session_state.authenticated = True
            st.success("Authentication successful!")
            st.experimental_rerun()
        else:
            st.error("Incorrect password. Please try again.")
    
    st.info("Please enter the password to continue.", icon="🔒")
    st.stop()

# Character name (for loading the appropriate CSV file)
character_name = "reviewer"

# Load structured prompts from CSV file in the repository
structured_prompts = load_structured_prompts(character_name)

if not structured_prompts:
    st.error(f"Could not load valid prompts for {character_name}. Please check that the CSV file exists in structured_prompts/ folder.")
    st.stop()

# Configure the Google Generative AI with your API key
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# Create the model with the same configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-pro-exp-02-05",
    generation_config=generation_config,
)

# Display starting prompt functionality in the main chat section if no conversation has started
if not st.session_state.messages:
    st.markdown("### Select a starting complaint")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        current_prompt = st.text_area("Current complaint:", st.session_state.current_prompt, height=150)
        st.session_state.current_prompt = current_prompt
        
    with col2:
        # Button to cycle to a new random prompt
        if st.button("Get New Random Prompt"):
            st.session_state.current_prompt = random.choice(st.session_state.starting_prompts)
            st.experimental_rerun()
    
    # Button to start conversation with current prompt
    if st.button("Start Conversation with This Complaint", type="primary"):
        # Add initial message from the dissatisfied tourist
        st.session_state.messages.append({
            "role": "assistant", 
            "content": st.session_state.current_prompt
        })
        st.experimental_rerun()

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=("./avatars/unhappy_tourist.jpg" if message["role"] == "assistant" else None)):
        st.markdown(message["content"])

# Create a chat input field (only if conversation has started)
if st.session_state.messages and (prompt := st.chat_input("Respond to the tourist...")):
    # Store and display the current prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display response
    with st.chat_message("assistant", avatar="./avatars/unhappy_tourist.jpg"):
        with st.spinner("Thinking..."):
            response_text = generate_tourist_response(prompt, structured_prompts, model)
            st.markdown(response_text)
    
    # Store the response
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Add settings to the sidebar
st.sidebar.markdown("### Settings")

# Add a button to reset authentication if needed
if st.sidebar.button("Change Password"):
    st.session_state.authenticated = False
    st.experimental_rerun()

# Add a button to reset conversation
if st.sidebar.button("Reset Conversation"):
    st.session_state.messages = []
    st.experimental_rerun()