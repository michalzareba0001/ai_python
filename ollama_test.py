import requests
import os
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





gmail_api_key = os.getenv("GMAIL_API_KEY")

conversation_history = []
MAX_TURNS = 20
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "Nazywasz się Janusz. Jesteś pomocnym asystentem, który odpowiada na pytania użytkownika. Odpowiadaj zwięźle i na temat. Odpowiadaj w języku polskim. Styl wypowiedzi nieformalny, koleżeński z nutą humoru."
}



def on_button_click():
    user_prompt = question.text().strip()
    temperature = temperature_input.value()
    top_p = top_p_input.value()

    if not user_prompt:
        answer.setPlainText("Wpisz najpierw pytanie.")
        return

    button.setEnabled(False)
    button.setText("Czekam na odpowiedź...")
    answer.setPlainText("Wysyłam zapytanie...")

    try:
        
        conversation_history.append({
                "role": "user", 
                "content": user_prompt
            })
        
        message_to_send = [SYSTEM_MESSAGE] + conversation_history[-MAX_TURNS * 2:]
        
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mwiewior/bielik:latest",
                "messages": message_to_send,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": 50,
                "stream": False
            }
        )
        data=response.json()
        assistant_message = data["message"]["content"]
        
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Czyścimy historię, żeby nie rosła bez końca
        conversation_history[:] = conversation_history[-MAX_TURNS * 2:]

        answer.setPlainText(assistant_message)
    except Exception as e:
        answer.setPlainText(f"Wystąpił błąd:\n\n{e}")

    finally:
        button.setEnabled(True)
        button.setText("Get Response")
        print(conversation_history)


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