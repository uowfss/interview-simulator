import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import google.generativeai as genai
import keyring
import threading
import requests
import json
import re
from config import APIS, SERVICE_NAME
from interview_window import InterviewWindow

class SpeechApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Interview Preparation Assistant")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.root.mainloop()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # API Selection
        ttk.Label(main_frame, text="Select API:").pack(pady=5)
        self.api_var = tk.StringVar()
        self.api_dropdown = ttk.Combobox(main_frame, textvariable=self.api_var, 
                                       values=list(APIS.keys()), state="readonly")
        self.api_dropdown.pack(pady=5)
        
        # API Key Entry
        ttk.Label(main_frame, text="API Key:").pack(pady=5)
        self.api_key_entry = ttk.Entry(main_frame, width=40, show="*")
        self.api_key_entry.pack(pady=5)
        
        # Key Management Buttons
        key_btn_frame = ttk.Frame(main_frame)
        key_btn_frame.pack(pady=10)
        ttk.Button(key_btn_frame, text="Update Key", command=self.update_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(key_btn_frame, text="Verify Key", command=self.verify_key).pack(side=tk.LEFT, padx=5)
        
        # Job Description Input
        ttk.Label(main_frame, text="Job Description:").pack(pady=5)
        self.job_desc_text = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD, 
            width=70, 
            height=10
        )
        self.job_desc_text.pack(pady=5)
        
        # Start Interview Button
        ttk.Button(
            main_frame, 
            text="Generate Questions & Start Interview", 
            command=self.start_interview
        ).pack(pady=20)
    
    def generate_questions(self, job_description):
        try:
            selected_api = self.api_var.get()
            prompt = f"""Generate two things based on this job description: 
            1. A friendly greeting mentioning the job role 
            2. 8 technical interview questions
            Return a JSON object with two keys: "greeting" (string) and "questions" (array).
            Job description: {job_description}"""

            if selected_api == "OpenAI":
                headers = {
                    "Authorization": f"Bearer {self.api_key_entry.get()}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                response = requests.post(
                    APIS["OpenAI"]["chat_url"],
                    headers=headers,
                    json=data
                )
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    print("OpenAI Raw Response:", content)
                    try:
                        data = json.loads(content)
                        greeting = data.get("greeting", "Welcome! Let's begin the interview.")
                        questions = data.get("questions", [])
                    except json.JSONDecodeError:
                        # Fallback to old format
                        greeting = "Welcome! Let's begin the interview."
                        questions = self.parse_questions(content)
                    return (greeting, questions[:8])

            elif selected_api == "Google":
                genai.configure(api_key=self.api_key_entry.get())
                model = genai.GenerativeModel(APIS["Google"]["model_name"])
            
                greeting_prompt = f"{APIS['Google']['greeting_prompt']} {job_description}"
                greeting_response = model.generate_content(greeting_prompt)
                greeting = greeting_response.text.strip() if greeting_response.text else "Welcome! Let's begin the interview."
            
                # Generate questions with explicit format request
                question_prompt = f"""Generate 8 technical interview questions based on this job description.
                Return ONLY a JSON array of question strings using format: ["question1?", "question2?", ...]
                Job description: {job_description}"""
            
                question_response = model.generate_content(question_prompt)
                raw_questions = question_response.text if question_response.text else ""
            
                # Parse using both JSON and regex methods
                try:
                    questions = json.loads(raw_questions)
                except json.JSONDecodeError:
                    questions = self.parse_questions(raw_questions)
            
                return (greeting, questions[:8])

        except genai.GenerativeServiceError as e:
            messagebox.showerror("Error", f"Google API Error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {str(e)}")
            return None

    def parse_questions(self, content):
        try:
            # First try direct JSON parsing
            questions = json.loads(content)
            if isinstance(questions, list):
                return questions[:8]
        except json.JSONDecodeError:
            pass
    
        try:
            # Enhanced pattern matching
            questions = re.findall(
                r'(?:\d+[\.\)]?|[-*])\s*"?(.+?)(?="?\s*(?:\n\s*\d+[\.\)]|$))', 
                content, 
                flags=re.DOTALL
            )
            # Clean up questions
            clean_questions = [q.strip().replace('"', '') for q in questions]
            return clean_questions[:8]
        except Exception as e:
            messagebox.showerror("Error", 
                f"Could not parse questions from:\n\n{content[:200]}...")
            return None
    
    def start_interview(self):
        job_description = self.job_desc_text.get("1.0", tk.END).strip()
        if not job_description:
            messagebox.showerror("Error", "Please enter a job description")
            return

        def generate_and_start():
            try:
                self.root.after(0, lambda: self.root.config(cursor="watch"))
            
                # Generate questions
                greeting, questions = self.generate_questions(job_description)
                if not questions or not greeting:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to generate content"))
                    return
                
                # Add self-introduction as first question
                self_intro = "Please introduce yourself, focusing on experience relevant to this role."
                all_questions = [self_intro] + questions
            
                # Get API key from keyring
                api_key = keyring.get_password(
                    SERVICE_NAME,
                    APIS[self.api_var.get()]["username"]
                )
                if not api_key:
                    self.root.after(0, lambda: messagebox.showerror("Error", "API key not found in system keyring"))
                    return
            
                # Create interview window
                self.root.after(0, lambda: InterviewWindow(
                    self.root, 
                    greeting,
                    questions, 
                    self.api_var.get(), 
                    api_key
                ))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Unexpected error: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))

        # Start the background thread
        threading.Thread(target=generate_and_start, daemon=True).start()

    def update_key(self):
        selected_api = self.api_var.get()
        if not selected_api:
            messagebox.showerror("Error", "Please select an API first")
            return
        
        new_key = self.api_key_entry.get()
        if not new_key:
            messagebox.showerror("Error", "API key cannot be empty")
            return
        
        # Store key in keyring
        keyring.set_password(
            service_name=SERVICE_NAME,
            username=APIS[selected_api]["username"],
            password=new_key
        )
        
        # For Google, also configure the API key
        if selected_api == "Google":
            genai.configure(api_key=new_key)
        
        messagebox.showinfo("Success", "API key updated successfully")

    def verify_key(self):
        selected_api = self.api_var.get()
        key = self.api_key_entry.get().strip()
        
        if not selected_api or not key:
            messagebox.showerror("Error", "Select API and enter key first")
            return
        
        try:
            if selected_api == "OpenAI":
                headers = {"Authorization": f"Bearer {key}"}
                response = requests.get(
                    APIS["OpenAI"]["test_url"], 
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200:
                    messagebox.showinfo("Success", "OpenAI API key is valid")
                else:
                    messagebox.showerror("Error", f"OpenAI verification failed: {response.status_code}")
            
            elif selected_api == "Google":
                genai.configure(api_key=key)
                model = genai.GenerativeModel(APIS["Google"]["model_name"])
                response = model.generate_content(APIS["Google"]["test_prompt"])
                if response.text:
                    messagebox.showinfo("Success", "Google API key is valid")
                else:
                    messagebox.showerror("Error", "Google API verification failed")
        
        except genai.GenerativeServiceError as e:
            messagebox.showerror("Error", f"Google API Error: {e}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {str(e)}")

if __name__ == "__main__":
    SpeechApp()
