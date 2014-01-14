/*
1 * Reads in an input file of sentences: words separated by a space
 * Outputs the longest word of each line to stdout.  If two words on the line
 * are the same length, it will output the first word of that length
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

/**
 * Object that calculates longest word on each line of an input file Output is
 * the longest word of each line (stdout)
 *
 * @author cpvalcourt
 */
public class Main {

    private String getLongestWord(String inputLine) {
        String[] words = inputLine.split(" ");
        String longest = "";
        return longest;
    }

    public static void main(String[] args) {

        try {
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            String longestWord = "";

            // Read each line
            while ((line = in.readLine()) != null) {
            	if (line.length() == 0) {
            		continue;
            	}
                String[] lineArray = line.split("\\s");
                if (lineArray.length > 0) {
                    for (String nextWord : lineArray) {
                        if (nextWord.length() > longestWord.length()) {
                            longestWord = nextWord;
                        }
                    }
                    // Output to stdout
                    System.out.println(longestWord);
                    longestWord = "";
                }
            }
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
