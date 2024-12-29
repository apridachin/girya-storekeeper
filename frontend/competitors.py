import streamlit as st

from api import run_async, get_competitors_stock


def create_competitors_tab():
    st.header("Current Stock")
    
    if st.button("🔄 Refresh Competitors Stock"):
        with st.spinner("Fetching stock data..."):
            stock_data = run_async(get_competitors_stock(credentials=st.session_state.credentials))
            if stock_data and "rows" in stock_data:
                if stock_data["size"] > 0:
                    table_data = [
                        {
                            "Product": row["name"],
                            "Warehouse Stock": f"{row['stock']:.0f}" if row.get("stock") else "—",
                            "Warehouse Price": f"{row['price'] / 100} RUB" if row.get("price") else "—",
                            "Competitor Link": row["url"] if row.get("url") else "Not Found",
                        } for row in stock_data["rows"]
                    ]
                    st.markdown(f"Found {stock_data['size']} products")
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
            else:
                st.error("Failed to fetch stock data")
