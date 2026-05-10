import os
from dotenv import load_dotenv
from openai import OpenAI
from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit, 
    QDoubleSpinBox,
    QSpinBox,
    QLabel
)

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Brak klucza OPENAI_API_KEY w pliku .env")

client = OpenAI(api_key=api_key)


def on_button_click():
    user_prompt = question.text().strip()
    temperature = temperature_input.value()
    top_p = top_p_input.value()

    if not user_prompt:
        answer.setPlainText("Wpisz najpierw pytanie.")
        return

    button.setEnabled(False)
    button.setText("Czekam na odpowiedź...")
    answer.setPlainText("Wysyłam zapytanie do OpenAI...")

    try:
        response = client.responses.create(
            model="gpt-4o",
            input=user_prompt,
            temperature=temperature,
            top_p=top_p
        )

        answer.setPlainText(response.output_text)

    except Exception as e:
        answer.setPlainText(f"Wystąpił błąd:\n\n{e}")

    finally:
        button.setEnabled(True)
        button.setText("Get Response")


app = QApplication([])

window = QWidget()
window.setWindowTitle("OpenAI API Test")
window.resize(600, 400)
layout = QVBoxLayout()
question = QLineEdit()
question.setPlaceholderText("Wpisz pytanie...")
button = QPushButton("Get Response")
answer = QTextEdit()
answer.setReadOnly(True)
temperature_input = QDoubleSpinBox()
temperature_input.setRange(0, 2)
temperature_input.setSingleStep(0.1)
temperature_input.setValue(0.7)
top_p_input = QDoubleSpinBox()
top_p_input.setRange(0, 1)
top_p_input.setSingleStep(0.1)
top_p_input.setValue(1.0)

button.clicked.connect(on_button_click)
question.returnPressed.connect(on_button_click)


layout.addWidget(question)
layout.addWidget(QLabel("Temperature:"))
layout.addWidget(temperature_input)
layout.addWidget(QLabel("Top Propobability (top_p):"))
layout.addWidget(top_p_input)
layout.addWidget(button)
layout.addWidget(answer)
window.setLayout(layout)
window.show()
app.exec()