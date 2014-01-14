/**
 * Codeeval Chain Inspection challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;

/**
 * 
 * @author cpvalcourt
 *
 */
public class Main {

	HashMap<String, String> chain;
	int noOfLinks = 0;

	public boolean createChain(String[] links) {
		String[] endPts;

		chain = new HashMap<String, String>(links.length);
		for (String nextLink : links) {
			endPts = nextLink.split("-");
			chain.put(endPts[0], endPts[1]);
		}
		noOfLinks = chain.size();
		return (chain.size() == links.length);
	}

	public boolean validateChain() {
		String curr = "BEGIN";
		String next="";
		for (int i = 0; i < chain.size(); i++) {
			next = chain.get(curr);
			curr = next;
		}
		return (next!= null && next.compareTo("END") == 0);
	}

	public static void main(String[] args) {
		String line;
		String[] links;
		Main x = new Main();

		// Get File
		File file = new File(args[0]);
		BufferedReader in;
		try {
			in = new BufferedReader(new FileReader(file));

			// Read each line into ArrayList
			while ((line = in.readLine()) != null) {
				line.trim();
				if (line.length() > 0) {
					links = line.split(";");
					if (x.createChain(links)) {
						System.out.println(x.validateChain() ? "GOOD" : "BAD");
					}
					else {
						System.out.println("BAD");
					}
				}
			}
			in.close();
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}
