import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext
import threading
import speech_recognition as sr
import requests
from config import APIS, SERVICE_NAME

class InterviewWindow(tk.Toplevel):
    def __init__(self, parent, questions, api_name, api_key):
        super().__init__(parent)
        self.title = "Interview Window"
        self.geometry("800x600")
        self.parent = parent
        self.api_name = api_name
        self.api_key = api_key
        self.questions = questions
        self.current_question = -1

        self.setup_ui()
        self.show_greeting()

    def setup_ui(self):
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=90, height=25)
        self.text_area.pack(pady=10, padx=10)
        
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=10)
        
        self.listen_btn = ttk.Button(
            self.button_frame, 
            text="Start Listening", 
            command=self.start_listening_thread
        )
        self.listen_btn.pack(side=tk.LEFT, padx=5)
        
        self.close_btn = ttk.Button(
            self.button_frame, 
            text="Close", 
            command=self.destroy
        )
        self.close_btn.pack(side=tk.LEFT, padx=5)
        
        self.r = sr.Recognizer()
    
    def show_greeting(self):
        self.text_area.insert(tk.END, f"\nInterviewer: {self.greeting}\n")
        self.text_area.insert(tk.END, "\nInterviewer: We'll start with your introduction.\n")
        self.text_area.see(tk.END)
        self.current_question = 0  # Points to self-intro question
        self.listen_btn.config(state=tk.NORMAL)

    def show_question(self):
        if 0 <= self.current_question < len(self.questions):
            q = self.questions[self.current_question]
            self.text_area.insert(tk.END, f"\nInterviewer: {q}\n")
            self.text_area.see(tk.END)
        elif self.current_question >= len(self.questions):
            self.text_area.insert(tk.END, "\n\nInterview completed! Thank you!\n")
            self.listen_btn.config(state=tk.DISABLED)

    def start_listening_thread(self):
        if self.current_question == -1:
            self.show_greeting()
        else:
            thread = threading.Thread(target=self.listen_and_convert)
            thread.start()

    def listen_and_convert(self):
        self.listen_btn.config(state=tk.DISABLED)
        try:
            with sr.Microphone() as source:
                self.update_display("\nCandidate: Listening... (speak now)")
                audio = self.r.listen(source, timeout=5)
                
                if self.api_name == "Google":
                    text = self.r.recognize_google(audio, key=self.api_key)
                elif self.api_name == "OpenAI":
                    wav_data = audio.get_wav_data()
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    response = requests.post(
                        APIS["OpenAI"]["audio_url"],
                        headers=headers,
                        files={"file": ("audio.wav", wav_data, "audio/wav")},
                        data={"model": "whisper-1"}
                    )
                    text = response.json().get("text", "") if response.status_code == 200 else ""
                
                self.update_display(f"Candidate: {text}")
                self.current_question += 1
                self.show_question()
                
        except Exception as e:
            self.update_display(f"\nSystem Error: {str(e)}")
        finally:
            self.listen_btn.config(state=tk.NORMAL)

    def update_display(self, message):
        self.text_area.insert(tk.END, f"\n{message}")
        self.text_area.see(tk.END)