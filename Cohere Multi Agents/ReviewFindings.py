from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain.schema.output_parser import StrOutputParser
from langchain.retrievers.multi_query import  MultiQueryRetriever
from datetime import datetime


import oracledb
import streamlit as st


pw = "AIWinter2024"
wp = 'GSCOracle@123'

#Hook
chat = ChatOCIGenAI(
    model_id="cohere.command-r-08-2024",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="ocid1.compartment.oc1..aaaaaaaaot4lwjjcw777uted5caozsgsop45mcd7hyu2ip2odwe6w5lj4s5a",
    model_kwargs={"temperature": 1.0, "max_tokens": 2000},
)
embeddings = OCIGenAIEmbeddings(
    model_id="cohere.embed-english-light-v3.0",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="ocid1.compartment.oc1..aaaaaaaaot4lwjjcw777uted5caozsgsop45mcd7hyu2ip2odwe6w5lj4s5a",
    model_kwargs={"truncate":True}
)
#DB Details
un = "RUKRISH"
cs = '''(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.us-ashburn-1.oraclecloud.com))(connect_data=(service_name=xc1jkwmwg759api_scmdevdb23ai_low.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'''
wl='C:\\Users\\Ashish\\PycharmProjects\\Wallet_scmdevdb23ai'
#Establish Connection
global connection
try:
    connection = oracledb.connect(user=un, password=pw, dsn=cs,config_dir=wl ,wallet_location=wl,wallet_password =wp)

    print("Successful Connection ")
except Exception as e:
    print("Connection failed")
    print(e)

st.title("Product Reviews & Insights ")
productName = st.text_input("Please provide the product name.")
question=""
print(f"Initial Query : {productName}")
if productName != "":
    WHAT_CUSTOMER_SAY = "What customers say about the product " + productName
    SENTIMENTS = "Provide the positive & negative sentiments from the reviews of " + productName
    IMPROVEMENT_AREAS = "Provide potential  improvement areas in design and features of " + productName
    question_options = [WHAT_CUSTOMER_SAY,SENTIMENTS ,IMPROVEMENT_AREAS]
    question = st.selectbox("Select the information you want to seek.",options=question_options)
    print(f"Query for the LLM : {question}")
    print(f"Question Name: {question}")
if st.button('Go'):
        print(f"Product Name: {productName}")
        template =     """You are helpful AI assistant.Use the following pieces of context to answer the question at the end.
                        If you do not know the answer just say you don't know,DO NOT try to make up the answer.
                        If the question is not related to the context ,politely respond that you are tuned to only answer questions related to the context.
                        Given the {context} information and not based on prior knowledge, answer the following {question}. 
                        Please align the response based on {productName}."""

        if question == "":
            query = productName
        else:
            query = question


        print(f"Query : {query}")


        vs= OracleVS(embedding_function = embeddings,client= connection,table_name = 'DOCS' ,  distance_strategy=DistanceStrategy.DOT_PRODUCT )

        # Naive RAG Method
        #retriever = vs.as_retriever(search_type = "similarity" , search_kwargs = {'k': 5})
        #documents= retriever.invoke(query)


        # Multi-query RAG goes here
        retriever = MultiQueryRetriever.from_llm(vs.as_retriever(search_type = "similarity" , search_kwargs = {'k': 5}),llm=chat)
        documents = retriever.invoke(query)
        #print(f"Context : {documents}")

        prompt = PromptTemplate.from_template(template)
        chain = (
            {"context": lambda x :documents,"question": lambda x :question,"productName": lambda x :productName }
            | prompt
            | chat
            | StrOutputParser()

        )
        response = chain.invoke(productName)
        st.text_area("Your response is listed below",response,600)

# Add a button that will trigger the API call & Capture the reviews

if st.button('Capture Reviews'):
    st.write("Capturing review data...")
    global cursor
    try:
        # Create a cursor object using the connection
        cursor = connection.cursor()
        # SQL query to insert a record into a table
        insert_query = """
        INSERT INTO XXPRODUCT_AI_REVIEW (PRODUCT_NUMBER,PRODUCT_DESCRIPTION,PRODUCT_REVIEW,CREATION_DATE,LAST_UPDATE_DATE)
        VALUES (:1, :2, :3,:4,:5)
        """
        # Values to insert into the table
        values = (productName, productName, response,datetime.now(),datetime.now())
        # Execute the SQL query and commit the transaction
        cursor.execute(insert_query, values)
        connection.commit()
        print("Record inserted successfully.")
        st.write("Review data successfully captured...")
    except Exception as e:
        # Handle any database errors
        print("There was an error while inserting data into the database:", e)
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()





