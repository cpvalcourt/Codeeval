
/*
1 * Codeeval bit position challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.BitSet;

/**
 * 
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
    	Integer first, second;
    	Long number;
    	int count;
    	int strlen;
    	String numAsBitString;
    	try {
        	// Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            // Read each line
            while ((line = in.readLine()) != null) {
            	//System.out.print(line + " ");
            	if (line.length() == 0) {
            		continue;
            	}
            	count = 0;
            	number = Long.parseLong(line.trim());
            	numAsBitString = Long.toBinaryString(number);
            	strlen = numAsBitString.length();
            	for (char next : numAsBitString.toCharArray()) {
            		if (next == '1') count++;
            	}
            	System.out.println(count);             
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
