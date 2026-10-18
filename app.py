import streamlit as st

from ui_components.session import (
    init_state,
    list_projects,
    create_project,
    set_active_project,
    llm_available,
)

st.set_page_config(
    page_title="SmartPID - IO Signal Sudoku",
    page_icon="S",
    layout="wide",
)

init_state()

with st.sidebar:
    st.title("SmartPID")
    st.caption("DeltaV IO Signal Sudoku")

    projects = list_projects()
    if projects:
        current = st.session_state["project_name"]
        index = projects.index(current) if current in projects else 0
        chosen = st.selectbox("Project", projects, index=index)
        if chosen != st.session_state["project_name"]:
            set_active_project(chosen)
            st.rerun()

    with st.expander("New project"):
        new_name = st.text_input("Project name", key="new_project_name")
        if st.button("Create", use_container_width=True):
            if new_name.strip():
                create_project(new_name.strip())
                st.rerun()
            else:
                st.warning("Enter a project name first.")

    st.divider()
    if llm_available():
        st.success("LLM assist: ON", icon="")
    else:
        st.info("LLM assist: OFF (set ai key)", icon="ℹ")

st.title("SmartPID - DeltaV IO Signal Sudoku")
st.markdown(
    "Allocate every field signal to **cabinet › CIOC › baseplate › CHARM** "
    "using editable rules, then verify the result with an independent checker."
)
st.caption(f"Active project: **{st.session_state['project_name']}**")

# Pipeline status: each step turns green when its data exists in session state.
steps = [
    ("1. Upload & map", st.session_state["signals_df"] is not None),
    ("2. Rules", bool(st.session_state["rules"])),
    ("3. Allocate", st.session_state["allocation"] is not None),
    ("4. Validate", st.session_state["violations"] is not None),
    ("5. Report", st.session_state["report_ready"]),
    ("6. Revise (Rev B)", st.session_state["rev_b_allocation"] is not None),
]

cols = st.columns(len(steps))
for col, (label, done) in zip(cols, steps):
    with col:
        st.metric(label, " Done" if done else " Pending")

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("How to use")
    st.markdown(

    )
with right:
    st.subheader("Project snapshot")
    df = st.session_state["signals_df"]
    alloc = st.session_state["allocation"]
    st.write(f"Signals loaded: **{0 if df is None else len(df):,}**")
    st.write(f"Active rules: **{sum(1 for r in st.session_state['rules'] if r.get('enabled', True))}**")
    st.write(f"Signals allocated: **{0 if alloc is None else len(alloc):,}**")
    viol = st.session_state["violations"]
    st.write(f"Rule violations: **{'-' if viol is None else len(viol)}**")

st.info("Use the pages in the left sidebar to move through the steps.", icon="")