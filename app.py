import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import date
import random

# Mobile-friendly page configuration
st.set_page_config(page_title="Grace's Dance App", page_icon="💃", layout="centered")

# Inject custom CSS to tighten up the UI padding for mobile screens
st.markdown("""
    <style>
        /* Shrink the padding inside the bordered containers (cards) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.5rem 1rem !important;
        }
        /* Reduce the vertical gap between elements inside the cards */
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.2rem !important;
        }
        /* Make the tertiary delete buttons smaller */
        button[kind="tertiary"] {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }
    </style>
""", unsafe_allow_html=True)

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
    
    today_str = str(date.today())

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

    if (last_motivation_date != today_str 
        and not st.session_state.motivation_checked 
        and active_goals):
        
        st.session_state.motivation_checked = True
        random_goal = random.choice(active_goals)
        motivation_popup(random_goal)

    # --- App Header ---
    st.title("💃 Grace's Irish Dance Hub")

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
            with st.container(border=True):
                is_completed = goal.get("completed", False)
                # Use markdown inside the checkbox label for a compact layout
                label = f"~~**{goal['text']}**~~" if is_completed else f"**{goal['text']}**"
                
                is_checked = st.checkbox(label, value=is_completed, key=f"goal_{goal['id']}")
                
                if is_checked != is_completed:
                    supabase.table("goals").update({"completed": is_checked}).eq("id", goal["id"]).execute()
                    st.rerun()
                
                # Tertiary button makes it text-only
                if st.button("❌ Remove", key=f"del_goal_{goal['id']}", type="tertiary"):
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
            is_completed_today = ex.get("last_completed_date") == today_str
            
            with st.container(border=True):
                # .strip() cleans up accidental trailing spaces that break markdown bolding
                name = ex['name'].strip()
                reps = ex['reps'].strip()
                
                # Put the main text INSIDE the checkbox label. This fixes the vertical stacking!
                label = f"~~**{name}** - *{reps}*~~" if is_completed_today else f"**{name}** - *{reps}*"
                
                ex_check = st.checkbox(label, value=is_completed_today, key=f"ex_check_{ex['id']}")
                
                if ex_check != is_completed_today:
                    new_date_value = today_str if ex_check else ""
                    supabase.table("exercises").update({"last_completed_date": new_date_value}).eq("id", ex["id"]).execute()
                    st.rerun()
                    
                if ex.get('notes'):
                    st.caption(f"📝 {ex['notes']}")
                    
                if st.button("❌ Remove", key=f"del_ex_{ex['id']}", type="tertiary"):
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
                st.write(corr["text"])
                
                if st.button("❌ Remove", key=f"del_corr_{corr['id']}", type="tertiary"):
                    supabase.table("corrections").delete().eq("id", corr["id"]).execute()
                    st.rerun()
