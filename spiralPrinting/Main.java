package codeval.spiralPrinting;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Main {

	public static void main(String[] args) {
		String line;
		String[][] matrix;
		String[] numbers;
		int m,n;

		// Get File
		File file;
		BufferedReader in;
		// LOCAL_TEST = true;// comment it before submitting

		file = new File(args[0]);

		try {
			in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList

			while ((line = in.readLine()) != null) {
				line.trim();
				if (line.length() > 0) {
					String[] lineArray = line.split(";");
					
					m = Integer.parseInt(lineArray[0].trim());
					n = Integer.parseInt(lineArray[1].trim());
					matrix = new String[m][n];
					numbers = lineArray[2].trim().split(" ");;
					for (int i=0;i<numbers.length;i++) {
						matrix[i/m][i%n] = numbers[i];
					}
					for (int i=0;i<m;i++) {
						for (int j=0;j<n;j++) {
							System.out.print(matrix[i][j]);
						}
						System.out.println();
					}
				}
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}

