package codeval.wordSearch;
/*
1 * Reads in an input file of sentences: words separated by a space
 * Outputs the longest word of each line to stdout.  If two words on the line
 * are the same length, it will output the first word of that length
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.BitSet;

/**
 * Object that calculates longest word on each line of an input file Output is
 * the longest word of each line (stdout)
 *
 * @author cpvalcourt
 */
public class Main {
	
	public static char[][] grid = {{'A','B','C','E'},{'S','F','C','S'},{'A','B','C','E'}};
	public static BitSet[] usedGrid;
	public static int minX, minY, maxX, maxY;
	
	public Main() {
		minX = minY = 0;
		maxX = 2;
		maxY = 3;
	}
	
	private void initGrid() {
		usedGrid = new BitSet[3];
		usedGrid[0].clear();
		usedGrid[1].clear();
		usedGrid[2].clear();
	}
	
	public boolean findWord(int x, int y, String in) {
		// Find instance of first letter
		
		// traverse grid to find next letter - recursive
	}

    public static void main(String[] args) {
    	Main x = new Main();
        try {
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line;
            String word;

            // Read each line
            while ((line = in.readLine()) != null) {
            	if (line.length() == 0) {
            		continue;
            	}
                word = line.trim();
                x.initGrid();
                System.out.println(x.findWord(0, 0, word));
                
            }
        } catch (IOException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
