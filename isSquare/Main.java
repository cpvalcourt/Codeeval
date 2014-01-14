

/*
 * Codeeval FInd a Square Challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 *
 * @author cpvalcourt
 */
public class Main {
	
	public class Coordinate {
		public int x;
		public int y;
		
		public Coordinate(int x, int y) {
			this.x = x;
			this.y = y;
		}
	}
	
	public static List<Coordinate> shape;
	
	public Main() {
		shape = new ArrayList<Coordinate>(4);
	}
	
	public List<Coordinate> getShape() {
		return shape;
	}
	
	public boolean isSquare() {
		Double[] ds = new Double[6];
		int index=0;
		boolean match4=false;
		boolean match2=false;
		int match4Index=0;
		int match2Index=0;
		DecimalFormat df = new DecimalFormat("#.#####");
		// Find the Six Distances between all points
		// 4 of them should be the same, the other two should be
		// that same distance * sqrt(2)
		for (int i=0;i<4;i++) {
			for (int j=i+1;j<4;j++) {
				ds[index] = (double) Math.sqrt((shape.get(i).x-shape.get(j).x)*
						(shape.get(i).x-shape.get(j).x) + 
						(shape.get(i).y-shape.get(j).y) *
						(shape.get(i).y-shape.get(j).y));
				index++;
			}
		}
		for (int j=0;j<6;j++) {
			if (Collections.frequency(Arrays.asList(ds), ds[j]) == 4) { 
				match4=true;
				match4Index = j;
			}
			else if (Collections.frequency(Arrays.asList(ds),  ds[j]) == 2) {
				match2 = true;
				match2Index = j;
			}
		}
		if (match2 && match4) {			
			if ((df.format(ds[match4Index]*Math.sqrt(2.0))).compareTo(df.format(ds[match2Index])) == 0) {
				return true;
			}
		}
		
		return false;
	}

	public static void main(String[] args) {
        try {
            String line;
            String currPt, trimPt;
            int x, y;
            int ptIndx=0;
            String[] values;
            Main myObj;

            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
            	myObj = new Main();
                if (line.length() > 0) {   
                	ptIndx = 0;
                    String[] lineArray = line.split(", ");  // separate into triplets
                    // For each coordinate pair, trim, then remove start ( and end )              
                    for (String sPoint : lineArray) {
                    	trimPt = sPoint.trim();
                    	currPt = trimPt.substring(1, trimPt.length()-1);
                    	
                    	// Parse each coordinate
                    	values = currPt.split(",");
                    	x = Integer.parseInt(values[0]);
                    	y = Integer.parseInt(values[1]);
                    	myObj.getShape().add(ptIndx, myObj.new Coordinate(x,y));
                    	ptIndx++;
                    }  
                    System.out.println(myObj.isSquare());
                }
            }
            in.close();
        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
