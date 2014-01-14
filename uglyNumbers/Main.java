
/**
 * Codeeval Ugly Numbers Challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Main {

	private static int uglyCount;

	/**
	 * Check for ugliness
	 * @param currentSum
	 * @return true if divisible by a one digit prime number
	 */
	public static void isUgly(long currentSum) {
		// 2, 3, 5 or 7
		if (currentSum % 2 == 0 || currentSum % 3 == 0 || currentSum % 5 == 0
				|| currentSum % 7 == 0) {
			uglyCount++;
		}
		return;
	}

	/**
	 * Recursively build up add and subtract operations of all permutations of the full string
	 * of digits and check ugly factor once all digits used.
	 * 
	 * @param currNum first part of number to operate on
	 * @param bAdd is the next op an addition, false if not
	 * @param full full string of digits
	 * @param currentSum current sum so far, checked if all digits use
	 * @param currIndx index within full string
	 */
	private static void Recurse(long currNum, boolean bAdd, String full, long currentSum,
			int currIndx) {
		long nextNumber;
		long newCurSum;
		String nextDigit;
		long nextValue;
		// If we haven't used all the digits, keep recursing
		if (currIndx != full.length()) {
			nextDigit = String.valueOf(full.charAt(currIndx));
			nextValue = Long.valueOf(nextDigit);
			// shift left by multiplying by 10 and adding new ones digit
			nextNumber = nextValue + (10 * Math.abs(currNum));
			if (bAdd)
				newCurSum = (currentSum - currNum) + nextNumber;
			else
				newCurSum = (currentSum + currNum) - nextNumber;
			
			// Recurse with same operation
			Recurse(nextNumber, bAdd, full, newCurSum, currIndx + 1);
			newCurSum = currentSum + nextValue;
			// Recurse with addition
			Recurse(nextValue, true, full, newCurSum, currIndx + 1);
			newCurSum = currentSum - nextValue;
			// Recurse with subtraction
			Recurse(nextValue, false, full, newCurSum, currIndx + 1);
		}
		else { // otherwise check for ugliness
			isUgly(currentSum);
		}
		return;
	}

	public static void main(String[] args) {
		String line;
		long startNum;
		long sum;

		try {
			// Get File
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			// Read each line
			while ((line = in.readLine()) != null) {
				String[] lineArray = line.split(",");
				uglyCount = 0;
				String curr = lineArray[0].trim();
				if (curr.length() > 0) {
					startNum = Long.valueOf(curr.substring(0, 1));
					sum = startNum;
					Recurse(startNum, true, curr, sum, 1);
				}
				System.out.println(uglyCount);
			}
			in.close();
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}

	}
}
