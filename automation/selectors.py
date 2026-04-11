SELECTORS = {
    # -----------------------------------------------------------------------
    # Subtopic — React Select
    # -----------------------------------------------------------------------
    "subtopic_input": "input[id^='react-select']",

    # -----------------------------------------------------------------------
    # Question Type — radio buttons (click LABEL to avoid span overlay)
    # -----------------------------------------------------------------------
    "qtype_normal":         "label[for='normal']",
    "qtype_statement":      "label[for='statement']",
    "qtype_pair":           "label[for='pair']",
    "qtype_normal_csat":    "label[for='Normal-Csat']",
    "qtype_statement_csat": "label[for='Statement-Csat']",

    # -----------------------------------------------------------------------
    # Category Type — radio buttons (click LABEL to avoid span overlay)
    # -----------------------------------------------------------------------
    "category_concept":  "label[for='concept']",
    "category_aptitude": "label[for='aptitude']",
    "category_random":   "label[for='random']",

    # -----------------------------------------------------------------------
    # English Question Section
    # -----------------------------------------------------------------------
    "en_question":      "input[name='englishQuestion.question']",
    # Statement type extras:
    "stmt_add_btn":     "button[title='Add Statement']",
    "stmt_remove_btn":  "button[title='Remove Statement']",
    "pair_add_btn":     "table button.bg-\\[\\#eb8844\\]",
    "add_column_btn":   "button:has-text('Add Column')",
    "en_last_question": "input[name='englishQuestion.lastQuestion']",
    # Options:
    "en_option_A": "input[name='englishQuestion.options.A']",
    "en_option_B": "input[name='englishQuestion.options.B']",
    "en_option_C": "input[name='englishQuestion.options.C']",
    "en_option_D": "input[name='englishQuestion.options.D']",
    # Answer radio (value must be uppercase A/B/C/D):
    "en_answer":   "input[name='englishQuestion.answer']",
    # Solution:
    "en_solution": "textarea[name='englishQuestion.solution']",

    # -----------------------------------------------------------------------
    # Hindi Question Section (mirrors English)
    # -----------------------------------------------------------------------
    "hi_question":      "input[name='hindiQuestion.question']",
    "hi_last_question": "input[name='hindiQuestion.lastQuestion']",
    "hi_option_A": "input[name='hindiQuestion.options.A']",
    "hi_option_B": "input[name='hindiQuestion.options.B']",
    "hi_option_C": "input[name='hindiQuestion.options.C']",
    "hi_option_D": "input[name='hindiQuestion.options.D']",
    "hi_answer":   "input[name='hindiQuestion.answer']",
    "hi_solution": "textarea[name='hindiQuestion.solution']",

    # -----------------------------------------------------------------------
    # Buttons
    # -----------------------------------------------------------------------
    "save_button":  "button[type='submit']:has-text('Save Question')",
    "new_question": "button:has-text('Create New Question')",
}

# Map question_type string from docx → selector key
QTYPE_SELECTOR_MAP = {
    "normal":         "qtype_normal",
    "statement":      "qtype_statement",
    "pair":           "qtype_pair",
    "normal-csat":    "qtype_normal_csat",
    "statement-csat": "qtype_statement_csat",
}