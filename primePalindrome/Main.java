

import java.util.Arrays;

/**
 * @author cpvalcourt
 */
public class Main {
	Boolean[] isPrime;

	/**
	 * Reverse in Long value
	 * 
	 * @param input
	 *            long to reverse
	 * @return reversed result
	 */
	public static Long reverseInt(Long input) {
		String reversed = new StringBuilder(input.toString()).reverse()
				.toString();
		return Long.parseLong(reversed);
	}

	/**
	 * Check input to see if it's a Palindrome by converting to String, making a
	 * copy, reversing the copy and comparing the strings to see if same
	 * 
	 * @param intValue
	 *            value to check palindrome pattern
	 */
	public static boolean isPanlindrome(Long intValue) {
		String reversedString = reverseInt(intValue).toString();
		return (reversedString.compareTo(intValue.toString()) == 0);
	}

	public void findPrimes(long maxValue) {
		isPrime = new Boolean[(int) maxValue];
		Arrays.fill(isPrime, Boolean.TRUE);
		isPrime[0] = false;
		isPrime[1] = false;
		for (int i = 2; i < maxValue; i++) {
			for (int j = 2; i * j < maxValue; j++) {
				if (isPrime[j]) {
					isPrime[i * j] = Boolean.FALSE;
				}
			}
		}
	}

	public static void main(String[] args) {

		String line;
		long maxValue = 0;
		boolean notFound = true;
		StringBuffer result = new StringBuffer();

		Main x = new Main();

		x.findPrimes(1000);
		for (int i=999;i>0;i--) {
			if (x.isPrime[i]) {
				if (x.isPanlindrome((long) i)) {
					System.out.println(i);
					break;
				}
			}

		}
	}
}