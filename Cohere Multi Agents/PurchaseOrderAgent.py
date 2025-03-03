from agent import Agent
import requests, json
from requests.auth import HTTPBasicAuth
import cohere
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

#API_KEY = "xjG5F5HbcF49gmKKYShwGRkndnSaJ4Gnc2HONg9m"  # fill in your Cohere API key here
#co = cohere.ClientV2(API_KEY)

purchase_order_tool_schemas = [
    {
        "type": "function",
        "function": {
            "name": "generate_purchase_order_filters",
            "description": "Use this tool to select appropriate filters for purchase orders from a list of predefined options based on user input, returning a dictionary of the selected filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "It is user input, don't modify it and pass as it is to this tool as parameter."
                    }
                },
                "required": ["user_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_purchase_order_filters",
            "description": "Use this tool to apply the selected filters to retrieve the purchase orders, returning a dictionary of the filtered purchase orders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "array",
                        "description": "list of filters to apply on purchase order details.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"}
                            },
                            "required": ["name", "value"]
                        }
                    }
                },
                "required": ["filters"]
            }
        }
    }
]


# Generate filters
def generate_purchase_order_filters(user_query: str) -> dict:
    """Use this tool to select appropriate filters for purchase orders from a list of predefined options based on user input, returning a dictionary of the selected filters."""

    preamble = """
    You are a Purchase Order assistant. Your task is to determine the appropriate filters for purchase orders based on the user's input. 
    """
    message = """
    Given the filter schema and the user's query, determine the appropriate filter(s). 

    ### Instructions
    - You are restricted to use only the provided filters. Do not create new filters. 
    - If you don't find any filters in the user query, generate an empty JSON array.
    - The response should be a JSON array of objects, where each object contains the filter name and its corresponding value. 
    - If you don't find any mentioned filters in the user query, generate an empty JSON array.

    ##Context : Filters Schema for Purchase Orders
    - {"name": "OrderNumber", "description": "Filter purchase orders by the order number", "examples": ["189", "59", "44"]},
    - {"name": "CurrencyCode", "description": "Filter purchase orders by the currency", "examples": ["USD", "EUR", "GBP"]},
    - {"name": "Supplier", "description": "Filter purchase orders by the supplier", "examples": ["Advanced Corp", "ABC Consulting"]},
    - {"name": "Buyer", "description": "Filter purchase orders by the Buyer", "examples": ["Gee, May", "Brown, Casey"]},
    - {"name": "Status", "description": "Filter purchase orders by the status", "examples": ["Open", "Closed", "Canceled","Incomplete","Pending Approval","Rejected"]}

    ### Validation: Don't include filter attributes with None or unknown values. Exclude them from the response.

    ###Follow the Examples for generating the response.If user query contains Ampersand (&) then replace it with "%26"
    Example 1:
    - User Input: "Show me purchase orders in USD currency and approved status"
    - Output: [{"name": "CurrencyCode", "value": "USD"},{"name": "Status", "value": "Approved"}]

    Example 2:
    - User Input: "List purchase orders handled by Gee, May and pending approval."
    - Output: [{"name": "Buyer", "value": "Gee, May"},{"name": "Status", "value": "Pending Approval"}]

    Example 3:
    - User Input: "Find purchase orders for Supplier ABC Consulting."
    - Output: [{"name": "Supplier", "value": "ABC Consulting"}]

    Example 4:
    - User Input: "Find purchase orders for Supplier W&W Glass LLC."
    - Output: [{"name": "Supplier", "value": "W%26W Glass LLC"}]

    Example 5:
    - User Input: "Retrieve purchase orders in EUR and rejected status."
    - Output: [{"name": "CurrencyCode", "value": "EUR"},{"name": "Status", "value": "Rejected"}]

    Example 6:
    - User Input: "What is the status of purchase order 162844."
    - Output: [{"name": "OrderNumber", "value": "162844"}]

    ###Response Evaluation:
    Ensure that the response is a valid JSON array and does not include any None values or extra formatting.
    Don't include ```json in response.

    ###response_format:
    {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["name", "value"]
        }
    }
    """
    message = f"""
    {message}
    ###User request: {user_query}
    """

    messages = [
        {"role": "system", "content": preamble},
        {"role": "user", "content": message}
    ]

    messages = [
    SystemMessage(content=preamble),
    AIMessage(content="Hi from Purchasing Agent!"),
    HumanMessage(content=message),
]
    chat=ChatOCIGenAI(
    model_id="cohere.command-r-08-2024",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="ocid1.compartment.oc1..aaaaaaaaot4lwjjcw777uted5caozsgsop45mcd7hyu2ip2odwe6w5lj4s5a",
    model_kwargs={"temperature": 1.0, "max_tokens": 2000},
    )
    response = chat.invoke(messages)
    print("printing response")
    print(response.content)

    filters = response.content
    return filters


def apply_purchase_order_filters(filters: dict) -> dict:
    """Use this tool to apply the selected filters to retrieve the purchase orders, returning a dictionary of the filtered purchase orders."""

    # Convert the filter list to the REST `q` parameter format
    query_parts = [f"{f['name']}='{f['value']}'" for f in filters]
    q_parameter = ";".join(query_parts)
    fields = "POHeaderId,OrderNumber,Supplier,ProcurementBU,Total,Status,Buyer,CurrencyCode,CreationDate"
    limit = 10
    print(q_parameter)
    auth = HTTPBasicAuth('ashish.k.das@oracle.com', 'Oracle@123')
    headers = {"REST-Framework-Version": "2"}
    url = f"https://ehso-dev2.fa.us2.oraclecloud.com/fscmRestApi/resources/11.13.18.05/purchaseOrders?q={q_parameter}&fields={fields}&limit={limit}&onlyData=true"
    print(url)
    response = requests.get(url, headers=headers, auth=auth)
    print(response)
    if response.status_code >= 200 and response.status_code < 300:
        items = response.json()['items']
        return json.dumps(items)
    else:
        return f"Failed to call events API with status code {response.status_code}"


purchase_order_tools_map = {
    "generate_purchase_order_filters": generate_purchase_order_filters,
    "apply_purchase_order_filters": apply_purchase_order_filters
}

purchase_order_agent = Agent(
    name="Purchase Order Agent",
    model="command-r-plus-08-2024",
    instructions="""
    You are a purchase order agent designed to generate the analytics data by utilizing a set of specialized tools. Your primary goal is to execute the tools in order to generate the analytics data.

    You are equipped with necessary tools to response to user query.
    - 1. Call generate_purchase_order_filters tool to generate the appropriate filters for purchase orders from a list of predefined options based on the user's input
    - 2. Call apply_purchase_order_filters to apply the generated filters on purchase orders and retrieve the filtered purchase orders.
    Make sure you call tools in order to generate the final data, don't generate your own responses.

    """,
    tool_schemas=purchase_order_tool_schemas,
    tools_map=purchase_order_tools_map
)