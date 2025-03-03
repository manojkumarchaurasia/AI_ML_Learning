from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.vectorstores import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
import oracledb
from langchain_text_splitters import CharacterTextSplitter
from ScrapeReview import scrape_reviews
from UseGoogle import google_search
import time

import agent
import cohere
import os
import streamlit as st
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

API_KEY = os.getenv('API_KEY')
##API_KEY = "u93owHrX5QEuO95K4zViM1vd0bnvkUBHIn4jDpbW"
#FA_POD_URL=os.getenv('FA_POD_URL')
#FA_USERNAME=os.getenv('FA_USERNAME')
#FA_PASSWORD=os.getenv('FA_PASSWORD')

print('API_KEY :',{API_KEY})
#print('FA_POD_URL :',{FA_POD_URL})
#print('FA_USERNAME :',{FA_USERNAME})
#print('FA_PASSWORD :',{FA_PASSWORD})

co = cohere.ClientV2(API_KEY)
pw = "AIWinter2024" # 23AI Vector DB User Name
wp = 'GSCOracle@123' # 23AI Vector DB Password

# Hook
chat = ChatOCIGenAI(
    model_id="cohere.command-r-08-2024",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com", # GC35013 OCI Server
    compartment_id="ocid1.compartment.oc1..aaaaaaaaot4lwjjcw777uted5caozsgsop45mcd7hyu2ip2odwe6w5lj4s5a",
    model_kwargs={"temperature": 1.0, "max_tokens": 2000},
)
embeddings = OCIGenAIEmbeddings(
    model_id="cohere.embed-english-light-v3.0",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="ocid1.compartment.oc1..aaaaaaaaot4lwjjcw777uted5caozsgsop45mcd7hyu2ip2odwe6w5lj4s5a",
    model_kwargs={"truncate": True}
)
# DB Details
un = "RUKRISH"
cs = '''(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.us-ashburn-1.oraclecloud.com))(connect_data=(service_name=xc1jkwmwg759api_scmdevdb23ai_low.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'''
wl = 'C:\\Users\\manchaur\\Documents\\MyProject\\Wallet_scmdevdb23ai'

# Establish Connection
global connection

collect_review_tool_schemas = [
    {
        "type": "function",
        "function": {
            "name": "collect_product_reviews",
            "description": "Use this tool to search from internet and collect review data based on the specified query",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "It is user input to be passed to this tool as parameter."
                    }
                },
                "required": ["user_input"]
            },

        }
    }
]

# Collect Reviews
def collect_product_reviews(user_input: str) -> dict:
    """Use this tool to collect  the reviews of the specified product."""
    print(f"Tool - collect_product_reviews")
    print(f"**************user_input*******************"+user_input)

    try:
        connection = oracledb.connect(user=un, password=pw, dsn=cs,config_dir=wl ,wallet_location=wl,wallet_password =wp)
        print("Successful Connection ")
    except Exception as e:
        print("Connection failed")
        print(e)

    reviewText=""
    # Example usage
    query = user_input
    results = google_search(query)

    if results:
        for idx, result in enumerate(results):
            title = result['title']
            link = result['link']
            snippet = result.get('snippet', 'No snippet available')
            print(f"{idx + 1}. {title}\n   {link}\n   {snippet}\n")
            st.write(f"{idx + 1}. {title}\n   {link}\n   {snippet}\n")
            review_url = link
            text = scrape_reviews(review_url)
            reviewText += text
    else:
        print("No results found.")

    #print(f"Review Text: {reviewText}")
    #Convert into chunks
    text_splitter = CharacterTextSplitter(separator='.',chunk_size=2000,chunk_overlap=100)
    chunks= text_splitter.split_text(reviewText)
    #Function to Add data to Vector Store
    def chunks_to_docs_wrapper(row:dict) -> Document:
        """Chunk conversion into document object
        A dictionary representing a row for data with keys for id, link and text"""
        metadata={'id':row['id'],'link':row['link']}
        return Document(page_content = row['text'], metadata = metadata)

    docs= [chunks_to_docs_wrapper({"id":str(page_num + time.time()), 'link': f'Page{page_num}','text': text }) for page_num,text in enumerate(chunks)]
    vector_store = OracleVS(embedding_function = embeddings,client=connection,table_name='DOCS',distance_strategy=DistanceStrategy.DOT_PRODUCT)
    try:
        vector_store.add_documents(docs)
        print(f"\n\n\nAdd texts complete for vector store\n\n\n")
    except Exception as ex:
        print(ex)

    SUCCESSFULL_VECTOR_STORE =  "Successfully captured the review data in vector store"
    return SUCCESSFULL_VECTOR_STORE


collect_review_tools_map = {
        "collect_product_reviews": collect_product_reviews,
       }

collect_review_agent = agent.Agent(
    name="Collect Review Agent",
    model="command-r-plus-08-2024",
    instructions="""
    You are a collect review agent designed to collect  the product review data by utilizing a set of specialized tools. Your primary goal is to execute the tools in order to collect the product review data.

    You should use the below tools to response to user query.

    - 1. Call collect_product_reviews tool when the user asks to collect the  review data based on the specified product in user input. 
    
    Make sure you call tools in order to generate the final data, don't generate your own responses.
    Please accept the user input as-is without modifying to pass on as arguments to the tool function

    """,
    tool_schemas=collect_review_tool_schemas,
    tools_map=collect_review_tools_map
)

st.title("Review Data Collection")
product_name = st.text_input("Please provide the product name.")
print(f"Initial Query : {product_name}")
if product_name != "":
    COLLECT_REVIEWS = "Reviews and feedbacks of " + product_name
    question_options = [COLLECT_REVIEWS]
    query = st.selectbox("Select the information you want to seek.",options=question_options)
    print(f"Query for the LLM : {query}")
    print(f"Question Name: {query}")
    messages = []
    print(f"User Input : {query}")
    messages.append({"role": "user", "content":query })
    response = agent.run(collect_review_agent, messages)
    messages.extend(response.messages)
    # messages.append("Please accept the user input as-is without modifying to pass on as arguments to the tool function")
    print("Final Agent Response:", messages[-1]["content"])
    st.write("Final Agent Response:")
    st.write(messages[-1]["content"])
