package com.bank.tests.login;

/**
 * ACC-1042 candidate C — ensemble generation #3.
 * Intended to add a "login then logout" flow for extra coverage, but the logout step
 * references a page object (LogoutScreen) that does not exist in the repo — compile failure.
 * The deterministic filter discards this at the static gate; no device time spent.
 */
public class LoginTestCandidateC {

    public void loginThenLogout() {
        // ... login steps ...
        new com.bank.pages.LogoutScreen(driver).logoutButton().click(); // COMPILE ERROR — type unresolved
    }
}
