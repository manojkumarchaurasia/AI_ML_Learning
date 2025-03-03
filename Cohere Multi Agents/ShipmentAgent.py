from agent import Agent
import requests, json
from requests.auth import HTTPBasicAuth
import cohere

API_KEY = "xjG5F5HbcF49gmKKYShwGRkndnSaJ4Gnc2HONg9m"  # fill in your Cohere API key here
co = cohere.ClientV2(API_KEY)

shipment_tool_schemas = [
    {
        "type": "function",
        "function": {
            "name": "generate_shipment_filters",
            "description": "Use this tool to select appropriate filters for shipment lines from a list of predefined options based on user input, returning a dictionary of the selected filters.",
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
            "name": "apply_shipment_filters",
            "description": "Use this tool to apply the selected filters to retrieve the shipment lines, returning a dictionary of the filtered shipment lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "array",
                        "description": "list of filters to apply on shipment lines.",
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
def generate_shipment_filters(user_query: str) -> dict:
    """Use this tool to select appropriate filters for shipment lines from a list of predefined options based on user input, returning a dictionary of the selected filters."""

    preamble = """
    You are a Shipment assistant. Your task is to determine the appropriate filters for shipment lines based on the user's input. 
    """
    message = """
    Given the filter schema and the user's query, determine the appropriate filter(s). 

    ### Instructions
    - You are restricted to use only the provided filters. Do not create new filters. 
    - If you don't find any filters in the user query, generate an empty JSON array.
    - The response should be a JSON array of objects, where each object contains the filter name and its corresponding value. 
    - If you don't find any mentioned filters in the user query, generate an empty JSON array.

    ##Context : Filters Schema for Shipment Lines
    - {"name": "Order", "description": "Filter shipment lines by the order number", "examples": ["404087", "404088", "404089"]},
    - {"name": "Item", "description": "Filter shipment lines by the Item", "examples": ["IS_MART001", "AIS_MART002"]},
    - {"name": "ShipToCustomer", "description": "Filter shipment lines  by Customer", "examples": ["PACE Enterprises", "Laxmi Textiles"]}
    - {"name": "Supplier", "description": "Filter shipment lines  by Supplier", "examples": ["HP Enterprises"]}
   
    ### Validation: Don't include filter attributes with None or unknown values. Exclude them from the response.

    ###Follow the Examples for generating the response.

    Example 1:
    - User Input: "Find the shipment lines for the sales order 2008."
    - Output: [{"name": "Order", "value": "2008"}]

    Example 2:
    - User Input: "Show shipment lines containing product IS_MART001 and sales order 2008."
    - Output: [{"name": "Item", "value": "IS_MART001"},{"name": "Order", "value": "2008"}]

    Example 3:
    - User Input: "Find the shipment lines for customer PACE Enterprises and sales order 130."
    - Output: [{"name": "ShipToCustomer", "value": "PACE Enterprises"},{"name": "Order", "value": "2008"}]

 Example 4:
    - User Input: "Find the shipment lines by Supplier HP Enterprises."
    - Output: [{"name": "Supplier", "value": "HP Enterprises"}]
    
    
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
    response = co.chat(
        model="command-r-plus",
        messages=messages,
        max_tokens=4000,
        temperature=0
    )

    filters = json.loads(response.message.content[0].text)
    filters = [filter for filter in filters if ('value' in filter)]
    filters = [filter for filter in filters if not (
            filter['value'] == None or filter['value'] == "null" or filter['value'] == "?" or filter['value'] ==
            filter['name'])]
    return json.dumps(filters)


def apply_shipment_filters(filters: dict) -> dict:
    """Use this tool to apply the selected filters to retrieve the shipment lines, returning a dictionary of the filtered shipment lines."""

    # Convert the filter list to the REST `q` parameter format
    query_parts = [f"{f['name']}='{f['value']}'" for f in filters]
    q_parameter = " and ".join(query_parts)
    fields = "ShipmentLine,OrderType,Order,ShipToCustomer,Item,ItemDescription,FOBCode,FreightTermsCode,Supplier,RequestedDate,ScheduledShipDate,DeliveredQuantity,PickedQuantity,PendingQuantity,CreationDate"
    limit = 10
    print(q_parameter)
    auth = HTTPBasicAuth('ashish.k.das@oracle.com', 'Oracle@123')
    headers = {"REST-Framework-Version": "2"}
    url = f"https://ehso-dev2.fa.us2.oraclecloud.com/fscmRestApi/resources/11.13.18.05/shipmentLines?q={q_parameter}&fields={fields}&limit={limit}&onlyData=true"
    print(url)
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code >= 200 and response.status_code < 300:
        items = response.json()['items']
        return json.dumps(items)
    else:
        return f"Failed to call events API with status code {response.status_code}"


shipment_tools_map = {
    "generate_shipment_filters": generate_shipment_filters,
    "apply_shipment_filters": apply_shipment_filters
}

shipment_agent = Agent(
    name="Shipment Agent",
    model="command-r-plus-08-2024",
    instructions="""
    You are a shipment agent designed to generate the analytics data by utilizing a set of specialized tools. Your primary goal is to execute the tools in order to generate the analytics data.

    You are equipped with necessary tools to response to user query.
    - 1. Call generate_shipment_filters tool to generate the appropriate filters for shipment lines from a list of predefined options based on the user's input
    - 2. Call apply_shipment_filters to apply the generated filters on shipment lines and retrieve the filtered shipment lines.
    Make sure you call tools  in order to generate the final data, don't generate your own responses.

    """,
    tool_schemas=shipment_tool_schemas,
    tools_map=shipment_tools_map
)