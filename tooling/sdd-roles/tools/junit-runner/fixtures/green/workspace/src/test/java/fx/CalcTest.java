package fx;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class CalcTest {
    @Test
    public void addsNumbers() {
        assertEquals(5, new Calc().add(2, 3));
    }

    @Test
    public void positiveIsDetected() {
        assertTrue(new Calc().isPositive(1));
    }

    @Test
    public void zeroIsNotPositive() {
        assertFalse(new Calc().isPositive(0));
    }
}
