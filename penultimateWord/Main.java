package codeval.penultimateWord;


/**
 * Codeeval challenge: Write a program which finds the next-to-last word in a string.
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Main {

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
			while ((line = in.readLine().trim()) != null) {
				if (line.length() > 0) {
					words = line.split("\\s");
					System.out.println(words[words.length-1]);
				}
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}