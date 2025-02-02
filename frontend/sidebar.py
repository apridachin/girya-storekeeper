import streamlit as st

from api import log_in, run_async

def create_sidebar():
    if "authorization" not in st.session_state:
        st.session_state.authorization = False
    
    st.title("🏪 Girya Storekeeper")
    
    with st.form("login_form"):
        st.subheader("🔑 Warehouse Credentials")
        login = st.text_input("Login", type="default")
        password = st.text_input("Password", type="password")
    
        if st.form_submit_button("Login"):
            run_async(log_in(login=login, password=password))
            if st.session_state.authorization:
                st.success("✅ Authenticated!")
            else:
                st.error("❌ Wrong credentials!")
    
    st.markdown("---")
    st.markdown("""
    This tool helps you manage your inventory by:
    - Creating demands in Warehouse from CSV files
    - Comparing stocks in Warehouse and Partners site
    - Comparing stocks in Warehouse and competitors sites
    """)