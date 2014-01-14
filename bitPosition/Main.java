
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
            	String[] lineArray = line.trim().split(",");
            	if (lineArray.length != 3) continue;
            	number = Long.parseLong(lineArray[0].trim());
            	numAsBitString = Long.toBinaryString(number);
            	//System.out.print(numAsBitString + " ");
            	
            	
            	// index of each is strlen - index
            	strlen = numAsBitString.length();
                first = strlen - Integer.parseInt(lineArray[1].trim());
                second = strlen - Integer.parseInt(lineArray[2].trim()); 
                
                
                if (first > -1 && second > -1 && first < strlen && second < strlen && 
                		numAsBitString.charAt(first)==numAsBitString.charAt(second)) {
                	//System.out.print(newSet.get(first) + " " + newSet.get(second));
                	System.out.println("true");
                }
                else {
                	System.out.println("false");
                }
               
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
