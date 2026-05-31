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
    st.stop()

if supabase is not None:
    
    # Get today's date string (e.g., "2026-05-31")
    today_str = str(date.today())

    # Initialize session state for tracking motivation across clicks
    if "motivation_checked" not in st.session_state:
        st.session_state.motivation_checked = False

    # --- Data Fetching ---
    try:
        goals_data = supabase.table("goals").select("*").order("id").execute().data
        exercises_data = supabase.table("exercises").select("*").order("id").execute().data
        corrections_data = supabase.table("corrections").select("*").order("id").execute().data
        metadata = supabase.table("app_metadata").select("*").eq("key", "last_motivation_date").execute().data
        last_motivation_date = metadata[0]["value"] if metadata else ""
    except Exception as data_err:
        st.error("⚠️ Database Table Error: Could not fetch data.")
        st.stop()

    # --- The Daily Motivation Pop-up ---
    active_goals = [g["text"] for g in goals_data if not g.get("completed", False)]

    @st.dialog("Daily Motivation 🌟")
    def motivation_popup(goal):
        st.write("Here is one of your goals to keep you moving today:")
        st.info(f"**{goal}**")
        if st.button("Let's Dance!", use_container_width=True):
            supabase.table("app_metadata").upsert({"key": "last_motivation_date", "value": today_str}).execute()
            st.rerun()

    # Only evaluate the pop-up logic ONCE per app run/session day
    if (last_motivation_date != today_str 
        and not st.session_state.motivation_checked 
        and active_goals):
        
        # Mark as checked for this session so interaction with forms won't re-trigger it
        st.session_state.motivation_checked = True
        random_goal = random.choice(active_goals)
        motivation_popup(random_goal)

    # --- App Header ---
    st.title("💃 Grace's Irish Dance Hub")

    # Use tabs for a clean, mobile-centric UI
    tab1, tab2, tab3 = st.tabs(["🎯 Goals", "💪 Exercises", "📝 Corrections"])

    # --- TAB 1: GOALS ---
    with tab1:
        st.header("My Goals")
        
        with st.form("new_goal_form", clear_on_submit=True):
            new_goal = st.text_input("Add a new goal:")
            submitted = st.form_submit_button("Add Goal", use_container_width=True)
            if submitted and new_goal:
                supabase.table("goals").insert({"text": new_goal, "completed": False}).execute()
                st.rerun()
                
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
                if is_checked != goal.get("completed", False):
                    supabase.table("goals").update({"completed": is_checked}).eq("id", goal["id"]).execute()
                    st.rerun()
            with col2:
                if st.button("❌", key=f"del_goal_{goal['id']}"):
                    supabase.table("goals").delete().eq("id", goal["id"]).execute()
                    st.rerun()

    # --- TAB 2: EXERCISES ---
    with tab2:
        st.header("Daily Exercise Routine")
        
        with st.expander("➕ Add New Exercise"):
            with st.form("new_exercise_form", clear_on_submit=True):
                ex_name = st.text_input("Exercise Name")
                ex_reps = st.text_input("Reps / Duration (e.g., 3x10)")
                ex_notes = st.text_area("Notes")
                ex_submit = st.form_submit_button("Save Exercise", use_container_width=True)
                if ex_submit and ex_name:
                    supabase.table("exercises").insert({
                        "name": ex_name,
                        "reps": ex_reps,
                        "notes": ex_notes,
                        "last_completed_date": ""
                    }).execute()
                    st.rerun()

        if not exercises_data:
            st.caption("No exercises added yet.")
            
        for ex in exercises_data:
            # Check if it was completed TODAY. If the date doesn't match today, it stays unchecked.
            is_completed_today = ex.get("last_completed_date") == today_str
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([0.15, 0.70, 0.15])
                
                with col1:
                    # Daily completion checkbox
                    ex_check = st.checkbox("Done", value=is_completed_today, key=f"ex_check_{ex['id']}", label_visibility="collapsed")
                    if ex_check != is_completed_today:
                        new_date_value = today_str if ex_check else ""
                        supabase.table("exercises").update({"last_completed_date": new_date_value}).eq("id", ex["id"]).execute()
                        st.rerun()
                        
                with col2:
                    # Text styling to cross out completed exercises
                    if is_completed_today:
                        st.markdown(f"~~**{ex['name']}** - *{ex['reps']}*~~")
                    else:
                        st.markdown(f"**{ex['name']}** - *{ex['reps']}*")
                        
                    if ex.get('notes'):
                        st.caption(ex['notes'])
                        
                with col3:
                    if st.button("❌", key=f"del_ex_{ex['id']}"):
                        supabase.table("exercises").delete().eq("id", ex["id"]).execute()
                        st.rerun()

    # --- TAB 3: CORRECTIONS ---
    with tab3:
        st.header("Teacher Corrections")
        
        with st.form("new_correction_form", clear_on_submit=True):
            new_corr = st.text_area("What did the teacher say to work on?")
            corr_submit = st.form_submit_button("Add Correction", use_container_width=True)
            if corr_submit and new_corr:
                supabase.table("corrections").insert({"text": new_corr}).execute()
                st.rerun()
            
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
