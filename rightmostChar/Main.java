
/*
1 * Codeeval rightmost Character index challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

/**
 * 
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
    	char toRemove;
    	String sentence;
    	boolean found=false;
    	
    	
        try {
        	char[] cArray;
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            // Read each line
            while ((line = in.readLine()) != null) {
            	if (line.length() == 0) {
            		continue;
            	}
            	String[] lineArray = line.trim().split(",");
            	if (lineArray.length != 2) continue;
                sentence = lineArray[0].trim();
                toRemove = lineArray[1].trim().charAt(0);
                cArray = sentence.trim().toCharArray();
                found=false;
                for (int i=cArray.length-1;i>-1;i--) {          
                	if (cArray[i] == toRemove) {
                		System.out.println(i);
                		found=true;
                		break;
                	}
                } 
                if (!found) System.out.println(0-1);
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
