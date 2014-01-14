
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
                    newSentence = new StringBuffer();
                    for (char next : line.toCharArray()) {
                    	if (next > 64 && next < 91) {
                    		next = (char) (next + 32);
                    	}
                    	else if (next > 96 && next < 123) {
                    		next = (char) (next - 32);
                    	}
                    	newSentence.append(next);
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
