"""
playwright_script.py
Automates filling UPSC questions on https://classes.bharatexamfest.com/addQuestion
Handles both Normal and Statement question types.
"""
import time
import json
import traceback
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from automation.selectors import SELECTORS, QTYPE_SELECTOR_MAP
from config.config import BASE_URL, MAX_RETRIES, DELAY_BETWEEN_QUESTIONS


# ---------------------------------------------------------------------------
# File Upload Helper
# ---------------------------------------------------------------------------

def upload_file_if_present(page, selector_key: str, file_path: str):
    """If file_path is provided, use playwright to upload it to the input[type=file]."""
    if not file_path:
        return
        
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f"    ⚠️ Warning: File not found: {abs_path}")
        return
        
    selector = SELECTORS.get(selector_key)
    if not selector:
        return
        
    print(f"    → Uploading image: {os.path.basename(abs_path)}")
    
    # Target the file input
    file_input = page.locator(selector)
    
    # Set the file
    file_input.set_input_files(abs_path)
    
    # Manually trigger events that React/Ant-Design might be listening for
    file_input.dispatch_event("change")
    file_input.dispatch_event("input")
    
    page.wait_for_timeout(1500) # Wait for background upload/preview generation
    file_input.blur()
    page.wait_for_timeout(500)


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
    selector = SELECTORS["subtopic_input"]
    print(f"    → Selecting Subtopic: {subtopic}")
    
    # Wait for at least one React-Select input to be available in the DOM
    page.wait_for_selector(selector, state="attached", timeout=10000)
    
    # Grab all react-select inputs. Subject is [0], Subtopic is [1].
    inputs = page.locator(selector).all()
    if len(inputs) > 1:
        input_el = inputs[1]  # The second box on the page is Subtopic
    else:
        input_el = inputs[0]  # Fallback if Subject isn't interactable/present

    # Ensure it's in view
    input_el.scroll_into_view_if_needed()
    
    # Focus the element directly. This bypasses strict visibility/overlay checks
    input_el.focus()
    page.wait_for_timeout(300)
    
    # Fallback to a forced click to ensure the browser has set focus
    input_el.click(force=True)
    page.wait_for_timeout(300)
    
    # Type out the text simulating real keystrokes into whatever has focus
    page.keyboard.type(subtopic, delay=50)
    
    # Wait for the dropdown to show the result and press Enter
    page.wait_for_timeout(1000)
    page.keyboard.press("Enter")
    page.wait_for_timeout(500)


# ---------------------------------------------------------------------------
# Question Type radio
# ---------------------------------------------------------------------------

def select_question_type(page, question_type: str):
    """Select the correct Question Type radio by clicking its label."""
    q_type_key = question_type.lower().replace(" ", "-")
    key = QTYPE_SELECTOR_MAP.get(q_type_key, "qtype_normal")
    
    selector = SELECTORS.get(key)
    if not selector:
        print(f"    ⚠️ Warning: No selector found for question type '{question_type}' (key: {key})")
        return

    print(f"    → Selecting Question Type: {question_type}")
    page.click(selector)
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

def fill_statements(page, statements: list, section: str = "english"):
    use_last = (section == "hindi")
    
    # Isolate the section wrapper to avoid mixing English and Hindi statement counts
    # The 'Subject' word is near the top of the form. The easiest way to isolate Hindi section 
    # is to slice the DOM. But since Playwright accesses the active DOM, we can use 
    # the Add Statement buttons as anchor points.
    
    for idx, stmt in enumerate(statements):
        if isinstance(stmt, dict):
            stmt_text = stmt["text"]
            stmt_image = stmt.get("image")
        else:
            stmt_text = stmt
            stmt_image = None
        
        placeholder = f"Statement {idx + 1}"
        locator = page.locator(f"input[placeholder='{placeholder}']")

        # Keep clicking adding statement until we can successfully target the input
        while True:
            target = locator.last if use_last else locator.first
            
            # If the specific target we need exists, we break!
            # (If English had 0 statements, count will be 1, but 'target' will resolve to it successfully)
            if locator.count() >= (2 if use_last else 1) or (use_last and locator.count() >= 1 and target.count() > 0):
                # We have what we need, break immediately
                break
                
            add_btn = page.locator(SELECTORS["stmt_add_btn"])
            if add_btn.count() == 0:
                print("    ⚠️ Warning: Could not find 'Add Statement' button.")
                break
                
            btn_target = add_btn.last if use_last else add_btn.first
            btn_target.click()
            page.wait_for_timeout(1000)

        target = locator.last if use_last else locator.first
        if target.count() > 0:
            target.fill(str(stmt_text), force=True)

        if stmt_image:
            img_selector = f"input[placeholder='{placeholder}'] ~ div input[type='file']"
            file_input = page.locator(img_selector).last if use_last else page.locator(img_selector).first
            abs_path = os.path.abspath(stmt_image)
            if os.path.exists(abs_path) and file_input.count() > 0:
                print(f"    → Uploading statement image: {os.path.basename(abs_path)}")
                file_input.set_input_files(abs_path)
                file_input.dispatch_event("change")
                file_input.dispatch_event("input")
                page.wait_for_timeout(1000)
                file_input.blur()

        page.wait_for_timeout(200)

def fill_pairs(page, pairs: list, section: str = "english"):
    use_last = (section == "hindi")
    N = len(pairs)
    if N == 0:
        return
    
    clean_pairs = []
    for p in pairs:
        if isinstance(p, dict):
            clean_pairs.append([p.get("left", ""), p.get("right", "")])
        else:
            clean_pairs.append(p)
            
    max_cols = max((len(row) for row in clean_pairs), default=2)

    # Wait for the table to render after the Pair radio button was clicked
    try:
        page.wait_for_selector("table", state="attached", timeout=5000)
    except Exception:
        pass

    tables = page.locator("table").all()
    if not tables:
        print("    ⚠️ Warning: No table found for pair inputs!")
        return
    
    # We assume first table is English, last is Hindi
    target_table = tables[-1] if use_last else tables[0]

    # Add columns if needed
    first_row_inputs = target_table.locator("tr").first.locator("input")
    while first_row_inputs.count() > 0 and first_row_inputs.count() < max_cols:
        add_col_btn = page.locator(SELECTORS.get("add_column_btn", "button:has-text('Add Column')"))
        if add_col_btn.count() > 0:
            btn_td = add_col_btn.last if use_last else add_col_btn.first
            btn_td.click()
            page.wait_for_timeout(1000)
        else:
            break

    # Add rows if needed. Count rows that actually have inputs.
    while True:
        data_rows = target_table.locator("tr:has(input)").all()
        if len(data_rows) >= len(clean_pairs):
            break
            
        add_btn = page.locator(SELECTORS["pair_add_btn"])
        if add_btn.count() == 0:
            print("    ⚠️ Warning: Could not find add pair button.")
            break
            
        btn_target = add_btn.last if use_last else add_btn.first
        btn_target.click()
        page.wait_for_timeout(1000)
        
    # Now fill data
    data_rows = target_table.locator("tr:has(input)").all()
    for idx, row_data in enumerate(clean_pairs):
        if idx < len(data_rows):
            inputs = data_rows[idx].locator("input").all()
            for col_i, cell in enumerate(row_data):
                cell_text = cell["text"] if isinstance(cell, dict) else cell
                if col_i < len(inputs):
                    # Force fill to avoid strict actionability blocks
                    inputs[col_i].fill(str(cell_text), force=True)
                else:
                    print(f"    ⚠️ Warning: Not enough columns in row {idx} for cell {col_i}")
        else:
            print(f"    ⚠️ Warning: Row {idx} not found in table.")

    page.wait_for_timeout(200)



# ---------------------------------------------------------------------------
# Fill English section
# ---------------------------------------------------------------------------

def fill_english(page, q: dict):
    eng = q["english"]
    q_type = q.get("question_type", "Normal").lower()

    # Top/preamble question
    q_txt = eng["question"]
    # Safety: If text looks like a URL/Path, it shouldn't be here (indicates parsing error or wrong field)
    if not (q_txt.startswith("http") or q_txt.startswith("C:/") or q_txt.startswith("D:/")):
        page.fill(SELECTORS["en_question"], q_txt)
    else:
        print(f"    ⚠️ Warning: Skipping question text because it looks like a URL/Path: {q_txt[:50]}...")
        
    upload_file_if_present(page, "en_question_img", eng.get("question_image"))

    # Statements or Pairs
    if q_type in ("statement", "statement-csat"):
        if eng.get("statements"):
            fill_statements(page, eng["statements"], section="english")
        
        lq = eng.get("lastQuestion")
        if lq:
            lq_txt = lq["text"] if isinstance(lq, dict) else lq
            page.fill(SELECTORS["en_last_question"], lq_txt)
            if isinstance(lq, dict) and lq.get("image"):
                upload_file_if_present(page, "en_last_question_img", lq["image"])
            
    elif q_type == "pair":
        if eng.get("pairs"):
            fill_pairs(page, eng["pairs"], section="english")
        
        lq = eng.get("lastQuestion")
        if lq:
            lq_txt = lq["text"] if isinstance(lq, dict) else lq
            page.fill(SELECTORS["en_last_question"], lq_txt)
            if isinstance(lq, dict) and lq.get("image"):
                upload_file_if_present(page, "en_last_question_img", lq["image"])
            
    # Options
    for letter in ("A", "B", "C", "D"):
        page.fill(SELECTORS[f"en_option_{letter}"], eng["options"].get(letter, ""))
        upload_file_if_present(page, f"en_option_{letter}_img", eng.get("options_images", {}).get(letter))

    # Answer — HTML values are UPPERCASE (A, B, C, D)
    answer = eng["answer"].upper()
    page.click(f"input[name='englishQuestion.answer'][value='{answer}']")

    # Solution
    page.fill(SELECTORS["en_solution"], eng["solution"])
    upload_file_if_present(page, "en_solution_img", eng.get("solution_image"))



# ---------------------------------------------------------------------------
# Fill Hindi section
# ---------------------------------------------------------------------------

def fill_hindi(page, q: dict):
    hi = q["hindi"]
    q_type = q.get("question_type", "Normal").lower()

    # Top/preamble question
    q_txt = hi["question"]
    if not (q_txt.startswith("http") or q_txt.startswith("C:/") or q_txt.startswith("D:/")):
        page.fill(SELECTORS["hi_question"], q_txt)
    else:
        print(f"    ⚠️ Warning: Skipping Hindi question text because it looks like a URL/Path: {q_txt[:50]}...")
        
    upload_file_if_present(page, "hi_question_img", hi.get("question_image"))

    # Statements or Pairs
    if q_type in ("statement", "statement-csat"):
        if hi.get("statements"):
            fill_statements(page, hi["statements"], section="hindi")
        
        lq = hi.get("lastQuestion")
        if lq:
            lq_txt = lq["text"] if isinstance(lq, dict) else lq
            page.fill(SELECTORS["hi_last_question"], lq_txt)
            if isinstance(lq, dict) and lq.get("image"):
                upload_file_if_present(page, "hi_last_question_img", lq["image"])
            
    elif q_type == "pair":
        if hi.get("pairs"):
            fill_pairs(page, hi["pairs"], section="hindi")
        
        lq = hi.get("lastQuestion")
        if lq:
            lq_txt = lq["text"] if isinstance(lq, dict) else lq
            page.fill(SELECTORS["hi_last_question"], lq_txt)
            if isinstance(lq, dict) and lq.get("image"):
                upload_file_if_present(page, "hi_last_question_img", lq["image"])

    # Options
    for letter in ("A", "B", "C", "D"):
        page.fill(SELECTORS[f"hi_option_{letter}"], hi["options"].get(letter, ""))
        upload_file_if_present(page, f"hi_option_{letter}_img", hi.get("options_images", {}).get(letter))

    # Answer — same as English (per website documentation)
    answer = q["english"]["answer"].upper()
    page.click(f"input[name='hindiQuestion.answer'][value='{answer}']")

    # Solution
    page.fill(SELECTORS["hi_solution"], hi["solution"])
    upload_file_if_present(page, "hi_solution_img", hi.get("solution_image"))



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
    
    save_btn.click(force=True)
    
    print("    → Waiting for save to process...")
    try:
        # Wait up to 10 seconds for the browser to redirect away from the 'addQuestion' page
        page.wait_for_url(lambda url: "addQuestion" not in url, timeout=10000)
    except Exception:
        # User requested to hard-fail and restart the entire question if the redirect doesn't happen
        raise PlaywrightTimeoutError("Dashboard redirect did not occur. Save likely failed.")



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

    # Reset/Initialize the failed indices log
    os.makedirs("logs", exist_ok=True)
    with open("logs/failed_indices.txt", "w", encoding="utf-8") as f:
        f.write("--- FAILED QUESTIONS LOG ---\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(BASE_URL)

        print("\n👉 Please login manually in the browser.")
        print("👉 Go to the Dashboard and find the 'Add Question' button for your target subject.")
        print("👉 Right-click it and select 'Copy link address' (or click it and copy URL from new window).")
        
        add_url = ""
        while not add_url or "addQuestion" not in add_url:
            add_url = input("\n👉 Paste the full 'Add Question' URL here and press ENTER: ").strip()

        for idx, q in enumerate(questions):
            label = f"[{idx+1}/{total}] {q.get('subtopic','?')} | {q.get('question_type','?')}"
            print(f"\n{label}")
            submitted = False

            # ALWAYS load a fresh instance using the direct URL before starting a NEW question
            # This handles the dashboard redirect from the previous successful question
            print("    → Loading Add Question form...")
            page.goto(add_url)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)

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
                    print(f"  🔄 Retrying in 3s without refreshing...")
                    time.sleep(3)

            if not submitted:
                print(f"  ❌ Failed after {MAX_RETRIES} attempts. Skipping.")
                failed.append(q)
                # Immediately save to failed.json
                os.makedirs("logs", exist_ok=True)
                with open("logs/failed.json", "w", encoding="utf-8") as f:
                    json.dump(failed, f, indent=2, ensure_ascii=False)
                
                # ALSO write the question index to a text file for easy reading
                with open("logs/failed_indices.txt", "a", encoding="utf-8") as f:
                    # idx starts at 0, so idx+1 is the human-readable question number
                    f.write(f"Question {idx+1} failed ({q.get('subtopic', 'Unknown')})\n")

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