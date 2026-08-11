package fx;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;

public class CalcTest {
    @Test
    public void addsNumbers() {
        assertEquals(4, new Calc().add(2, 3));
    }

    @Test
    public void zeroIsNotPositive() {
        assertFalse(new Calc().isPositive(0));
    }
}
