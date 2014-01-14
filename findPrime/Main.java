/**
 * Codeeval challenge: Print out the prime numbers less than a given number N.
 */
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.Arrays;

/**
* @author cpvalcourt
*/
public class Main {
	Boolean[] isPrime;

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
		StringBuffer result = new StringBuffer();

		// Get File
		File file;
		BufferedReader in;
		// LOCAL_TEST = true;// comment it before submitting

		Main x = new Main();
		file = new File(args[0]);

		try {
			in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList

			while ((line = in.readLine()) != null) {
				line.trim();
				if (line.length() > 0) {
					maxValue = Integer.parseInt(line);
					x.findPrimes(maxValue);
				}

				Boolean next;
				for (int i = 0; i < maxValue; i++) {
					next = x.isPrime[i];
					if (next) {
						result.append(i);
						result.append(',');
					}										
				}
				result.setLength(result.length() - 1);
				System.out.println(result);
				result = new StringBuffer();
			}

		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}