import streamlit as st

st.set_page_config(page_title="Jalan_Ready", page_icon="🛣️")

st.title("Jalan_Ready")
st.write("Environment setup successful!")

if st.button("Test"):
    st.success("Streamlit is working!")