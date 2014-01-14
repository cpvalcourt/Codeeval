
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Main {

	public static void main(String[] args) {
		String line;
		int mthIndex = 0;
		int inLength= 0;
		int lastVal= 0;

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
					String[] lineArray = line.split(" ");
					inLength = lineArray.length - 1;
					lastVal = Integer.parseInt(lineArray[lineArray.length - 1]);
					if ( lastVal> inLength)
						continue;
					mthIndex = inLength - lastVal;
					System.out.println(lineArray[mthIndex]);
				}
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}
