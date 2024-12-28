import streamlit as st

def create_sidebar():
    if "credentials" not in st.session_state:
        st.session_state.credentials = {
            "login": "",
            "password": "",
        }
    
    st.title("🏪 Girya Storekeeper")
    
    with st.form("credentials_form"):
        st.subheader("🔑 Credentials")
        
        # Warehouse credentials
        st.markdown("#### Warehouse")
        login = st.text_input(
            "Login",
            value=st.session_state.credentials["login"],
            type="default"
        )
        password = st.text_input(
            "Password",
            value=st.session_state.credentials["password"],
            type="password"
        )
        
        if st.form_submit_button("Save Credentials"):
            st.session_state.credentials.update({
                "login": login,
                "password": password,
            })
            st.success("✅ Credentials saved!")
    
    st.markdown("---")
    st.markdown("""
    This tool helps you manage your inventory by:
    - Creating demands in Warehouse from CSV files
    - Comparing stocks in Warehouse and Partners site
    """)