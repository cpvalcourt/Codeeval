/*
 * Codeeval Self Describing Numbers: A number is a self-describing number when (assuming digit positions are labeled 0 to N-1), the digit 
 * in each position is equal to the number of times that that digit appears in the number. 
 */


import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
    	Map<Integer, Integer> numberMap;
    	Integer nextInt;
    	
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
            	numberMap = new HashMap<Integer, Integer>(line.length());
            	char[] chars = line.trim().toCharArray();
            	for (char next : chars) {
            		nextInt = next - 48;
            		if (numberMap.containsKey(nextInt)) {
            			numberMap.put(nextInt, numberMap.get(nextInt) + 1);
            		}
            		else {
            			numberMap.put(nextInt, 1);
            		}
            	}
            	boolean isGood = true;
            	
            	for (int i=0;i<chars.length;i++) {
            		if (chars[i]-48 == 0 && numberMap.containsKey(i)) { 
            			isGood = false;
            			break;
            		}
            		else if (chars[i]-48 != 0 && !numberMap.containsKey(i)) {
            			isGood = false;
            			break;
            		}
            		else if (chars[i]-48 != 0 && (chars[i]-48 != numberMap.get(i))) {
            			isGood = false;
            			break;
            		}
            	}
            	
                System.out.println(isGood ? "1" : "0");
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
