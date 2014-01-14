

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
		isPrime = new Boolean[(int) maxValue+1];
		Arrays.fill(isPrime, Boolean.TRUE);
		isPrime[0] = false;
		isPrime[1] = false;
		for (int i = 2; i < maxValue+1; i++) {
			for (int j = 2; i * j < maxValue+1; j++) {
				if (isPrime[j]) {
					isPrime[i * j] = Boolean.FALSE;
				}
			}
		}
	}

	public static void main(String[] args) {

		String line;
		String[] values;
		Integer max = 0;
		Integer min = 0;
		int count = 0 ;

		Main x = new Main();

		try {
			// Get File
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				if (line.trim().length() > 0) {
					values = line.split(",");
					min = Integer.parseInt(values[0]);
					max = Integer.parseInt(values[1]);
					x.findPrimes(max);
				}
				//System.out.print(min + " to " + max + ": ");
				for (int i=min;i<max+1;i++) {
					if (x.isPrime[i])  {
						//System.out.print(i + ",");
						count++;
					}
				}
				//System.out.println(" - " + count);
				System.out.println(count);
				count = 0;
			}
			in.close();
		} catch (IOException ioE) {
			System.out.println(ioE.getMessage());
		}

	}
}