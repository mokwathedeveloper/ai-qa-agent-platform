"""
Test Runner Module
Handles automated test execution using Playwright
"""

import asyncio
import os
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup_browser(self):
        """Initialize browser for testing"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            return True
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return False
    
    async def cleanup_browser(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")
    
    async def run_basic_tests(self, url: str) -> Dict[str, Any]:
        """Run basic automated tests on the given URL"""
        results = {
            "status": "COMPLETED",
            "logs": [],
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": []
        }
        
        try:
            results["logs"].append(f"Starting tests for URL: {url}")
            
            if not await self.setup_browser():
                results["status"] = "ERROR"
                results["logs"].append("Failed to initialize browser")
                return results
            
            # Test 1: Page Load (reduced timeout)
            results["logs"].append("Test 1: Checking page load...")
            results["tests_run"] += 1
            
            try:
                response = await self.page.goto(url, wait_until='domcontentloaded', timeout=10000)  # Reduced from 30s to 10s
                if response and response.status < 400:
                    results["tests_passed"] += 1
                    results["logs"].append("✅ Page loaded successfully")
                else:
                    results["tests_failed"] += 1
                    results["failures"].append({
                        "test": "Page Load",
                        "error": f"HTTP {response.status if response else 'No response'}"
                    })
                    results["logs"].append(f"❌ Page load failed: HTTP {response.status if response else 'No response'}")
            except Exception as e:
                results["tests_failed"] += 1
                results["failures"].append({
                    "test": "Page Load",
                    "error": str(e)
                })
                results["logs"].append(f"❌ Page load error: {str(e)}")
            
            # Test 2: Title Check (no wait)
            results["logs"].append("Test 2: Checking page title...")
            results["tests_run"] += 1
            
            try:
                title = await self.page.title()
                if title and len(title.strip()) > 0:
                    results["tests_passed"] += 1
                    results["logs"].append(f"✅ Page title found: '{title}'")
                else:
                    results["tests_failed"] += 1
                    results["failures"].append({
                        "test": "Title Check",
                        "error": "Page title is empty or missing"
                    })
                    results["logs"].append("❌ Page title is empty or missing")
            except Exception as e:
                results["tests_failed"] += 1
                results["failures"].append({
                    "test": "Title Check",
                    "error": str(e)
                })
                results["logs"].append(f"❌ Title check error: {str(e)}")
            
            # Test 3: Basic Elements Check (faster)
            results["logs"].append("Test 3: Checking for basic HTML elements...")
            results["tests_run"] += 1
            
            try:
                # Quick check for essential elements
                body = await self.page.query_selector('body')
                if body:
                    results["tests_passed"] += 1
                    results["logs"].append("✅ Found basic HTML structure")
                else:
                    results["tests_failed"] += 1
                    results["failures"].append({
                        "test": "Basic Elements Check",
                        "error": "No body element found"
                    })
                    results["logs"].append("❌ No body element found")
            except Exception as e:
                results["tests_failed"] += 1
                results["failures"].append({
                    "test": "Basic Elements Check",
                    "error": str(e)
                })
                results["logs"].append(f"❌ Elements check error: {str(e)}")
            
            # Skip slow tests for faster results
            results["logs"].append("✅ Quick tests completed")
            
            # Determine overall status
            if results["tests_failed"] > 0:
                results["status"] = "FAILED"
                results["logs"].append(f"Tests completed: {results['tests_passed']}/{results['tests_run']} passed")
            else:
                results["status"] = "COMPLETED"
                results["logs"].append(f"All tests passed: {results['tests_passed']}/{results['tests_run']}")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["logs"].append(f"Critical error during test execution: {str(e)}")
            logger.error(f"Critical error in run_basic_tests: {traceback.format_exc()}")
        
        finally:
            await self.cleanup_browser()
        
        return results

def run_automation_tests(url: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for running automation tests
    """
    try:
        runner = TestRunner()
        
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, runner.run_basic_tests(url))
                result = future.result()
                return result
        except RuntimeError:
            # No event loop running, safe to create one
            return asyncio.run(runner.run_basic_tests(url))
    
    except Exception as e:
        logger.error(f"Error in run_automation_tests: {traceback.format_exc()}")
        return {
            "status": "ERROR",
            "logs": [f"Failed to execute tests: {str(e)}"],
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [{"test": "Test Execution", "error": str(e)}]
        }