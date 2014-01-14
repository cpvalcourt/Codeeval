package codeval.panagram;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.BitSet;

	/**
	 *
	 * @author cpvalcourt
	 */
	public class Main {
		
		/**
		 * Check for alpha character and return BitSet position (0-25)
		 * @param in character to check
		 * @return position in the bitset (0 based) or -1 if not in range
		 */
		public static int alphaBitPos(char in) {
			int i = in;
			if (i>64 && i<91) {
				return i-65;
			}
			else if (i>96 && i<123) {
				return i-97;
			}
			else return -1;
		}

	    public static void main(String[] args) {
	    	BufferedReader in;
	        try {
	            String line;
	            BitSet fillArray;
	            int pos=0;
	            boolean foundOne=false;
	            StringBuffer missLetter;

	            // Get File
	            File file = new File(args[0]);
	            in = new BufferedReader(new FileReader(file));
	            
	            fillArray = new BitSet(26);  // Bit Set of 26 characters, all set to 0
                fillArray.clear();

	            // Read each line into ArrayList
	            while ((line = in.readLine()) != null) {
	                if (line.trim().length() > 0) {
	                    for (char c : line.toCharArray()) {
	                    	pos = Main.alphaBitPos(c);
	                    	if (pos != -1) fillArray.set(pos);
	                    }
	                }
	                // traverse thru bitset to find index of not found letters
	                foundOne = false;
	                missLetter=new StringBuffer();
	                for (int i=0;i<26;i++) {
	                	if (!fillArray.get(i)) {
	                		missLetter.append((char)(i+97));
	                		foundOne = true;
	                	}
	                }
	                if (foundOne) System.out.println(missLetter.toString());
	                else System.out.println("NULL");
	                fillArray.clear();
	            }
	            in.close();
	        } catch (IOException | NumberFormatException e) {
	            System.out.println("File Read Error: " + e.getMessage());
	        }
	    }
}
