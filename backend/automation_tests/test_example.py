import pytest
from playwright.sync_api import Page, expect
import os
import re

def test_example_domain(page: Page):
    """
    Test case to verify the domain provided in the TARGET_URL environment variable.
    """
    target_url = os.environ.get("TARGET_URL", "https://example.com")
    page.goto(target_url)
    # A generic check that might work for many pages, but can be improved.
    # For now, we just check that the page title is not empty.
    expect(page).to_have_title(re.compile(r".+"))
