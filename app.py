import streamlit as st

st.set_page_config(page_title="Selangor RoadCare", page_icon="🛣️")

st.title("Selangor Intelligent RoadCare")
st.write("Environment setup successful!")

if st.button("Test"):
    st.success("Streamlit is working!")