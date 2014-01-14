
/**
 * Codeeval challenge: sorted sets
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashSet;
import java.util.TreeSet;

public class Main {

	public static void main(String[] args) {
		String line;
		String[] lineArray;
		String[] left;
		String[] right;
		// I'm using a TreeSet here, but this could be done with a simple array
		// as well
		// why? I wanted to use a Set...I never get to use those
		TreeSet<Integer> leftSet;
		HashSet<Integer> rightSet;
		StringBuffer output;

		try {
			// Get File
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			// Read each line
			while ((line = in.readLine()) != null) {
				output = new StringBuffer();
				lineArray = line.split(";");
				left = lineArray[0].split(",");
				right = lineArray[1].split(",");
				leftSet = new TreeSet<Integer>();
				rightSet = new HashSet<Integer>();
				for (String nextLeft : left) {
					leftSet.add(Integer.parseInt(nextLeft));
				}
				for (String nextRight : right) {
					rightSet.add(Integer.parseInt(nextRight));
				}
				// for every element in Left
				for (Integer nextLeft : leftSet) {
					if (rightSet.contains(nextLeft)) {
						output.append(nextLeft + ",");
					}
				}
				if (output.length() > 1)
					output.setLength(output.length() - 1);
				System.out.println(output.toString());
			}
			in.close();
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}

	}
}
