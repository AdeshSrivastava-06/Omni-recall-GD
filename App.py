import streamlit as st
from search import answer_question, generate_daily_summary
from db import get_all_app_settings, set_app_blocked, add_custom_app

st.set_page_config(page_title="OmniRecall", layout="centered")
st.title("OmniRecall — Your Local Screen Memory")
st.caption("Ask about anything you've seen on your screen. Fully offline.")

tab_search, tab_privacy, tab_summary = st.tabs(["🔍 Search", "🔒 Privacy Settings", "📅 Daily Summary"])

# ---------------- SEARCH TAB ----------------
with tab_search:
    query = st.text_input("What are you trying to remember?")

    if st.button("Search") and query.strip():
        with st.spinner("Searching your screen memory..."):
            answer, matches = answer_question(query)

        st.subheader("Answer")
        st.markdown(answer)

        if matches:
            best_score, best_cap = matches[0]
            if best_score < 0.4:
                st.warning("Low confidence match — this might not be exactly what you're looking for.")

            st.subheader("Best Match")
            confidence_pct = int(best_score * 100)
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Confidence", f"{confidence_pct}%")
            with col2:
                st.markdown(f"**Captured:** {best_cap['timestamp']}")
            if best_cap.get("screenshot_path"):
                st.image(best_cap["screenshot_path"], use_container_width=True)
            else:
                st.caption("Screenshot was archived (text-only record retained).")

            if len(matches) > 1:
                with st.expander("Not what you were looking for? Show more matches"):
                    for score, cap in matches[1:]:
                        confidence_pct = int(score * 100)
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.metric("Confidence", f"{confidence_pct}%")
                        with col2:
                            st.markdown(f"**Captured:** {cap['timestamp']}")
                        if cap.get("screenshot_path"):
                            st.image(cap["screenshot_path"], use_container_width=True)
                        else:
                            st.caption("Screenshot was archived (text-only record retained).")
                        st.divider()

# ---------------- PRIVACY / BLOCKED APPS TAB ----------------
with tab_privacy:
    st.subheader("Blocked Applications")
    st.caption("Apps in this list are never captured or indexed, even if visible on screen.")

    settings = get_all_app_settings()

    if settings:
        for entry in settings:
            app_name = entry["app_name"]
            currently_blocked = entry["blocked"]
            new_value = st.checkbox(app_name, value=currently_blocked, key=f"block_{app_name}")
            if new_value != currently_blocked:
                set_app_blocked(app_name, new_value)
                st.rerun()
    else:
        st.info("No app settings found yet.")

    st.divider()
    st.subheader("Add a custom app to block")
    with st.form("add_app_form", clear_on_submit=True):
        new_app_name = st.text_input("Window title or app name (partial match, case-insensitive)")
        submitted = st.form_submit_button("Add & Block")
        if submitted and new_app_name.strip():
            add_custom_app(new_app_name.strip(), blocked=True)
            st.success(f"'{new_app_name.strip()}' added and blocked.")
            st.rerun()

# ---------------- DAILY SUMMARY TAB ----------------
with tab_summary:
    st.subheader("What did I do today?")
    if st.button("Generate Summary"):
        with st.spinner("Summarizing today's activity..."):
            summary = generate_daily_summary()
        st.markdown(summary)
