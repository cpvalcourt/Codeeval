import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Write a program implementing a stack inteface for integers.The interface
 * should have 'push' and 'pop' functions. You will be asked to 'push' a series
 * of integers and then 'pop' and print out every alternate integer.
 * 
 * @author cpvalcourt
 * 
 */
public class Main {
	static List<Integer> Q;
	static int top;

	public Main() {
		top = 0;
		Q = new ArrayList<Integer>(20);
	}

	public void push(Integer on) {
		Q.add(on);
		top = top + 1;
	}

	public Integer pop() throws ArrayIndexOutOfBoundsException {
		top = top - 1;
		return (Integer) Q.get(top);
	}

	public static void main(String... args) {
		String line;
		Integer dummy;
		String[] values;
		try {
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			while ((line = in.readLine()) != null) {
				if (line.trim().length() > 0) {
					Main stack = new Main();
					values = line.split("\\s");
					for (String nextValue : values) {
						stack.push(Integer.parseInt(nextValue));
					}
					try {
						while (true) {
							System.out.print(stack.pop() + " ");
							dummy = stack.pop();
						}
					} catch (ArrayIndexOutOfBoundsException bE) {
						dummy = 0;
					}
					System.out.println();
				}
			}
			in.close();
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}
	}
}
