/**
 * Codeeval Challenge: String Rotation - it's almost not fair that I'm doing this in java with the Collections.rotate
 * @author cpvalcourt
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;


public class Main {
	public static void main(String[] args) {
		String line;
		String[] lineArray;
		List<Character> leftList;
		List<Character> rightList;
		boolean notDone = true;

		int rotateCount = 0;

		try {
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			while ((line = in.readLine()) != null) {
				lineArray = line.split(",");
				leftList = new ArrayList<Character>();
				rightList = new ArrayList<Character>();

				for (char charLeft : lineArray[0].toCharArray()) {
					leftList.add(charLeft);
				}
				for (char charRight : lineArray[1].toCharArray()) {
					rightList.add(charRight);
				}
				if (leftList.size() == rightList.size()) {
					while (notDone) {
						Collections.rotate(rightList, 1);
						rotateCount = rotateCount + 1;
						if (leftList.equals(rightList)) {
							notDone = false;
							System.out.println("True");
						} else if (rotateCount > leftList.size()) {
							notDone = false;
							System.out.println("False");
						}
					}
				}
				notDone = true;
				rotateCount = 0;
			}
			in.close();
		} catch (IOException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}

	}
}
