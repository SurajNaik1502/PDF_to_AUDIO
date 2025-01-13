from flask import Flask, request, render_template, send_file
import os
import PyPDF2
from gtts import gTTS
import pyttsx3
import tempfile

# Initialize Flask app
app = Flask(__name__)

# Directories for uploaded files and outputs
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Utility to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        return f"Error: Failed to extract text from PDF. {e}"

# Utility to split text into manageable chunks
def split_text_into_chunks(text, max_length=5000):
    """Split text into smaller chunks to handle gTTS limits."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# Convert text to audio using pyttsx3
def text_to_audio_pyttsx3(text, output_path):
    try:
        engine = pyttsx3.init()
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return True, output_path
    except Exception as e:
        return False, f"Error: Failed to convert text to audio with pyttsx3. {e}"

# Convert text to audio using gTTS
def text_to_audio_gtts(text, output_path):
    try:
        chunks = split_text_into_chunks(text)
        with tempfile.TemporaryDirectory() as tempdir:
            chunk_files = []
            for i, chunk in enumerate(chunks):
                chunk_path = os.path.join(tempdir, f"chunk_{i}.mp3")
                tts = gTTS(text=chunk, lang='en')
                tts.save(chunk_path)
                chunk_files.append(chunk_path)

            # Combine chunks into a single audio file
            with open(output_path, 'wb') as output_file:
                for chunk_path in chunk_files:
                    with open(chunk_path, 'rb') as chunk_file:
                        output_file.write(chunk_file.read())
        return True, output_path
    except Exception as e:
        return False, f"Error: Failed to convert text to audio with gTTS. {e}"

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
