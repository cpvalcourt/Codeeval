

/**
 * Codeeval challenge: An Armstrong number is an n-digit number that is equal to the sum of the n'th powers of 
 * its digits.  Determine if the input numbers are Armstrong numbers.
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Main {

	public static void main(String[] args) {
		String line;
		String nString;
		int nValue = 0;
		int sum = 0;

		// Get File
		File file;
		BufferedReader in;
		file = new File(args[0]);
		try {
			in = new BufferedReader(new FileReader(file));
			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				line.trim();
				if (line.length() > 0) {
					nString = line.trim();
					nValue = nString.length(); // Number of Digits
					sum = 0;
					for (Character nS : nString.toCharArray()) {
						sum = (int) (sum + Math.pow(
								Integer.parseInt(nS.toString()), nValue));
					}
					System.out.println(sum == Integer.parseInt(nString) ? "True" : "False");
				}
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}
