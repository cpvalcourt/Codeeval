/*
 * Codeeval Capitalize Challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.awt.geom.Line2D;

/**
 * 
 * @author cpvalcourt
 */
public class Main {

	/*
	 * This class creates a set of combinations for the bridges, based on number of bridges
	 * Instead of coming up with this algorithm myself, I've copied/borrowed it from
	 * http://kosbie.net/cmu/spring-10/15-190-mini/handouts/Combinations.java, which does a
	 * pretty decent job....The rest of the code is my own
	 */
	class Combination {
		private int n, r;
		private int[] index;
		private boolean hasNext = true;

		public Combination(int n, int r) {
			this.n = n;
			this.r = r;
			index = new int[r];
			for (int i = 0; i < r; i++)
				index[i] = i;
		}

		public boolean hasNext() {
			return hasNext;
		}

		private void moveIndex() {
			int i = rightmostIndexBelowMax();
			if (i >= 0) {
				index[i] = index[i] + 1;
				for (int j = i + 1; j < r; j++)
					index[j] = index[j - 1] + 1;
			} else
				hasNext = false;
		}

		public int[] next() {
			if (!hasNext)
				return null;
			int[] result = new int[r];
			for (int i = 0; i < r; i++)
				result[i] = index[i];
			moveIndex();
			return result;
		}

		private int rightmostIndexBelowMax() {
			for (int i = r - 1; i >= 0; i--)
				if (index[i] < n - r + i)
					return i;
			return -1;
		}
	}  // End Combinations

	public class Coordinate {
		public Float x;
		public Float y;

		public Coordinate(Float x, Float y) {
			this.x = x;
			this.y = y;
		}
	}

	public class Bridge {
		public Integer bNumber;
		public Coordinate coor1;
		public Coordinate coor2;

		public Bridge(Integer numb, Coordinate c1, Coordinate c2) {
			bNumber = numb;
			coor1 = c1;
			coor2 = c2;
		}
	}

	/*
	 * Use Line2D package to calculate if two line segments intersect
	 */
	public boolean doesIntersect(Bridge b1, Bridge b2) {
		Line2D line1 = new Line2D.Float(b1.coor1.x, b1.coor1.y, b1.coor2.x, b1.coor2.y);
		Line2D line2 = new Line2D.Float(b2.coor1.x, b2.coor1.y, b2.coor2.x, b2.coor2.y);
		boolean result = line2.intersectsLine(line1);
		return result;
	}
	
	/*
	 * FindMaxIntersections starts with Max number of bridges and counts backward
	 * using a set of combinations (generated indexes using Combinations class).
	 * Once we find a set of bridges that don't have any intersections we are 
	 * done.  It would be really inefficient to go from 1 to Max
	 */
	public static void findMaxIntersection(List<Bridge> bridges, Main b) {
		List<Bridge> testBridge;
		boolean notFound = true;
		for (int i = bridges.size(); i > 0; i--) {
			Combination c = b.new Combination(bridges.size(), i);
			while (c.hasNext() && notFound) {
				int[] bIndexes = c.next();
				notFound = true;
				testBridge = new ArrayList<Bridge>(bIndexes.length);
				for (int j = 0; j < bIndexes.length; j++) {
					testBridge.add(b.new Bridge(bridges.get(bIndexes[j]).bNumber, bridges
							.get(bIndexes[j]).coor1, bridges.get(bIndexes[j]).coor2));
				}
				boolean noIntersect = true;
				for (int k = 0; k < testBridge.size() && noIntersect; k++) {
					for (int l = k + 1; l < testBridge.size() && noIntersect; l++) {
						if (b.doesIntersect(testBridge.get(k),
								testBridge.get(l))) {
							noIntersect = false;
						}
					}
				}
				if (noIntersect) { // Eureka
					for (int m = 0; m < testBridge.size(); m++) {
						System.out.println(testBridge.get(m).bNumber);
					}
					notFound = false;
				}
			}
		}
	}

	public static void main(String[] args) {
		try {
			String line;
			String[] CoordSet;
			String[] coords;
			String tmpCoords;
			int tmpBN;
			Coordinate tmpC1;
			Coordinate tmpC2;
			List<Bridge> bridges = new ArrayList<Bridge>();
			Main x = new Main();

			// Get File
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				line.trim();
				if (line.length() > 0) {
					String[] lineArray = line.split(":");
					// First part is bridge number
					tmpBN = Integer.parseInt(lineArray[0]);

					// Second part is coordinates
					// trim and remove outside parentheses and bracket
					// coordinates separate by '], ['
					tmpCoords = lineArray[1].trim().substring(2,
							lineArray[1].length() - 3);
					CoordSet = tmpCoords.split("], \\[");
					coords = CoordSet[0].split(",");
					tmpC1 = x.new Coordinate(Float.parseFloat(coords[0]),
							Float.parseFloat(coords[1]));
					coords = CoordSet[1].split(",");
					tmpC2 = x.new Coordinate(Float.parseFloat(coords[0]),
							Float.parseFloat(coords[1]));
					bridges.add(x.new Bridge(tmpBN, tmpC1, tmpC2));
				}
			}
			Main.findMaxIntersection(bridges, x);
			in.close();
		} catch (IOException | NumberFormatException e) {
			System.out.println("Exception: " + e.getMessage());
		}
	}
}
