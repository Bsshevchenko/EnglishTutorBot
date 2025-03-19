

def exercise_prompt(level, topic, exercise_type):
    return f"""
        You are a professional English tutor.  
        Create EXACTLY 3 {exercise_type} questions for a student with {level} English level on the topic "{topic}".  
        
        Important Instructions:
        - DO NOT write your thought process, explanations, answers, or any additional text. ONLY QUESTIONS!
        - Each question must contain exactly one blank "___".
        - Each question must have exactly 4 answer choices labeled as a), b), c), d).
        - Separate lines clearly by newline characters (\n). Do NOT use <br> tags.
        
        Strict example of correct output (HTML):
        
        <b>📝 Past Simple Exercise</b>
        
        1️⃣ She ___ to school yesterday.
        a) goes
        b) go
        c) went
        d) going
        
        2️⃣ They ___ dinner at 6 pm last night.
        a) have
        b) has
        c) had
        d) having
        
        3️⃣ He ___ the book last week.
        a) read
        b) reading
        c) reads
        d) readed
"""

def check_answers_prompt(exercise_text, user_answers):
    return f"""
        You are a professional English tutor. You provided a student with the following exercise:
        
        {exercise_text}
        
        The student answered:
        {user_answers}
        
        Instructions for your reply:
        
        - If all answers are correct, praise the student enthusiastically.
        - If any answer is incorrect, clearly state:
          - Which answers are wrong.
          - The correct answers.
          - Short grammar explanation why the correct answers are right.
        
        Provide the response clearly formatted using emojis and simple HTML formatting. 
        
        Example of correct output if all answers are right:
        
        <b>🎉 Fantastic! All your answers are correct!</b> Keep up the great work! 🚀
        
        Example if some answers are wrong:
        
        <b>❌ Let's review your answers:</b>
        
        - <b>Question 1:</b> Your answer: a ❌, Correct answer: c ✔️  
          <i>"Went"</i> is correct because the action happened in the past (yesterday).
        
        - <b>Question 3:</b> Your answer: b ❌, Correct answer: d ✔️  
          <i>"Read"</i> is the correct past simple form (irregular verb).
        
        Great effort! Review these rules and try again! 🌟
"""

