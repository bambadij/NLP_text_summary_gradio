import gradio as gr
from transformers import pipeline
import pytesseract
from PIL import Image, UnidentifiedImageError
import re
import os
import logging

# Configurer les répertoires de cache
os.environ['TRANSFORMERS_CACHE'] = '/app/.cache'
os.environ['HF_HOME'] = '/app/.cache'

# Configurer les logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialiser les pipelines
summarize = pipeline('summarization', model="facebook/bart-large-cnn")
pipe = pipeline("summarization", model="plguillou/t5-base-fr-sum-cnndm")
classify_zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Fonction de résumé de texte avec classification
def summarize_text(text):
    if text.strip() == "":
        return "Veuillez entrer un texte", {}
    
    preprocessing_text = re.sub(r'\s+', ' ', text).strip()
    summary = pipe(preprocessing_text, do_sample=False,min_length=50, max_length=512)
    summary_text = summary[0].get('summary_text')
    
    logger.info(f"[INFO] Input data: {preprocessing_text}")
    logger.info(f"[INFO] Summary: {summary_text}")
    
    result = classify_zero_shot(
        summary_text,
        candidate_labels=["En Cours", "Non traiter", "Terminer"],
        hypothesis_template="Cet Résumé est sur {}."
    )
    
    scores = {label: float(score)  for label, score in zip(result['labels'], result['scores'])}
    
    return summary_text, scores

# Fonction de chargement d'image
def image_load(image):
    try:
        if image is None:
            return "Aucune image fournie", {}
        
        raw_text = pytesseract.image_to_string(image, lang='fra')
        preprocessing = re.sub(r'\s+', ' ', raw_text).strip()
        text_summary = pipe(preprocessing, do_sample=False,min_length=50, max_length=512)
        summary_text_from_image = text_summary[0].get('summary_text')
        result = classify_zero_shot(
        summary_text_from_image,
        candidate_labels=["En Cours", "Non traiter", "Terminer"],
        hypothesis_template="Cet Résumé est sur {}."
        )
        scores = {label: float(score)  for label, score in zip(result['labels'], result['scores'])}
        logger.info(f"[INFO] Input data: {preprocessing}")
        logger.info(f"[INFO] Summary: {result}")
        return summary_text_from_image,scores
    except UnidentifiedImageError:
        return "Impossible de charger l'image", {}
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return str(e), {}

# Fonction de gestion des entrées
def handle_input(text_input, image_input, mode):
    if mode == "Texte":
        return summarize_text(text_input)
    elif mode == "Image":
        return image_load(image_input)
    else:
        return "Sélectionnez une option valide", {}

# Interface Gradio
with gr.Blocks() as iface:
    gr.Markdown("## Sélectionnez une option")
    
    with gr.Row():
        with gr.Column():
            mode = gr.Dropdown(choices=["Texte", "Image"], label="Resumé Texte ou Image",info="Selectionner une options")
            text_input = gr.Textbox(lines=4,label="Entrée de texte")
            image_input = gr.Image(label="Téléverser une image", type="pil")
            submit_btn = gr.Button("Soumettre")
        
        with gr.Column():
            output_summary = gr.Textbox(label="Résumé")
            output_classification = gr.Label(label="Classification")

    def update_inputs(mode_select):
        if mode_select == "Texte":
            return gr.update(visible=True), gr.update(visible=False)
        elif mode_select == "Image":
            return gr.update(visible=False), gr.update(visible=True)
    logger.info(f"[INFO] input mode: {update_inputs}")
    mode.change(fn=update_inputs, inputs=mode, outputs=[text_input, image_input])
    submit_btn.click(fn=handle_input, inputs=[text_input, image_input, mode], outputs=[output_summary, output_classification])

if __name__ == "__main__":
    iface.launch()
