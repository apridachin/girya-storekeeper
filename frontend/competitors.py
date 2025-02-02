import streamlit as st
import time

from api import run_async, get_competitors_stock, get_product_groups, get_competitors_search_status


def create_competitors_tab():
    st.header("Warehouse Product Groups")
    product_groups = run_async(get_product_groups())
    
    if product_groups:
        selected_group = st.selectbox(
            "Select a Product Group",
            options=[group["name"] for group in product_groups],
            key="selected_product_group"
        )
        st.session_state.selected_product_group_id = next(
            (group["id"] for group in product_groups if group["name"] == selected_group),
            None
        )
                
    st.divider()
    st.header("Competitors Stock")
    if product_groups and selected_group:
        st.write(f"Check competitors stock for {selected_group}")
    else:
        st.warning("Please select a group")

    # Initialize session state for task status
    if 'competitors_task_running' not in st.session_state:
        st.session_state.competitors_task_running = False
        st.session_state.competitors_data = None

    if st.button("🔄 Refresh Competitors Stock", disabled=st.session_state.competitors_task_running):
        st.session_state.competitors_task_running = True
        response = run_async(get_competitors_stock(product_group_id=st.session_state.selected_product_group_id))
        
        if response and response.get("status") == "success":
            st.session_state.task_id = response["task_id"]
            st.session_state.competitors_data = None
        else:
            st.error("Failed to start competitors search")
            st.session_state.competitors_task_running = False

    if st.session_state.competitors_task_running:
        with st.spinner("Searching competitors..."):
            placeholder = st.empty()
            while True:
                status_response = run_async(get_competitors_search_status(task_id=st.session_state.task_id))
                
                if status_response:
                    status = status_response.get("status")
                    if status == "completed":
                        st.session_state.competitors_task_running = False
                        st.session_state.competitors_data = status_response.get("result")
                        break
                    elif status == "failed":
                        placeholder.error(f"Search failed: {status_response.get('error', 'Unknown error')}")
                        st.session_state.competitors_task_running = False
                        break
                    elif status == "not_found":
                        placeholder.error("Search task not found")
                        st.session_state.competitors_task_running = False
                        break
                    else:
                        time.sleep(5)

    # Display results if available
    if st.session_state.competitors_data:
        if st.session_state.competitors_data["size"] > 0:
            table_data = [
                {
                    "Product": row.get("name", "Not Found"),
                    "Warehouse Stock": row.get("stock", "-"),
                    "Warehouse Price": f"{row.get('price', 0) / 100} RUB",
                    "Competitor Product": row.get("found_name", "Not Found"),
                    "Competitor Price": row.get("found_price", "Not Found"),
                    "Competitor Link": row.get("found_url", "Not Found"),
                } for row in st.session_state.competitors_data["rows"]
            ]
            st.markdown(f"Found {st.session_state.competitors_data['size']} products")
            st.dataframe(
                data=table_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Competitor Link": st.column_config.LinkColumn(
                        "Competitor Link",
                        validate="^https?://.*",
                    ),
                }
            )
        else:
            st.info("No stock data available")
