import gradio as gr 

def square_number(x): 
    return x ** 2 

interface = gr.Interface(fn=square_number, inputs="number", outputs="number") 

interface.launch(share=True)
