package fx;

public final class Grader {
    public int add(int a, int b) {
        return a + b;
    }

    /** Complex and untested on purpose: CRAP = 5^2 * (1-0)^3 + 5 = 30 > 6. */
    public String grade(int score) {
        if (score >= 90) {
            return "A";
        }
        if (score >= 80) {
            return "B";
        }
        if (score >= 70) {
            return "C";
        }
        if (score >= 60) {
            return "D";
        }
        return "F";
    }
}
