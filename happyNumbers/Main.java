
/*
 * Codeeval happy number challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;

/**
 * 
 *
 * @author cpvalcourt
 */
public class Main {

    public static void main(String[] args) {
    	int factor=10;
    	Integer number;
    	Integer sumOfSquares;
    	ArrayList<Integer> numSeq;
    	
    	try {
        	// Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            // Read each line
            while ((line = in.readLine()) != null) {
            	numSeq = new ArrayList<Integer>();
            	//System.out.print(line + " ");
            	if (line.length() == 0) {
            		continue;
            	}
            	number = Integer.parseInt(line);
            	//System.out.println("orig: " + number);
            	while (!numSeq.contains(number) && number != 1)  {
            		numSeq.add(number);
            		sumOfSquares = 0;
            		factor = 10;
            		//System.out.println("factor: " + factor + " add: " + (int) Math.pow((number%factor),2));
            		sumOfSquares = sumOfSquares + (int) Math.pow((number%factor),2);
            		while (number / factor > 0) {  
            			factor = factor * 10 ;
            			//System.out.println("factor: " + factor + " add: " + (int) Math.pow(((number % factor*10)/factor),2));
            			sumOfSquares = sumOfSquares + (int) Math.pow(((number % factor*10)/factor),2);	
            		}
            		number = sumOfSquares;
            		//System.out.println("result: " + number);
            	}
            	if (number == 1) System.out.println("1");
            	else System.out.println("0");
            	
            }
            in.close();
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
