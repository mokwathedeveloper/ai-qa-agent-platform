import pytest
from playwright.sync_api import Page, expect

def test_example_domain(page: Page):
    """
    Test case to verify Example Domain.
    """
    page.goto("https://example.com")
    expect(page).to_have_title("Example Domain")
    # Intentional failure for demo purposes? No, let's make it pass first.
    # We can add a failing one later to test the bug reporting.
