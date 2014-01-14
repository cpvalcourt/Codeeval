

/*
1 * Codeeval bit position challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Map.Entry;
import java.util.TreeMap;

/**
 * 
 *
 * @author cpvalcourt
 */
public class Main {
	
	static TreeMap<Integer, Integer> guesses;

    public static void main(String[] args) {
    	Integer first, second;
    	Long number;
    	int strlen;
    	String numAsBitString;
    	boolean found = false;
    	ArrayList<Integer> orig;
    	
    	try {
        	// Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            Integer currVal;
            Integer thisCount=0;
            // Read each line
            while ((line = in.readLine()) != null) {
            	//System.out.print(line + " ");
            	if (line.length() == 0) {
            		continue;
            	}
            	guesses = new TreeMap<Integer, Integer>();
            	orig = new ArrayList<Integer>(line.length());
            	
            	String[] lineArray = line.trim().split(" ");
            	for (String next : lineArray) {
            		currVal = Integer.parseInt(next);
            		orig.add(Integer.parseInt(next));
            		thisCount=0;
            		if (guesses.containsKey(currVal)) {
            			thisCount = (Integer) guesses.get(currVal);
            		}
            		thisCount++;
            		guesses.put(currVal, thisCount);
            	}
            	found = false;
            	for(Entry<Integer, Integer> entry : guesses.entrySet()) {
            		  Integer key = entry.getKey();
            		  Integer value = entry.getValue();
            		  if (value == 1) {
            			  System.out.println(orig.indexOf(key) + 1);
            			  found = true;
            			  break;
            		  }
            	}
            	if (!found) { 
      			  System.out.println("0");
      		  }
               
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
