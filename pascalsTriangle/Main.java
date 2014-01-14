
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Main {

	public static void main(String[] args) {
		String line;
		int passes = 0;
		int elementCount = 1;  // Initialize to 1, increment each pass
		Integer[][] triangle;
		StringBuffer outBuff;

		// Get File
		File file;
		BufferedReader in;

		file = new File(args[0]);

		try {
			in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				line.trim();
				outBuff = new StringBuffer();
				if (line.length() > 0) {
					passes = Integer.parseInt(line);
					// Initialize outside array
					triangle = new Integer[passes][];
					triangle[0] = new Integer[1];
					triangle[0][0] = 1;
					if (passes > 1) {
						for (int i=1;i<passes;i++) {
							elementCount++;
							triangle[i] = new Integer[elementCount];
							for (int j=0;j<elementCount;j++) {
								if (j==0 || j==elementCount-1) {
									triangle[i][j] = triangle[i-1][0];
								}
								else {
									triangle[i][j] = triangle[i-1][j-1] +
											triangle[i-1][j];
								}
							}
						}
					}
					for (Integer[] row : triangle) {
						for (Integer col : row) {
							outBuff.append(col).append(" ");
						}
					}
					System.out.println(outBuff.toString());
					elementCount = 1;
				}
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}
