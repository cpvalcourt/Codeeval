

/**
 * Codeeval Challenge: String Substitution: 
 * Given a string S, and a list of strings of positive length, F1,R1,F2,R2,...,FN,RN, 
 * proceed to find in order the occurrences (left-to-right) of Fi in S and replace them 
 * with Ri. All strings are over alphabet { 0, 1 }. Searching should consider only contiguous 
 * pieces of S that have not been subject to replacements on prior iterations. An iteration 
 * of the algorithm should not write over any previous replacement by the algorithm.
 *
 * 10011011001;0110,1001,1001,0,10,11
 * 11100110
 * @author cpvalcourt
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.BitSet;
import java.util.List;

public class Main {
	public static void main(String[] args) {
		String line;
		String[] inputs;
		String left;
		String temp;
		String right;
		List<String> rightList;
		int startIndex = 0;
		int lastIndex = 0;
		BitSet trackSub;
		BitSet tmpSub;
		int diff;

		try {
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			while ((line = in.readLine()) != null) {
				//System.out.println(line);
				rightList = new ArrayList<String>();
				inputs = line.split(";");
				left = inputs[0].trim();
				right = inputs[1].trim();
				for (String next : right.trim().split(",")) {
					rightList.add(next);
				}
				trackSub = new BitSet(left.length());
				trackSub.clear();
				// Process two at a time:
				// 1. string to find
				// 2. string to replace
				for (int i = 0; i < rightList.size(); i = i + 2) {
					// Starting at startIndx, look for nextSub
					startIndex = left.indexOf(rightList.get(i).substring(startIndex));
					while (startIndex != -1 ) {
						if (trackSub.get(startIndex, startIndex + rightList.get(i).length()).isEmpty()) {
							temp = new String(left.substring(lastIndex, startIndex) + rightList.get(i + 1)
									+ left.substring(startIndex	+ rightList.get(i).length()));
							left = new String(temp);
							tmpSub = trackSub;
							trackSub = new BitSet(left.length());
							trackSub.clear();
							diff = rightList.get(i).length() - rightList.get(i+1).length();
							for (int j=0;j<startIndex;j++) {
								trackSub.set(j,tmpSub.get(j));
							}
							for (int k=startIndex+rightList.get(i+1).length();k<tmpSub.length()-diff;k++){
								trackSub.set(k,tmpSub.get(k+diff));
							}
							trackSub.set(startIndex,
									startIndex + rightList.get(i + 1).length());
						}
						startIndex = left.indexOf(rightList.get(i), startIndex + 1);
						//startIndex = left.indexOf(rightList.get(i).substring(startIndex));
					}
					startIndex = 0;
				}
				System.out.println(left);
			}
			in.close();
		} catch (IOException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}

	}
};

