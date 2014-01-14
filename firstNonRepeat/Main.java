
/**
 * Codeeval: Write a program to find the first non repeated character in a string.
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.ArrayList;

/**
 * @author cpvalcourt
 */
public class Main {
	public static void main(String[] args) {
		try {
			String line;
			List<Character> repeatChars;
			List<Character> nonRepeatChars;
			;
			StringBuffer newSentence;

			// Get File
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				line.trim();
				repeatChars = new ArrayList<Character>(line.length());
				nonRepeatChars = new ArrayList<Character>(line.length());
				if (line.length() > 0) {
					for (Character next : line.toCharArray()) {
						if (!repeatChars.contains(next)) {
							if (nonRepeatChars.contains(next)) {
								repeatChars.add(next);
								nonRepeatChars.remove(next);
							} else {
								nonRepeatChars.add(next);
							}
						}
					}
				}
				System.out.println(nonRepeatChars.get(0));
			}
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}
	}
}