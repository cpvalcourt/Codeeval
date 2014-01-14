

/*
 * Codeeval text to Dollars challenge
 */

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

/**
 * 
 * @author cpvalcourt
 */
public class Main {

	private static Integer dollarAmt;
	int hundredMillion;
	int tenMillion;
	int millions;
	int hundredThousand;
	int tenThousand;
	int thousands;
	int hundreds;
	int tens;
	int ones;

	String words1[] = { "", "One", "Two", "Three", "Four", "Five", "Six",
			"Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
			"Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen",
			"Nineteen" };
	String words2[] = { "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty",
			"Seventy", "Eighty", "Ninety" };

	public Main(int dollars) {
		dollarAmt = dollars;
		tens = 0;
		ones = 0;
	}

	public Main() {
		this(0);
	}

	public String translateToEnglish(int num) {
		if (num > 999999999 || num < 0)
			throw new IllegalArgumentException(
					"Cannot get hundred word of a number not in the range 0-999");
		if (num == 0)
			return "zero";
		hundredMillion = num / 100000000;
		tenMillion = (num % 100000000) / 10000000;
		millions = (num % 10000000) / 1000000;
		hundredThousand = (num % 1000000) / 100000;
		tenThousand = (num % 100000) / 10000;
		thousands = (num % 10000) / 1000;
		hundreds = (num % 1000) / 100;
		tens = (num % 100) / 10;
		ones = num % 10;
		String retstr = "";
		if (hundredMillion > 0) {
			retstr = retstr + words1[hundredMillion] + "Hundred";
			
		} 

		if (hundredMillion != 0 || tenMillion != 0 || millions != 0) {
			if (tenMillion < 2) {
				retstr = retstr + words1[tenMillion * 10 + millions];
			} else {
				retstr = retstr + words2[tenMillion];
				if (millions != 0) {
					retstr = retstr + words1[millions];
				}
			}
			retstr = retstr + "Million";
		}
		
		if (hundredThousand > 0) {
			retstr = retstr + words1[hundredThousand] + "Hundred";	
		} 

		if (hundredThousand != 0 || tenThousand != 0 || thousands != 0) {
			if (tenThousand < 2) {
				retstr = retstr + words1[tenThousand * 10 + thousands];
			} else {
				retstr = retstr + words2[tenThousand];
				if (thousands != 0) {
					retstr = retstr + words1[thousands];
				}
			}
			retstr = retstr + "Thousand";
		}
		if (hundreds > 0) {
			retstr = retstr + words1[hundreds] + "Hundred";			
		} 

		// The rest is simply treating values from zero to nineteen as special,
		// otherwise we treat it as Xty Y (like forty two or seventy seven):

		if (hundreds != 0 || tens != 0 || ones != 0) {
			if (tens < 2) {
				retstr = retstr + words1[tens * 10 + ones];
			} else {
				retstr = retstr + words2[tens];
				if (ones != 0) {
					retstr = retstr + words1[ones];
				}
			}
		}
		/*if (num == 1) {
			return retstr+"Dollar";
		}
		else {
		*/
			return retstr+"Dollars";
		//}
	}

	public String toString() {
		return translateToEnglish(dollarAmt);
	}

	public static void main(String[] args) {
		String line;
		File inFile = new File(args[0]);
		Main next;

		BufferedReader inBuff;
		try {
			inBuff = new BufferedReader(new FileReader(inFile));
			while ((line = inBuff.readLine()) != null) {
				dollarAmt = Integer.parseInt(line.trim());
				next = new Main(dollarAmt);
				System.out.println(next.toString());
			}
			inBuff.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}