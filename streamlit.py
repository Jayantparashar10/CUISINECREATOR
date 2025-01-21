import streamlit as st
from snowflake.core import Root  # requires snowflake>=0.8.0
from snowflake.snowpark.functions import col

# Use st.connection instead of get_active_session
DB = "cortex_search"  # Update with your database name
SCHEMA = "public"  # Update with your schema name
SERVICE = "recipe"  # Update with your Cortex Search service name
BASE_TABLE = "cortex_search.public.recipe"  # Update with your recipe table
ARRAY_ATTRIBUTES = {"INGREDIENTS"}  # Update with array-type columns (e.g., ingredients)

SUPPORTED_MODELS = [
    "mistral-large2"
]

def setup_chat_history():
    if st.session_state.clear_conversation or "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def load_search_services():
    if "search_services" not in st.session_state:
        try:
            # Set the default database (if not already set)
            session.use_database("cortex_search")

            # Show Cortex Search Services
            services = session.sql("SHOW CORTEX SEARCH SERVICES;").collect()

            service_data = []
            if services:
                for service in services:
                    service_name = service["name"]

                    # Describe the Cortex Search Service using fully qualified name
                    search_service_result = session.sql(
                        f"DESC CORTEX SEARCH SERVICE cortex_search.public.{service_name};"
                    ).collect()

                    # Extract the search column
                    if search_service_result:
                        search_column = search_service_result[0]["search_column"]
                        service_data.append({
                            "name": service_name, 
                            "search_column": search_column
                        })
                    else:
                        st.error(f"No results found for Cortex Search Service: {service_name}")

            st.session_state.search_services = service_data
        except Exception as e:
            st.error(f"An error occurred while loading search services: {e}")

def configure_settings():
    st.title("Let's cook something!")
    
    # Move settings to the main app area
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("AI Chef Model:", SUPPORTED_MODELS, key="chef_model")
    with col2:
        st.number_input(
            "Ingredient Context Chunks",
            value=5,
            key="context_chunk_count",
            min_value=1,
            max_value=10
        )

    st.number_input(
        "Chat Memory Length",
        value=5,
        key="chat_memory_length",
        min_value=1,
        max_value=10
    )

def fetch_recipe_context(query):
    current_db, current_schema = session.get_current_database(), session.get_current_schema()
    
    search_service = (
        root.databases[current_db]
        .schemas[current_schema]
        .cortex_search_services[st.session_state.selected_search_service]
    )

    context_results = search_service.search(
        query, columns=[], limit=st.session_state.context_chunk_count
    ).results

    service_info = st.session_state.search_services
    search_column = [s["search_column"] for s in service_info
                    if s["name"] == st.session_state.selected_search_service][0]

    context_text = ""
    for idx, result in enumerate(context_results):
        context_text += f"Ingredient Context {idx+1}: {result[search_column]}\n\n"

    if st.session_state.debug_mode:
        st.text_area("Discovered Ingredients", context_text, height=500)

    return context_text

def get_recent_chat():
    start_idx = max(
        0, len(st.session_state.chat_history) - st.session_state.chat_memory_length
    )
    return st.session_state.chat_history[start_idx : len(st.session_state.chat_history) - 1]

def generate_completion(model_name, prompt_text):
    return session.sql("SELECT snowflake.cortex.complete(?,?)", 
                      (model_name, prompt_text)).collect()[0][0]

def summarize_chat_for_query(chat_history, current_question):
    summary_prompt = f"""
        [INST]
        Analyze this cooking conversation history and current question to create 
        an enhanced ingredient search query. Respond only with the final query.
        
        <chat_history>
        {chat_history}
        </chat_history>
        <current_question>
        {current_question}
        </current_question>
        [/INST]
    """

    optimized_query = generate_completion(st.session_state.chef_model, summary_prompt)

    if st.session_state.debug_mode:
        st.text_area("Optimized Search Query", optimized_query.replace("$", "\$"), height=150)

    return optimized_query

def construct_recipe_prompt(user_query):
    if st.session_state.use_history:
        previous_chat = get_recent_chat()
        if previous_chat:
            enhanced_query = summarize_chat_for_query(previous_chat, user_query)
            retrieved_context = fetch_recipe_context(enhanced_query)
        else:
            retrieved_context = fetch_recipe_context(user_query)
    else:
        retrieved_context = fetch_recipe_context(user_query)
        previous_chat = ""

    recipe_prompt = f"""
        [INST]
        You are a creative AI Chef Assistant. Using the ingredient context between <context> tags 
        and any relevant chat history between <history> tags, create a delicious recipe that 
        addresses the user's request. Keep responses focused on cooking instructions and 
        ingredient combinations.
        
        If the request can't be fulfilled with available context, respond politely.
        Avoid referencing the context sources directly.
        
        <history>
        {previous_chat}
        </history>
        <context>
        {retrieved_context}
        </context>
        <request>
        {user_query}
        </request>
        [/INST]
        Recipe Suggestion:
    """
    return recipe_prompt

def run_recipe_app():
    # Configure settings
    configure_settings()
    setup_chat_history()

    AVATARS = {"assistant": "❄️", "user": "🍴"}

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
            st.markdown(msg["content"])

    chat_disabled = (
        "search_services" not in st.session_state
        or len(st.session_state.search_services) == 0
    )
    
    if user_query := st.chat_input("What ingredients do you have?", disabled=chat_disabled):
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        with st.chat_message("user", avatar=AVATARS["user"]):
            st.markdown(user_query.replace("$", "\$"))

        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            response_placeholder = st.empty()
            with st.spinner("Cooking up ideas..."):
                sanitized_query = user_query.replace("'", "")
                ai_response = generate_completion(
                    st.session_state.chef_model, 
                    construct_recipe_prompt(sanitized_query)
                )
                response_placeholder.markdown(ai_response)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": ai_response}
        )

if __name__ == "__main__":
    # Use st.connection instead of get_active_session
    try:
        # Try to get the active session (works in Snowflake)
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
    except:
        # Fallback to st.connection (works locally or on Streamlit Cloud)
        cnx = st.connection("snowflake")
        session = cnx.session()

    root = Root(session)
    run_recipe_app()
