
/*
 * Codeeval FInd a Square Challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 *
 * @author cpvalcourt
 */
public class Main {
	

	public static void main(String[] args) {
		int curr, div;
		String line;
		String[] values;
        try {
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
                if (line.length() > 0) {  
                	//System.out.println(line);
                    values = line.split(",");  // separate into triplets
                    curr = Integer.parseInt(values[0]);
                    div = Integer.parseInt(values[1]);
                    while (curr+1 > div) {
                    	curr = curr - div;
                    }
                    System.out.println(curr);
                }
            }
            in.close();
        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
