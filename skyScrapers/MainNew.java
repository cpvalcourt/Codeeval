package codeval.skyScrapers;
/*
 * Codeeval SkyScraper Challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 *
 * @author cpvalcourt
 */
public class MainNew {
	
	public class Coordinate {
		public int x;
		public int y;
		
		public Coordinate(int x, int y) {
			this.x = x;
			this.y = y;
		}
	}
	
	public static List<Coordinate> shape;
	
	public boolean isSquare() {

	}

	public static void main(String[] args) {
        try {
            String line;
            String currPt, trimPt;
            int x, y;
            int ptIndx=0;
            String[] values;

            MainNew myObj = new MainNew();
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
            	shape = new ArrayList<Coordinate>(4);
                if (line.length() > 0) {              
                    String[] lineArray = line.split(",");  // separate into triplets
                    // For each triplet, trim, then remove start ( and end )              
                    for (String sPoint : lineArray) {
                    	trimPt = sPoint.trim();
                    	currPt = trimPt.substring(1, trimPt.length()-1);
                    	
                    	// Parse each triplet
                    	values = currPt.split(",");
                    	x = Integer.parseInt(values[0]);
                    	y = Integer.parseInt(values[1]);
                    	MainNew.shape.set(ptIndx, new Coordinate(x,y));
                    	ptIndx++;
                    }     
                    System.out.println("Points: " + MainNew.shape);
                }
            }
            in.close();
        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
