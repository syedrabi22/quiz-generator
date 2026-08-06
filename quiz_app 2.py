# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 21:17:38 2026

@author: pc
"""
import customtkinter as ctk
import google.generativeai as genai
import json
import threading
import re

# ---------------- CONFIG ----------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class QuizApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("AI Quiz Master")
        self.geometry("700x600")
        self.resizable(False, False)

        # ---------------- SETTINGS ----------------
        # PASTE YOUR API KEY HERE
        self.api_key = "AIzaSyBwPg92sxSNyArFzDFMLYV0Jp6iFBW1yCo" 
        # Use the latest model available in 2026
        self.model_name = "gemini-3-flash-preview" 

        # Quiz State
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.current_level = 1
        self.difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}

        # User Inputs
        self.field = ""
        self.subject = ""
        self.topic = ""

        self.create_widgets()
        self.show_setup_screen()

    # ---------------- UI SETUP ----------------
    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True)

        # ---------- SETUP SCREEN ----------
        self.setup_frame = ctk.CTkFrame(self.main_frame)

        ctk.CTkLabel(
            self.setup_frame,
            text="AI Quiz Generator",
            font=("Roboto", 28, "bold")
        ).pack(pady=(40, 20))

        # We removed the API Key entry box here

        self.entry_field = ctk.CTkEntry(
            self.setup_frame,
            placeholder_text="Field (e.g., Science)",
            width=350, height=40
        )
        self.entry_field.pack(pady=10)

        self.entry_subject = ctk.CTkEntry(
            self.setup_frame,
            placeholder_text="Subject (e.g., Physics)",
            width=350, height=40
        )
        self.entry_subject.pack(pady=10)

        self.entry_topic = ctk.CTkEntry(
            self.setup_frame,
            placeholder_text="Topic (e.g., Thermodynamics)",
            width=350, height=40
        )
        self.entry_topic.pack(pady=10)

        self.btn_start = ctk.CTkButton(
            self.setup_frame,
            text="Generate Quiz",
            command=self.start_generation_thread,
            width=200, height=45,
            font=("Roboto", 16, "bold")
        )
        self.btn_start.pack(pady=40)

        # ---------- QUIZ SCREEN ----------
        self.quiz_frame = ctk.CTkFrame(self.main_frame)

        self.top_bar = ctk.CTkFrame(self.quiz_frame, height=50)
        self.top_bar.pack(fill="x", padx=20, pady=10)
        self.top_bar.pack_propagate(False)

        self.lbl_level = ctk.CTkLabel(self.top_bar, text="Level: 1", font=("Roboto", 14, "bold"))
        self.lbl_level.pack(side="left", padx=10)

        self.lbl_score = ctk.CTkLabel(self.top_bar, text="Score: 0", font=("Roboto", 14))
        self.lbl_score.pack(side="right", padx=10)

        self.lbl_question = ctk.CTkLabel(
            self.quiz_frame,
            text="Question...",
            wraplength=600,
            font=("Roboto", 20)
        )
        self.lbl_question.pack(pady=40)

        self.option_buttons = []
        for i in range(4):
            btn = ctk.CTkButton(
                self.quiz_frame,
                text="",
                height=50,
                font=("Roboto", 14),
                command=lambda idx=i: self.check_answer(idx)
            )
            btn.pack(fill="x", padx=60, pady=8)
            self.option_buttons.append(btn)

        self.btn_next = ctk.CTkButton(
            self.quiz_frame,
            text="Next Question",
            state="disabled",
            command=self.next_question
        )
        self.btn_next.pack(pady=30)

        # ---------- LOADING SCREEN ----------
        self.loading_frame = ctk.CTkFrame(self.main_frame)
        ctk.CTkLabel(
            self.loading_frame,
            text="🤖 AI is crafting your quiz...\nPlease wait a few seconds",
            font=("Roboto", 22)
        ).pack(expand=True)

    # ---------------- LOGIC ----------------
    def show_setup_screen(self):
        self.quiz_frame.pack_forget()
        self.loading_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)
        self.btn_start.configure(state="normal")

    def show_loading_screen(self):
        self.setup_frame.pack_forget()
        self.loading_frame.pack(fill="both", expand=True)

    def show_quiz_screen(self):
        self.loading_frame.pack_forget()
        self.quiz_frame.pack(fill="both", expand=True)
        self.current_question_index = 0
        self.score = 0
        self.update_ui_stats()
        self.display_question()

    def start_generation_thread(self):
        self.field = self.entry_field.get().strip()
        self.subject = self.entry_subject.get().strip()
        self.topic = self.entry_topic.get().strip()

        if not self.topic:
            self.show_popup("Missing Info", "Please provide at least a Topic.")
            return

        self.btn_start.configure(state="disabled")
        self.show_loading_screen()
        threading.Thread(target=self.generate_questions, daemon=True).start()

    def generate_questions(self):
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            difficulty = self.difficulty_map[self.current_level]

            prompt = f"""
Generate 5 MCQs about "{self.topic}" in "{self.subject}" (Field: {self.field}).
Difficulty Level: {difficulty}

Return ONLY a valid JSON array:
[
  {{
    "question": "Question text here",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_answer": 0
  }}
]
Rules:
- 4 options per question.
- "correct_answer" must be the integer index (0, 1, 2, or 3).
- No markdown formatting outside the JSON code block.
"""
            response = model.generate_content(prompt)
            # Use regex to find the JSON block even if model adds conversational text
            match = re.search(r'\[.*\]', response.text, re.DOTALL)
            
            if match:
                self.questions = json.loads(match.group(0))
                self.after(0, self.show_quiz_screen)
            else:
                raise Exception("AI failed to produce a valid quiz format. Please try again.")

        except Exception as e:
            self.after(0, lambda: self.show_popup("Error", str(e)))
            self.after(0, self.show_setup_screen)

    def display_question(self):
        if self.current_question_index >= len(self.questions):
            self.finish_quiz()
            return

        q = self.questions[self.current_question_index]
        self.lbl_question.configure(text=q["question"])

        for i, option in enumerate(q["options"]):
            self.option_buttons[i].configure(
                text=option,
                state="normal",
                fg_color=("#3B8ED0", "#1f538d") # Default theme colors
            )
        self.btn_next.configure(state="disabled")

    def check_answer(self, selected_index):
        q = self.questions[self.current_question_index]
        correct = q["correct_answer"]

        for btn in self.option_buttons:
            btn.configure(state="disabled")

        if selected_index == correct:
            self.score += 1
            self.option_buttons[selected_index].configure(fg_color="green")
        else:
            self.option_buttons[selected_index].configure(fg_color="#942727") # Soft Red
            self.option_buttons[correct].configure(fg_color="green")

        self.update_ui_stats()
        self.btn_next.configure(state="normal")

    def next_question(self):
        self.current_question_index += 1
        self.display_question()

    def finish_quiz(self):
        perc = (self.score / len(self.questions)) * 100
        old_level = self.current_level

        if perc >= 80 and self.current_level < 3:
            self.current_level += 1
        elif perc < 40 and self.current_level > 1:
            self.current_level -= 1

        result_msg = f"Quiz Complete!\nScore: {self.score}/{len(self.questions)}\n\n"
        result_msg += f"New Difficulty: {self.difficulty_map[self.current_level]}"
        
        self.show_popup("Results", result_msg)
        self.show_setup_screen()

    def update_ui_stats(self):
        self.lbl_score.configure(text=f"Score: {self.score}")
        self.lbl_level.configure(text=f"Level: {self.current_level} ({self.difficulty_map[self.current_level]})")

    def show_popup(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("350x200")
        popup.attributes("-topmost", True)
        
        # Center popup
        x = self.winfo_x() + (self.winfo_width() // 2) - 175
        y = self.winfo_y() + (self.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(popup, text=message, wraplength=300).pack(pady=30)
        ctk.CTkButton(popup, text="OK", command=popup.destroy).pack(pady=10)
        popup.grab_set()

if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()