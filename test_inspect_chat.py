import sys
sys.stdout.reconfigure(encoding='utf-8')
from DrissionPage import ChromiumOptions, ChromiumPage

co = ChromiumOptions()
co.set_local_port(9555)
page = ChromiumPage(co)

# Click on the first chat in recents to see what an assistant turn looks like
recents = page.eles('xpath://a[contains(@href, "/c/")]')
print(f"Found {len(recents)} chat links")
if recents:
    first_chat_url = recents[0].attr('href')
    print("Opening chat:", first_chat_url)
    page.get(first_chat_url)
    page.wait(3)
    
    # Now inspect the chat turns
    print("\nPage URL:", page.url)
    
    # 1. Check user vs assistant message indicators
    # In ChatGPT:
    # Look for elements with data-message-author-role
    user_msgs = page.eles('xpath://*[@data-message-author-role="user"]')
    asst_msgs = page.eles('xpath://*[@data-message-author-role="assistant"]')
    print(f"data-message-author-role user: {len(user_msgs)}, assistant: {len(asst_msgs)}")
    
    # Look for articles
    articles = page.eles('tag:article')
    print(f"Articles: {len(articles)}")
    for i, a in enumerate(articles):
        # Check if user or assistant
        role = a.attr('data-testid') or a.attr('aria-label') or 'unknown'
        print(f"Article {i}: len={len(a.text)}, preview={repr(a.text[:120])}")
    
    # Look for markdown divs (assistant answers are in .markdown)
    markdowns = page.eles('xpath://div[contains(@class, "markdown")]')
    print(f"Markdown elements: {len(markdowns)}")
    for i, m in enumerate(markdowns):
        print(f"Markdown {i}: len={len(m.text)}, preview={repr(m.text[:150])}")

