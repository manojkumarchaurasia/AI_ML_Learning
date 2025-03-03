import pandas as pd
import ollama

# Assuming you have your dataframe 'df'

# File path with raw string (r"" ensures no escape characters)
url = r"C:\Users\manchaur\Documents\MyProject\EDA_INTEGRATION_LLM\titanic_ dataset_final.csv" 

# Reading the CSV file into a DataFrame
# df = pd.read_csv('path_to_your_file.csv') # Ensure you have your dataframe loaded
df = pd.read_csv(url) 

def generate_insights(df_summary):
    prompt = f"Analyze the dataset summary and provide insights:\n\n{df_summary}"
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    
    # Print the entire response to inspect the structure
    print(response)
    
    # Access the message content if the structure is as expected
    return response.get('message', {}).get('content', 'No insights available')

# Generate summary of dataset
summary = df.describe().to_string()

# Generate AI insights
insights = generate_insights(summary)

# Print AI-Generated Insights
print("\nAI-Generated Insights:\n", insights)