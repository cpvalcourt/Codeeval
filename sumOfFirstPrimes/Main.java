/**
 * Codeeval Challenge: output sum of the first 1000 prime numbers
 * @author cpvalcourt
 */


import java.util.Arrays;

public class Main {
	boolean[] isPrime;
	int sum = 0;

	public int countPrimes(int max, long nPrimes) {
		int count = 0;
		for (int j = 0; j < max; j++) {
			if (isPrime[j]) {
				count++;
				sum = sum + j;
			}
			if (count == nPrimes) {
				continue;
			}
		}
		return count;
	}

	public void findFirstNPrimes(long nPrimes) {
		int count = 0;
		boolean notFinished = true;
		isPrime = new boolean[9000];
		Arrays.fill(isPrime, true);
		isPrime[0] = false;
		isPrime[1] = false;
		int max = 3;
		int increment = 30;
		while (notFinished) {
			sum = 0;
			for (int i = 2; i < max; i++) {
				for (int j = 2; i * j < max; j++) {
					if (isPrime[j]) {
						isPrime[i * j] = Boolean.FALSE;
					}
				}
			}
			count = countPrimes(max, nPrimes);
			if ( count >= nPrimes) {
				notFinished = false;
			}
			max=max+increment;
			if (count > (max*.95)) increment = 1;
		}
		System.out.println(sum);
	}

	public static void main(String[] args) {

		new StringBuffer();
		Main x = new Main();
		try {
			x.findFirstNPrimes(1000);

		} catch (Exception e) {
			e.printStackTrace();
		}
	}
}