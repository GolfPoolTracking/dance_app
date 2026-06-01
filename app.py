import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import date
import random

# Mobile-friendly page configuration
st.set_page_config(page_title="Grace's Dance App", page_icon="💃", layout="centered")

# The UI/UX Master CSS Hack
st.markdown("""
    <style>
        /* 1. Ultra-tight container padding to make the boxes smaller */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0.4rem 0.6rem !important;
        }
        
        /* 2. Remove default gap between the checkbox and the notes */
        div[data-testid="stVerticalBlock"] > div {
            gap: 0rem !important;
        }
        
        /* 3. Align notes perfectly under the text, skipping the checkbox square */
        div[data-testid="stCaptionContainer"] {
            padding-left: 1.8rem; 
            margin-top: -0.4rem;
            padding-bottom: 0.2rem;
        }
        
        /* 4. FORCE COLUMNS TO STAY INLINE ON MOBILE */
        @media (max-width: 600px) {
            div[data-testid="stHorizontalBlock"] {
                flex-wrap: nowrap !important;
                align-items: center !important;
            }
            div[data-testid="column"] {
                width: auto !important;
                flex: 1 1 auto !important;
                min-width: 0 !important; /* Allows text to wrap instead of pushing button down */
            }
        }
        
        /* 5. Clean up the toggle button alignment */
        label[data-testid="stWidgetLabel"] {
            padding-bottom: 0 !important;
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
        col_hdr, col_edit = st.columns([0.6, 0.4])
        with col_hdr:
            st.header("My Goals")
        with col_edit:
            edit_goals = st.toggle("✏️ Edit List", key="toggle_goals")
        
        with st.form("new_goal_form", clear_on_submit=True):
            new_goal = st.text_input("Add a new goal:")
            submitted = st.form_submit_button("Add Goal", use_container_width=True)
            if submitted and new_goal:
                supabase.table("goals").insert({"text": new_goal, "completed": False}).execute()
                st.rerun()
                
        if not goals_data:
            st.caption("No goals added yet.")
            
        for goal in goals_data:
            with st.container(border=True):
                is_completed = goal.get("completed", False)
                label = f"~~**{goal['text']}**~~" if is_completed else f"**{goal['text']}**"
                
                if edit_goals:
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        is_checked = st.checkbox(label, value=is_completed, key=f"goal_{goal['id']}")
                    with c2:
                        if st.button("❌", key=f"del_goal_{goal['id']}", type="tertiary", help="Remove"):
                            supabase.table("goals").delete().eq("id", goal["id"]).execute()
                            st.rerun()
                else:
                    is_checked = st.checkbox(label, value=is_completed, key=f"goal_{goal['id']}")
                
                if is_checked != is_completed:
                    supabase.table("goals").update({"completed": is_checked}).eq("id", goal["id"]).execute()
                    st.rerun()

    # --- TAB 2: EXERCISES ---
    with tab2:
        col_hdr, col_edit = st.columns([0.6, 0.4])
        with col_hdr:
            st.header("Daily Routine")
        with col_edit:
            edit_exercises = st.toggle("✏️ Edit List", key="toggle_ex")
        
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
                name = ex['name'].strip()
                reps = ex['reps'].strip()
                label = f"~~**{name}** - *{reps}*~~" if is_completed_today else f"**{name}** - *{reps}*"
                
                if edit_exercises:
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        ex_check = st.checkbox(label, value=is_completed_today, key=f"ex_check_{ex['id']}")
                        if ex.get('notes'):
                            st.caption(f"📝 {ex['notes']}")
                    with c2:
                        if st.button("❌", key=f"del_ex_{ex['id']}", type="tertiary", help="Remove"):
                            supabase.table("exercises").delete().eq("id", ex["id"]).execute()
                            st.rerun()
                else:
                    ex_check = st.checkbox(label, value=is_completed_today, key=f"ex_check_{ex['id']}")
                    if ex.get('notes'):
                        st.caption(f"📝 {ex['notes']}")
                
                if ex_check != is_completed_today:
                    new_date_value = today_str if ex_check else ""
                    supabase.table("exercises").update({"last_completed_date": new_date_value}).eq("id", ex["id"]).execute()
                    st.rerun()

    # --- TAB 3: CORRECTIONS ---
    with tab3:
        col_hdr, col_edit = st.columns([0.6, 0.4])
        with col_hdr:
            st.header("Corrections")
        with col_edit:
            edit_corr = st.toggle("✏️ Edit List", key="toggle_corr")
        
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
                if edit_corr:
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        st.write(corr["text"])
                    with c2:
                        if st.button("❌", key=f"del_corr_{corr['id']}", type="tertiary", help="Remove"):
                            supabase.table("corrections").delete().eq("id", corr["id"]).execute()
                            st.rerun()
                else:
                    st.write(corr["text"])
