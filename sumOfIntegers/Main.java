package codeval.sumOfIntegers;

/**
 * Codeeval challenge: Write a program which finds the next-to-last word in a string.
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Main {

	/**
	 * Get new array
	 * @param inArray input array
	 * @param count size of array 
	 * @return
	 */
	public static Integer getMaxContSum(List<Integer> inArray, int count) {
		int currentSum = 0;
		int currMax = (Integer) Collections.max(inArray);

		for (int i = 0; i < count; i++) {
			if (currentSum + inArray.get(i) > inArray.get(i))
				currentSum = currentSum + inArray.get(i);
			else
				currentSum = inArray.get(i);
			if (currentSum > currMax) 
				currMax = currentSum;
		}
		return currMax;
	}

	public static void main(String[] args) {
		String line;
		String[] numbers;
		List<Integer> values;
		// Get File
		File file;
		BufferedReader in;
		file = new File(args[0]);
		try {
			in = new BufferedReader(new FileReader(file));
			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				if (line.length() > 0) {
					numbers = line.trim().split(",");
					values = new ArrayList<Integer>(numbers.length);
					for (int i=0;i<numbers.length;i++) {
						values.add(Integer.parseInt(numbers[i].trim()));
					}
					System.out.println(getMaxContSum(values, values.size()));
				}
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}