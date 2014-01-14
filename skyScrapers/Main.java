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
public class Main {
	
	public class minMaxObj {
		public int min;
		public int max;
		public int height;
		
		public minMaxObj(int min, int max, int height) {
			this.min = min;
			this.max = max;
			this.height = height;
		}
	}
	
	static List<minMaxObj> buildings;
	List<Integer> maxHeight;
	private int minx;
	public int maxx;
	
	public void createMaxHeightList(List<minMaxObj> buildings) {
		minMaxObj tmpObj;
		int start, end, height;
		maxHeight = new ArrayList<Integer>(maxx+1);
		for (int i=0;i<maxx+1;i++) maxHeight.add(i,new Integer(0));
		
		for (int i=0;i<buildings.size();i++) {
			tmpObj = buildings.get(i);
			start = tmpObj.min;
			end = tmpObj.max+1;
			height = tmpObj.height;
			
			for (int j=start;j<end-1;j++) {
				
				if (height > maxHeight.get(j)) {
					maxHeight.set(j,  height);
				}
			}
		}
	}
	
	public void outputSkyScraper() {
		StringBuffer newSS = new StringBuffer();
		int currHeight = maxHeight.get(0);
		// Output Starting x,h
		if (currHeight !=0) {
			newSS.append(0).append(" ").append(currHeight).append(" ");
		}
		
		// Iterate over x+1 through end
		// If height changes, output x-i, h
		for (int i=1;i<maxHeight.size();i++) {
			if (currHeight != maxHeight.get(i)) {
				currHeight = maxHeight.get(i);
				newSS.append(i).append(" ").append(currHeight).append(" ");
			}
		}
		System.out.println(newSS.toString().trim());
	}

	public static void main(String[] args) {
        try {
            String line;
            String trimD;
            String currTriplet;
            String[] values;
            int tmpMin=-1;
            int tmpMax=-1;
            int tmpHeight=-1;

            Main x = new Main();
            // Get File
            File file = new File(args[0]);
            BufferedReader in = new BufferedReader(new FileReader(file));

            // Read each line into ArrayList
            while ((line = in.readLine()) != null) {
            	buildings = new ArrayList<minMaxObj>(50);
                line.trim();
                x.minx = -1;
                x.maxx = -1;
                if (line.length() > 0) {              
                    String[] lineArray = line.split(";");  // separate into triplets
                    // For each triplet, trim, then remove start ( and end )              
                    for (String triplet : lineArray) {
                    	trimD = triplet.trim();
                    	currTriplet = trimD.substring(1, trimD.length()-1);
                    	
                    	// Parse each triplet
                    	values = currTriplet.split(",");
                    	tmpMin = Integer.parseInt(values[0]);
                    	tmpMax = Integer.parseInt(values[2]);
                    	
                    	tmpHeight = Integer.parseInt(values[1]);
                    	buildings.add(x.new minMaxObj(tmpMin, tmpMax, tmpHeight));
                    	if (tmpMin == -1 || tmpMin < x.minx) {
                    		x.minx = tmpMin;
                    	}
                    	if (tmpMax > x.maxx){
                    		x.maxx = tmpMax;
                    	}
                    }  
                    x.createMaxHeightList(buildings);
                    x.outputSkyScraper();
                }
            }
            in.close();
        } catch (IOException | NumberFormatException e) {
            System.out.println("File Read Error: " + e.getMessage());
        }
    }
}
