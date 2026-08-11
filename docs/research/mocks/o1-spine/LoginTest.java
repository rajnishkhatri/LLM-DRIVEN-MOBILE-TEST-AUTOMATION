package com.bank.tests.login;

import static org.testng.Assert.assertEquals;
import org.testng.annotations.Test;

import com.bank.framework.BaseTest;
import com.bank.pages.HomeScreen;
import com.bank.pages.LoginScreen;

/**
 * ACC-1042: Login with valid credentials shows welcome.
 * Generated from TestCaseIR (irVersion sha:4f2c91e8...) via /generate-test.
 * Reviewed and committed by an engineer; static-gate passed (mvn compile, Checkstyle, locator-manifest).
 */
public class LoginTest extends BaseTest {

    @Test(description = "ACC-1042: Login with valid credentials shows welcome")
    public void loginShowsWelcome() {
        LoginScreen login = new LoginScreen(driver);

        login.usernameField().click();                    // step 0
        login.usernameField().sendKeys(vault("user_qa")); // step 1
        login.passwordField().click();                    // step 2
        login.passwordField().sendKeys(vault("pass_qa")); // step 3
        login.loginButton().click();                      // step 4

        HomeScreen home = new HomeScreen(driver);
        assertEquals(home.welcomeBanner().getText(), "Welcome, QA User"); // step 5
    }
}
