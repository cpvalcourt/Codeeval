/*
 * Codeeval challenge: program to read a multiple line text file and write the 'N' longest lines to stdout
 */

package codeval.longestLines;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

/**
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
        try {
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            String nextLine;
            List<String> linesRead = new ArrayList<>();
            line = in.readLine();
            // Keep array of [Index of String Array,Length]
            int lengthOfResult = Integer.parseInt(line);
            Integer[][] longest = new Integer[lengthOfResult][2];

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
                if (line.trim().length() > 0) {
                    linesRead.add(line.trim());
                }
            }

            // Initialize the first N line lengths into longest
            // Track Index that holds the shortest Length pointer
            int shortestLenIndex = 0;
            for (int i = 0; i < lengthOfResult; i++) {
                longest[i][0] = i;
                longest[i][1] = linesRead.get(i).length();
                if (longest[i][1] < longest[shortestLenIndex][1]) {
                    shortestLenIndex = i;
                }
            }

            for (int k = lengthOfResult; k < linesRead.size(); k++) {
                nextLine = linesRead.get(k);
                if (nextLine.length() > longest[shortestLenIndex][1]) {  // Only if it's longer than the shortest entry
                    // Replace the shortest with new and recalculate shortestIndex
                    longest[shortestLenIndex][0] = k;
                    longest[shortestLenIndex][1] = nextLine.length();
                    shortestLenIndex = 0;  // Reset to 0 and calculate again
                    for (int j = 0; j < longest.length; j++) {
                        if (longest[j][1] < longest[shortestLenIndex][1]) {
                            shortestLenIndex = j;
                        }
                    }
                }
            }
            // Sort the longest[][] by [][1] - the Length
            int temp;
            for (int i=0; i<longest.length ; i++) {
                for (int j=i+1; j<longest.length; j++) {
                    if (longest[i][1] < longest[j][1]) { // swap them
                        temp = longest[i][0];
                        longest[i][0] = longest[j][0];
                        longest[j][0] = temp;
                        temp = longest[i][1];
                        longest[i][1] = longest[j][1];
                        longest[j][1] = temp;                     
                    }
                }
            }
            // Output linesRead using longest array 'index'
            for (int i = 0; i < lengthOfResult; i++) {
                System.out.println(linesRead.get(longest[i][0]));
            }
        } catch (Exception e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
