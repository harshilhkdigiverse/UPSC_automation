# UPSC Automation: CSAT Input Format Guide

To ensure your questions are correctly identified as **CSAT Type** by the automation, use the following structure in your `data/english.docx` and `data/hindi.docx` files.

---

## 1. Normal CSAT Format
Use this for standard multiple-choice questions.

**Format:**
```text
[Subtopic Name]
[Category (Concept/Aptitude)]
Normal Csat
[Question Number]. [Question Text]
(a) [Option A]
(b) [Option B]
(c) [Option C]
(d) [Option D]
Answer: ([Letter])
Solution: [Your explanation here]
```

**Real Example:**
```text
Number System
Concept
Normal Csat
1. What is the remainder when 2^31 is divided by 7?
(a) 1
(b) 2
(c) 4
(d) 6
Answer: (b)
Solution: 2^3 = 8, which gives remainder 1 when divided by 7. 2^31 = (2^3)^10 * 2^1. Remainder = 1^10 * 2 = 2.
```

---

## 2. Statement CSAT Format
Use this for questions that involve multiple numbered statements (e.g., "Consider the following statements").

**Format:**
```text
[Subtopic Name]
[Category (Concept/Aptitude)]
Statement Csat
[Question Number]. [Introductory Text]
1. [Statement 1]
2. [Statement 2]
[Last Question/Conclusion Text]
(a) [Option A]
(b) [Option B]
(c) [Option C]
(d) [Option D]
Answer: ([Letter])
Solution: [Your explanation here]
```

**Real Example:**
```text
Data Sufficiency
Concept
Statement Csat
2. Consider the following statements regarding a natural number 'n':
1. n is a prime number.
2. n leaves a remainder of 1 when divided by 6.
Which of the statements given above is/are sufficient to determine if n is greater than 10?
(a) 1 only
(b) 2 only
(c) Both 1 and 2
(d) Neither 1 nor 2
Answer: (d)
Solution: Statement 1: n could be 7 (<=10) or 11 (>10). Statement 2: n could be 7 (<=10) or 13 (>10). Even combined, we cannot be sure.
```

---

## Key Requirements for Successful Parsing:
1.  **The "Normal Csat" or "Statement Csat" label** must be on the **3rd line** of the question block.
2.  **Options** must use parentheses like `(a)`, `(b)`, etc.
3.  **The Answer line** must start with `Answer:` followed by the option in parentheses.
4.  **The Solution line** must start with `Solution:` to be captured correctly.
