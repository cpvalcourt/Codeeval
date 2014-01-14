
/**
 * Codeeval challenge: You are given two strings 'A' and 'B'. Print out a 1 if string 'B' occurs at the end of string 'A'. Else a zero.
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Main {

	/**
	 * Get new array
	 * @param inArray input array
	 * @param count size of array 
	 * @return
	 */
	public static boolean isLastPartOfString(String one, String two) {
		int start = one.length() - two.length();
		int end = start + two.length();
		if (start < 0 || end > Math.max(one.length(), two.length()) || end < 0) return false;
		String sub = one.substring(start,  end);
		
		boolean isFound = (sub.compareTo(two)==0) ? true : false;
		return (isFound);
	}

	public static void main(String[] args) {
		String line;
		String[] words;
		// Get File
		File file;
		BufferedReader in;
		file = new File(args[0]);
		try {
			in = new BufferedReader(new FileReader(file));
			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				if (line.length() > 0) {
					words = line.trim().split(",");
					System.out.println(isLastPartOfString(words[0], words[1]) ? "1" : "0");
				}
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}