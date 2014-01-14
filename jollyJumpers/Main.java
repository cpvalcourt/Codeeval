
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.BitSet;


/**
 * A sequence of n > 0 integers is called a jolly jumper if the absolute values of the 
 * differences between successive elements take on all possible values 1 through n - 1. eg.
 * 1 4 2 3 
 * is a jolly jumper, because the absolute differences are 3, 2, and 1, respectively. 
 * The definition implies that any sequence of a single integer is a jolly jumper. 
 * Write a program to determine whether each of a number of sequences is a jolly jumper. 
 * @author cpvalcourt
 *
 */
public class Main {
	
	public static void main(String[] args) {
		String line;
		BitSet tracker;
		String[] input;
		Integer[] values;
		Main x = new Main();

		// Get File
		File file = new File(args[0]);
		BufferedReader in;
		try {
			in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				line.trim();
				if (line.length() > 0) {
					input = line.trim().split("\\s");
					values = new Integer[Integer.parseInt(input[0])];
					int numbValues = Integer.parseInt(input[0]);
					tracker = new BitSet(numbValues-1);
					tracker.clear();
					boolean isGood = true;
					if (numbValues == input.length -1) {
						for (int i=0;i<numbValues;i++){
							values[i] = Integer.parseInt(input[i+1]);
							if (i != 0) {
								int diff = Math.abs(values[i]-values[i-1]);
								if (diff > 0 && diff < numbValues) {
									tracker.set(diff-1);
								}
								else {
									isGood = false;
								}
							}
						}
					}
					else isGood = false;
					if (isGood) {
						for (int i=0;i<values.length-1;i++) {
							if (!tracker.get(i)) {
								isGood = false;
								break;
							}
						}
					}
					System.out.println(isGood ? "Jolly" : "Not jolly");
				}
				else {
					System.out.println("mmm Not Jolly");
				}
			}
			in.close();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}
