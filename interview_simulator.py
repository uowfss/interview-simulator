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
    
    def start_interview(self):
        job_description = self.job_desc_text.get("1.0", tk.END).strip()
        if not job_description:
            messagebox.showerror("Error", "Please enter a job description")
            return

        def generate_and_start():
            try:
                self.root.after(0, lambda: self.root.config(cursor="watch"))

                # Generate initial greeting
                greeting = self.generate_greeting(job_description)
                api_key = keyring.get_password(
                    SERVICE_NAME,
                    APIS[self.api_var.get()]["username"]
                )

                # Create interview window with just greeting and job description
                self.root.after(0, lambda: InterviewWindow(
                    self, 
                    greeting,
                    job_description,
                    self.api_var.get(), 
                    api_key
                ))
            
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))

        threading.Thread(target=generate_and_start, daemon=True).start()
            
        def generate_next_question(self, conversation_history, job_description):
            try:
                selected_api = self.api_var.get()
                prompt = f"""Generate one follow-up interview question based on:
                - This job description: {job_description}
                - The conversation so far: {conversation_history}
                Return ONLY the question text without any formatting."""

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
                    response = requests.post(APIS["OpenAI"]["chat_url"], headers=headers, json=data)
                    if response.status_code == 200:
                        return response.json()["choices"][0]["message"]["content"].strip()
            
                elif selected_api == "Google":
                    genai.configure(api_key=self.api_key_entry.get())
                    model = genai.GenerativeModel(APIS["Google"]["model_name"])
                    response = model.generate_content(prompt)
                    return response.text.strip() if response.text else ""
            
                return "Could you elaborate on that?"
        
            except Exception as e:
                return "Let's move to the next question."

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
