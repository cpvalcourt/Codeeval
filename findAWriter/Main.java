package codeval.findAWriter;

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
		String[] input;
		String writer;
		String[] key;

		// Get File
		File file;
		BufferedReader in;
		StringBuffer output=null;
		file = new File(args[0]);
		try {
			in = new BufferedReader(new FileReader(file));
			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				line.trim();
				if (line.length() > 0) {
					input = line.split("\\|");
					writer = input[0];
					key = input[1].trim().split(" ");
					output=new StringBuffer("");
					for (String next : key) {
						output.append(writer.charAt(Integer.parseInt(next.trim())-1));
					}
				}
				System.out.println(output.toString());
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}
