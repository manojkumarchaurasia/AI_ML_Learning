import gradio as gr
import pandas as pd

# Assuming generate_insights is already defined
def generate_insights(df_summary):
    prompt = f"Analyze the dataset summary and provide insights:\n\n{df_summary}"
    # You should replace this with your actual ollama logic or any AI model you are using
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    return response.get('message', {}).get('content', 'No insights available')

def eda_analysis(file):
    # Read the CSV file
    df = pd.read_csv(file)
    
    # Generate summary
    summary = df.describe().to_string()
    
    # Generate insights based on summary
    insights = generate_insights(summary)
    
    return insights

# Create Gradio interface
demo = gr.Interface(fn=eda_analysis, inputs="file", outputs="text")

# Launch the interface
demo.launch(share=True)
