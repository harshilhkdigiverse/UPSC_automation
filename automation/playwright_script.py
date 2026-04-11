"""
playwright_script.py
Automates filling UPSC questions on https://classes.bharatexamfest.com/addQuestion
Handles both Normal and Statement question types.
"""
import time
import json
import traceback
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from automation.selectors import SELECTORS, QTYPE_SELECTOR_MAP
from config.config import BASE_URL, MAX_RETRIES, DELAY_BETWEEN_QUESTIONS


# ---------------------------------------------------------------------------
# Load questions
# ---------------------------------------------------------------------------

def load_questions() -> list:
    with open("data/parsed_questions.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Subtopic — React Select dropdown
# ---------------------------------------------------------------------------

def select_subtopic(page, subtopic: str):
    """Click the React Select input, type the subtopic, and confirm with Enter."""
    input_el = page.locator(SELECTORS["subtopic_input"]).first
    input_el.click()
    time.sleep(0.3)
    input_el.fill("")
    input_el.type(subtopic, delay=40)
    time.sleep(1)            # wait for dropdown to render
    page.keyboard.press("Enter")
    time.sleep(0.5)


# ---------------------------------------------------------------------------
# Question Type radio
# ---------------------------------------------------------------------------

def select_question_type(page, question_type: str):
    """Select the correct Question Type radio by clicking its label."""
    key = QTYPE_SELECTOR_MAP.get(question_type.lower(), "qtype_normal")
    page.click(SELECTORS[key])
    time.sleep(0.5)


# ---------------------------------------------------------------------------
# Category radio (concept / aptitude / random)
# ---------------------------------------------------------------------------

def select_category(page, category: str):
    """Click the category label — the span overlay blocks direct input clicks."""
    selector = SELECTORS.get(f"category_{category.lower()}")
    if not selector:
        raise ValueError(f"Unknown category: {category!r}")
    page.click(selector)
    time.sleep(0.3)


# ---------------------------------------------------------------------------
# Statement inputs helper
# ---------------------------------------------------------------------------

def fill_statements(page, statements: list[str], section: str = "english"):
    use_last = (section == "hindi")
    # For English, we expect 1 match across the DOM. For Hindi, we expect 2 (English + Hindi)
    expected_count = 2 if use_last else 1

    for idx, stmt_text in enumerate(statements):
        placeholder = f"Statement {idx + 1}"
        locator = page.locator(f"input[placeholder='{placeholder}']")

        # Dynamically check if the statement box already exists on the page.
        # If it doesn't, we click '+' until it spawns.
        while locator.count() < expected_count:
            add_btn = page.locator(SELECTORS["stmt_add_btn"])
            btn_target = add_btn.last if use_last else add_btn.first
            btn_target.click()
            page.wait_for_timeout(1000) # Give React time to render the new input box

        # Now fill the specific target (English = first, Hindi = last)
        target = locator.last if use_last else locator.first
        target.fill(stmt_text)

        page.wait_for_timeout(200)

def fill_pairs(page, pairs: list, section: str = "english"):
    use_last = (section == "hindi")
    N = len(pairs)
    if N == 0:
        return
    
    # English inputs are indices 0 to N-1. Hindi inputs are indices N to 2N-1.
    offset = N if use_last else 0

    # Ensure format is a list of lists representing columns (backward compatible with dicts)
    clean_pairs = []
    for p in pairs:
        if isinstance(p, dict):
            clean_pairs.append([p.get("left", ""), p.get("right", "")])
        else:
            clean_pairs.append(p)
            
    max_cols = max((len(row) for row in clean_pairs), default=2)

    # Ensure adequate columns exist (Default assumes pair1 and pair2 already exist)
    for col_idx in range(3, max_cols + 1):
        col_locator = page.locator(f"input[placeholder='pair{col_idx}']")
        while col_locator.count() < (offset + 1):
            add_col_btn = page.locator(SELECTORS["add_column_btn"])
            target_btn = add_col_btn.last if use_last else add_col_btn.first
            target_btn.click()
            page.wait_for_timeout(1000)

    left_locator = page.locator("input[placeholder='pair1']")

    for idx, row_data in enumerate(clean_pairs):
        required_rows = offset + idx + 1

        # Click '+' until the required row exists
        while left_locator.count() < required_rows:
            add_btn = page.locator(SELECTORS["pair_add_btn"])
            btn_target = add_btn.last if use_last else add_btn.first
            btn_target.click()
            page.wait_for_timeout(1000)

        # Fill dynamically for each column
        current_index = offset + idx
        for col_i, text_val in enumerate(row_data):
            col_id = col_i + 1
            col_loc = page.locator(f"input[placeholder='pair{col_id}']")
            col_loc.nth(current_index).fill(text_val)
        
        page.wait_for_timeout(200)


# ---------------------------------------------------------------------------
# Fill English section
# ---------------------------------------------------------------------------

def fill_english(page, q: dict):
    eng = q["english"]
    q_type = q.get("question_type", "Normal").lower()

    # Top/preamble question
    page.fill(SELECTORS["en_question"], eng["question"])

    # Statements or Pairs
    if q_type in ("statement", "statement-csat"):
        if eng.get("statements"):
            fill_statements(page, eng["statements"], section="english")
        # Fill the closing question
        if eng.get("lastQuestion"):
            page.fill(SELECTORS["en_last_question"], eng["lastQuestion"])
            
    elif q_type == "pair":
        if eng.get("pairs"):
            fill_pairs(page, eng["pairs"], section="english")
        if eng.get("lastQuestion"):
            page.fill(SELECTORS["en_last_question"], eng["lastQuestion"])
            
    # Options
    page.fill(SELECTORS["en_option_A"], eng["options"]["A"])
    page.fill(SELECTORS["en_option_B"], eng["options"]["B"])
    page.fill(SELECTORS["en_option_C"], eng["options"]["C"])
    page.fill(SELECTORS["en_option_D"], eng["options"]["D"])

    # Answer — HTML values are UPPERCASE (A, B, C, D)
    answer = eng["answer"].upper()
    page.click(f"input[name='englishQuestion.answer'][value='{answer}']")

    # Solution
    page.fill(SELECTORS["en_solution"], eng["solution"])


# ---------------------------------------------------------------------------
# Fill Hindi section
# ---------------------------------------------------------------------------

def fill_hindi(page, q: dict):
    hi = q["hindi"]
    q_type = q.get("question_type", "Normal").lower()

    # Top/preamble question
    page.fill(SELECTORS["hi_question"], hi["question"])

    # Statements or Pairs
    if q_type in ("statement", "statement-csat"):
        if hi.get("statements"):
            fill_statements(page, hi["statements"], section="hindi")
        if hi.get("lastQuestion"):
            page.fill(SELECTORS["hi_last_question"], hi["lastQuestion"])
            
    elif q_type == "pair":
        if hi.get("pairs"):
            fill_pairs(page, hi["pairs"], section="hindi")
        if hi.get("lastQuestion"):
            page.fill(SELECTORS["hi_last_question"], hi["lastQuestion"])

    # Options
    page.fill(SELECTORS["hi_option_A"], hi["options"]["A"])
    page.fill(SELECTORS["hi_option_B"], hi["options"]["B"])
    page.fill(SELECTORS["hi_option_C"], hi["options"]["C"])
    page.fill(SELECTORS["hi_option_D"], hi["options"]["D"])

    # Answer — same as English (per website documentation)
    answer = q["english"]["answer"].upper()
    page.click(f"input[name='hindiQuestion.answer'][value='{answer}']")

    # Solution
    page.fill(SELECTORS["hi_solution"], hi["solution"])


# ---------------------------------------------------------------------------
# Submit and move to next question
# ---------------------------------------------------------------------------

def submit_question(page):
    print("    → Clicking Save Question...")
    
    # Press Tab to blur the last input and trigger any pending React state validations
    page.keyboard.press("Tab")
    
    # IMPORTANT: Wait for debounced React form validations to complete before clicking
    page.wait_for_timeout(2500)

    save_btn = page.locator(SELECTORS["save_button"])
    save_btn.scroll_into_view_if_needed()
    
    # Move mouse to the exact center of the button and physically click it
    box = save_btn.bounding_box()
    if box:
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.wait_for_timeout(50)
        page.mouse.up()
    else:
        # Fallback if somehow it's not laid out
        save_btn.click(force=True)
    
    # The website redirects to the Subject Details Dashboard after saving.
    page.wait_for_timeout(3000)
    
    print("    → Waiting for Dashboard redirect...")
    # Click 'Create New Question' on the dashboard to start the next question
    new_q_btn = page.locator(SELECTORS["new_question"])
    new_q_btn.click()
    
    # Wait for the fresh form to load
    page.wait_for_timeout(2000)


# ---------------------------------------------------------------------------
# Full question pipeline
# ---------------------------------------------------------------------------

def process_question(page, q: dict):
    select_subtopic(page, q["subtopic"])
    select_question_type(page, q.get("question_type", "Normal"))
    select_category(page, q["category"])
    fill_english(page, q)
    fill_hindi(page, q)
    submit_question(page)


# ---------------------------------------------------------------------------
# Main run loop
# ---------------------------------------------------------------------------

def run():
    questions = load_questions()
    success, failed = [], []
    total = len(questions)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(BASE_URL)

        print("\n👉 Please login manually in the browser, then press ENTER here...")
        input()

        for idx, q in enumerate(questions):
            label = f"[{idx+1}/{total}] {q.get('subtopic','?')} | {q.get('question_type','?')}"
            print(f"\n{label}")
            submitted = False

            for attempt in range(MAX_RETRIES):
                try:
                    process_question(page, q)
                    success.append(q)
                    print(f"  ✅ Done")
                    submitted = True
                    break
                except PlaywrightTimeoutError as e:
                    print(f"  ⚠️  Attempt {attempt+1}/{MAX_RETRIES} — Timeout: {e}")
                except Exception as e:
                    print(f"  ⚠️  Attempt {attempt+1}/{MAX_RETRIES} — Error: {e}")
                    traceback.print_exc()

                if attempt < MAX_RETRIES - 1:
                    print(f"  🔄 Retrying in 3s...")
                    time.sleep(3)

            if not submitted:
                print(f"  ❌ Failed after {MAX_RETRIES} attempts. Skipping.")
                failed.append(q)

            time.sleep(DELAY_BETWEEN_QUESTIONS)

        browser.close()

    with open("logs/success.json", "w", encoding="utf-8") as f:
        json.dump(success, f, indent=2, ensure_ascii=False)
    with open("logs/failed.json", "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2, ensure_ascii=False)

    print(f"\n🏁 Done! ✅ Success: {len(success)}  ❌ Failed: {len(failed)}")
    if failed:
        print("  → Failed questions saved to logs/failed.json")


if __name__ == "__main__":
    run()