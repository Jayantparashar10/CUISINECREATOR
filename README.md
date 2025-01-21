# AI Chef Assistant 🍴❄️

A Streamlit application hosted in Snowflake that leverages Snowflake Cortex Search and LLMs to generate creative recipes based on available ingredients.

![App Preview](https://app.snowflake.com/dlkhopg/ytb91182/#/streamlit-apps/CORTEX_SEARCH.PUBLIC.S0N_UK8ZQC20ZQLJ?ref=snowsight_shared)

## Features
- 🧠 Uses Snowflake Cortex Search for ingredient context retrieval
- 👩🍳 Generates recipes using Snowflake Cortex LLM (Mistral model)
- 💬 Interactive chat interface with conversation memory
- ⚙️ Configurable search parameters and model settings
- 🐞 Debug mode for development and troubleshooting

## Prerequisites
- Snowflake account with access to:
  - Streamlit in Snowflake (SiS)
  - Cortex Search Services
  - Cortex LLM functions
- Proper role permissions:
  - `USAGE` on database/schema
  - `CREATE STREAMLIT` privilege
  - Access to Cortex functions

## Installation (Snowflake Deployment)

### 1. Create Streamlit App
```sql
CREATE STREAMLIT RECIPE_ASSISTANT
ROOT_LOCATION = '@<stage_name>/path/to/app'
MAIN_FILE = '/app.py'
