import streamlit as st
from search import answer_question

st.set_page_config(page_title="OmniRecall", layout="centered")
st.title("OmniRecall — Your Local Screen Memory")
st.caption("Ask about anything you've seen on your screen. Fully offline.")

query = st.text_input("What are you trying to remember?")

if st.button("Search") and query.strip():
    with st.spinner("Searching your screen memory..."):
        answer, matches = answer_question(query)

    st.subheader("Answer")
    st.markdown(answer)

    if matches:
        best_score = matches[0][0]
        if best_score < 0.4:
            st.warning("Low confidence match — this might not be exactly what you're looking for.")

        best_score, best_cap = matches[0]
        st.subheader("Best Match")
        confidence_pct = int(best_score * 100)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Confidence", f"{confidence_pct}%")
        with col2:
            st.markdown(f"**Captured:** {best_cap['timestamp']}")
        st.image(best_cap["screenshot_path"], use_container_width=True)

        if len(matches) > 1:
            with st.expander("Not what you were looking for? Show more matches"):
                for score, cap in matches[1:]:
                    confidence_pct = int(score * 100)
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.metric("Confidence", f"{confidence_pct}%")
                    with col2:
                        st.markdown(f"**Captured:** {cap['timestamp']}")
                    st.image(cap["screenshot_path"], use_container_width=True)
                    st.divider()
