import gradio as gr

def echo_text(text):
    return text

iface = gr.Interface(fn=echo_text, inputs="text", outputs="text")
iface.launch()
