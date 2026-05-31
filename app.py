import streamlit as st
import json
import os
from datetime import date
import random

# For demonstration, we are using a local JSON file. 
# Swap this with a database (like Supabase) for permanent web deployment.
DATA_FILE = "grace_dance_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "goals": [],
        "exercises": [],
        "corrections": [],
        "last_motivation_date": ""
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Mobile-friendly page configuration
st.set_page_config(page_title="Grace's Dance App", page_icon="💃", layout="centered")

# Initialize session state variables
if "data" not in st.session_state:
    st.session_state.data = load_data()

if "motivation_cleared" not in st.session_state:
    st.session_state.motivation_cleared = False

# The Daily Motivation Pop-up
@st.dialog("Daily Motivation 🌟")
def motivation_popup(goal):
    st.write("Here is one of your goals to keep you moving today:")
    st.info(f"**{goal}**")
    if st.button("Let's Dance!", use_container_width=True):
        st.session_state.motivation_cleared = True
        st.session_state.data["last_motivation_date"] = str(date.today())
        save_data(st.session_state.data)
        st.rerun()

# Check if we need to show the pop-up today
today_str = str(date.today())
active_goals = [g["text"] for g in st.session_state.data["goals"] if not g.get("completed", False)]

if (st.session_state.data["last_motivation_date"] != today_str 
    and not st.session_state.motivation_cleared 
    and active_goals):
    random_goal = random.choice(active_goals)
    motivation_popup(random_goal)

# App Header
st.title("💃 Grace's Irish Dance Hub")

# Use tabs for a clean, mobile-centric UI
tab1, tab2, tab3 = st.tabs(["🎯 Goals", "💪 Exercises", "📝 Corrections"])

# --- TAB 1: GOALS ---
with tab1:
    st.header("My Goals")
    
    # Add new goal
    with st.form("new_goal_form", clear_on_submit=True):
        new_goal = st.text_input("Add a new goal:")
        submitted = st.form_submit_button("Add Goal", use_container_width=True)
        if submitted and new_goal:
            st.session_state.data["goals"].append({"text": new_goal, "completed": False})
            save_data(st.session_state.data)
            st.rerun()
            
    # List goals with checkboxes
    st.subheader("Progress")
    if not st.session_state.data["goals"]:
        st.caption("No goals added yet.")
        
    for i, goal in enumerate(st.session_state.data["goals"]):
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            is_checked = st.checkbox(
                goal["text"], 
                value=goal.get("completed", False), 
                key=f"goal_{i}"
            )
            # Save state if checkbox changes
            if is_checked != goal.get("completed", False):
                st.session_state.data["goals"][i]["completed"] = is_checked
                save_data(st.session_state.data)
                st.rerun()
        with col2:
            if st.button("❌", key=f"del_goal_{i}", help="Delete Goal"):
                st.session_state.data["goals"].pop(i)
                save_data(st.session_state.data)
                st.rerun()

# --- TAB 2: EXERCISES ---
with tab2:
    st.header("Exercise Routine")
    
    # Hidden behind an expander to save screen space on mobile
    with st.expander("➕ Add New Exercise"):
        with st.form("new_exercise_form", clear_on_submit=True):
            ex_name = st.text_input("Exercise Name")
            ex_reps = st.text_input("Reps / Duration (e.g., 3x10 or 1 min)")
            ex_notes = st.text_area("Notes")
            ex_submit = st.form_submit_button("Save Exercise", use_container_width=True)
            if ex_submit and ex_name:
                st.session_state.data["exercises"].append({
                    "name": ex_name,
                    "reps": ex_reps,
                    "notes": ex_notes
                })
                save_data(st.session_state.data)
                st.rerun()

    # Display exercises as clean cards
    if not st.session_state.data["exercises"]:
        st.caption("No exercises added yet.")
        
    for i, ex in enumerate(st.session_state.data["exercises"]):
        with st.container(border=True):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(f"**{ex['name']}** - *{ex['reps']}*")
                if ex['notes']:
                    st.caption(ex['notes'])
            with col2:
                if st.button("❌", key=f"del_ex_{i}"):
                    st.session_state.data["exercises"].pop(i)
                    save_data(st.session_state.data)
                    st.rerun()

# --- TAB 3: CORRECTIONS ---
with tab3:
    st.header("Teacher Corrections")
    
    with st.form("new_correction_form", clear_on_submit=True):
        new_corr = st.text_area("What did the teacher say to work on?")
        corr_submit = st.form_submit_button("Add Correction", use_container_width=True)
        if corr_submit and new_corr:
            st.session_state.data["corrections"].append(new_corr)
            save_data(st.session_state.data)
            st.rerun()
            
    # List corrections
    if not st.session_state.data["corrections"]:
        st.caption("No corrections added yet.")
        
    for i, corr in enumerate(st.session_state.data["corrections"]):
        with st.container(border=True):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.write(corr)
            with col2:
                if st.button("❌", key=f"del_corr_{i}"):
                    st.session_state.data["corrections"].pop(i)
                    save_data(st.session_state.data)
                    st.rerun()
