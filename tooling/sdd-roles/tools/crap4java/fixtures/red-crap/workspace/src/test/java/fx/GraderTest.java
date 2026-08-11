package fx;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class GraderTest {
    @Test
    public void addsNumbers() {
        assertEquals(5, new Grader().add(2, 3));
    }
}
