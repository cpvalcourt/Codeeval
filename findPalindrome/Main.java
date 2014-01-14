/*
 * The problem is as follows: choose a number, reverse its digits and add it to the original. 
 * If the sum is not a palindrome, repeat this procedure.
 */

package codeval.findPalindrome;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

/**
 *
 * @author cpvalcourt
 */
public class Main {

    /**
     * Reverse in Long value
     *
     * @param input long to reverse
     * @return reversed result
     */
    public static Long reverseInt(Long input) {
        String reversed = new StringBuilder(input.toString()).reverse().toString();
        return Long.parseLong(reversed);
    }

    /**
     * Check input to see if it's a Palindrome by converting to String,
     * making a copy, reversing the copy and comparing the strings to see if same
     *
     * @param intValue value to check palindrome pattern
     */
    public static boolean isPanlindrome(Long intValue) {
        String reversedString = reverseInt(intValue).toString();
        return (reversedString.compareTo(intValue.toString()) == 0);
    }

    public static void main(String[] args) {
        try {
            String line;
            boolean pFound = false;
            Long addResult;
            int count = 0;  // number of adds to find palindrome
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
                addResult = Long.parseLong(line.trim());
                while (!pFound) {
                    pFound = isPanlindrome(addResult);
                    if (!pFound) {
                        addResult += reverseInt(addResult);
                        count++;
                    }
                }
                System.out.println(count + " " + addResult);
                pFound = false;
                count = 0;
            }

        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}