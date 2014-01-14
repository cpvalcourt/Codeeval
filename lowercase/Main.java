
/*
 * Codeeval Capitalize Challenge
 */


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

/**
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
        try {
            String line;
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
                    	newSentence.append(word.toLowerCase()).append(" ");
                    }
                    System.out.println(newSentence.toString().trim());
                }
            }
            in.close();
        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
