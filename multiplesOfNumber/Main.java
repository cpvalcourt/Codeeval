package codeval.multiplesOfNumber;

/*
 * Codeeval multiples of a number challenge
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
    	String[] inputs;
    	int result, increment;
    	int max;
    	
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
            	inputs = line.trim().split(",");
            	max = Integer.parseInt(inputs[0]);
            	result = 0;
            	increment = Integer.parseInt(inputs[1]);
            	while (result < max) result = result + increment;
            	
                System.out.println(result);
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
