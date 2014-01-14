
/**
 * Codeeval: 
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.Map;

/**
 * @author cpvalcourt
 */
public class Main {
	public static Map<Character, Integer> beauty;

	public static void main(String... args) {
		String line;
		String[] input;
		String[] values;
		String[] results;
		int jump;
		int start;
		int end;

		try {
			
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			while ((line = in.readLine()) != null) {
				// Split over ;
				input = line.split(";");
				jump = Integer.parseInt(input[1]);
				//split first over ,
				values = input[0].split(",");
				results = new String[values.length];
				
				for (int i=0;i<values.length;i=i+jump) {
					start = i;
					end = start + jump - 1;
					
					if (start + jump > values.length) {
						while (start < values.length) {
							results[start] = values[start++];
						}
					}
					else {
						while (start <= end) {
							if (end > values.length-1) end = values.length - 1;
							results[start] = values[end];
							results[end--] = values[start++];
						}
					}
				}
				StringBuffer output = new StringBuffer("");
				for (String next : results) {
					output.append(next + ",");
				}
				System.out.println(output.substring(0, output.length()-1));
			}
			in.close();
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}
	}
}