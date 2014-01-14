

/*
 * Codeeval sum of digits challenge
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
    	String numbers;
    	int result;
    	
        try {
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            // Read each line
            while ((line = in.readLine()) != null) {
            	if (line.length() == 0) {
            		continue;
            	}
            	numbers = line.trim();
            	result = 0;
   
            	for (int i=0;i<numbers.length();i++) {
            		result = result + Integer.parseInt(numbers.substring(i,i+1));
            	}
            	
            	
                System.out.println(result);
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
