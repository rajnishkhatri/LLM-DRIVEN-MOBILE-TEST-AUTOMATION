package fx;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class ClampTest {
    @Test
    public void passesSmallValuesThrough() {
        assertEquals(50, new Clamp().clamp(50));
    }
}
