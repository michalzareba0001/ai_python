import requests
from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QDoubleSpinBox,
    QLabel,
    QRadioButton
)


OLLAMA_URL = "http://localhost:11434/api/chat"

conversation_history = []
MAX_TURNS = 20

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "Jesteś pomocnym asystentem, który odpowiada na pytania użytkownika. "
        "Odpowiadaj w języku polskim. "
        "Styl wypowiedzi nieformalny"
    )
}

SYSTEM_MESSAGE_HALINA = {
    "role": "system",
    "content": (
        "Wcielasz się w postać z Gry RPG. "
        "Nazywasz się Halina. Jesteś prostą wieśniaczką z małej wioski daleko za górami. Szukasz swojej siostry, która zaginęła podczas burzy. Jesteś odważna i zdeterminowana, ale nie masz dużej wiedzy o świecie poza swoją wioską. Odpowiadaj na pytania użytkownika zgodnie z charakterem Haliny. "
        "Masz zadanie dla gracza - znajdź moją siostrę, która zaginęła podczas burzy. Za wykonanie zadania zaproponuj nagrodę 50 złotych monet. Gracz może się targować o nagrodę - nie możesz zaoferować więcej niż 100 złotych monet. "
        "Posiadasz pewne cenne dla użytkownika informacje, ale nie zdradzaj ich od razu. Istotne informacje: 1) Wiesz że daleko stąd za górami żyje smok. 2) Wiesz że w pobliskim lesie mieszka stara wiedźma, która zna wiele tajemnic. 3) Wiesz że w jaskini niedaleko wioski ukryty jest skarb, ale jest strzeżony przez potwora. 4) Wiesz że twoja siostra była ostatnio widziana w karczmie na skraju lasu. "
        "Odpowiadaj w języku polskim. "
        "Styl wypowiedzi nieformalny, prosty, z nutą humoru."
    )
}

SYSTEM_MESSAGE_JANUSZ = {
    "role": "system",
    "content": (
        "Wcielasz się w postać z Gry RPG. "
        "Nazywasz się Janusz. Jesteś doświadczonym wojownikiem, który podróżuje po świecie w poszukiwaniu przygód. Jesteś odważny, ale czasami zbyt pewny siebie. Odpowiadaj na pytania użytkownika zgodnie z charakterem Janusza. Szukasz zleceń jako wojownik, ale jesteś też otwarty na inne możliwości. Posiadasz wiedzę o różnych potworach i miejscach w świecie gry, ale nie zdradzaj jej od razu. "
        "Posiadasz pewne cenne dla użytkownika informacje, ale nie zdradzaj ich od razu. Istotne informacje: 1) Wiesz że daleko stąd za górami żyje smok. 2) Wiesz że w pobliskim lesie mieszka stara wiedźma, która zna wiele tajemnic. 3) Wiesz kto posiada magiczny miecz, który może pokonać smoka. 4) Wiesz że w jaskini niedaleko wioski ukryty jest skarb, ale jest strzeżony przez potwora."
        "Odpowiadaj w języku polskim. "
        "Styl wypowiedzi nieformalny, pewny siebie doświadczony"
    )
}


SYSTEM_MESSAGE_ZDZISLAW = {
    "role": "system",
    "content": (
        "Wcielasz się w postać z Gry RPG. "
        "Nazywasz się Zdzisław. Jesteś tajemniczym czarodziejem, który mieszka w odległej wieży. Jesteś mądry i posiadasz dużą wiedzę o magii, ale jesteś też nieco ekscentryczny. Odpowiadaj na pytania użytkownika zgodnie z charakterem Zdzisława. Posiadasz wiedzę o różnych zaklęciach i magicznych artefaktach, ale nie zdradzaj jej od razu. "
        "Posiadasz pewne cenne dla użytkownika informacje, ale nie zdradzaj ich od razu. Istotne informacje: 1) Wiesz że daleko stąd za górami żyje smok. 2) Wiesz że w pobliskim lesie mieszka stara wiedźma, która zna wiele tajemnic. 3) Wiesz że w jaskini niedaleko wioski ukryty jest skarb, ale jest strzeżony przez potwora. 4) Wiesz gdzie można znaleźć rzadkie zioła potrzebne do stworzenia eliksiru ochrony przed ogniem. "
        "Odpowiadaj w języku polskim. "
        "Styl wypowiedzi nieformalny, pewny siebie doświadczony"
    )
}

def get_selected_system_message():
    if radio_1.isChecked():
        aiName = "Halina"
        return aiName, SYSTEM_MESSAGE_HALINA

    if radio_2.isChecked():
        aiName = "Janusz"
        return aiName, SYSTEM_MESSAGE_JANUSZ

    if radio_3.isChecked():
        aiName = "Zdzisław"
        return aiName, SYSTEM_MESSAGE_ZDZISLAW
        

    return "AI", SYSTEM_MESSAGE


def add_message_to_chat(role, content):
    if role == "user":
        chat_window.append(f"<b>Ty:</b> {content}")
    elif role == "assistant":
        aiName, _ = get_selected_system_message()
        chat_window.append(f"<b>{aiName}:</b> {content.replace('<s>', '').replace('</s>', '')}")
    else:
        chat_window.append(content)

    chat_window.append("")


def on_button_click():
    global conversation_history

    user_prompt = question.text().strip()

    if not user_prompt:
        chat_window.append("<b>System:</b> Wpisz najpierw pytanie.")
        chat_window.append("")
        return

    question.clear()

    button.setEnabled(False)
    button.setText("Czekam na odpowiedź...")

    add_message_to_chat("user", user_prompt)

    try:
        aiName, selected_system_message = get_selected_system_message()
        messages_to_send = (
            [selected_system_message]
            + conversation_history[-MAX_TURNS * 2:]
            + [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "mwiewior/bielik:latest",
                "messages": messages_to_send,
                "stream": False,
                "options": {
                    "temperature": 1.0,
                    "top_p": 1.0,
                    "top_k": 50
                }
            },
            timeout=(5, 180)
        )

        response.raise_for_status()

        data = response.json()
        assistant_message = data["message"]["content"]

        conversation_history.append({
            "role": "user",
            "content": user_prompt
        })

        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        conversation_history = conversation_history[-MAX_TURNS * 2:]

        add_message_to_chat("assistant", assistant_message)

    except Exception as e:
        chat_window.append(f"<b>Błąd:</b><br>{e}")
        chat_window.append("")

    finally:
        button.setEnabled(True)
        button.setText("Wyślij")


def clear_history():
    conversation_history.clear()
    chat_window.clear()
    chat_window.append("<b>System:</b> Historia rozmowy została wyczyszczona.")
    chat_window.append("")


app = QApplication([])

window = QWidget()
window.setWindowTitle("gaming AI - Eksperymentalna wersja 1.0")
window.resize(700, 500)

layout = QVBoxLayout()

chat_window = QTextEdit()
chat_window.setReadOnly(True)

question = QLineEdit()
radio_1 = QRadioButton("Halina")
radio_2 = QRadioButton("Janusz")
radio_3 = QRadioButton("Zdzisław")
radio_1.setChecked(True)
question.setPlaceholderText("Napisz wiadomość...")
question.setFixedHeight(50)
button = QPushButton("Wyślij")
clear_button = QPushButton("Wyczyść historię")

button.clicked.connect(on_button_click)
question.returnPressed.connect(on_button_click)
clear_button.clicked.connect(clear_history)

layout.addWidget(QLabel("Eksperymentalna wersja gamingowego AI. ver.1.0"))
layout.addWidget(QLabel("Wybierz swojego bohatera:"))
layout.addWidget(radio_1)
layout.addWidget(radio_2)
layout.addWidget(radio_3)

layout.addWidget(question)

layout.addWidget(button)
layout.addWidget(clear_button)
layout.addWidget(chat_window)

window.setLayout(layout)
window.show()

app.exec()