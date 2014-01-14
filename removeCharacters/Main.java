
/*
1 * Codeeval removeCharacters challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;

/**
 * Object that calculates longest word on each line of an input file Output is
 * the longest word of each line (stdout)
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
    	char[] toRemove;
    	String removeWord;
    	String sentence;
    	String[] words;
    	int charIndex;
    	StringBuffer result=null;
    	ArrayList<Character> tempWordChars=null;
    	
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
            	
            	String[] lineArray = line.trim().split(",");
                sentence = lineArray[0];
                removeWord = lineArray[1];
                toRemove = removeWord.trim().toCharArray();         
                words = sentence.trim().split("\\s");
                if (words.length > 0) {
                	result = new StringBuffer();
                    for (String nextWord : words) { 
                    	
                        for (char nextC : toRemove) {
                        	charIndex = 0;
                        	while (charIndex != -1 && nextWord.length() > 0) {
                        		charIndex = tempWordChars.indexOf(nextC);
                        		if (charIndex != -1) {		
                        			tempWordChars.remove(charIndex);
                        		}
                        	}
                        }
                        for (char next : tempWordChars) {
                        	result.append(next);
                        }
                        result.append(" ");
                    }
                    
                    
                }
                System.out.println(result.toString().trim());
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
