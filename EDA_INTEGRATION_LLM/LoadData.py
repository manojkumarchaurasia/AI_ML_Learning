import pandas as pd

# File path with raw string (r"" ensures no escape characters)
url = r"C:\Users\manchaur\Documents\MyProject\EDA_INTEGRATION_LLM\titanic_ dataset_final.csv" 

# Reading the CSV file into a DataFrame
df = pd.read_csv(url) 

# Display the DataFrame
print(df)