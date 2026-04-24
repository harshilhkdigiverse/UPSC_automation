import time
from playwright.sync_api import sync_playwright
from automation.selectors import SELECTORS
from config.config import BASE_URL

def debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL)

        print("\n👉 Please navigate to the 'Add Question' page where the Subtopic field follows...")
        print("👉 Press ENTER in this terminal when the page is fully loaded and you see the Subtopic box.")
        input()

        print("\n--- DEBUGGING SELECTORS ---")
        
        # 1. Try to find all inputs with role='combobox'
        inputs = page.locator("input[role='combobox']").all()
        print(f"Found {len(inputs)} inputs with role='combobox'")
        for i, el in enumerate(inputs):
            html = el.evaluate("el => el.outerHTML")
            parent_html = el.locator("..").evaluate("el => el.outerHTML")
            print(f"\n[Input {i}]")
            print(f"HTML: {html}")
            # Try to find a label or text near it
            placeholder = el.get_attribute("aria-describedby")
            if placeholder:
                p_text = page.locator(f"#{placeholder}").inner_text()
                print(f"Linked Placeholder Text: {p_text}")

        # 2. Try to find the label 'Subtopic'
        labels = page.locator("label").all()
        for label in labels:
            text = label.inner_text()
            if "Subtopic" in text:
                print(f"\nFound label with text: '{text}'")
                # Check siblings
                next_div = label.locator("xpath=following-sibling::div").first
                if next_div.count() > 0:
                    print("Has following sibling div.")
                    sub_inputs = next_div.locator("input").all()
                    print(f"Inner inputs in sibling: {len(sub_inputs)}")

        print("\n--- END OF DEBUG ---")
        print("Press ENTER to close browser...")
        input()
        browser.close()

if __name__ == "__main__":
    debug()
