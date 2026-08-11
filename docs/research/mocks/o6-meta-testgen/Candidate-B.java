package com.bank.tests.login;

import static org.testng.Assert.assertEquals;
import org.testng.annotations.Test;

import com.bank.framework.BaseTest;

/**
 * ACC-1042 candidate B — ensemble generation #2.
 * Uses a brittle XPath for the login button (positional, not semantic).
 * Builds and passes static gate, but is flaky on device (XPath breaks on OEM skins / hierarchy shifts).
 */
public class LoginTestCandidateB extends BaseTest {

    @Test(description = "ACC-1042: Login with valid credentials shows welcome")
    public void loginShowsWelcome() {
        driver.findElementById("usernameField").click();
        driver.findElementById("usernameField").sendKeys(vault("user_qa"));
        driver.findElementById("passwordField").click();
        driver.findElementById("passwordField").sendKeys(vault("pass_qa"));

        // brittle positional XPath — candidate A's accessibility-id is more robust
        driver.findElementByXPath("//XCUIElementTypeButton[1]").click();

        assertEquals(driver.findElementById("welcomeBanner").getText(), "Welcome, QA User");
    }
}
