import streamlit as st
from snowflake.snowpark import Session

class SnowflakeConnector:
    def __init__(self):
        self.session = Session.builder.configs({
            "account": st.secrets["snowflake"]["account"],
            "user": st.secrets["snowflake"]["user"],
            "password": st.secrets["snowflake"]["password"],
            "warehouse": st.secrets["snowflake"]["warehouse"],
            "database": st.secrets["snowflake"]["database"],
            "schema": st.secrets["snowflake"]["schema"]
        }).create()

    def execute_query(self, query):
        return self.session.sql(query).collect()
