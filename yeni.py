from flask import Flask, request, render_template_string, send_from_directory
import os
import fitz  
import zipfile
import tempfile
from google import generativeai as genai

app = Flask(__name__, static_url_path='/static')

API_KEY = "api_key"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

ZIP_PATH = "C:/Masaüstü/tumDatalar.zip"

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def extract_text_from_zip(zip_file_path):
    all_text = ""
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        for file_name in os.listdir(temp_dir):
            if file_name.endswith('.pdf'):
                file_path = os.path.join(temp_dir, file_name)
                text = extract_text_from_pdf(file_path)
                all_text += f"\n\n--- {file_name} ---\n\n{text}"
    return all_text

def ask_question_about_pdf(pdf_text, question):
    prompt = f"""
Sen PDF okuyabilen bir asistansın. Aşağıdaki içerikten faydalanarak soruyu yanıtla:

PDF İçeriği:
\"\"\"{pdf_text}\"\"\"

Soru:
{question}

Cevap:
"""
    response = model.generate_content(prompt)
    return response.text.strip()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>BilChat</title>
    <style>
        body {
            margin: 0;
            padding: 0;
        }
        .chatbot-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            background: #f9f9f9;
            border: 2px solid #ccc;
            border-radius: 20px;
            box-shadow: 0px 0px 15px rgba(0,0,0,0.2);
            padding: 15px;
            font-family: Arial, sans-serif;
        }
        .chatbot-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .chatbot-header img {
            width: 40px;
            height: 40px;
            margin-right: 10px;
        }
        .chatbot-header h3 {
            margin: 0;
            font-size: 18px;
            color: #333;
        }
        .chatbot-body {
            max-height: 300px;
            overflow-y: auto;
            font-size: 14px;
            color: #333;
        }
        .chatbot-footer {
            margin-top: 10px;
        }
        textarea {
            width: 100%;
            resize: none;
            height: 60px;
            border-radius: 10px;
            border: 1px solid #ccc;
            padding: 8px;
        }
        input[type="submit"] {
            margin-top: 8px;
            padding: 8px 15px;
            border: none;
            background-color: #ffb300;
            color: white;
            border-radius: 10px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #ffa000;
        }
    </style>
</head>
<body>

<div class="chatbot-container">
    <div class="chatbot-header">
        <img src="/static/ChatBootLogo.jpeg" alt="Logo">
        <h3>BilChat</h3>
    </div>

    <form method="post">
        <div class="chatbot-body">
            {% if answer %}
                <b> Cevap:</b>
                <p>{{ answer | safe }}</p>
            {% else %}
                <p> BilChat'e hoşgeldin bana bir şeyler sor...</p>
            {% endif %}
        </div>
        <div class="chatbot-footer">
            <textarea name="question" placeholder="Sorunuzu yazın..." required></textarea>
            <input type="submit" value="Gönder">
        </div>
    </form>
</div>

</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if question:
            pdf_text = extract_text_from_zip(ZIP_PATH)
            answer = ask_question_about_pdf(pdf_text, question)
    return render_template_string(HTML_TEMPLATE, answer=answer)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run(debug=True)
