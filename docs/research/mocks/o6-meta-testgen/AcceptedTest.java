package com.bank.tests.login;

import static org.testng.Assert.assertEquals;
import org.testng.annotations.Test;

import com.bank.framework.BaseTest;
import com.bank.pages.HomeScreen;
import com.bank.pages.LoginScreen;

/**
 * ACC-1042 — accepted survivor of the Meta-TestGen ensemble+filter (see FilterResults.json).
 * Originally Candidate-A; reviewed and committed by an engineer.
 * This is committed, auditable code — the same shape as O1's LoginTest.java.
 * The difference from O1 is the MAINTENANCE MODEL: on drift, this file is REGENERATED and
 * re-filtered, not hand-edited. The engineer reviews survivors, never writes XPath by hand.
 */
public class LoginTest extends BaseTest {

    @Test(description = "ACC-1042: Login with valid credentials shows welcome")
    public void loginShowsWelcome() {
        LoginScreen login = new LoginScreen(driver);

        login.usernameField().click();
        login.usernameField().sendKeys(vault("user_qa"));
        login.passwordField().click();
        login.passwordField().sendKeys(vault("pass_qa"));
        login.loginButton().click();

        HomeScreen home = new HomeScreen(driver);
        assertEquals(home.welcomeBanner().getText(), "Welcome, QA User");
    }
}
