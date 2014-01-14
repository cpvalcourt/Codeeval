
/**
 * Codeeval: A message has balanced parentheses if it consists of one of the following:
 * 
 * - An empty string ""
 * - One or more of the following characters: 'a' to 'z', ' ' (a space) or ':' (a colon)
 *- An open parenthesis '(', followed by a message with balanced parentheses, followed by a close parenthesis ')'.
 *- A message with balanced parentheses followed by another message with balanced parentheses.
 *- A smiley face ":)" or a frowny face ":("
 *
 * Write a program that determines if there is a way to interpret his message while leaving the parentheses balanced.
 *
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @author cpvalcourt
 */
public class Main {
	public static Map<Character, Integer> beauty;

	public static void main(String... args) {
		String line;
		int sum=0;

		try {
			
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			while ((line = in.readLine()) != null) {
				sum = 0;
				beauty = new HashMap<Character, Integer>();
				if (line.length() > 0) {
					for (char c : line.toCharArray()) {
						Character check = Character.toLowerCase(c);
						if (check.charValue() >96 && check.charValue()<123) {
							beauty.put(check,  (beauty.get(check) != null ? beauty.get(check)+1 : 1));
						}
					}
				}
				List<Integer> newList = new ArrayList<Integer>();
				for (Map.Entry<Character, Integer> entry : beauty.entrySet()) {
					newList.add(entry.getValue());
				}

				Collections.sort(newList, new Comparator<Integer>() {

			        @Override
			        public int compare(Integer i1, Integer i2) {
			            return i2 - i1;
			        }
			    });
				
				int val=26;	
				for (Integer next : newList) {
					sum = sum + (val*next);
					val--;
				}
				System.out.println(sum);
			}
			in.close();
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}
	}
}