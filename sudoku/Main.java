
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.BitSet;

public class Main {

	public boolean checkBoard(Integer[][] inBoard, int dimen) {
		boolean isValid = true;
		BitSet currRow = new BitSet(dimen);
		BitSet currCol = new BitSet(dimen);
		BitSet currSquare = new BitSet(dimen);

		int squareRt = (int) Math.sqrt(dimen);
		// Check each vertical
		for (int i = 0; i < dimen; i++) {
			currRow.clear();
			currCol.clear();
			for (int j = 0; j < dimen; j++) {
				currRow.set(inBoard[i][j]-1);
				currCol.set(inBoard[j][i]-1);
			}
			for (int k = 0; k < dimen; k++) {
				if (!currRow.get(k) || !currCol.get(k)) {
					isValid = false;
				}
			}
			if (!isValid)
				break;
		}

		// Check each NxN square, left to right, top to bottom
		for (int m = 0; m < squareRt; m++) { // number of squares
			currSquare.clear();		
			for (int i = m/squareRt*squareRt; i < m/squareRt*squareRt+squareRt; i++) {				
				for (int j = m*squareRt; j < m*squareRt+squareRt; j++) {			
					currSquare.set(inBoard[i][j]-1);
				}
			}
			for (int k=0;k<dimen;k++) {
				if (!currSquare.get(k))  {
					isValid = false;
				}
			}
			if (!isValid)
				break;
			currSquare.clear();
		}

		return isValid;
	}

	public static void main(String[] args) {
		String line;
		String[] inputLine;
		Integer[][] board;
		int dimension;

		try {
			// Get File
			File file = new File(args[0]);
			BufferedReader in = new BufferedReader(new FileReader(file));

			// Read each line
			while ((line = in.readLine()) != null) {
				String[] lineArray = line.split(";");
				// initialize NxN array with lineArray[0]
				dimension = Integer.parseInt(lineArray[0]);
				if (lineArray[1].trim().length() == 0) continue;
				inputLine = lineArray[1].trim().split(",");
				board = new Integer[dimension][dimension];
				for (int i = 0; i < dimension; i++) {
					for (int j = 0; j < dimension; j++) {
						board[i][j] = Integer.parseInt(inputLine[i * dimension
								+ j]);						
					}
				}
				Main x = new Main();
				boolean isGood = x.checkBoard(board, dimension);
				System.out.println(isGood ? "True" : "False");
			}
		} catch (IOException | NumberFormatException e) {
			System.out.println("File Read Error: " + e.getMessage());
		}

	}
}
