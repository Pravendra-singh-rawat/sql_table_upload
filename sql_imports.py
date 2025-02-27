import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import time

# Custom CSS for better styling
st.markdown("""
    <style>
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            padding: 10px 24px;
            border: none;
            border-radius: 5px;
        }
        .stFileUploader > div > div {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 10px;
        }
        h1 {
            color: #4CAF50;
        }
        h2 {
            color: #008CBA;
        }
        footer {
            text-align: center;
            margin-top: 50px;
            font-size: 14px;
            color: #6c757d;
        }
    </style>
""", unsafe_allow_html=True)

# Add Font Awesome for icons
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

# Title with an icon
st.markdown("""
    <h1 style="color: #4CAF50;"> <i class="fas fa-database"></i> Upload Excel/CSV to SQL Database </h1>
""", unsafe_allow_html=True)

# Tabs for better organization
tab1, tab2, tab3 = st.tabs(["Database Connection", "File Upload", "Advanced Settings"])

# Tab 1: Database Connection
with tab1:
    st.header("Database Connection")
    col1, col2 = st.columns(2)
    
    with col1:
        db_type = st.selectbox("Select Database Type", ["MySQL", "PostgreSQL", "SQL Server"], help="Choose the type of database you want to connect to.")
        host = st.text_input("Host", value="localhost", help="Enter the database host (e.g., localhost or 127.0.0.1)")
        port = st.text_input("Port", value="3306", help="Enter the database port (default is 3306 for MySQL)")
    
    with col2:
        username = st.text_input("Username", value="root", help="Enter your database username")
        password = st.text_input("Password", type="password", help="Enter your database password")
        database = st.text_input("Database Name", help="Enter the name of the database")

# Tab 2: File Upload
with tab2:
    st.header("File Upload")
    uploaded_file = st.file_uploader("Choose an Excel or CSV file", type=["csv", "xlsx"], help="Upload your Excel or CSV file here.")
    
    if uploaded_file is not None:
        # Read the file into a DataFrame
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.write("Preview of the uploaded data:")
        st.dataframe(df.head())
        
        # Column Selection and Data Type Modification
        st.subheader("Column Selection and Data Type Modification")
        st.info("Select the columns you want to upload and modify their data types if needed.")
        
        # Create a dictionary to store column names, their selected status, and data types
        column_config = {}
        for col in df.columns:
            col_name = col
            col_type = str(df[col].dtype)  # Default data type
            
            # Allow user to select columns for upload
            col_selected = st.checkbox(f"Include '{col_name}'", value=True, key=f"include_{col_name}")
            
            # Allow user to change the data type
            new_col_type = st.selectbox(
                f"Data Type for '{col_name}'",
                options=["int64", "float64", "object", "bool", "datetime64[ns]"],
                index=["int64", "float64", "object", "bool", "datetime64[ns]"].index(col_type) if col_type in ["int64", "float64", "object", "bool", "datetime64[ns]"] else 2,
                key=f"type_{col_name}"
            )
            
            # Store column configuration
            column_config[col_name] = {
                "selected": col_selected,
                "type": new_col_type
            }
        
        # Filter DataFrame based on selected columns and convert data types
        selected_columns = [col for col, config in column_config.items() if config["selected"]]
        df_filtered = df[selected_columns]
        
        # Convert data types
        for col, config in column_config.items():
            if config["selected"]:
                try:
                    if config["type"] == "datetime64[ns]":
                        df_filtered[col] = pd.to_datetime(df_filtered[col], errors='coerce')
                    else:
                        df_filtered[col] = df_filtered[col].astype(config["type"])
                except Exception as e:
                    st.warning(f"Could not convert column '{col}' to {config['type']}: {e}")
        
        st.write("Filtered and Modified Data Preview:")
        st.dataframe(df_filtered.head())

# Tab 3: Advanced Settings
with tab3:
    st.header("Advanced Settings")
    table_name = st.text_input("Enter Table Name", value="new_table", help="Enter the name of the table where the data will be stored.")
    if_exists_option = st.selectbox("If table already exists", ["replace", "append", "fail"], help="Choose what to do if the table already exists.")

# Footer
st.markdown("""
    <footer>
        Made with ❤️ by Pravendra Singh 
    </footer>
""", unsafe_allow_html=True)

# Upload Button
if st.button("Upload to Database 🚀"):
    if uploaded_file is None:
        st.error("❌ Please upload a file first!")
    elif not table_name:
        st.error("❌ Please enter a valid table name!")
    else:
        try:
            # URL-encode the password to handle special characters
            encoded_password = quote_plus(password)
            # Create the database engine
            if db_type == "MySQL":
                engine = create_engine(f"mysql+pymysql://{username}:{encoded_password}@{host}:{port}/{database}")
            elif db_type == "PostgreSQL":
                engine = create_engine(f"postgresql+psycopg2://{username}:{encoded_password}@{host}:{port}/{database}")
            elif db_type == "SQL Server":
                engine = create_engine(f"mssql+pyodbc://{username}:{encoded_password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server")
            
            # Show progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            for i in range(100):
                time.sleep(0.05)  # Simulate delay
                progress_bar.progress(i + 1)
                status_text.text(f"Uploading data... {i + 1}%")
            
            # Upload the filtered DataFrame to the database
            df_filtered.to_sql(name=table_name, con=engine, index=False, if_exists=if_exists_option)
            st.success("✅ Data successfully uploaded to the database!")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
