import agent
from PurchaseOrderAgent import purchase_order_agent
from SalesOrderAgent import sales_order_agent
from ShipmentAgent import shipment_agent

import streamlit as st


# Define Function Object
triage_agent_tool_schemas = [
    {
        "type": "function",
        "function": {
            "name": "transfer_to_purchase_order_agent",
            "description": "Use this to transfer to purchase_order_agent for query related to purchase order.",
            "parameters": {
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_sales_order_agent",
            "description": "Use this to transfer to sales_order_agent for query related to sales order.",
            "parameters": {
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_shipment_agent",
            "description": "Use this to transfer to shipment_agent for query related to shipment.",
            "parameters": {
                "type": "object"
            }
        }
    }
]

def transfer_to_purchase_order_agent():
    """Use this to transfer to purchase_order_agent for query related to purchase order"""
    return purchase_order_agent

def transfer_to_sales_order_agent():
    """Use this to transfer to sales_order_agent for query related to sales order"""
    return sales_order_agent

def transfer_to_shipment_agent():
    """Use this to transfer to shipment_agent for query related to shipment"""
    return shipment_agent

# Define object
triage_agent_tools_map = {
    "transfer_to_purchase_order_agent": transfer_to_purchase_order_agent,
    "transfer_to_sales_order_agent": transfer_to_sales_order_agent,
    "transfer_to_shipment_agent": transfer_to_shipment_agent
}

# Calling Agent and passing the control
# Chat model= "command-r-plus-08-2024"
triage_agent = agent.Agent(
    name="Triage Agent",
    model= "command-r-plus-08-2024", 
    instructions="""
    - You are a fusion assistant bot.
    - You are equipped with necessary purchase_order_agent ,sales_order_agent and shipment_agent to respond to user query.
    """,
    tool_schemas=triage_agent_tool_schemas,
    tools_map=triage_agent_tools_map
)

# Streamlit function for calling the UI
st.title("Tell me how can I assist you ?")

# Text area for getting string input
user_input = st.text_area("Please ask your specific question.")
#user_input="Who is the party for sales order 2008."
print(f"Query : {user_input}")

if st.button('Submit'):
    messages = []
    messages.append({"role": "user", "content": user_input})
    
    # Calling function of Agent
    response = agent.run(triage_agent, messages)
    messages.extend(response.messages)
    print("Final Agent Response:", messages[-1]["content"])
    st.write("Final Agent Response:")
    st.write(messages[-1]["content"])
