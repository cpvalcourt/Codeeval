/*
 * Codeeval Capitalize Challenge
 */


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
        try {
            String line;
            String[] words;
            StringBuffer newSentence;

            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
                line.trim();
                if (line.length() > 0) {
                    String[] lineArray = line.split("\\s");
                    // First part is input array
                    
                    
                    newSentence = new StringBuffer();
                    for (String word : lineArray) {
                    	newSentence.append(Character.toUpperCase(word.charAt(0))).append(word.substring(1)).append(" ");
                    }
                    System.out.println(newSentence.toString().trim());
                }
            }
        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
