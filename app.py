import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import date
import random

# Mobile-friendly page configuration
st.set_page_config(page_title="Grace's Dance App", page_icon="💃", layout="centered")

# Initialize the variable to prevent NameError
supabase = None

# Initialize the Supabase connection safely
try:
    conn = st.connection("supabase", type=SupabaseConnection)
    supabase = conn.client 
except Exception as e:
    st.error("⚠️ Connection Error: Could not authenticate with Supabase.")
    st.info("Please verify that your Streamlit Cloud Secrets contain the exact text below:")
    st.code("""
[connections.supabase]
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
    """, language="toml")
    st.stop()

# Only run the rest of the app if the connection was successfully established
if supabase is not None:
    
    # Initialize session state for the daily popup
    if "motivation_cleared" not in st.session_state:
        st.session_state.motivation_cleared = False

    # --- Data Fetching ---
    try:
        goals_data = supabase.table("goals").select("*").order("id").execute().data
        exercises_data = supabase.table("exercises").select("*").order("id").execute().data
        corrections_data = supabase.table("corrections").select("*").order("id").execute().data
        metadata = supabase.table("app_metadata").select("*").eq("key", "last_motivation_date").execute().data
        last_motivation_date = metadata[0]["value"] if metadata else ""
    except Exception as data_err:
        st.error("⚠️ Database Table Error: Could not fetch data.")
        st.warning(f"Details: {data_err}")
        st.info("Make sure you ran the SQL script in your Supabase SQL Editor to create the 'goals', 'exercises', 'corrections', and 'app_metadata' tables.")
        st.stop()

    # --- The Daily Motivation Pop-up ---
    today_str = str(date.today())
    active_goals = [g["text"] for g in goals_data if not g.get("completed", False)]

    @st.dialog("Daily Motivation 🌟")
    def motivation_popup(goal):
        st.write("Here is one of your goals to keep you moving today:")
        st.info(f"**{goal}**")
        if st.button("Let's Dance!", use_container_width=True):
            st.session_state.motivation_cleared = True
            supabase.table("app_metadata").upsert({"key": "last_motivation_date", "value": today_str}).execute()
            st.rerun()

    # Trigger the pop-up if it hasn't been cleared today and there are active goals
    if (last_motivation_date != today_str 
        and not st.session_state.motivation_cleared 
        and active_goals):
        random_goal = random.choice(active_goals)
        motivation_popup(random_goal)

    # --- App Header ---
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
                supabase.table("goals").insert({"text": new_goal, "completed": False}).execute()
                st.rerun()
                
        # List goals with checkboxes
        st.subheader("Progress")
        if not goals_data:
            st.caption("No goals added yet.")
            
        for goal in goals_data:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                is_checked = st.checkbox(
                    goal["text"], 
                    value=goal.get("completed", False), 
                    key=f"goal_{goal['id']}"
                )
                # Update database if checkbox state changes
                if is_checked != goal.get("completed", False):
                    supabase.table("goals").update({"completed": is_checked}).eq("id", goal["id"]).execute()
                    st.rerun()
            with col2:
                if st.button("❌", key=f"del_goal_{goal['id']}", help="Delete Goal"):
                    supabase.table("goals").delete().eq("id", goal["id"]).execute()
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
                    supabase.table("exercises").insert({
                        "name": ex_name,
                        "reps": ex_reps,
                        "notes": ex_notes
                    }).execute()
                    st.rerun()

        # Display exercises as clean cards
        if not exercises_data:
            st.caption("No exercises added yet.")
            
        for ex in exercises_data:
            with st.container(border=True):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    st.markdown(f"**{ex['name']}** - *{ex['reps']}*")
                    if ex.get('notes'):
                        st.caption(ex['notes'])
                with col2:
                    if st.button("❌", key=f"del_ex_{ex['id']}"):
                        supabase.table("exercises").delete().eq("id", ex["id"]).execute()
                        st.rerun()

    # --- TAB 3: CORRECTIONS ---
    with tab3:
        st.header("Teacher Corrections")
        
        # Add new correction
        with st.form("new_correction_form", clear_on_submit=True):
            new_corr = st.text_area("What did the teacher say to work on?")
            corr_submit = st.form_submit_button("Add Correction", use_container_width=True)
            if corr_submit and new_corr:
                supabase.table("corrections").insert({"text": new_corr}).execute()
                st.rerun()
                
        # List corrections
        if not corrections_data:
            st.caption("No corrections added yet.")
            
        for corr in corrections_data:
            with st.container(border=True):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    st.write(corr["text"])
                with col2:
                    if st.button("❌", key=f"del_corr_{corr['id']}"):
                        supabase.table("corrections").delete().eq("id", corr["id"]).execute()
                        st.rerun()
