from flask import Flask, request, render_template, send_file
import os
import PyPDF2
import pyttsx3
from gtts import gTTS

def extract_text_from_pdf(pdf_path):
    """Extract text from the provided PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        return f"Error: Failed to extract text from PDF. {e}"

def text_to_audio_pyttsx3(text, output_path):
    """Convert text to speech using pyttsx3 and save as an audio file."""
    try:
        engine = pyttsx3.init()
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return True, output_path
    except Exception as e:
        return False, f"Error: Failed to convert text to audio with pyttsx3. {e}"

def text_to_audio_gtts(text, output_path):
    """Convert text to speech using gTTS and save as an audio file."""
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
        return True, output_path
    except Exception as e:
        return False, f"Error: Failed to convert text to audio with gTTS. {e}"

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'pdf_file' not in request.files:
        return "Error: No PDF file uploaded.", 400

    pdf_file = request.files['pdf_file']
    if pdf_file.filename == '':
        return "Error: No selected file.", 400

    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    pdf_file.save(pdf_path)

    text = extract_text_from_pdf(pdf_path)
    if text.startswith("Error"):
        return text, 500

    output_filename = os.path.splitext(pdf_file.filename)[0] + ".mp3"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    use_gtts = request.form.get('use_gtts') == 'true'
    if use_gtts:
        success, result = text_to_audio_gtts(text, output_path)
    else:
        success, result = text_to_audio_pyttsx3(text, output_path)

    if success:
        return send_file(result, as_attachment=True)
    else:
        return result, 500

if __name__ == "__main__":
    app.run(debug=True)
