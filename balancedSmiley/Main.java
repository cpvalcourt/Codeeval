

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
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Stack;

/**
 * @author cpvalcourt
 */
public class Main {
	public static Map<Character, Character> mapper;
	public static List<Character> parens;
	public static void main(String... args) {
		String line;
		String newLine;
		Stack<Character> checker;
		Character previous=0;
		try {
			mapper = new HashMap<Character, Character>();
			parens = new ArrayList<Character>(2);
			mapper.put(')', '(');
			parens.add('(');
			parens.add(')');
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			while ((line = in.readLine()) != null) {
				newLine = new String("");
				if (line.length() > 0) {
					//System.out.println("Before: " + line);
					//newLine = line.replaceAll(":\\)", "  ");
					//line = newLine.replaceAll(":\\(", "  ");
					//System.out.println(" After: " + line);
					checker = new Stack<Character>();
					char[] newArray = line.toCharArray();
					// Remove all non smiley and parens
					for (Character next : newArray) {
						if (parens.contains(next) || next.charValue() == 58) {
							newLine = newLine.concat(next.toString());
						}
						else {
							newLine = newLine.concat(" ");
						}
					}
					//System.out.println(" After: " + newLine);
					// Check without smiley filtering				
					for (int i=0;i<newLine.length();i++) {
						Character next = newArray[i];
						if (checker.empty() && parens.contains(next)
								&& previous.charValue() != 58) {
							//System.out.print(",push-" + next);
							checker.push(next);
						}
						else {
						    Character onMap = (Character) mapper.get(next);
						    if (onMap != null  && checker.size() > 0 &&
						    		checker.peek().compareTo(onMap)==0
						    		&& (previous.charValue() != 58 || (i+1) == line.length())) {
						    	//System.out.print(",pop-" + checker.peek());
							    checker.pop();
						    }
						    else {
						    	if (parens.contains(next)
						    			&& previous.charValue() != 58) {
						    		//System.out.print(",push-" + next);
						    		checker.push(next);
						    	}
						    	else {
						    		//System.out.print(",ignore-"+next);
						    	}
						    }
						}
						previous = next;
					}
					System.out.println(checker.empty() ? "YES" : "NO");

				}
				else System.out.println("YES");
				
			}
			in.close();
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}
	}
}