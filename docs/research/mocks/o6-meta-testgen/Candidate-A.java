package com.bank.tests.login;

import static org.testng.Assert.assertEquals;
import org.testng.annotations.Test;

import com.bank.framework.BaseTest;
import com.bank.pages.HomeScreen;
import com.bank.pages.LoginScreen;

/**
 * ACC-1042 candidate A — ensemble generation #1.
 * Uses accessibility-ids from the object repo; clean waits; no Thread.sleep.
 */
public class LoginTestCandidateA extends BaseTest {

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
