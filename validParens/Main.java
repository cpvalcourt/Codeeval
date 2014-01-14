
/**
 * Codeeval: Given a string comprising just of the characters (,),{,},[,] determine if it is well-formed or not.
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Stack;

/**
 * @author cpvalcourt
 */
public class Main {
	public static Map<Character, Character> mapper;
	public static void main(String... args) {
		String line;
		Stack<Character> checker;
		try {
			mapper = new HashMap<Character, Character>();
			mapper.put('}', '{');
			mapper.put(']', '[');
			mapper.put(')', '(');
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			while ((line = in.readLine()) != null) {
				
				if (line.trim().length() > 0) {
					checker = new Stack<Character>();
					for (Character next : line.toCharArray()) {
						if (checker.empty()) {
							checker.push(next);
						}
						else {
						    Character onMap = (Character) mapper.get(next);
						    if (onMap != null  && 
						    		checker.peek().compareTo(onMap)==0) {
							    checker.pop();
						    }
						    else {
							    checker.push(next);
						    }
						}
					}
					System.out.println(checker.empty() ? "True" : "False");
				}
				
			}
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}
	}
}